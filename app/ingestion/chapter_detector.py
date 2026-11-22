
import re
from typing import Any


class ChapterDetector:

    # Patterns commonly used in textbooks
    CHAPTER_PATTERNS = [
        r"^\s*chapter\s+(\d+)\s*[:.\-–—]?\s*(.*?)\s*$",
        r"^\s*chap\.\s*(\d+)\s*[:.\-–—]?\s*(.*?)\s*$",
        r"^\s*(\d+)\s*[:.\-–—]\s+(.+?)\s*$",
    ]

    def detect_chapters(
        self,
        pages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:

        detected_chapters = []

        for page in pages:

            page_number = page["page_number"]
            text = page["text"]

            if not text:
                continue

            lines = text.splitlines()

            for line in lines:

                cleaned_line = line.strip()

                if not cleaned_line:
                    continue

                chapter_match = self._match_chapter_heading(
                    cleaned_line
                )

                if chapter_match:

                    chapter_number, chapter_title = chapter_match

                    detected_chapters.append({
                        "chapter_number": chapter_number,
                        "chapter_title": chapter_title,
                        "start_page": page_number,
                        "heading": cleaned_line
                    })

        detected_chapters = self._remove_duplicates(
            detected_chapters
        )

        detected_chapters = self._assign_end_pages(
            detected_chapters,
            len(pages)
        )

        return detected_chapters

    def _match_chapter_heading(
        self,
        line: str
    ) -> tuple[int, str] | None:

        for pattern in self.CHAPTER_PATTERNS:

            match = re.match(
                pattern,
                line,
                flags=re.IGNORECASE
            )

            if match:

                groups = match.groups()

                chapter_number = int(groups[0])
                chapter_title = groups[1].strip()

                if chapter_number <= 0:
                    continue

                return chapter_number, chapter_title

        return None

    def _remove_duplicates(
        self,
        chapters: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:

        unique_chapters = []
        seen = set()

        for chapter in chapters:

            key = (
                chapter["chapter_number"],
                chapter["start_page"]
            )

            if key not in seen:

                seen.add(key)

                unique_chapters.append(chapter)

        unique_chapters.sort(
            key=lambda chapter: chapter["start_page"]
        )

        return unique_chapters

    def _assign_end_pages(
        self,
        chapters: list[dict[str, Any]],
        total_pages: int
    ) -> list[dict[str, Any]]:

        for index, chapter in enumerate(chapters):

            if index + 1 < len(chapters):

                next_chapter = chapters[index + 1]

                chapter["end_page"] = (
                    next_chapter["start_page"] - 1
                )

            else:

                chapter["end_page"] = total_pages

        return chapters
