from app.database.neo4j_client import verify_connection, ensure_schema, run_query

def main():
    print("Connecting to Neo4j...")

    verify_connection()
    print("Connection successful!")

    print("\nCreating constraints and indexes...")
    ensure_schema()

    print("Schema created successfully!")

    print("\nChecking indexes:")
    indexes = run_query("SHOW INDEXES")

    for index in indexes:
        print(
            f"Name: {index.get('name')} | "
            f"Type: {index.get('type')} | "
            f"State: {index.get('state')}"
        )

    print("\nChecking constraints:")
    constraints = run_query("SHOW CONSTRAINTS")

    for constraint in constraints:
        print(
            f"Name: {constraint.get('name')} | "
            f"Type: {constraint.get('type')}"
        )

if __name__ == "__main__":
    main()