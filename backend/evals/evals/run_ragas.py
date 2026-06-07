"""
Offline RAGAS evaluation script.
Usage: python evals/run_ragas.py --lang en
       python evals/run_ragas.py --lang ur
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, "/app")  # inside Docker the backend is mounted at /app

from rag.pipeline import get_rag_graph
from voice.language_router import detect_lang


def run_eval(lang: str) -> None:
    dataset_path = Path(__file__).parent / f"test_dataset_{lang}.json"
    with open(dataset_path) as f:
        dataset = json.load(f)

    graph = get_rag_graph()
    questions, answers, contexts, ground_truths = [], [], [], []

    for item in dataset:
        result = graph.invoke({
            "session_id": "eval",
            "query": item["question"],
            "language": lang,
            "is_voice": False,
            "audio_bytes": None,
            "transcript": None,
            "hyde_query": None,
            "retrieved_chunks": None,
            "reranked_chunks": None,
            "context": None,
            "response": None,
            "audio_response": None,
            "error": None,
        })

        questions.append(item["question"])
        answers.append(result.get("response", ""))
        ctx = [c["text"] for c in (result.get("reranked_chunks") or [])]
        contexts.append(ctx)
        ground_truths.append(item["ground_truth"])
        print(f"Q: {item['question'][:60]}... → {result.get('response', '')[:80]}...")

    from monitoring.ragas_evaluator import evaluate_sample
    scores = evaluate_sample(questions, answers, contexts, ground_truths)

    output_path = Path(__file__).parent / "results" / f"ragas_{lang}.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(scores, f, indent=2, default=str)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=["en", "ur"], default="en")
    args = parser.parse_args()
    run_eval(args.lang)
