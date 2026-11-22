
from typing import Any

class ChapterMapper:

    # Verified against the textbook
    PDF_PAGE_OFFSET = 37

    # Appendix A begins on printed page 1029
    APPENDIX_A_PRINTED_PAGE = 1029

    def map_chapters(
        self,
        pages: list[dict[str, Any]],
        chapters: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:

        if not chapters:
            return []

        if not pages:
            raise ValueError("PDF pages list cannot be empty.")

        mapped_chapters = []

        total_pdf_pages = max(
            page["page_number"] for page in pages
        )

        # Convert printed page numbers into PDF page numbers
        for chapter in chapters:

            printed_start = chapter.get(
                "printed_start_page",
                chapter.get("printed_page")
            )

            if printed_start is None:
                raise ValueError(
                    f"Missing printed page for chapter "
                    f"{chapter.get('chapter_number')}"
                )

            pdf_start = printed_start + self.PDF_PAGE_OFFSET

            mapped_chapters.append({
                **chapter,
                "printed_start_page": printed_start,
                "start_pdf_page": pdf_start
            })

        # Sort chapters by their actual PDF starting page
        mapped_chapters.sort(
            key=lambda chapter: chapter["start_pdf_page"]
        )

        # Calculate chapter ending pages
        for index, chapter in enumerate(mapped_chapters):

            if index + 1 < len(mapped_chapters):

                next_chapter = mapped_chapters[index + 1]

                chapter["end_pdf_page"] = (
                    next_chapter["start_pdf_page"] - 1
                )

            else:
                # Final chapter ends before Appendix A
                appendix_start = (
                    self.APPENDIX_A_PRINTED_PAGE
                    + self.PDF_PAGE_OFFSET
                )

                chapter["end_pdf_page"] = min(
                    appendix_start - 1,
                    total_pdf_pages
                )

        return mapped_chapters