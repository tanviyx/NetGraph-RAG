from app.database.neo4j_client import verify_connection, run_query

try:
    verify_connection()
    print("Successfully connected to Neo4j!")

    result = run_query(
        "RETURN 'Python connected to Neo4j!' AS message"
    )

    print(result[0]["message"])

except Exception as e:
    print("Connection failed!")
    print(e)