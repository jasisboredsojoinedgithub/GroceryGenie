import unittest
import backend.src.config as config

class TestConfig(unittest.TestCase):
    def test_mongo_uri(self):
        self.assertIsNotNone(config.MONGO_URI)

    def test_secret_key(self):
        self.assertIsNotNone(config.SECRET_KEY)
