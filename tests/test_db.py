from sqlalchemy import text  # pyright: ignore[reportMissingImports]
from backend.core.database import engine

def test_postgresql_connection():
    with engine.begin() as connection:
        # Confirm which database is connected
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        print(f"Connected database: {database_name}")

        if database_name != "taskproject":
            raise RuntimeError(
                f"Wrong database! Expected taskproject, got {database_name}"
            )

        # Create a small table specifically for this test
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL
            )
        """))

        # Insert a test record
        connection.execute(
            text("""
                INSERT INTO connection_test (message)
                VALUES (:message)
            """),
            {"message": "PostgreSQL connection test successful"}
        )

        # Retrieve the inserted record
        result = connection.execute(text("""
            SELECT id, message
            FROM connection_test
            ORDER BY id DESC
            LIMIT 1
        """)).one()

        print(f"Test record ID: {result.id}")
        print(f"Test record: {result.message}")

        assert result.message == "PostgreSQL connection test successful"

        print("SUCCESS: PostgreSQL connection, INSERT, and SELECT all work!")

if __name__ == "__main__":
    test_postgresql_connection()
