
from app.ingestion.chapter_extractor import ChapterExtractor
from app.ingestion.content_extractor import ContentExtractor
from app.ingestion.structure_classifier import StructureClassifier
from app.ingestion.paragraph_reconstructor import ParagraphReconstructor
from app.ingestion.hierarchy_assigner import HierarchyAssigner
from app.ingestion.chunker import chunk_blocks


PDF_PATH = "book.pdf"


def main():

    print("Extracting chapters...")

    chapter_result = ChapterExtractor().extract_chapters(
        PDF_PATH
    )

    chapter = chapter_result["chapters"][0]

    print(f"Chapter: {chapter['title']}")

    blocks = ContentExtractor().extract_chapter_content(
        PDF_PATH,
        chapter
    )["blocks"]

    print(f"Extracted blocks: {len(blocks)}")

    # 1. Classification
    classifier = StructureClassifier()

    classified = []

    for block in blocks:

        classified.append({
            **block,
            "structure_type": classifier.classify_block(block)
        })

    # 2. Paragraph reconstruction
    reconstructed = ParagraphReconstructor().reconstruct(
        classified
    )

    print(f"Reconstructed blocks: {len(reconstructed)}")

    # 3. Hierarchy assignment
    hierarchical = HierarchyAssigner().assign(
        reconstructed
    )

    # 4. Chunking using the existing chunker
    chunks = chunk_blocks(
        hierarchical,
        chunk_chars=2200,
        overlap_chars=300
    )

    print(f"Generated chunks: {len(chunks)}")

    print("\n========== CHUNK RESULTS ==========")

    for chunk in chunks:

        print("\n" + "=" * 60)

        print(f"Chunk ID: {chunk['chunk_id']}")
        print(f"Chapter: {chunk['chapter_title']}")
        print(f"Section: {chunk['section']}")
        print(f"Subsection: {chunk['subsection']}")

        print(
            f"PDF Pages: {chunk['start_pdf_page']} - "
            f"{chunk['end_pdf_page']}"
        )

        print(
            f"Printed Pages: {chunk['start_printed_page']} - "
            f"{chunk['end_printed_page']}"
        )

        print(f"Words: {chunk['word_count']}")
        print(f"Characters: {chunk['character_count']}")

        print("\nTEXT:")
        print(chunk["text"][:1000])


if __name__ == "__main__":
    main()
