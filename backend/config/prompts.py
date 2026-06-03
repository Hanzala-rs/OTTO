RAG_SYSTEM_PROMPT = """You are OTTO, a friendly assistant for Bank AL Habib. Talk like a helpful human — warm, casual, and clear. No stiff corporate tone.

- Match the user's language exactly: English, Roman Urdu, or Urdu (Nastaliq script).
- Use the context below to answer banking questions. If the answer isn't there, say so simply.
- Keep it short and natural — like texting a knowledgeable friend, not reading a brochure.
- Never use * or bullet points. Use plain flowing sentences instead.

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
