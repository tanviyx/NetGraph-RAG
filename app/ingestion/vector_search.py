
from app.ingestion.embedding_generator import embed_texts
from app.database.neo4j_client import run_query


def vector_search(query: str, top_k: int = 5):
    """
    Search textbook chunks using semantic similarity.
    Returns text, scores, and source metadata.
    """

    query_embedding = embed_texts([query])[0]

    cypher = """
    CALL db.index.vector.queryNodes(
        'chunk_embedding',
        $top_k,
        $embedding
    )
    YIELD node, score

    RETURN
        node.id AS id,
        node.text AS text,
        score,
        node.chapter_number AS chapter_number,
        node.chapter_title AS chapter_title,
        node.section AS section,
        node.subsection AS subsection,
        node.start_pdf_page AS start_pdf_page,
        node.end_pdf_page AS end_pdf_page,
        node.start_printed_page AS start_printed_page,
        node.end_printed_page AS end_printed_page

    ORDER BY score DESC
    """

    results = run_query(
        cypher,
        {
            "top_k": top_k,
            "embedding": query_embedding
        }
    )

    return [dict(record) for record in results]
