import unittest
from src.db import get_db_connection

class TestDB(unittest.TestCase):
    def test_db_connection(self):
        conn = get_db_connection()
        self.assertIsNotNone(conn)
        conn.close()

if __name__ == '__main__':
    unittest.main() 