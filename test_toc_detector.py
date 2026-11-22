
from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.toc_detector import TOCDetector

def main():

    pdf_path = input("Enter PDF path: ").strip().strip('"')

    loader = PDFLoader()
    detector = TOCDetector()

    extracted = loader.load_pdf(pdf_path)

    pages = extracted["pages"]

    toc_pages = detector.detect_toc_pages(pages)

    chapters = detector.extract_chapters(
        pages,
        toc_pages,
        pdf_path
    )

    print("\n========== INTEGRATED TOC DETECTION ==========\n")

    for chapter in chapters:

        print(
            f"Chapter {chapter['chapter_number']}: "
            f"{chapter['title']} | "
            f"Printed page: {chapter['printed_start_page']}"
        )

    print(f"\nTotal chapters detected: {len(chapters)}")

if __name__ == "__main__":
    main()