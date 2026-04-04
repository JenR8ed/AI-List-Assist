import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock missing modules to allow running the test without installing dependencies
mock_requests = MagicMock()
mock_psycopg2 = MagicMock()
mock_redis_mod = MagicMock()

sys.modules['requests'] = mock_requests
sys.modules['psycopg2'] = mock_psycopg2
sys.modules['redis'] = mock_redis_mod

import runpy

class TestSeedDB(unittest.TestCase):
    @patch('time.sleep', return_value=None)
    def test_env_vars_used(self, mock_sleep):
        # Set environment variables
        env_vars = {
            "POSTGRES_DB": "test_db",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_password",
            "POSTGRES_HOST": "test_host",
            "POSTGRES_PORT": "1234",
            "REDIS_HOST": "redis_test_host",
            "REDIS_PORT": "9999",
            "PERPLEXITY_API_KEY": "mock_key_if_missing"
        }

        with patch.dict(os.environ, env_vars):
            # Reset mocks
            mock_psycopg2.connect.reset_mock()
            mock_redis_mod.Redis.reset_mock()

            # Mock the database cursor and connection
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cur = MagicMock()
            mock_conn.cursor.return_value = mock_cur

            try:
                runpy.run_path('seed_db.py')
            except SystemExit:
                pass

            # Verify Redis called with env vars
            mock_redis_mod.Redis.assert_called_with(host="redis_test_host", port=9999, db=0)

            # Verify Postgres called with env vars
            mock_psycopg2.connect.assert_called_with(
                dbname="test_db",
                user="test_user",
                password="test_password",
                host="test_host",
                port="1234"
            )

    @patch('time.sleep', return_value=None)
    def test_missing_credentials_exit(self, mock_sleep):
        # Clear environment variables for the test
        # We need to preserve PERPLEXITY_API_KEY if we want to avoid logic branches,
        # but let's see how it behaves with empty env.

        with patch.dict(os.environ, {"PERPLEXITY_API_KEY": "mock_key_if_missing"}, clear=True):
            # Reset mocks
            mock_psycopg2.connect.reset_mock()
            mock_redis_mod.Redis.reset_mock()

            with self.assertRaises(SystemExit) as cm:
                runpy.run_path('seed_db.py')

            self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
