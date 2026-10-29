"""
LangGraph RAG pipeline.

State machine nodes:
  guardrails → query_engine (HyDE) → retriever → reranker → llm → output_guard
Voice path inserts stt before guardrails and tts after output_guard.
"""
from __future__ import annotations
import re
from typing import TypedDict, Optional, List, Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from config.prompts import RAG_SYSTEM_PROMPT
from config.settings import get_settings
from rag.llm_client import get_llm
from rag.query_engine import build_hyde_query, rewrite_query
from rag.retriever import get_retriever
from rag.reranker import get_reranker
from memory.message_history import get_history
from voice.language_router import reply_language


# ── State ─────────────────────────────────────────────────────────────────────

class RAGState(TypedDict):
    session_id: str
    query: str
    language: str
    is_voice: bool
    audio_bytes: Optional[bytes]
    transcript: Optional[str]
    hyde_query: Optional[str]
    search_query: Optional[str]   # English form of query used for retrieval/rerank
    query_language: Optional[str]  # language the user wrote in, detected by the rewrite LLM
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
    injection_patterns = [
        "ignore previous", "ignore all", "ignore above", "ignore instructions",
        "system:", "system prompt", "###", "<<<", ">>>",
        "you are now", "act as", "pretend to be", "forget everything",
        "new instruction", "override", "jailbreak", "dan mode",
    ]
    lower = query.lower()
    if any(p in lower for p in injection_patterns):
        return {**state, "error": "injection_detected"}
    return {**state, "query": query}


def hyde_node(state: RAGState) -> RAGState:
    if state.get("error"):
        return state
    try:
        search_query, query_language = rewrite_query(state["query"], fast=bool(state.get("is_voice")))
    except Exception as exc:
        # Usually the main model's Groq quota; a fast-model rewrite beats searching
        # with the raw (often non-English) query
        logger.warning(f"Query rewrite failed, retrying on fast model: {exc}")
        try:
            search_query, query_language = rewrite_query(state["query"], fast=True)
        except Exception as exc2:
            logger.warning(f"Query rewrite failed, using raw query: {exc2}")
            search_query, query_language = state["query"], None
    state = {**state, "search_query": search_query, "query_language": query_language}
    # Voice skips HyDE to save one LLM round-trip
    if state.get("is_voice"):
        return {**state, "hyde_query": None}
    try:
        hyde_query = build_hyde_query(search_query)
    except Exception as exc:
        logger.warning(f"HyDE failed, falling back to raw query: {exc}")
        hyde_query = search_query
    return {**state, "hyde_query": hyde_query}


def retriever_node(state: RAGState) -> RAGState:
    if state.get("error"):
        return state
    retriever = get_retriever()
    query = state["hyde_query"] or state.get("search_query") or state["query"]
    if state["query"] not in query:
        # Original wording too: the rewrite can translate a product name away.
        # Appended, since the keyword search reads only the first line.
        query = f"{query}\n{state['query']}"
    chunks = retriever.retrieve(query=query, lang=state["language"])
    return {**state, "retrieved_chunks": chunks}


PARENT_WINDOW_CHARS = 600   # parent text kept on each side of the matched child
MAX_CHUNK_CHARS = 1500      # cap for chunks without a locatable child
# Markdown table separator row (| :--- | --- |); stored chunk text has newlines flattened
_TABLE_SEPARATOR = re.compile(r"(?:\|\s*:?-{3,}:?\s*)+\|")
_NON_TABLE_TEXT = re.compile(r"[^|]{300,}")


def _table_header(text: str, start: int) -> str | None:
    """Header row of the table that `start` falls inside, or None."""
    sep = None
    for sep in _TABLE_SEPARATOR.finditer(text, 0, start):
        pass
    if not sep or _NON_TABLE_TEXT.search(text, sep.end(), start):
        return None   # no table before start, or it ended before start
    ncols = sep.group(0).count("|") - 1
    cells = text[:sep.start()].rstrip().split("|")[-(ncols + 1):-1]
    if len(cells) != ncols:
        return None
    return "| " + " | ".join(c.strip() for c in cells) + " |"


def _parent_window(chunk: dict, parent: str | None) -> str:
    """Matched child plus surrounding parent text: keeps the answer, limits tokens
    (Groq free tier allows 8k tokens/minute; full parents cost ~4.5k per answer)."""
    # Keyword hits carry the passage that matched; centre the window on it
    matched = chunk.get("rerank_text") or chunk["text"]
    if not parent:
        if not chunk.get("rerank_text"):
            return chunk["text"][:MAX_CHUNK_CHARS]
        parent = chunk["text"]
    pos = parent.find(matched[:200])
    if pos < 0:
        return parent[:MAX_CHUNK_CHARS]
    start = max(0, pos - PARENT_WINDOW_CHARS)
    window = parent[start: pos + len(matched) + PARENT_WINDOW_CHARS]
    # Keep the header of a table the window starts inside, so column meaning
    # (e.g. previous vs revised charges) isn't lost
    header = _table_header(parent, start)
    return f"{header}\n{window}" if header else window


def reranker_node(state: RAGState) -> RAGState:
    if state.get("error"):
        return state
    reranker = get_reranker()
    retriever = get_retriever()
    chunks = state["retrieved_chunks"] or []

    reranked = reranker.rerank(state.get("search_query") or state["query"], chunks)

    # Promote child chunks → fetch their parent for richer LLM context
    parents = retriever.fetch_parents(
        list({c["parent_id"] for c in reranked if c.get("parent_id")})
    )
    enriched = [{**c, "text": _parent_window(c, parents.get(c.get("parent_id")))} for c in reranked]
    context = "\n\n---\n\n".join(f"[Source: {c.get('source') or 'unknown'}]\n{c['text']}" for c in enriched)
    return {**state, "reranked_chunks": enriched, "context": context}


def llm_node(state: RAGState) -> RAGState:
    if state.get("error"):
        return state

    try:
        history = get_history(state["session_id"])
        messages = history.get_messages()

        prompt = ChatPromptTemplate.from_messages([
            ("system", RAG_SYSTEM_PROMPT),
            *[(m.type, m.content) for m in messages],
            ("human", "{query}"),
        ])
        inputs = {
            "context": state.get("context", "No relevant context found."),
            "query": state["query"],
            "reply_language": reply_language(state.get("query_language"), state["query"]),
        }

        fast_model = get_settings().llm_voice_model
        try:
            llm = get_llm(fast_model if state.get("is_voice") else None)
            response = (prompt | llm | StrOutputParser()).invoke(inputs)
        except Exception as exc:
            if state.get("is_voice"):
                raise
            # Main model rate-limited/timed out: answer with the fast model instead of failing
            logger.warning(f"Main LLM failed, retrying on fast model: {exc}")
            response = (prompt | get_llm(fast_model) | StrOutputParser()).invoke(inputs)

        history.add_message(HumanMessage(content=state["query"]))
        history.add_message(AIMessage(content=response))

        return {**state, "response": response}

    except Exception as exc:
        logger.error(f"LLM node failed: {exc}")
        return {**state, "response": "I'm having trouble connecting right now. Please try again in a moment."}


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
