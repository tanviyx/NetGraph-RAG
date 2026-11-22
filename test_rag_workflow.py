from app.graph.workflow import run_question


def main():

    questions = [
        "What is a computer network?",
        "What are the five components of data communication?",
        "What is the difference between LAN and WAN?"
    ]

    for i, question in enumerate(questions, start=1):

        print("\n" + "=" * 80)
        print(f"QUESTION {i}: {question}")
        print("=" * 80)

        result = run_question(
            question,
            thread_id=f"test_question_{i}"
        )

        print("\nANSWER:")
        print(result.get("answer", "No answer generated."))

        print("\nCITATIONS:")

        for citation in result.get("citations", []):

            print(
                f"Source {citation['source']} | "
                f"Chunk: {citation['chunk_id']} | "
                f"Chapter: {citation['chapter']} | "
                f"Pages: {citation['start_printed_page']}-"
                f"{citation['end_printed_page']}"
            )

        print("\nRETRIEVAL ATTEMPTS:")
        print(result.get("attempts", 0))


if __name__ == "__main__":
    main()