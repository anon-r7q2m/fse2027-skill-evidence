import unittest
from django.db.models.fields.json import compile_json_path

class Behavior(unittest.TestCase):
    def test_numeric_string_key_quoted(self):
        # The lookup should treat numeric string keys as object keys (quoted),
        # not as array indexes. On the buggy base this assertion will fail.
        self.assertEqual(compile_json_path(["1111"]), '$."1111"')

    def test_non_numeric_string_key(self):
        self.assertEqual(compile_json_path(["foo"]), '$."foo"')

    def test_integer_index(self):
        self.assertEqual(compile_json_path([3]), '$[3]')
