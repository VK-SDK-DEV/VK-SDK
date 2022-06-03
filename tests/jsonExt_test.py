from unittest import TestCase, main
from vk_sdk.jsonExtension import loadAdvanced, load

class JsonExtTest(TestCase):
    def test_mixed(self):
        j = loadAdvanced("tests/data/1.json", 4, "[]")
        j.dictionary = []
        j.content_changed()
        self.assertEquals(load("tests/data/1.json").dictionary, [])
        j.append({"1":"2", "3": []})
        j.insert(0, "123")
        self.assertEquals(len(j), 2)
        j[1]["3"].append({"1": "5"})


