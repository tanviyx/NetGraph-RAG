from app.database.neo4j_client import run_query
from app.ingestion.embedding_generator import embed_texts
from app.ingestion.entity_extractor import extract_concepts

def upsert_document(document_id, filename):
    run_query(
        "MERGE (d:Document {id:$id}) SET d.filename=$filename, d.updatedAt=datetime()",
        {"id": document_id, "filename": filename},
    )

def upsert_chapter(document_id, chapter_id, title, start_page, end_page, content_hash):
    run_query(
        "MERGE (d:Document {id:$doc_id}) "
        "MERGE (c:Chapter {id:$chapter_id}) "
        "SET c.title=$title, c.startPage=$start_page, c.endPage=$end_page, c.contentHash=$hash, c.status='processed' "
        "MERGE (d)-[:HAS_CHAPTER]->(c)",
        {"doc_id": document_id, "chapter_id": chapter_id, "title": title,
         "start_page": start_page, "end_page": end_page, "hash": content_hash},
    )

def ingest_chunks(document_id, chapter_id, chunks):
    vectors = embed_texts([c["text"] for c in chunks])
    for chunk, vector in zip(chunks, vectors):
        run_query(
            "MERGE (c:Chunk {id:$id}) SET c.text=$text, c.embedding=$embedding, c.chunkHash=$hash "
            "MERGE (ch:Chapter {id:$chapter_id}) MERGE (ch)-[:HAS_CHUNK]->(c)",
            {"id": f"{chapter_id}:{chunk['chunk_hash']}", "text": chunk["text"],
             "embedding": vector, "hash": chunk["chunk_hash"], "chapter_id": chapter_id},
        )
        concepts = extract_concepts(chunk["text"])
        for concept in concepts:
            run_query(
                "MERGE (e:Concept {name:$name}) SET e.description=$description "
                "MERGE (c:Chunk {id:$chunk_id}) MERGE (c)-[:MENTIONS]->(e)",
                {"name": concept.name, "description": concept.description,
                 "chunk_id": f"{chapter_id}:{chunk['chunk_hash']}"},
            )
            for related in concept.related_to:
                if related.strip() and related.lower() != concept.name.lower():
                    run_query(
                        "MATCH (a:Concept {name:$a}) MERGE (b:Concept {name:$b}) "
                        "MERGE (a)-[:RELATED_TO]->(b)",
                        {"a": concept.name, "b": related.strip()},
                    )
