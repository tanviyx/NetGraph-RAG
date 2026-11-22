
import json
import re

from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.database.neo4j_client import run_query


def extract_query_concepts(query):
    """Extract specific technical concepts from a user's question."""

    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing from .env")

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0
    )

    prompt = f"""
Extract the specific technical concepts that are central to answering
this computer networking question.

Return ONLY valid JSON:
{{
    "concepts": ["LAN", "WAN"]
}}

Rules:
- Extract 2 to 6 concepts when appropriate.
- Prefer specific concepts explicitly asked about.
- Do not add broad parent concepts when specific concepts are present.
- Do not include generic words or question phrases.
- Use standard textbook terminology.
- Do not invent concepts.

Question: {query}
"""

    response = llm.invoke(prompt)
    content = response.content.strip()

    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    start = content.find("{")

    if start == -1:
        raise ValueError("No JSON object found in response.")

    data, _ = json.JSONDecoder().raw_decode(content[start:])

    concepts = data.get("concepts", [])

    return list(dict.fromkeys(
        str(item).strip()
        for item in concepts
        if str(item).strip()
    ))


def graph_search(
    query: str,
    top_k: int = 5,
    document_id: str | None = None,
    chapter_id: str | None = None
):
    """Retrieve directly mentioned and graph-related textbook chunks."""

    try:
        concepts = extract_query_concepts(query)
    except Exception as exc:
        print(f"Graph concept extraction unavailable: {exc}")
        return []

    if not concepts:
        return []

    print("Graph search concepts:", concepts)

    parameters = {
        "terms": concepts,
        "k": top_k,
        "document_id": document_id,
        "chapter_id": chapter_id
    }

    direct_query = """
    MATCH (e:Concept)
    WHERE any(
        term IN $terms
        WHERE toLower(e.name) = toLower(term)
    )

    MATCH (e)<-[:MENTIONS]-(c:Chunk)

    WHERE
        ($document_id IS NULL OR c.document_id = $document_id)
        AND
        ($chapter_id IS NULL OR c.chapter_id = $chapter_id)

    WITH c, count(DISTINCT e) AS matched_concepts

    RETURN
        c.id AS id,
        c.text AS text,
        toFloat(matched_concepts) AS score,
        c.document_id AS document_id,
        c.chapter_id AS chapter_id,
        c.chapter_number AS chapter_number,
        c.chapter_title AS chapter_title,
        c.section AS section,
        c.subsection AS subsection,
        c.start_pdf_page AS start_pdf_page,
        c.end_pdf_page AS end_pdf_page,
        c.start_printed_page AS start_printed_page,
        c.end_printed_page AS end_printed_page

    ORDER BY score DESC
    LIMIT $k
    """

    related_query = """
    MATCH (e:Concept)
    WHERE any(
        term IN $terms
        WHERE toLower(e.name) = toLower(term)
    )

    MATCH (e)-[:RELATED_TO]-(related:Concept)
    MATCH (related)<-[:MENTIONS]-(c:Chunk)

    WHERE
        ($document_id IS NULL OR c.document_id = $document_id)
        AND
        ($chapter_id IS NULL OR c.chapter_id = $chapter_id)

    WITH c, count(DISTINCT related) AS related_matches

    RETURN
        c.id AS id,
        c.text AS text,
        0.5 + 0.1 * toFloat(related_matches) AS score,
        c.document_id AS document_id,
        c.chapter_id AS chapter_id,
        c.chapter_number AS chapter_number,
        c.chapter_title AS chapter_title,
        c.section AS section,
        c.subsection AS subsection,
        c.start_pdf_page AS start_pdf_page,
        c.end_pdf_page AS end_pdf_page,
        c.start_printed_page AS start_printed_page,
        c.end_printed_page AS end_printed_page

    ORDER BY score DESC
    LIMIT $k
    """

    direct_results = [
        dict(record)
        for record in run_query(direct_query, parameters)
    ]

    related_results = [
        dict(record)
        for record in run_query(related_query, parameters)
    ]

    combined = {}

    for result in direct_results + related_results:

        chunk_id = result["id"]

        if (
            chunk_id not in combined
            or result["score"] > combined[chunk_id]["score"]
        ):
            combined[chunk_id] = result

    return sorted(
        combined.values(),
        key=lambda item: item["score"],
        reverse=True
    )[:top_k]
