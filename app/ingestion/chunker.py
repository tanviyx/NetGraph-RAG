
import re
from hashlib import sha256


def chunk_pages(pages, chunk_chars=2200, overlap_chars=300):
    """
    Original page-based chunking function.
    Retained for backward compatibility.
    """

    chunks = []

    text = "\n".join(
        f"[Page {p['page']}]\n{p['text']}"
        for p in pages
    )

    text = re.sub(r"\s+", " ", text).strip()

    start = 0

    while start < len(text):

        end = min(start + chunk_chars, len(text))

        piece = text[start:end].strip()

        if piece:

            chunks.append({
                "text": piece,
                "chunk_hash": sha256(
                    piece.encode("utf-8")
                ).hexdigest()
            })

        if end >= len(text):
            break

        start = max(0, end - overlap_chars)

    return chunks



def chunk_blocks(
    blocks,
    chunk_chars=2200,
    overlap_chars=300
):
    """
    Structure-aware chunking of reconstructed textbook blocks.

    Preserves chapter, section, subsection and accurate
    PDF page metadata.
    """

    chunks = []

    excluded_types = {
        "chapter_label",
        "chapter_heading",
        "section_heading",
        "subsection_heading",
        "page_header",
        "page_number",
        "noise",
        "figure_content",
    }

    groups = []
    current_group = []
    current_key = None

    for block in blocks:

        structure_type = block.get("structure_type")

        if structure_type in excluded_types:
            continue

        text = block.get("text", "").strip()

        if not text:
            continue

        hierarchy = block.get("hierarchy", {})

        key = (
            block.get("chapter_number"),
            hierarchy.get("section"),
            hierarchy.get("subsection"),
        )

        if current_key is not None and key != current_key:

            if current_group:
                groups.append(current_group)

            current_group = []

        current_key = key
        current_group.append(block)

    if current_group:
        groups.append(current_group)

    for group in groups:

        first_block = group[0]

        hierarchy = first_block.get(
            "hierarchy", {}
        )

        chapter_number = first_block.get(
            "chapter_number"
        )

        chapter_title = first_block.get(
            "chapter_title"
        )

        section = hierarchy.get("section")
        subsection = hierarchy.get("subsection")

        # Build text while tracking the source block offsets.
        text_parts = []
        block_offsets = []

        position = 0

        for block in group:

            block_text = block["text"].strip()

            if not block_text:
                continue

            if text_parts:
                position += 2

            start = position
            end = start + len(block_text)

            text_parts.append(block_text)

            block_offsets.append({
                "start": start,
                "end": end,
                "block": block,
            })

            position = end

        group_text = "\n\n".join(text_parts)

        if not group_text:
            continue

        start = 0

        while start < len(group_text):

            end = min(
                start + chunk_chars,
                len(group_text)
            )

            piece = group_text[start:end].strip()

            if piece:

                overlapping_blocks = [
                    item["block"]
                    for item in block_offsets
                    if item["end"] > start
                    and item["start"] < end
                ]

                pages = [
                    block.get("pdf_page_number")
                    for block in overlapping_blocks
                    if block.get("pdf_page_number") is not None
                ]

                printed_pages = [
                    block.get("printed_page_number")
                    for block in overlapping_blocks
                    if block.get("printed_page_number") is not None
                ]

                chunk_hash = sha256(
                    piece.encode("utf-8")
                ).hexdigest()

                chunks.append({

                    "chunk_id": chunk_hash[:16],

                    "chunk_hash": chunk_hash,

                    "text": piece,

                    "chapter_number": chapter_number,

                    "chapter_title": chapter_title,

                    "section": section,

                    "subsection": subsection,

                    "start_pdf_page": min(pages) if pages else None,

                    "end_pdf_page": max(pages) if pages else None,

                    "start_printed_page": (
                        min(printed_pages)
                        if printed_pages else None
                    ),

                    "end_printed_page": (
                        max(printed_pages)
                        if printed_pages else None
                    ),

                    "word_count": len(piece.split()),

                    "character_count": len(piece),

                    "block_count": len(overlapping_blocks),
                })

            if end >= len(group_text):
                break

            start = max(
                0,
                end - overlap_chars
            )

    return chunks