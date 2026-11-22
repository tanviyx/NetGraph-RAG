
from app.graph.graph_builder import build_knowledge_graph


def main():
    result = build_knowledge_graph(
        chapter_number=1,
        batch_size=1
    )

    print("\nGraph building test completed.")
    print(result)


if __name__ == "__main__":
    main()
