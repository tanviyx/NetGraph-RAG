
import pymupdf

pdf_path = r"C:\Users\tanvi\Downloads\NetGraph-RAG\book.pdf"

with pymupdf.open(pdf_path) as pdf:

    for page_number in [40, 41, 42, 43]:

        page = pdf[page_number - 1]
        data = page.get_text("dict")

        print("\n" + "=" * 80)
        print(f"PDF PAGE: {page_number}")
        print("=" * 80)

        for block in data["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:

                    text = span["text"].strip()

                    if text:
                        print(
                            f"Text: {text[:100]:<100} | "
                            f"Font size: {span['size']:.1f} | "
                            f"Bold: {bool(span['flags'] & 16)}"
                        )