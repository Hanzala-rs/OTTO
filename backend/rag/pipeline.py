"""
LangGraph RAG pipeline.

State machine nodes:
  guardrails → query_engine (HyDE) → retriever → reranker → llm → output_guard
Voice path inserts stt before guardrails and tts after output_guard.
"""
from __future__ import annotations
from typing import TypedDict, Optional, List, Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from config.prompts import RAG_SYSTEM_PROMPT
from config.settings import get_settings
from rag.llm_client import get_llm
from rag.query_engine import build_hyde_query
from rag.retriever import get_retriever
from rag.reranker import get_reranker
from memory.message_history import get_history


# ── State ─────────────────────────────────────────────────────────────────────

class RAGState(TypedDict):
    session_id: str
    query: str
    language: str
    is_voice: bool
    audio_bytes: Optional[bytes]
    transcript: Optional[str]
    hyde_query: Optional[str]
    retrieved_chunks: Optional[List[dict]]
    reranked_chunks: Optional[List[dict]]
    context: Optional[str]
    response: Optional[str]
    audio_response: Optional[bytes]
    error: Optional[str]


# ── Nodes ─────────────────────────────────────────────────────────────────────

def guardrails_node(state: RAGState) -> RAGState:
    """Basic input guardrails: length check, injection patterns."""
    query = state["query"] or state.get("transcript", "")
    if not query or len(query.strip()) < 2:
        return {**state, "error": "empty_query"}
    if len(query) > 2000:
        return {**state, "error": "query_too_long"}
    # Naive injection check
    injection_patterns = ["ignore previous", "ignore all", "system:", "###"]
    lower = query.lower()
    if any(p in lower for p in injection_patterns):
        return {**state, "error": "injection_detected"}
    return {**state, "query": query}


def hyde_node(state: RAGState) -> RAGState:
    if state.get("error"):
        return state
    try:
        hyde_query = build_hyde_query(state["query"])
    except Exception as exc:
        logger.warning(f"HyDE failed, falling back to raw query: {exc}")
        hyde_query = state["query"]
    return {**state, "hyde_query": hyde_query}


def retriever_node(state: RAGState) -> RAGState:
    if state.get("error"):
        return state
    retriever = get_retriever()
    chunks = retriever.retrieve(
        query=state["hyde_query"] or state["query"],
        lang=state["language"],
    )
    return {**state, "retrieved_chunks": chunks}


def reranker_node(state: RAGState) -> RAGState:
    if state.get("error"):
        return state
    reranker = get_reranker()
    retriever = get_retriever()
    chunks = state["retrieved_chunks"] or []

    reranked = reranker.rerank(state["query"], chunks)

    # Promote child chunks → fetch their parent for richer LLM context
    enriched = []
    for chunk in reranked:
        if chunk.get("parent_id"):
            parent_text = retriever.fetch_parent(chunk["parent_id"])
            if parent_text:
                chunk = {**chunk, "text": parent_text}
        enriched.append(chunk)

    context = "\n\n---\n\n".join(c["text"] for c in enriched)
    return {**state, "reranked_chunks": enriched, "context": context}


def llm_node(state: RAGState) -> RAGState:
    if state.get("error"):
        return state

    llm = get_llm()
    history = get_history(state["session_id"])
    messages = history.get_messages()

    prompt = ChatPromptTemplate.from_messages([
        ("system", RAG_SYSTEM_PROMPT),
        *[(m.type, m.content) for m in messages],
        ("human", "{query}"),
    ])

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({
        "context": state.get("context", "No relevant context found."),
        "query": state["query"],
    })

    # Persist to session history
    history.add_message(HumanMessage(content=state["query"]))
    history.add_message(AIMessage(content=response))

    return {**state, "response": response}


def output_guard_node(state: RAGState) -> RAGState:
    return state


def error_node(state: RAGState) -> RAGState:
    error_messages = {
        "empty_query": "Please type a message.",
        "query_too_long": "Your message is too long. Please shorten it.",
        "injection_detected": "Invalid input detected.",
    }
    msg = error_messages.get(state.get("error", ""), "Something went wrong.")
    return {**state, "response": msg}


# ── Graph ─────────────────────────────────────────────────────────────────────

def _route_after_guardrails(state: RAGState) -> str:
    return "error" if state.get("error") else "hyde"


def build_rag_graph() -> Any:
    graph = StateGraph(RAGState)

    graph.add_node("guardrails", guardrails_node)
    graph.add_node("hyde", hyde_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("reranker", reranker_node)
    graph.add_node("llm", llm_node)
    graph.add_node("output_guard", output_guard_node)
    graph.add_node("handle_error", error_node)

    graph.set_entry_point("guardrails")
    graph.add_conditional_edges("guardrails", _route_after_guardrails, {
        "hyde": "hyde",
        "error": "handle_error",
    })
    graph.add_edge("hyde", "retriever")
    graph.add_edge("retriever", "reranker")
    graph.add_edge("reranker", "llm")
    graph.add_edge("llm", "output_guard")
    graph.add_edge("output_guard", END)
    graph.add_edge("handle_error", END)

    return graph.compile()


# Singleton compiled graph
_graph = None

def get_rag_graph():
    global _graph
    if _graph is None:
        _graph = build_rag_graph()
    return _graph
