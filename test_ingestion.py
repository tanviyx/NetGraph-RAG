
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chapter_detector import ChapterDetector


def main():

    pdf_path = input(
        "Enter the path to your textbook PDF: "
    ).strip().strip('"')

    print("\nLoading PDF...")

    loader = PDFLoader()

    document = loader.load_pdf(pdf_path)

    statistics = loader.get_document_statistics(
        document
    )

    print("\n========== DOCUMENT INFORMATION ==========")

    print(document["document"])

    print("\n========== STATISTICS ==========")

    for key, value in statistics.items():
        print(f"{key}: {value}")

    print("\nDetecting chapters...")

    detector = ChapterDetector()

    chapters = detector.detect_chapters(
        document["pages"]
    )

    print("\n========== DETECTED CHAPTERS ==========")

    if not chapters:

        print("No chapters detected.")

        print(
            "We may need to adjust the chapter detection "
            "patterns for this textbook."
        )

    else:

        for chapter in chapters:

            print(
                f"\nChapter {chapter['chapter_number']}: "
                f"{chapter['chapter_title']}"
            )

            print(
                f"Pages: {chapter['start_page']} - "
                f"{chapter['end_page']}"
            )

    print("\n========== FIRST PAGE PREVIEW ==========")

    first_page = document["pages"][0]

    print(first_page["text"][:1500])


if __name__ == "__main__":
    main()
