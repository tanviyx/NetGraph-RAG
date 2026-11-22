from pathlib import Path
from typing import Any

import pymupdf


class PDFLoader:

    def load_pdf(self, pdf_path: str) -> dict[str, Any]:
        """
        Extract text from a PDF page-by-page.

        Returns:
            Document metadata and extracted page content.
        """

        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF not found: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "Input file must be a PDF."
            )

        pages = []

        with pymupdf.open(path) as pdf:

            metadata = pdf.metadata or {}

            for page_index, page in enumerate(pdf):

                text = page.get_text("text").strip()

                pages.append({
                    "page_number": page_index + 1,
                    "text": text,
                    "character_count": len(text),
                    "is_empty": len(text) == 0
                })

            document_info = {
                "file_name": path.name,
                "file_path": str(path.resolve()),
                "total_pages": len(pdf),
                "title": metadata.get("title") or path.stem,
                "author": metadata.get("author") or "",
                "subject": metadata.get("subject") or ""
            }

        return {
            "document": document_info,
            "pages": pages
        }

    def get_document_statistics(
        self,
        extracted_document: dict[str, Any]
    ) -> dict[str, Any]:

        pages = extracted_document["pages"]

        total_characters = sum(
            page["character_count"]
            for page in pages
        )

        empty_pages = [
            page["page_number"]
            for page in pages
            if page["is_empty"]
        ]

        return {
            "total_pages": len(pages),
            "total_characters": total_characters,
            "empty_pages": empty_pages,
            "average_characters_per_page": (
                round(total_characters / len(pages), 2)
                if pages else 0
            )
        }