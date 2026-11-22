import pymupdf
from test_toc_parser import parse_toc

PDF_PAGE_OFFSET = 37


def main():
    pdf_path = input("Enter PDF path: ").strip().strip('"')

    chapters = parse_toc(pdf_path)
    doc = pymupdf.open(pdf_path)

    print("\n========== CHAPTER PAGE MAPPING ==========\n")

    for i, chapter in enumerate(chapters):

        start_page = chapter["printed_page"] + PDF_PAGE_OFFSET

        if i < len(chapters) - 1:
            next_chapter_start = (
                chapters[i + 1]["printed_page"] + PDF_PAGE_OFFSET
            )

            end_page = next_chapter_start - 1

        else:
            # Chapter 32 ends before Appendix A
            appendix_a_start = 1029 + PDF_PAGE_OFFSET
            end_page = appendix_a_start - 1

        # Extract text from the first page of the chapter
        page_text = doc[start_page - 1].get_text()

        # Show first few lines for verification
        first_lines = [
            line.strip()
            for line in page_text.splitlines()
            if line.strip()
        ][:5]

        print(
            f"Chapter {chapter['chapter_number']}: "
            f"{chapter['title']}"
        )

        print(f"PDF pages: {start_page} - {end_page}")

        print("Text on starting page:")
        for line in first_lines:
            print(f"  {line}")

        print("-" * 60)

    doc.close()


if __name__ == "__main__":
    main()