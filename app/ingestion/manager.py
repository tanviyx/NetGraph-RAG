
from pathlib import Path
from hashlib import sha256

from app.ingestion.chapter_extractor import ChapterExtractor
from app.ingestion.content_extractor import ContentExtractor
from app.ingestion.structure_classifier import StructureClassifier
from app.ingestion.paragraph_reconstructor import ParagraphReconstructor
from app.ingestion.hierarchy_assigner import HierarchyAssigner
from app.ingestion.chunker import chunk_blocks
from app.ingestion.neo4j_writer import store_chunks


def ingest_pdf(
    path: str,
    selected_chapters: list[int] | None = None,
    document_id: str | None = None,
    document_title: str | None = None,
    standalone_chapter: bool = False,
    standalone_chapter_title: str | None = None
):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    document_title = document_title or path.stem

    if document_id is None:
        document_id = sha256(
            path.read_bytes()
        ).hexdigest()[:20]

    print(f"\nStarting ingestion: {path.name}")
    print(f"Document ID: {document_id}")

    chapter_extractor = ChapterExtractor()
    chapter_result = chapter_extractor.extract_chapters(str(path))

    chapters = chapter_result["chapters"]

    # Standalone chapter mode: treat the entire PDF as one chapter.
    if standalone_chapter:
        total_pages = chapter_result["document"]["total_pages"]

        chapters = [{
            "chapter_number": 1,
            "title": standalone_chapter_title or path.stem,
            "start_pdf_page": 1,
            "end_pdf_page": total_pages,
            "page_offset": 0,
            "document_name": document_title
        }]

    else:
        # Preserve the existing textbook's verified page offset.
        for chapter in chapters:
            chapter["page_offset"] = 37
            chapter["document_name"] = document_title

    print(f"Total chapters detected: {len(chapters)}")

    if selected_chapters is not None and not standalone_chapter:
        chapters = [
            chapter for chapter in chapters
            if chapter["chapter_number"] in selected_chapters
        ]

    if not chapters:
        raise ValueError(
            "No chapters were selected or detected in this PDF."
        )

    content_extractor = ContentExtractor()
    classifier = StructureClassifier()
    reconstructor = ParagraphReconstructor()
    hierarchy_assigner = HierarchyAssigner()

    all_chunks = []

    for chapter in chapters:

        print(
            f"\nProcessing Chapter {chapter['chapter_number']}: "
            f"{chapter['title']}"
        )

        content_result = content_extractor.extract_chapter_content(
            str(path),
            chapter
        )

        blocks = content_result["blocks"]

        for block in blocks:
            block["structure_type"] = classifier.classify_block(block)

        blocks = reconstructor.reconstruct(blocks)
        blocks = hierarchy_assigner.assign(blocks)

        chunks = chunk_blocks(blocks)

        print(f"Chunks generated: {len(chunks)}")

        all_chunks.extend(chunks)

    print("\nStoring chunks in Neo4j...")

    storage_result = store_chunks(
        all_chunks,
        document_id=document_id,
        document_title=document_title
    )

    return {
        "document_name": path.name,
        "document_title": document_title,
        "document_id": document_id,
        "chapters_processed": len(chapters),
        "chunks_generated": len(all_chunks),
        "storage_result": storage_result,
        "status": "completed"
    }
