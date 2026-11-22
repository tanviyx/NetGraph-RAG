
import re
from typing import Any


class ParagraphReconstructor:

    SKIP_TYPES = {
        "page_header",
        "page_number",
        "noise",
        "figure_content",
    }

    def clean_text(self, text: str) -> str:

        if not text:
            return ""

        text = text.replace("\u00ad", "")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        # Repair words split by PDF line breaks
        text = re.sub(
            r"(\w+)-\s+(\w+)",
            r"\1\2",
            text
        )

        return text

    def get_type(self, block: dict[str, Any]) -> str:

        return (
            block.get("structure_type")
            or block.get("classification")
            or block.get("type")
            or "paragraph"
        )

    def should_merge(
        self,
        previous: dict[str, Any],
        current: dict[str, Any]
    ) -> bool:

        if self.get_type(previous) != "paragraph":
            return False

        if self.get_type(current) != "paragraph":
            return False

        if (
            previous.get("pdf_page_number")
            != current.get("pdf_page_number")
        ):
            return False

        previous_text = previous["text"].strip()
        current_text = current["text"].strip()

        # Merge obvious continuation fragments only
        if previous_text.endswith(
            (".", "!", "?", ":", ";")
        ):
            return False

        if not current_text:
            return False

        if current_text[0].isupper():
            return False

        return True

    def reconstruct(
        self,
        blocks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:

        reconstructed = []

        for block in blocks:

            block_type = self.get_type(block)

            if block_type in self.SKIP_TYPES:
                continue

            text = self.clean_text(
                block.get("text", "")
            )

            if not text:
                continue

            current = {
                **block,
                "text": text,
                "structure_type": block_type,
            }

            current["start_pdf_page"] = (
                current.get("pdf_page_number")
            )

            current["end_pdf_page"] = (
                current.get("pdf_page_number")
            )

            if (
                reconstructed
                and self.should_merge(
                    reconstructed[-1],
                    current
                )
            ):

                previous = reconstructed[-1]

                previous["text"] = (
                    previous["text"].rstrip()
                    + " "
                    + current["text"].lstrip()
                )

            else:

                reconstructed.append(current)

        return reconstructed
