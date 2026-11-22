import re


class StructureClassifier:

    SENTENCE_STARTERS = {
        "in", "when", "if", "as", "this", "that",
        "it", "we", "they", "the", "a", "an",
        "most", "each", "however", "because", "while",
        "for", "there", "these", "those", "which",
        "what", "network", "data", "communication"
    }

    def classify_block(self, block: dict) -> str:

        text = block.get("text", "").strip()

        normalized = re.sub(r"\s+", " ", text)

        font_size = block.get("font_size", 0)
        line_count = block.get("line_count", 0)

        if not text:
            return "noise"

        # 1. Page numbers
        if re.fullmatch(r"\d{1,4}", normalized):
            return "page_number"

        # 2. Running headers
        if re.search(
            r"\bCHAPTER\s+\d+\b",
            normalized,
            re.IGNORECASE
        ):
            return "page_header"

        if re.search(
            r"\bSECTION\s+\d+\.\d+\b",
            normalized,
            re.IGNORECASE
        ):
            return "page_header"

        # 3. Chapter labels
        if re.fullmatch(
            r"CHAPTER\s*[0-9Il|]+",
            normalized,
            re.IGNORECASE
        ):
            return "chapter_label"

        # 4. Chapter headings
        y0 = block.get(
            "block_position", {}
        ).get("y0", 999)

        if (
            font_size >= 20
            and line_count <= 3
            and y0 < 300
            and normalized.isalpha()
        ):
            return "chapter_heading"

        # 5. Numbered subsection headings
        if re.match(
            r"^\d+\.\d+\.\d+\s+\S",
            normalized
        ):
            return "subsection_heading"

        # 6. Numbered section headings
        if re.match(
            r"^\d+\.\d+\s+[A-Z]",
            normalized
        ):
            return "section_heading"

        # 7. Figure captions
        if re.match(
            r"^(Figure|Fig\.)\s+\d+(?:\.\d+)*",
            normalized,
            re.IGNORECASE
        ):
            return "figure_caption"

        # 8. Diagram content
        if font_size < 9:
            return "figure_content"

        # 9. Normal numbered list items
        # Examples: 1. Delivery, 2) Accuracy, 3 Timeliness

        if re.match(
            r"^\d+[.)]?\s+[A-Z]",
            normalized
        ):
            return "list_item"

        # 10. OCR numbered list items
        # Examples: I. Delivery, I Sender, 7 Accuracy

        if re.match(
            r"^[0-9Il|][.)]?\s+[A-Z]",
            normalized
        ):
            return "list_item"

        # 11. OCR list markers containing malformed punctuation
        # Examples: -1 Message, -1.. Transmission medium,
        #           -\.. Jitter

        if re.match(
            r"^[-–—.\\]+\s*[0-9Il|]*[.)]*\s*[A-Z]",
            normalized
        ):
            return "list_item"

        # 12. Bullet lists
        if re.match(
            r"^[•●▪◦]\s+\S",
            normalized
        ):
            return "list_item"

        # 13. Single-character OCR fragments
        if len(normalized) <= 1:
            return "noise"

        # 14. Punctuation-only blocks
        if re.fullmatch(
            r"[^a-zA-Z0-9]+",
            normalized
        ):
            return "noise"

        # 15. Excessive punctuation
        punctuation_count = sum(
            not character.isalnum() and not character.isspace()
            for character in normalized
        )

        if (
            punctuation_count >= 2
            and punctuation_count / len(normalized) > 0.35
        ):
            return "noise"

        # 16. Unnumbered headings

        words = normalized.split()

        first_word = words[0].lower()

        is_short_heading = (
            line_count == 1
            and 1 <= len(words) <= 5
            and not normalized.endswith(
                (".", ",", ";", ":")
            )
            and first_word not in self.SENTENCE_STARTERS
            and not normalized[0].islower()
        )

        if (
            is_short_heading
            and font_size >= 13
        ):
            return "subsection_heading"
        # Larger-font, short standalone headings
        if (
            font_size >= 13
            and line_count <= 2
            and len(normalized.split()) <= 5
            and not normalized.endswith((".", ",", ";", ":"))
        ):return "subsection_heading"

        if (
            is_short_heading
            and font_size >= 11
            and len(words) <= 3
        ):
            return "subsection_heading"

        # 17. Default classification
        return "paragraph"