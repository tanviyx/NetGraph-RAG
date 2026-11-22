
from app.ingestion.chapter_extractor import ChapterExtractor
from app.ingestion.content_extractor import ContentExtractor
from app.ingestion.structure_classifier import StructureClassifier
from app.ingestion.paragraph_reconstructor import ParagraphReconstructor


PDF_PATH = "book.pdf"


def main():

    print("Extracting chapters...")

    chapter_extractor = ChapterExtractor()
    chapter_result = chapter_extractor.extract_chapters(PDF_PATH)

    chapter = chapter_result["chapters"][0]

    print(f"Testing Chapter {chapter['chapter_number']}")
    print(chapter["title"])

    content_extractor = ContentExtractor()

    extracted = content_extractor.extract_chapter_content(
        PDF_PATH,
        chapter
    )

    blocks = extracted["blocks"]

    # Classify every block
    classifier = StructureClassifier()

    classified_blocks = []

    for block in blocks:

        structure_type = classifier.classify_block(block)

        classified_block = {
            **block,
            "structure_type": structure_type
        }

        classified_blocks.append(classified_block)

    # Reconstruct paragraphs
    reconstructor = ParagraphReconstructor()

    reconstructed = reconstructor.reconstruct(
        classified_blocks
    )

    print("\n========== RECONSTRUCTION RESULTS ==========")

    print(f"Original blocks: {len(blocks)}")
    print(f"Classified blocks: {len(classified_blocks)}")
    print(f"Reconstructed blocks: {len(reconstructed)}")

    print("\n========== FIRST 30 BLOCKS ==========")

    for i, block in enumerate(reconstructed[:30]):

        print(f"\nBlock {i + 1}")
        print(f"Type: {block['structure_type']}")
        print(f"PDF Page: {block.get('pdf_page_number')}")
        print(f"Text: {block['text']}")


if __name__ == "__main__":
    main()
