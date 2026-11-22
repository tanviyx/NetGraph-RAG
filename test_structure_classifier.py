
from app.ingestion.chapter_extractor import ChapterExtractor
from app.ingestion.content_extractor import ContentExtractor
from app.ingestion.structure_classifier import StructureClassifier


PDF_PATH = r"C:\Users\tanvi\Downloads\NetGraph-RAG\book.pdf"


def main():

    chapter_extractor = ChapterExtractor()
    chapters = chapter_extractor.extract_chapters(PDF_PATH)

    chapter = chapters["chapters"][0]

    content_extractor = ContentExtractor()
    content = content_extractor.extract_chapter_content(
        PDF_PATH,
        chapter
    )

    classifier = StructureClassifier()

    print("\n========== CLASSIFICATION RESULTS ==========\n")

    for block in content["blocks"][:80]:

        classification = classifier.classify_block(block)

        print(
            f"Page {block['printed_page_number']} | "
            f"{classification:20} | "
            f"{block['font_size']:5} | "
            f"{block['text'][:100].replace(chr(10), ' ')}"
        )
        print(
            f"Page {block['pdf_page_number']} | "
            f"Type: {classification:<20} | "
            f"Font: {block['font_size']:<6} | "
            f"Lines: {block['line_count']:<3} | "
            f"Text: {block['text'][:100]}"
        )


if __name__ == "__main__":
    main()
