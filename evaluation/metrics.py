"""Retrieval evaluation metrics for NetGraph-RAG.

Ground-truth relevance must be supplied as chunk IDs for each question.
The expected_concepts field in test_questions.json is not ground truth.
"""

from statistics import mean
from typing import Any, Iterable


def _result_id(item: Any) -> str:
    """Accept either a chunk ID string or a retrieval result dictionary."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        value = item.get("id")
        return str(value) if value is not None else ""
    raise TypeError("Retrieved items must be chunk ID strings or dictionaries.")


def precision_at_k(
    retrieved: Iterable[Any],
    relevant_ids: Iterable[str],
    k: int = 5,
) -> float:
    """Fraction of the first k retrieved chunks that are relevant."""
    if k <= 0:
        raise ValueError("k must be greater than zero.")

    retrieved_ids = [_result_id(item) for item in retrieved][:k]
    if not retrieved_ids:
        return 0.0

    relevant = {str(item) for item in relevant_ids}
    hits = sum(1 for chunk_id in retrieved_ids if chunk_id in relevant)
    return hits / len(retrieved_ids)


def recall_at_k(
    retrieved: Iterable[Any],
    relevant_ids: Iterable[str],
    k: int = 5,
) -> float:
    """Fraction of all known relevant chunks found in the first k results."""
    if k <= 0:
        raise ValueError("k must be greater than zero.")

    relevant = {str(item) for item in relevant_ids}
    if not relevant:
        return 0.0

    retrieved_ids = [_result_id(item) for item in retrieved][:k]
    hits = len(set(retrieved_ids) & relevant)
    return hits / len(relevant)


def reciprocal_rank(
    retrieved: Iterable[Any],
    relevant_ids: Iterable[str],
) -> float:
    """Reciprocal rank of the first relevant result; zero if none is found."""
    relevant = {str(item) for item in relevant_ids}

    for rank, item in enumerate(retrieved, start=1):
        if _result_id(item) in relevant:
            return 1.0 / rank

    return 0.0


def evaluate_retrieval(
    retrieved: Iterable[Any],
    relevant_ids: Iterable[str],
    k: int = 5,
    latency_ms: float | None = None,
) -> dict[str, float | int | None]:
    """Calculate metrics for one retrieval run."""
    retrieved_list = list(retrieved)
    relevant_list = list(relevant_ids)

    return {
        f"precision@{k}": precision_at_k(retrieved_list, relevant_list, k),
        f"recall@{k}": recall_at_k(retrieved_list, relevant_list, k),
        "mrr": reciprocal_rank(retrieved_list, relevant_list),
        "latency_ms": round(float(latency_ms), 3)
        if latency_ms is not None
        else None,
        "retrieved_count": len(retrieved_list),
        "relevant_count": len(set(str(item) for item in relevant_list)),
    }


def aggregate_metrics(
    rows: Iterable[dict[str, Any]],
    k: int = 5,
) -> dict[str, float | int]:
    """Average metrics across questions, excluding missing latency values."""
    rows = list(rows)
    if not rows:
        return {
            "question_count": 0,
            f"mean_precision@{k}": 0.0,
            f"mean_recall@{k}": 0.0,
            "mean_mrr": 0.0,
            "mean_latency_ms": 0.0,
        }

    latency_values = [
        float(row["latency_ms"])
        for row in rows
        if row.get("latency_ms") is not None
    ]

    return {
        "question_count": len(rows),
        f"mean_precision@{k}": round(
            mean(float(row[f"precision@{k}"]) for row in rows), 4
        ),
        f"mean_recall@{k}": round(
            mean(float(row[f"recall@{k}"]) for row in rows), 4
        ),
        "mean_mrr": round(mean(float(row["mrr"]) for row in rows), 4),
        "mean_latency_ms": round(mean(latency_values), 3)
        if latency_values
        else 0.0,
    }
