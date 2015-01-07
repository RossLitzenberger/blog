import unittest
from blog import core
import os


this_dir = os.path.dirname(os.path.realpath(__file__))


class TestConfig(unittest.TestCase):
    def test_read_config(self):
        config = core.Config()
        self.assertIsNotNone(config)