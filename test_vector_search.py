from app.retrieval.vector_search import vector_search


def main():

    questions = [
        "What is a computer network?",
        "What is the difference between LAN and WAN?",
        "What are the components of data communication?"
    ]

    for question in questions:

        print("\n" + "=" * 80)

        print(f"QUESTION: {question}")

        print("=" * 80)

        results = vector_search(
            question,
            top_k=3
        )

        for i, result in enumerate(results, start=1):

            print(f"\nRESULT {i}")

            print(f"Score: {result['score']:.4f}")

            print(f"Chapter: {result['chapter_title']}")

            print(f"Section: {result['section']}")

            print(f"Subsection: {result['subsection']}")

            print(
                f"PDF pages: "
                f"{result['start_pdf_page']} - "
                f"{result['end_pdf_page']}"
            )

            print(
                f"Printed pages: "
                f"{result['start_printed_page']} - "
                f"{result['end_printed_page']}"
            )

            print("\nText:")

            print(result["text"][:1000])


if __name__ == "__main__":
    main()  