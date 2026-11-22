
from app.retrieval.graph_search import graph_search


def main():
    questions = [
        "What is a computer network?",
        "What is the difference between LAN and WAN?",
        "What are the components of data communication?"
    ]

    for question in questions:
        print("\n" + "=" * 80)
        print("QUESTION:", question)
        print("=" * 80)

        results = graph_search(question, top_k=5)

        print("Results found:", len(results))

        for index, result in enumerate(results, start=1):
            print(f"\nResult {index}")
            print("Chunk ID:", result["id"])
            print("Score:", result["score"])
            print("Chapter:", result["chapter_title"])
            print("Section:", result["section"])
            print("Printed pages:",
                  result["start_printed_page"],
                  "-",
                  result["end_printed_page"])
            print("Text:", result["text"][:400])


if __name__ == "__main__":
    main()
