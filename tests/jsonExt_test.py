from unittest import TestCase, main
from vk_sdk.jsonExtension import loadAdvanced, load

class JsonExtTest(TestCase):
    def test_mixed(self):
        j = loadAdvanced("tests/data/1.json", 4, "[]")
        j.append("1")


