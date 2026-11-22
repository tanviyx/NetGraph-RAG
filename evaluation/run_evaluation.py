"""
Collect retrieval candidates for the NetGraph-RAG evaluation dataset.

Run from the project root:
    python -m evaluation.run_evaluation --document-id 0c117748d724721d736a

This script does NOT calculate final Precision/Recall/MRR. The exported candidates
must first be manually judged and relevant chunk IDs recorded as ground truth.
"""

import argparse
import contextlib
import csv
import io
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database.neo4j_client import run_query
from app.retrieval.vector_search import vector_search
from app.retrieval.graph_search import graph_search
from app.retrieval.hybrid_search import reciprocal_rank_fusion


DATASET_PATH = PROJECT_ROOT / "evaluation" / "test_questions.json"
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"


def json_safe(value: Any) -> Any:
    """Convert common non-JSON values into serializable values."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def get_chapter_id(document_id: str, chapter_number: int) -> str:
    query = """
    MATCH (c:Chunk)
    WHERE c.document_id = $document_id
      AND c.chapter_number = $chapter_number
    RETURN DISTINCT c.chapter_id AS chapter_id
    """
    rows = run_query(
        query,
        {"document_id": document_id, "chapter_number": chapter_number},
    )
    chapter_ids = sorted({
        str(row["chapter_id"])
        for row in rows
        if row.get("chapter_id") is not None
    })

    if len(chapter_ids) != 1:
        raise ValueError(
            f"Expected exactly one chapter_id for chapter {chapter_number}; "
            f"found {len(chapter_ids)}: {chapter_ids}"
        )
    return chapter_ids[0]


def run_one_question(question_data: dict, document_id: str, top_k: int) -> dict:
    question_id = question_data["id"]
    chapter_number = int(question_data["chapter_number"])
    question = question_data["question"]
    chapter_id = get_chapter_id(document_id, chapter_number)

    vector_results = []
    graph_results = []
    hybrid_results = []
    errors = []
    graph_status = "not_run"

    vector_start = time.perf_counter()
    try:
        vector_results = vector_search(
            question,
            top_k=top_k,
            document_id=document_id,
            chapter_id=chapter_id,
        )
    except Exception as exc:
        errors.append(f"vector_search: {type(exc).__name__}: {exc}")
    vector_ms = (time.perf_counter() - vector_start) * 1000

    graph_output = io.StringIO()
    graph_start = time.perf_counter()
    try:
        with contextlib.redirect_stdout(graph_output):
            graph_results = graph_search(
                question,
                top_k=top_k,
                document_id=document_id,
                chapter_id=chapter_id,
            )
        captured_output = graph_output.getvalue()
        if "Graph concept extraction unavailable:" in captured_output:
            graph_status = "unavailable"
        elif graph_results:
            graph_status = "ok"
        else:
            graph_status = "no_results"
    except Exception as exc:
        graph_status = "error"
        errors.append(f"graph_search: {type(exc).__name__}: {exc}")
    graph_ms = (time.perf_counter() - graph_start) * 1000

    hybrid_start = time.perf_counter()
    try:
        hybrid_results = reciprocal_rank_fusion(
            vector_results,
            graph_results,
        )[:top_k]
    except Exception as exc:
        errors.append(f"reciprocal_rank_fusion: {type(exc).__name__}: {exc}")
    hybrid_ms = (time.perf_counter() - hybrid_start) * 1000

    return {
        "question_id": question_id,
        "chapter_number": chapter_number,
        "category": question_data.get("category"),
        "question": question,
        "expected_concepts": question_data.get("expected_concepts", []),
        "document_id": document_id,
        "chapter_id": chapter_id,
        "top_k": top_k,
        "graph_status": graph_status,
        "vector_latency_ms": round(vector_ms, 3),
        "graph_latency_ms": round(graph_ms, 3),
        "hybrid_fusion_latency_ms": round(hybrid_ms, 3),
        "hybrid_total_latency_ms": round(vector_ms + graph_ms + hybrid_ms, 3),
        "vector_count": len(vector_results),
        "graph_count": len(graph_results),
        "hybrid_count": len(hybrid_results),
        "vector_results": json_safe(vector_results[:top_k]),
        "graph_results": json_safe(graph_results[:top_k]),
        "hybrid_results": json_safe(hybrid_results),
        "captured_graph_output": graph_output.getvalue().strip(),
        "errors": errors,
    }


def write_csv(rows: list[dict], output_path: Path) -> None:
    columns = [
        "question_id", "chapter_number", "category", "question",
        "method", "rank", "chunk_id", "score", "section",
        "subsection", "start_pdf_page", "end_pdf_page",
        "start_printed_page", "end_printed_page", "text",
        "graph_status", "latency_ms",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()

        for row in rows:
            methods = [
                ("vector", row["vector_results"], row["vector_latency_ms"]),
                ("graph", row["graph_results"], row["graph_latency_ms"]),
                ("hybrid", row["hybrid_results"], row["hybrid_total_latency_ms"]),
            ]
            for method, results, latency in methods:
                for rank, item in enumerate(results, start=1):
                    writer.writerow({
                        "question_id": row["question_id"],
                        "chapter_number": row["chapter_number"],
                        "category": row["category"],
                        "question": row["question"],
                        "method": method,
                        "rank": rank,
                        "chunk_id": item.get("id"),
                        "score": item.get("score", item.get("rrf_score")),
                        "section": item.get("section"),
                        "subsection": item.get("subsection"),
                        "start_pdf_page": item.get("start_pdf_page"),
                        "end_pdf_page": item.get("end_pdf_page"),
                        "start_printed_page": item.get("start_printed_page"),
                        "end_printed_page": item.get("end_printed_page"),
                        "text": item.get("text"),
                        "graph_status": row["graph_status"],
                        "latency_ms": latency,
                    })


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export vector, graph, and hybrid retrieval candidates."
    )
    parser.add_argument(
        "--document-id",
        required=True,
        help="Neo4j document_id for the textbook to evaluate.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of candidates to retain per retrieval method (default: 5).",
    )
    parser.add_argument(
        "--chapters",
        type=int,
        nargs="*",
        help="Optional chapter numbers to run, e.g. --chapters 1 2 3. "
             "By default, all dataset questions are run.",
    )
    args = parser.parse_args()

    if args.top_k < 1:
        parser.error("--top-k must be at least 1")

    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        dataset = json.load(handle)

    questions = dataset["questions"]
    if args.chapters:
        selected = set(args.chapters)
        questions = [
            item for item in questions
            if int(item["chapter_number"]) in selected
        ]

    if not questions:
        raise SystemExit("No questions selected. Check --chapters.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"retrieval_candidates_{timestamp}"
    json_path = RESULTS_DIR / f"{stem}.json"
    csv_path = RESULTS_DIR / f"{stem}.csv"

    results = []
    total = len(questions)

    print(f"Document ID: {args.document_id}")
    print(f"Questions: {total}")
    print(f"Top-k: {args.top_k}")
    print("-" * 60)

    for index, question_data in enumerate(questions, start=1):
        qid = question_data.get("id", f"question_{index}")
        print(f"[{index}/{total}] Running {qid} (chapter {question_data['chapter_number']})")
        try:
            result = run_one_question(question_data, args.document_id, args.top_k)
        except Exception as exc:
            result = {
                "question_id": qid,
                "chapter_number": question_data.get("chapter_number"),
                "category": question_data.get("category"),
                "question": question_data.get("question"),
                "document_id": args.document_id,
                "graph_status": "not_evaluated",
                "errors": [f"{type(exc).__name__}: {exc}"],
                "vector_results": [],
                "graph_results": [],
                "hybrid_results": [],
                "vector_latency_ms": 0,
                "graph_latency_ms": 0,
                "hybrid_fusion_latency_ms": 0,
                "hybrid_total_latency_ms": 0,
            }

        results.append(result)
        print(
            f"  vector={result.get('vector_count', 0)}, "
            f"graph={result.get('graph_count', 0)}, "
            f"hybrid={result.get('hybrid_count', 0)}, "
            f"graph_status={result.get('graph_status')}"
        )
        if result.get("errors"):
            for error in result["errors"]:
                print(f"  ERROR: {error}")

    output = {
        "dataset_name": dataset.get("dataset_name"),
        "document_id": args.document_id,
        "top_k": args.top_k,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "note": (
            "These are retrieval candidates, not relevance labels. "
            "Manually judge relevant chunk IDs before calculating final "
            "Precision@K, Recall@K, or MRR. expected_concepts are guidance only."
        ),
        "results": results,
    }

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(json_safe(output), handle, ensure_ascii=False, indent=2)

    write_csv(results, csv_path)

    successful_graph = sum(r.get("graph_status") == "ok" for r in results)
    unavailable_graph = sum(
        r.get("graph_status") in {"unavailable", "error"}
        for r in results
    )

    print("-" * 60)
    print("Candidate collection complete.")
    print(f"Graph search returned results for {successful_graph}/{len(results)} questions.")
    print(f"Graph search unavailable/errored for {unavailable_graph}/{len(results)} questions.")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    print("Do not calculate final retrieval metrics until relevant chunk IDs are manually labelled.")


if __name__ == "__main__":
    main()
