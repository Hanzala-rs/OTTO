"""
RAGAS offline evaluation helper.
Call evaluate_sample() from the /evals scripts, not from the request path.
"""
from __future__ import annotations
from typing import List


def evaluate_sample(
    questions: List[str],
    answers: List[str],
    contexts: List[List[str]],
    ground_truths: List[str],
) -> dict:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_recall

    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }
    dataset = Dataset.from_dict(data)
    result = evaluate(dataset, metrics=[faithfulness, answer_relevancy, context_recall])
    return result.to_pandas().to_dict()
