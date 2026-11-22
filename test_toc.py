from app.ingestion.pdf_loader import PDFLoader


def main():
    pdf_path = input("Enter PDF path: ").strip().strip('"')

    loader = PDFLoader()
    document = loader.load_pdf(pdf_path)

    for page_number in [10, 11]:
        page = document["pages"][page_number - 1]

        print(f"\n{'=' * 80}")
        print(f"PDF PAGE {page_number}")
        print("=" * 80)

        print(page["text"])


if __name__ == "__main__":
    main()