"""
Query engine — applies HyDE (Hypothetical Document Embeddings) before retrieval.
Generates a fake answer, embeds it, and uses that embedding to search Qdrant.
This significantly improves recall for Urdu queries.
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from config.prompts import HYDE_PROMPT
from rag.llm_client import get_llm


def build_hyde_query(query: str) -> str:
    """Generate a hypothetical answer and return it as the search query."""
    llm = get_llm()
    prompt = PromptTemplate.from_template(HYDE_PROMPT)
    chain = prompt | llm | StrOutputParser()
    hypothetical = chain.invoke({"query": query})
    # Combine original query + hypothetical for richer embedding
    return f"{query}\n\n{hypothetical}"
