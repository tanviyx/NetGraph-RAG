
from typing import Any


class HierarchyAssigner:

    def assign(
        self,
        blocks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:

        assigned = []

        current_chapter = None
        current_section = None
        current_subsection = None

        for block in blocks:

            block_type = block.get("structure_type")
            text = block.get("text", "").strip()

            if block_type == "chapter_heading":
                current_chapter = text
                current_section = None
                current_subsection = None

            elif block_type == "section_heading":
                current_section = text
                current_subsection = None

            elif block_type == "subsection_heading":
                current_subsection = text

            enriched_block = {
                **block,
                "hierarchy": {
                    "chapter": block.get("chapter_title")
                    or current_chapter,
                    "section": current_section,
                    "subsection": current_subsection,
                }
            }

            assigned.append(enriched_block)

        return assigned
