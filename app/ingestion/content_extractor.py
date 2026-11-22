
import re
from typing import Any

import pymupdf


class ContentExtractor:

    def extract_chapter_content(
        self,
        pdf_path: str,
        chapter: dict[str, Any]
    ) -> dict[str, Any]:

        extracted_blocks = []

        # Existing textbook uses an offset of 37.
        # Standalone PDFs can provide page_offset=0.
        page_offset = chapter.get("page_offset", 37)

        document_name = chapter.get(
            "document_name",
            "Computer Networking"
        )

        with pymupdf.open(pdf_path) as pdf:

            start_page = chapter["start_pdf_page"]
            end_page = chapter["end_pdf_page"]

            if start_page < 1 or end_page > len(pdf):
                raise ValueError(
                    f"Invalid PDF page range: "
                    f"{start_page}-{end_page}. "
                    f"PDF contains {len(pdf)} pages."
                )

            for pdf_page_number in range(
                start_page,
                end_page + 1
            ):

                page = pdf[pdf_page_number - 1]

                printed_page_number = (
                    pdf_page_number - page_offset
                    if page_offset is not None
                    else None
                )

                page_dict = page.get_text("dict")

                for block in page_dict["blocks"]:

                    if "lines" not in block:
                        continue

                    block_text = []
                    font_sizes = []
                    font_names = []
                    font_flags = []
                    line_count = 0

                    for line in block["lines"]:

                        line_text = []
                        line_count += 1

                        for span in line["spans"]:

                            text = span["text"].strip()

                            if text:
                                line_text.append(text)
                                font_sizes.append(span["size"])
                                font_names.append(span["font"])
                                font_flags.append(span["flags"])

                        if line_text:
                            block_text.append(
                                " ".join(line_text)
                            )

                    text = "\n".join(block_text).strip()

                    if not text:
                        continue

                    text = re.sub(r"[ \t]+", " ", text)

                    extracted_blocks.append({

                        "document_name": document_name,

                        "chapter_number": chapter["chapter_number"],

                        "chapter_title": chapter["title"],

                        "section": None,

                        "subsection": None,

                        "text": text,

                        "pdf_page_number": pdf_page_number,

                        "printed_page_number": printed_page_number,

                        "font_size": (
                            round(
                                sum(font_sizes) / len(font_sizes),
                                2
                            )
                            if font_sizes else None
                        ),

                        "line_count": line_count,

                        "font_names": list(set(font_names)),

                        "is_bold": any(
                            flags & 16
                            for flags in font_flags
                        ),

                        "is_single_line": line_count == 1,

                        "chapter_start_pdf_page": start_page,

                        "block_position": {
                            "x0": block["bbox"][0],
                            "y0": block["bbox"][1],
                            "x1": block["bbox"][2],
                            "y1": block["bbox"][3]
                        }
                    })

        return {
            "chapter_number": chapter["chapter_number"],
            "chapter_title": chapter["title"],
            "start_pdf_page": chapter["start_pdf_page"],
            "end_pdf_page": chapter["end_pdf_page"],
            "total_blocks": len(extracted_blocks),
            "blocks": extracted_blocks
        }
