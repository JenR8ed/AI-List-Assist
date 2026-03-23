import sqlite3
import tempfile
from pathlib import Path

from services import consignment_database


def test_init_db(capsys):
    """
    Test that init_db correctly creates the expected tables
    in the database and prints the initialization message.
    """
    # Create a temporary file to act as the database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        tmp_db_path = tmp_file.name

    try:
        # Save the original DB_PATH to restore it later
        original_db_path = consignment_database.DB_PATH

        # Override DB_PATH with the temporary file
        consignment_database.DB_PATH = tmp_db_path

        # Call the function we are testing
        consignment_database.init_db()

        # Check standard output
        captured = capsys.readouterr()
        assert f"Consignment DB initialised at {tmp_db_path}" in captured.out

        # Connect to the temporary database and verify tables
        conn = sqlite3.connect(tmp_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        # The exact tables created by the schema
        expected_tables = {"participants", "assets", "transactions", "documents"}

        # Assert that all expected tables are in the created tables
        for table in expected_tables:
            assert table in tables, f"Expected table '{table}' was not created."

        conn.close()

    finally:
        # Restore original DB_PATH
        consignment_database.DB_PATH = original_db_path

        # Clean up temporary file
        Path(tmp_db_path).unlink(missing_ok=True)
