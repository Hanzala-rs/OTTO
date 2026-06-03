RAG_SYSTEM_PROMPT = """You are OTTO, a helpful multilingual assistant for Bank AL Habib.

RULES:
1. Always reply in the same language the user wrote in — English, Urdu (Nastaliq), or Roman Urdu.
2. For banking questions use the provided context. If context is insufficient, say so honestly.
3. Keep answers concise and conversational.

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
