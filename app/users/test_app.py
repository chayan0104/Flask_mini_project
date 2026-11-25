import atexit
import os
import tempfile
import unittest
from pathlib import Path

test_database_directory = tempfile.TemporaryDirectory()
atexit.register(test_database_directory.cleanup)
os.environ["DATABASE_PATH"] = str(
    Path(test_database_directory.name) / "users.sqlite3"
)

import app as users_service


class UsersApiTests(unittest.TestCase):
    def setUp(self):
        self.database_directory = tempfile.TemporaryDirectory()
        users_service.DATABASE_PATH = str(
            Path(self.database_directory.name) / "users.sqlite3"
        )
        users_service.initialize_database()
        self.client = users_service.app.test_client()

    def tearDown(self):
        self.database_directory.cleanup()

    def test_posted_user_is_persisted_and_returned(self):
        response = self.client.post("/api/users", json={"name": "Dana"})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            self.client.get("/api/users").get_json(),
            {"users": ["Alice", "Bob", "Charlie", "Dana"]},
        )

    def test_invalid_and_duplicate_names_are_rejected(self):
        invalid_response = self.client.post("/api/users", json={"name": " "})
        duplicate_response = self.client.post(
            "/api/users", json={"name": "Alice"}
        )

        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(duplicate_response.status_code, 409)

    def test_metrics_endpoint_reports_api_requests(self):
        self.client.get("/api/users")

        response = self.client.get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"http_requests_total", response.data)


if __name__ == "__main__":
    unittest.main()
