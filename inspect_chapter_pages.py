
import pymupdf

pdf_path = r"C:\Users\tanvi\Downloads\NetGraph-RAG\book.pdf"

# Chapter 1 starts at PDF page 40.
# Inspect its first three pages.
start_pdf_page = 40
end_pdf_page = 42

with pymupdf.open(pdf_path) as pdf:

    for page_number in range(start_pdf_page, end_pdf_page + 1):

        page = pdf[page_number - 1]
        text = page.get_text("text")

        print("\n" + "=" * 70)
        print(f"PDF PAGE: {page_number}")
        print(f"PRINTED PAGE: {page_number - 37}")
        print("=" * 70)

        print(text[:4000])
