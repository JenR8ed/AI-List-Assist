import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.models import BoundingBox

class TestBoundingBox(unittest.TestCase):
    def test_to_dict(self):
        bbox = BoundingBox(x=10, y=20, width=100, height=200)

        result = bbox.to_dict()

        self.assertEqual(result, {
            "x": 10,
            "y": 20,
            "width": 100,
            "height": 200
        })

    def test_to_dict_zero_values(self):
        bbox = BoundingBox(x=0, y=0, width=0, height=0)

        result = bbox.to_dict()

        self.assertEqual(result, {
            "x": 0,
            "y": 0,
            "width": 0,
            "height": 0
        })

    def test_to_dict_negative_values(self):
        bbox = BoundingBox(x=-10, y=-20, width=100, height=200)

        result = bbox.to_dict()

        self.assertEqual(result, {
            "x": -10,
            "y": -20,
            "width": 100,
            "height": 200
        })

if __name__ == '__main__':
    unittest.main()
