import time
from pathlib import Path

import json
import re

from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY, GROQ_MODEL


def get_llm():
    if not GROQ_API_KEY:
        raise RuntimeError("Set GROQ_API_KEY in .env before extracting concepts.")

    return ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0,
    )


def normalize_name(name):
    """Normalize concept names to avoid duplicate variations."""
    return " ".join(str(name).strip().split())


def parse_json_response(content):
    """Extract JSON from the LLM response, including fenced JSON."""
    if not isinstance(content, str):
        content = str(content)

    content = content.strip()

    # Remove Markdown code fences if present.
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    # Locate the JSON object in the response.
    start = content.find("{")

    if start == -1:
        raise ValueError("No JSON object found in Groq response.")

    decoder = json.JSONDecoder()
    data, _ = decoder.raw_decode(content[start:])

    return data



def extract_concepts(chunks, batch_size=1, checkpoint_file=None):
    """
    Extract concepts in small batches.
    Save each successful batch so extraction can resume after interruption.
    """

    llm = get_llm()
    checkpoint_path = Path(
        checkpoint_file or "data/checkpoints/concept_extraction.json"
    )

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    # Load previously completed extraction results.
    extracted_results = []

    if checkpoint_path.exists():
        try:
            saved_data = json.loads(
                checkpoint_path.read_text(encoding="utf-8")
            )
            extracted_results = saved_data.get("results", [])
            print(
                f"Resuming from checkpoint: "
                f"{len(extracted_results)} chunks already processed."
            )
        except (json.JSONDecodeError, AttributeError):
            print("Checkpoint could not be read. Starting fresh.")
            extracted_results = []

    completed_ids = {
        item["chunk_id"] for item in extracted_results
    }

    pending_chunks = [
        chunk for chunk in chunks
        if chunk["id"] not in completed_ids
    ]

    print(f"Chunks remaining: {len(pending_chunks)}")

    for batch_start in range(0, len(pending_chunks), batch_size):

        batch = pending_chunks[batch_start:batch_start + batch_size]

        input_chunks = [
            {
                "chunk_id": chunk["id"],
                "text": chunk["text"]
            }
            for chunk in batch
        ]

        prompt = f"""
You are an expert in computer networking and data communications.

Extract important technical concepts and relationships from each
textbook chunk.

Rules:
1. Extract a maximum of 6 important technical concepts per chunk.
2. Extract a maximum of 5 relationships per chunk.
3. Prefer standard computer networking terminology.
4. Do not invent information.
5. Avoid duplicate concepts.
6. Keep concept names concise and consistent.
7. Keep descriptions under 20 words.
8. Return the original chunk_id exactly as provided.
9. Return ONLY valid JSON.

Use this exact structure:

{{
  "chunks": [
    {{
      "chunk_id": "original_chunk_id",
      "concepts": [
        {{
          "name": "Computer Network",
          "description": "A set of devices connected through communication links."
        }}
      ],
      "relationships": [
        {{
          "source": "Computer Network",
          "target": "Communication Link",
          "type": "USES"
        }}
      ]
    }}
  ]
}}

TEXTBOOK CHUNKS:

{json.dumps(input_chunks, ensure_ascii=False)}
"""

        batch_number = batch_start // batch_size + 1
        print(f"\nExtracting batch {batch_number}...")

        # Retry temporary Groq rate limits.
        for attempt in range(6):
            try:
                response = llm.invoke(prompt)
                data = parse_json_response(response.content)

                returned_chunks = data.get("chunks", [])
                valid_chunk_ids = {
                    chunk["id"] for chunk in batch
                }

                batch_results = []

                for item in returned_chunks:
                    chunk_id = item.get("chunk_id")

                    if chunk_id not in valid_chunk_ids:
                        continue

                    concepts = []
                    seen_concepts = set()

                    for concept in item.get("concepts", []):
                        name = normalize_name(
                            concept.get("name", "")
                        )

                        if not name:
                            continue

                        key = name.casefold()

                        if key in seen_concepts:
                            continue

                        seen_concepts.add(key)

                        concepts.append({
                            "name": name,
                            "description": str(
                                concept.get("description", "")
                            ).strip()
                        })

                    relationships = []

                    for relation in item.get("relationships", []):
                        source = normalize_name(
                            relation.get("source", "")
                        )
                        target = normalize_name(
                            relation.get("target", "")
                        )
                        relation_type = normalize_name(
                            relation.get("type", "")
                        ).upper().replace(" ", "_")

                        if (
                            source
                            and target
                            and source.casefold() != target.casefold()
                            and relation_type
                        ):
                            relationships.append({
                                "source": source,
                                "target": target,
                                "type": relation_type
                            })

                    batch_results.append({
                        "chunk_id": chunk_id,
                        "concepts": concepts,
                        "relationships": relationships
                    })

                if not batch_results:
                    raise ValueError(
                        f"Groq returned no valid result for batch {batch_number}."
                    )

                # Save after every successful batch.
                extracted_results.extend(batch_results)

                checkpoint_path.write_text(
                    json.dumps(
                        {"results": extracted_results},
                        indent=2,
                        ensure_ascii=False
                    ),
                    encoding="utf-8"
                )

                print(
                    f"Checkpoint saved: "
                    f"{len(extracted_results)} chunks completed."
                )

                break

            except Exception as error:
                message = str(error).lower()

                is_rate_limit = (
                    "429" in message
                    or "rate_limit" in message
                    or "rate limit" in message
                )

                if not is_rate_limit or attempt == 5:
                    raise RuntimeError(
                        f"Concept extraction failed in batch "
                        f"{batch_number}: {error}"
                    ) from error

                wait_seconds = min(10 * (2 ** attempt), 60)

                print(
                    f"Groq rate limit reached. "
                    f"Retrying in {wait_seconds} seconds "
                    f"(attempt {attempt + 1}/6)..."
                )

                time.sleep(wait_seconds)

        # Spread requests across the token-per-minute window.
        if batch_start + batch_size < len(pending_chunks):
            time.sleep(10)

    print("\nConcept extraction completed.")
    print(f"Chunks processed: {len(extracted_results)}")

    return extracted_results
