from pathlib import Path
from app.database.neo4j_client import run_query, ensure_schema
from app.graph.concept_extractor import extract_concepts


def get_chapter_chunks(chapter_number):
    """Fetch previously stored chunks for a chapter from Neo4j."""

    query = """
    MATCH (c:Chunk)
    WHERE c.chapter_number = $chapter_number
    RETURN c.id AS id, c.text AS text
    ORDER BY c.id
    """

    results = run_query(query, {"chapter_number": chapter_number})

    return [dict(record) for record in results]


def store_extracted_graph(extraction_results):
    """Store concepts, chunk mentions, and concept relationships."""

    concept_rows = []
    relationship_rows = []

    for result in extraction_results:
        chunk_id = result["chunk_id"]

        for concept in result.get("concepts", []):
            concept_rows.append({
                "chunk_id": chunk_id,
                "name": concept["name"],
                "description": concept.get("description", "")
            })

        for relation in result.get("relationships", []):
            relationship_rows.append({
                "source": relation["source"],
                "target": relation["target"],
                "type": relation["type"]
            })

    # Create Concept nodes and connect them to their source chunks.
    if concept_rows:
        concept_query = """
        UNWIND $concepts AS item

        MATCH (c:Chunk {id: item.chunk_id})

        MERGE (e:Concept {name: item.name})

        ON CREATE SET e.description = item.description

        ON MATCH SET e.description =
            CASE
                WHEN coalesce(e.description, '') = ''
                THEN item.description
                ELSE e.description
            END

        MERGE (c)-[:MENTIONS]->(e)
        """

        run_query(concept_query, {"concepts": concept_rows})

    # Create relationships between extracted concepts.
    if relationship_rows:
        relationship_query = """
        UNWIND $relationships AS item

        MERGE (source:Concept {name: item.source})
        MERGE (target:Concept {name: item.target})

        MERGE (source)-[r:RELATED_TO {type: item.type}]->(target)
        """

        run_query(
            relationship_query,
            {"relationships": relationship_rows}
        )

    unique_concepts = len({
        item["name"].casefold()
        for item in concept_rows
    })

    return {
        "concept_mentions_created": len(concept_rows),
        "unique_concepts_submitted": unique_concepts,
        "relationships_submitted": len(relationship_rows)
    }


def build_knowledge_graph(chapter_number=1, batch_size=3):
    """Build the knowledge graph for one chapter."""

    print("\n========== KNOWLEDGE GRAPH BUILDING ==========")

    print("\nChecking Neo4j connection and schema...")
    ensure_schema()

    print(f"\nFetching Chapter {chapter_number} chunks...")
    chunks = get_chapter_chunks(chapter_number)

    print(f"Chunks found: {len(chunks)}")

    if not chunks:
        print("No chunks found. Check whether this chapter was ingested.")
        return {
            "chunks_found": 0,
            "concept_mentions_created": 0,
            "unique_concepts_submitted": 0,
            "relationships_submitted": 0
        }

    checkpoint_file = (
    Path("data/checkpoints")
    / f"concepts_chapter_{chapter_number}.json"
    )
    extraction_results = extract_concepts(
        chunks,
        batch_size=1,
        checkpoint_file=checkpoint_file
    )

    print("\nStoring extracted graph in Neo4j...")
    storage_result = store_extracted_graph(extraction_results)

    final_result = {
        "chunks_found": len(chunks),
        **storage_result
    }

    print("\n========== FINAL GRAPH RESULT ==========")
    print(final_result)

    return final_result
 