
from app.retrieval.vector_search import vector_search
from app.retrieval.graph_search import graph_search


def reciprocal_rank_fusion(
    vector_results,
    graph_results,
    k=60
):
    scores = {}
    docs = {}

    for result_list in (vector_results, graph_results):

        for rank, item in enumerate(result_list, start=1):

            doc_id = item["id"]

            scores[doc_id] = (
                scores.get(doc_id, 0.0)
                + 1.0 / (k + rank)
            )

            docs[doc_id] = item

    return sorted(
        [
            {
                **docs[key],
                "rrf_score": score
            }
            for key, score in scores.items()
        ],
        key=lambda item: item["rrf_score"],
        reverse=True
    )


def hybrid_search(
    query: str,
    top_k: int = 5,
    document_id: str | None = None,
    chapter_id: str | None = None
):
    vector_results = vector_search(
        query=query,
        top_k=top_k,
        document_id=document_id,
        chapter_id=chapter_id
    )

    graph_results = graph_search(
        query=query,
        top_k=top_k,
        document_id=document_id,
        chapter_id=chapter_id
    )

    return reciprocal_rank_fusion(
        vector_results,
        graph_results
    )[:top_k]
