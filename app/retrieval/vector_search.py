
from app.ingestion.embedding_generator import embed_texts
from app.database.neo4j_client import run_query


def vector_search(
    query: str,
    top_k: int = 5,
    document_id: str | None = None,
    chapter_id: str | None = None
):
    query_embedding = embed_texts([query])[0]

    # Retrieve a larger candidate pool before applying scope filters.
    candidate_k = max(top_k * 20, 100)

    cypher = """
    CALL db.index.vector.queryNodes(
        'chunk_embedding', $candidate_k, $embedding
    )
    YIELD node, score

    WHERE
        ($document_id IS NULL OR node.document_id = $document_id)
        AND
        ($chapter_id IS NULL OR node.chapter_id = $chapter_id)

    RETURN
        node.id AS id,
        node.text AS text,
        score,
        node.document_id AS document_id,
        node.chapter_id AS chapter_id,
        node.chapter_number AS chapter_number,
        node.chapter_title AS chapter_title,
        node.section AS section,
        node.subsection AS subsection,
        node.start_pdf_page AS start_pdf_page,
        node.end_pdf_page AS end_pdf_page,
        node.start_printed_page AS start_printed_page,
        node.end_printed_page AS end_printed_page

    ORDER BY score DESC
    LIMIT $top_k
    """

    results = run_query(cypher, {
        "candidate_k": candidate_k,
        "top_k": top_k,
        "embedding": query_embedding,
        "document_id": document_id,
        "chapter_id": chapter_id
    })

    return [dict(record) for record in results]
