import os
import sys

# Ensure the project root is on sys.path when running from /tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from shared.models import BoundingBox

def test_bounding_box_to_dict_standard():
    """Test to_dict with standard positive integer coordinates."""
    bbox = BoundingBox(x=10, y=20, width=100, height=200)
    expected = {
        "x": 10,
        "y": 20,
        "width": 100,
        "height": 200
    }
    assert bbox.to_dict() == expected

def test_bounding_box_to_dict_zeros():
    """Test to_dict with zero values."""
    bbox = BoundingBox(x=0, y=0, width=0, height=0)
    expected = {
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0
    }
    assert bbox.to_dict() == expected

def test_bounding_box_to_dict_negative():
    """Test to_dict with negative values (testing data mapping, not logic validation)."""
    bbox = BoundingBox(x=-10, y=-20, width=-5, height=-15)
    expected = {
        "x": -10,
        "y": -20,
        "width": -5,
        "height": -15
    }
    assert bbox.to_dict() == expected
