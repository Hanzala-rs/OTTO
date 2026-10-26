"""
Query engine — applies HyDE (Hypothetical Document Embeddings) before retrieval.
Generates a fake answer, embeds it, and uses that embedding to search Qdrant.
This significantly improves recall for Urdu queries.
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

import re

from config.prompts import HYDE_PROMPT, TRANSLATE_PROMPT
from config.settings import get_settings
from rag.llm_client import get_llm

_URDU_SCRIPT = re.compile(r"[؀-ۿ]")


def to_search_query(query: str) -> str:
    """Corpus, keyword fallback and reranker are English-only — translate Urdu-script queries."""
    if not _URDU_SCRIPT.search(query):
        return query
    llm = get_llm(get_settings().llm_voice_model)
    chain = PromptTemplate.from_template(TRANSLATE_PROMPT) | llm | StrOutputParser()
    return chain.invoke({"query": query}).strip() or query


def build_hyde_query(query: str) -> str:
    """Generate a hypothetical answer and return it as the search query."""
    llm = get_llm()
    prompt = PromptTemplate.from_template(HYDE_PROMPT)
    chain = prompt | llm | StrOutputParser()
    hypothetical = chain.invoke({"query": query})
    # Combine original query + hypothetical for richer embedding
    return f"{query}\n\n{hypothetical}"
