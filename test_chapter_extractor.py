
from app.ingestion.chapter_extractor import ChapterExtractor


def main():

    pdf_path = input("Enter PDF path: ").strip().strip('"')

    extractor = ChapterExtractor()

    result = extractor.extract_chapters(pdf_path)

    print("\n========== FINAL CHAPTER MAPPING ==========\n")

    for chapter in result["chapters"]:

        print(
            f'Chapter {chapter["chapter_number"]}: '
            f'{chapter["title"]}'
        )

        print(
            f'Printed pages: {chapter["printed_start_page"]}'
        )

        print(
            f'PDF pages: {chapter["start_pdf_page"]} - '
            f'{chapter["end_pdf_page"]}'
        )

        print("-" * 60)

    print("\nTotal chapters:", result["total_chapters"])


if __name__ == "__main__":
    main()
