
from typing import Any

from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.toc_detector import TOCDetector
from app.ingestion.chapter_mapper import ChapterMapper


class ChapterExtractor:

    def __init__(self):
        self.pdf_loader = PDFLoader()
        self.toc_detector = TOCDetector()
        self.chapter_mapper = ChapterMapper()

    def extract_chapters(self, pdf_path: str) -> dict[str, Any]:

        # Step 1: Load the PDF
        extracted = self.pdf_loader.load_pdf(pdf_path)

        pages = extracted["pages"]
        document = extracted["document"]

        # Step 2: Detect TOC pages
        toc_pages = self.toc_detector.detect_toc_pages(pages)

        # Step 3: Extract chapter information
        chapters = self.toc_detector.extract_chapters(
            pages,
            toc_pages,
            pdf_path
        )

        # Step 4: Map printed pages to actual PDF pages
        mapped_chapters = self.chapter_mapper.map_chapters(
            pages,
            chapters
        )

        return {
            "document": document,
            "chapters": mapped_chapters,
            "total_chapters": len(mapped_chapters)
        }
