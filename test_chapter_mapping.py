
import pymupdf

from test_toc_parser import parse_toc
from app.ingestion.chapter_mapper import ChapterMapper

def main():

    pdf_path = input("Enter PDF path: ").strip().strip('"')

    doc = pymupdf.open(pdf_path)

    pages = [
        {"page_number": i + 1}
        for i in range(len(doc))
    ]

    chapters = parse_toc(pdf_path)

    mapper = ChapterMapper()

    mapped = mapper.map_chapters(pages, chapters)

    print("\n========== FINAL CHAPTER MAPPING ==========\n")

    for chapter in mapped:

        print(
            f"Chapter {chapter['chapter_number']}: "
            f"{chapter['title']}"
        )

        print(
            f"Printed pages: "
            f"{chapter['printed_start_page']}"
        )

        print(
            f"PDF pages: "
            f"{chapter['start_pdf_page']} - "
            f"{chapter['end_pdf_page']}"
        )

        print("-" * 55)

    print(f"\nTotal chapters mapped: {len(mapped)}")

    doc.close()

if __name__ == "__main__":
    main()