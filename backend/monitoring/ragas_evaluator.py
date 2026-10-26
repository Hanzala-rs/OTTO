"""
RAGAS offline evaluation helper.
Call evaluate_sample() from the /evals scripts, not from the request path.

Judged with the project's own Groq LLM + embedding model rather than RAGAS's
OpenAI default, since no OPENAI_API_KEY is configured anywhere in this project.
"""
from __future__ import annotations
from functools import lru_cache
from typing import List


@lru_cache
def _judge_llm():
    from ragas.llms import LangchainLLMWrapper
    from rag.llm_client import get_llm
    return LangchainLLMWrapper(get_llm())


@lru_cache
def _judge_embeddings():
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from config.settings import get_settings
    return LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=get_settings().embedding_model))


def evaluate_sample(
    questions: List[str],
    answers: List[str],
    contexts: List[List[str]],
    ground_truths: List[str],
) -> dict:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_recall
    from ragas.run_config import RunConfig

    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
    dataset = Dataset.from_dict(data)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall],
        llm=_judge_llm(),
        embeddings=_judge_embeddings(),
        # Judge calls share the same 0.4 req/s Groq rate limiter as live traffic
        # (rag/llm_client.py) — low concurrency + a long per-job timeout lets
        # jobs queue behind it instead of hitting RAGAS's default 180s timeout.
        run_config=RunConfig(timeout=900, max_workers=2),
    )
    return result.to_pandas().to_dict()
