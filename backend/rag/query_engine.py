"""
Query engine — applies HyDE (Hypothetical Document Embeddings) before retrieval.
Generates a fake answer, embeds it, and uses that embedding to search Qdrant.
This significantly improves recall for Urdu queries.
"""
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from config.prompts import HYDE_PROMPT, TRANSLATE_PROMPT
from config.settings import get_settings
from rag.llm_client import get_llm


_FIELD = re.compile(r"^\s*(LANGUAGE|QUERY)\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def rewrite_query(query: str, fast: bool = False) -> tuple[str, str | None]:
    """Corpus, keyword fallback and reranker are English-only — rewrite every query
    (Urdu, Roman Urdu, slang, typos) as a clean English search query, and detect the
    language the user wrote in. Returns (search_query, language or None).
    The main model is used unless `fast` (voice): the fast one mislabels languages
    and drops product names."""
    llm = get_llm(get_settings().llm_voice_model if fast else None)
    chain = PromptTemplate.from_template(TRANSLATE_PROMPT) | llm | StrOutputParser()
    output = chain.invoke({"query": query})
    fields = {k.upper(): v for k, v in _FIELD.findall(output)}
    return fields.get("QUERY") or query, fields.get("LANGUAGE")


def build_hyde_query(query: str) -> str:
    """Generate a hypothetical answer and return it as the search query."""
    # Fast model: the text is only embedded, and it keeps the main model's token budget for answers
    llm = get_llm(get_settings().llm_voice_model)
    prompt = PromptTemplate.from_template(HYDE_PROMPT)
    chain = prompt | llm | StrOutputParser()
    hypothetical = chain.invoke({"query": query})
    # Combine original query + hypothetical for richer embedding
    return f"{query}\n\n{hypothetical}"
