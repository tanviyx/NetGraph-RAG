
from app.retrieval.vector_search import vector_search
from app.retrieval.graph_search import graph_search
from app.retrieval.hybrid_search import hybrid_search

def main():
    questions = [
        "What is a computer network?",
        "What is the difference between LAN and WAN?",
        "What are the components of data communication?"
    ]

    for question in questions:

        print("\n" + "=" * 100)
        print("QUESTION:", question)
        print("=" * 100)

        print("\n========== VECTOR SEARCH ==========")
        vector_results = vector_search(question, top_k=5)

        for i, result in enumerate(vector_results, 1):
            print(f"\n{i}. Chunk: {result['id']}")
            print("Score:", round(result["score"], 4))
            print("Section:", result.get("section"))
            print("Pages:", result.get("start_printed_page"),
                  "-", result.get("end_printed_page"))
            print("Text:", result["text"][:250])

        print("\n========== GRAPH SEARCH ==========")
        graph_results = graph_search(question, top_k=5)

        for i, result in enumerate(graph_results, 1):
            print(f"\n{i}. Chunk: {result['id']}")
            print("Score:", result["score"])
            print("Section:", result.get("section"))
            print("Pages:", result.get("start_printed_page"),
                  "-", result.get("end_printed_page"))
            print("Text:", result["text"][:250])

        print("\n========== HYBRID SEARCH ==========")
        hybrid_results = hybrid_search(question, top_k=5)

        for i, result in enumerate(hybrid_results, 1):
            print(f"\n{i}. Chunk: {result['id']}")
            print("RRF Score:", round(result["rrf_score"], 5))
            print("Section:", result.get("section"))
            print("Pages:", result.get("start_printed_page"),
                  "-", result.get("end_printed_page"))
            print("Text:", result["text"][:250])

if __name__ == "__main__":
    main()