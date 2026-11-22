
from app.ingestion.chapter_extractor import ChapterExtractor
from app.ingestion.content_extractor import ContentExtractor


PDF_PATH = r"C:\Users\tanvi\Downloads\NetGraph-RAG\book.pdf"


def main():

    # Get chapter metadata
    chapter_extractor = ChapterExtractor()
    result = chapter_extractor.extract_chapters(PDF_PATH)

    # Select Chapter 1
    chapter = result["chapters"][0]

    # Extract chapter content
    content_extractor = ContentExtractor()

    extracted = content_extractor.extract_chapter_content(
        PDF_PATH,
        chapter
    )

    print("\n========== CHAPTER CONTENT EXTRACTION ==========")

    print("Chapter:", extracted["chapter_title"])
    print("Total blocks:", extracted["total_blocks"])

    print("\n========== FIRST 20 BLOCKS ==========\n")

    for index, block in enumerate(extracted["blocks"][:80], start=1):

        print(f"\nBLOCK {index}")
        print("PDF Page:", block["pdf_page_number"])
        print("Printed Page:", block["printed_page_number"])
        print("Font Size:", block["font_size"])
        print("Text:")
        print(block["text"])
        print("-" * 70)


if __name__ == "__main__":
    main()
