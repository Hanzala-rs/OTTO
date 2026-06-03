RAG_SYSTEM_PROMPT = """You are OTTO, a friendly assistant for Bank AL Habib.

Reply in the same language and script the user used. Be warm, natural and concise — like a knowledgeable friend, not a brochure. Use the context to answer; if it's not there, say so honestly.

Context:
{context}
"""

HYDE_PROMPT = """Generate a short hypothetical document that would answer the following question.
Write in the same language as the question. Be concise (2-3 sentences max).

Question: {query}
Hypothetical answer:"""

LANGUAGE_GUARD_PROMPT = """Check if the following response is in the correct language.
Expected language: {expected_lang}
Response: {response}

If the response is NOT in the expected language, rewrite it correctly.
If it IS correct, return it unchanged."""
