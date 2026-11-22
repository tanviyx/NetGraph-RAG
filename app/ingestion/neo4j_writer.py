
from hashlib import sha256

from app.database.neo4j_client import run_query, ensure_schema
from app.ingestion.embedding_generator import embed_texts


def store_chunks(
    chunks,
    batch_size=32,
    document_id="networking_textbook",
    document_title="Computer Networking Textbook"
):
    """
    Generate embeddings and store document-specific chunks in Neo4j.

    Creates:
        Document
        Chapter
        Chunk

    Relationships:
        Chapter -> Document
        Chunk -> Chapter
    """

    if not chunks:
        print("No chunks to store.")
        return {
            "chunks_stored": 0,
            "chapters_stored": 0
        }

    print("Checking Neo4j schema...")
    ensure_schema()

    total_chunks = len(chunks)

    print(f"Total chunks to store: {total_chunks}")
    print(f"Document ID: {document_id}")
    print(f"Document title: {document_title}")

    stored_chunks = 0
    processed_chapters = set()

    for batch_start in range(0, total_chunks, batch_size):

        batch = chunks[batch_start:batch_start + batch_size]

        print(
            f"\nProcessing batch "
            f"{batch_start // batch_size + 1}..."
        )

        texts = [chunk["text"] for chunk in batch]
        embeddings = embed_texts(texts)

        rows = []

        for chunk, embedding in zip(batch, embeddings):

            chapter_number = chunk.get("chapter_number")
            chapter_title = chunk.get("chapter_title")

            # Preserve the existing IDs for the original textbook.
            if document_id == "networking_textbook":
                chapter_id = (
                    f"chapter_{chapter_number}"
                    if chapter_number is not None
                    else f"chapter_{chapter_title}"
                )
                chunk_id = chunk["chunk_id"]

            else:
                chapter_identity = (
                    str(chapter_number)
                    if chapter_number is not None
                    else str(chapter_title or "untitled")
                )

                chapter_id = (
                    f"{document_id}_chapter_{chapter_identity}"
                )

                chunk_id = sha256(
                    f"{document_id}:{chunk['chunk_id']}".encode("utf-8")
                ).hexdigest()[:24]

            rows.append({
                "document_id": document_id,
                "document_title": document_title,

                "chapter_id": chapter_id,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,

                "chunk_id": chunk_id,
                "chunk_hash": chunk["chunk_hash"],
                "text": chunk["text"],
                "embedding": embedding,

                "section": chunk.get("section"),
                "subsection": chunk.get("subsection"),

                "start_pdf_page": chunk.get("start_pdf_page"),
                "end_pdf_page": chunk.get("end_pdf_page"),

                "start_printed_page": chunk.get("start_printed_page"),
                "end_printed_page": chunk.get("end_printed_page"),

                "word_count": chunk.get("word_count"),
                "character_count": chunk.get("character_count"),
                "block_count": chunk.get("block_count")
            })

            processed_chapters.add(chapter_id)

        query = """
        UNWIND $rows AS row

        MERGE (d:Document {id: row.document_id})
        SET d.title = row.document_title

        MERGE (ch:Chapter {id: row.chapter_id})
        SET ch.chapter_number = row.chapter_number,
            ch.title = row.chapter_title,
            ch.document_id = row.document_id

        MERGE (ch)-[:PART_OF]->(d)

        MERGE (c:Chunk {id: row.chunk_id})
        SET c.document_id = row.document_id,
            c.chapter_id = row.chapter_id,
            c.chunk_hash = row.chunk_hash,
            c.text = row.text,
            c.embedding = row.embedding,

            c.chapter_number = row.chapter_number,
            c.chapter_title = row.chapter_title,

            c.section = row.section,
            c.subsection = row.subsection,

            c.start_pdf_page = row.start_pdf_page,
            c.end_pdf_page = row.end_pdf_page,

            c.start_printed_page = row.start_printed_page,
            c.end_printed_page = row.end_printed_page,

            c.word_count = row.word_count,
            c.character_count = row.character_count,
            c.block_count = row.block_count

        MERGE (c)-[:PART_OF]->(ch)
        """

        run_query(query, {"rows": rows})

        stored_chunks += len(batch)

        print(
            f"Stored {stored_chunks}/{total_chunks} chunks"
        )

    print("\n========== INGESTION COMPLETE ==========")
    print(f"Chunks stored: {stored_chunks}")
    print(f"Chapters encountered: {len(processed_chapters)}")

    return {
        "document_id": document_id,
        "document_title": document_title,
        "chunks_stored": stored_chunks,
        "chapters_stored": len(processed_chapters)
    }
