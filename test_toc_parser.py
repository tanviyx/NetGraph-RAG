import pymupdf
import re


def clean_text(text):
    return " ".join(text.split()).strip()


def extract_page_number(text):
    # Remove Roman numeral page footer if present
    text = re.sub(
        r"\s+(?:vii|viii|ix|x)\s*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    match = re.search(r"(\d{1,4})\s*$", text)

    if match:
        return int(match.group(1))

    return None


def extract_title(text):
    text = clean_text(text)

    # Remove Roman numeral footer
    text = re.sub(
        r"\s+(?:vii|viii|ix|x)\s*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove printed page number
    text = re.sub(r"\s+\d{1,4}\s*$", "", text)

    return text.strip()
    text = clean_text(text)

    # Remove the printed page number from the end
    text = re.sub(r"\s+\d{1,4}\s*$", "", text)

    return text.strip()


def parse_toc(pdf_path):
    doc = pymupdf.open(pdf_path)
    chapters = []

    # Actual PDF pages containing the chapter TOC
    toc_pages = [10, 11]

    for pdf_page_number in toc_pages:
        page = doc[pdf_page_number - 1]
        blocks = page.get_text("blocks")

        chapter_blocks = []
        title_blocks = []

        for block in blocks:
            x0, y0, x1, y1, text, *_ = block

            text = clean_text(text)

            if not text:
                continue

            chapter_match = re.search(
                r"Chapter\s+(\d+)",
                text,
                re.IGNORECASE
                )

            if chapter_match:
                chapter_number = int(chapter_match.group(1))

                # Chapter number, title and page in the same block
                remainder = text[chapter_match.end():].strip()

                page_number = extract_page_number(remainder)

                if page_number is not None:
                    title = extract_title(remainder)

                    if title:
                        chapters.append({
                            "chapter_number": chapter_number,
                            "title": title,
                            "printed_page": page_number,
                            "pdf_toc_page": pdf_page_number
                        })

                else:
                    # Chapter number is in a separate block
                    chapter_blocks.append({
                        "chapter_number": chapter_number,
                        "y": y0
                    })

            elif x0 > 180 and extract_page_number(text) is not None:
                # Right-side TOC title and printed page
                title_blocks.append({
                    "text": text,
                    "y": y0
                })

        # Match separate chapter numbers with title blocks
        used_titles = set()

        for chapter in chapter_blocks:

            best_match = None
            best_distance = float("inf")

            for index, title_block in enumerate(title_blocks):

                if index in used_titles:
                    continue

                distance = abs(chapter["y"] - title_block["y"])

                if distance < best_distance:
                    best_distance = distance
                    best_match = index

            if best_match is not None and best_distance <= 8:

                title_block = title_blocks[best_match]

                text = title_block["text"]

                printed_page = extract_page_number(text)
                title = extract_title(text)

                chapters.append({
                    "chapter_number": chapter["chapter_number"],
                    "title": title,
                    "printed_page": printed_page,
                    "pdf_toc_page": pdf_page_number
                })

                used_titles.add(best_match)

    doc.close()

    # Remove duplicate chapters
    unique_chapters = {}

    for chapter in chapters:
        unique_chapters[chapter["chapter_number"]] = chapter

    return sorted(
        unique_chapters.values(),
        key=lambda chapter: chapter["chapter_number"]
    )


def main():
    pdf_path = input("Enter PDF path: ").strip().strip('"')

    chapters = parse_toc(pdf_path)

    print("\n========== EXTRACTED CHAPTERS ==========\n")

    for chapter in chapters:
        print(
            f"Chapter {chapter['chapter_number']}: "
            f"{chapter['title']} | "
            f"Printed page: {chapter['printed_page']}"
        )

    print(f"\nTotal chapters detected: {len(chapters)}")


if __name__ == "__main__":
    main()