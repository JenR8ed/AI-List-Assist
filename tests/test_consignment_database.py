import unittest
import os
import sqlite3
import tempfile
from datetime import datetime
from unittest.mock import patch
import services.consignment_database as cdb

class TestConsignmentDatabase(unittest.TestCase):
    def setUp(self):
        # Create a temporary file to act as the database
        self.db_fd, self.db_path = tempfile.mkstemp()

        # Override the DB_PATH in the module
        self.original_db_path = cdb.DB_PATH
        cdb.DB_PATH = self.db_path

        # Initialize the database
        cdb.init_db()

    def tearDown(self):
        # Restore the original DB_PATH
        cdb.DB_PATH = self.original_db_path

        # Close the file descriptor and remove the temporary file
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_get_document(self):
        # Create participant
        participant = cdb.create_participant("Test User", "test@example.com")
        pid = participant["participant_id"]

        # Create asset
        asset = cdb.create_asset(pid, 100.0)
        asset_id = asset["asset_id"]

        # Attach document
        doc = cdb.attach_document(asset_id, "VALUATION", "http://example.com/doc.pdf")
        doc_id = doc["document_id"]

        # Retrieve document
        retrieved_doc = cdb.get_document(doc_id)

        self.assertIsNotNone(retrieved_doc)
        self.assertEqual(retrieved_doc["document_id"], doc_id)
        self.assertEqual(retrieved_doc["asset_id"], asset_id)
        self.assertEqual(retrieved_doc["document_category"], "VALUATION")
        self.assertEqual(retrieved_doc["persistent_url"], "http://example.com/doc.pdf")
        self.assertEqual(retrieved_doc["mime_type"], "application/pdf")

if __name__ == '__main__':
    unittest.main()
