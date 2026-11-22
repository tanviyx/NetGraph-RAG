import pymupdf

def main():
    pdf_path = input("Enter PDF path: ").strip().strip('"')

    doc = pymupdf.open(pdf_path)

    for page_number in [10, 11]:
        page = doc[page_number - 1]

        print(f"\n{'=' * 80}")
        print(f"PDF PAGE {page_number}")
        print(f"{'=' * 80}")

        blocks = page.get_text("blocks")

        for block in blocks:
            x0, y0, x1, y1, text, *_ = block

            text = text.strip().replace("\n", " | ")

            if text:
                print(
                    f"X: {x0:.0f}-{x1:.0f} | "
                    f"Y: {y0:.0f}-{y1:.0f} | "
                    f"{text}"
                )

    doc.close()


if __name__ == "__main__":
    main()