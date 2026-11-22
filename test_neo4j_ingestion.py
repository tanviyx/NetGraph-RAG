from app.ingestion.chapter_extractor import ChapterExtractor
from app.ingestion.content_extractor import ContentExtractor
from app.ingestion.structure_classifier import StructureClassifier
from app.ingestion.paragraph_reconstructor import ParagraphReconstructor
from app.ingestion.hierarchy_assigner import HierarchyAssigner
from app.ingestion.chunker import chunk_blocks
from app.ingestion.neo4j_writer import store_chunks


PDF_PATH = "book.pdf"


def main():

    print("Extracting chapters...")

    chapter_extractor = ChapterExtractor()

    chapter_result = chapter_extractor.extract_chapters(
        PDF_PATH
    )

    chapters = chapter_result["chapters"]

    print(f"Total chapters found: {len(chapters)}")

    # Select Chapter 1
    chapter = chapters[0]

    print(f"\nSelected chapter: {chapter}")

    print("\nExtracting chapter content...")

    content_extractor = ContentExtractor()

    content_result = content_extractor.extract_chapter_content(
        PDF_PATH,
        chapter
    )

    blocks = content_result["blocks"]

    print(f"Blocks extracted: {len(blocks)}")

    print("\nClassifying blocks...")

    classifier = StructureClassifier()

    for block in blocks:

        block["structure_type"] = classifier.classify_block(
            block
        )

    print("\nReconstructing paragraphs...")

    reconstructor = ParagraphReconstructor()

    blocks = reconstructor.reconstruct(blocks)

    print(f"Blocks after reconstruction: {len(blocks)}")

    print("\nAssigning hierarchy...")

    hierarchy_assigner = HierarchyAssigner()

    blocks = hierarchy_assigner.assign(blocks)

    print("\nGenerating chunks...")

    chunks = chunk_blocks(blocks)

    print(f"Chunks generated: {len(chunks)}")

    print("\nStoring chunks in Neo4j...")

    result = store_chunks(chunks)

    print("\n========== FINAL RESULT ==========")

    print(result)


if __name__ == "__main__":
    main()