
import re
from typing import Any

import pymupdf

class TOCDetector:

    TOC_START_PDF_PAGE = 10
    TOC_END_PDF_PAGE = 18

    def detect_toc_pages(
        self,
        pages: list[dict[str, Any]]
    ) -> list[int]:

        return [
            page["page_number"]
            for page in pages
            if self.TOC_START_PDF_PAGE
            <= page["page_number"]
            <= self.TOC_END_PDF_PAGE
        ]

    @staticmethod
    def clean_text(text: str) -> str:
        return " ".join(text.split()).strip()

    @staticmethod
    def extract_page_number(text: str):
        text = re.sub(
            r"\s+(?:vii|viii|ix|x)\s*$",
            "",
            text,
            flags=re.IGNORECASE
        )

        match = re.search(r"(\d{1,4})\s*$", text)

        return int(match.group(1)) if match else None

    @classmethod
    def extract_title(cls, text: str) -> str:
        text = cls.clean_text(text)

        text = re.sub(
            r"\s+(?:vii|viii|ix|x)\s*$",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(r"\s+\d{1,4}\s*$", "", text)

        return text.strip()

    def extract_chapters(
        self,
        pages: list[dict[str, Any]],
        toc_page_numbers: list[int],
        pdf_path: str
    ) -> list[dict[str, Any]]:

        chapters = []

        with pymupdf.open(pdf_path) as pdf:

            for pdf_page_number in toc_page_numbers:

                page = pdf[pdf_page_number - 1]
                blocks = page.get_text("blocks")

                chapter_blocks = []
                title_blocks = []

                for block in blocks:

                    x0, y0, x1, y1, raw_text, *_ = block

                    text = self.clean_text(raw_text)

                    if not text:
                        continue

                    match = re.search(
                        r"Chapter\s+(\d+)",
                        text,
                        re.IGNORECASE
                    )

                    if not match:
                        continue

                    chapter_number = int(match.group(1))

                    if not 1 <= chapter_number <= 32:
                        continue

                    remainder = text[match.end():].strip()

                    # Chapter number, title and page in one block
                    printed_page = self.extract_page_number(
                        remainder
                    )

                    if printed_page is not None:

                        title = self.extract_title(remainder)

                        if title:
                            chapters.append({
                                "chapter_number": chapter_number,
                                "title": title,
                                "printed_start_page": printed_page,
                                "toc_pdf_page": pdf_page_number
                            })

                    else:
                        # Chapter number and title are in
                        # separate horizontal blocks
                        chapter_blocks.append({
                            "chapter_number": chapter_number,
                            "x1": x1,
                            "y": y0
                        })

                # Collect title blocks from the right side
                for block in blocks:

                    x0, y0, x1, y1, raw_text, *_ = block

                    text = self.clean_text(raw_text)

                    if not text or x0 <= 180:
                        continue

                    printed_page = self.extract_page_number(text)

                    if printed_page is None:
                        continue

                    title = self.extract_title(text)

                    if title:
                        title_blocks.append({
                            "title": title,
                            "printed_page": printed_page,
                            "x": x0,
                            "y": y0
                        })

                used_titles = set()

                # Match chapter numbers with nearby title blocks
                for chapter in chapter_blocks:

                    best_match = None
                    best_distance = float("inf")

                    for index, title in enumerate(title_blocks):

                        if index in used_titles:
                            continue

                        if title["x"] <= chapter["x1"]:
                            continue

                        distance = abs(
                            chapter["y"] - title["y"]
                        )

                        if distance < best_distance:
                            best_distance = distance
                            best_match = index

                    if best_match is None or best_distance > 8:
                        continue

                    matched_title = title_blocks[best_match]

                    chapters.append({
                        "chapter_number": chapter["chapter_number"],
                        "title": matched_title["title"],
                        "printed_start_page": matched_title["printed_page"],
                        "toc_pdf_page": pdf_page_number
                    })

                    used_titles.add(best_match)

        # Remove duplicates
        unique_chapters = {}

        for chapter in chapters:
            number = chapter["chapter_number"]

            if number not in unique_chapters:
                unique_chapters[number] = chapter

        return sorted(
            unique_chapters.values(),
            key=lambda chapter: chapter["chapter_number"]
        )