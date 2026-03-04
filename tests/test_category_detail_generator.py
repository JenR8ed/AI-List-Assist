import pytest
import os
from unittest.mock import patch, MagicMock
from services.category_detail_generator import CategoryDetailGenerator

@patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy_key"})
@patch('services.category_detail_generator.GeminiRestClient')
@patch('services.category_detail_generator.EBayCategoryService')
def test_init_success(mock_ebay_service, mock_gemini_client):
    generator = CategoryDetailGenerator()
    assert generator.category_service is not None
    assert generator.gemini_client is not None
    mock_gemini_client.assert_called_once_with(api_key="dummy_key")

@patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy_key"})
@patch('services.category_detail_generator.GeminiRestClient', side_effect=Exception("Failed"))
@patch('services.category_detail_generator.EBayCategoryService')
def test_init_failure(mock_ebay_service, mock_gemini_client):
    generator = CategoryDetailGenerator()
    assert generator.gemini_client is None

@patch('services.category_detail_generator.GeminiRestClient')
@patch('services.category_detail_generator.EBayCategoryService')
def test_get_required_fields(mock_ebay_service, mock_gemini_client):
    generator = CategoryDetailGenerator()
    generator.category_service.get_category_aspects.return_value = {
        "required": [
            {"name": "Brand", "dataType": "STRING", "mode": "FREETEXT"},
            {"name": "Type", "dataType": "STRING", "mode": "SELECT", "values": ["Shirt", "Pants"]}
        ]
    }

    fields = generator.get_required_fields("1059")

    assert len(fields) == 2
    assert fields[0]["name"] == "Brand"
    assert fields[0]["required"] is True
    assert fields[0]["data_type"] == "STRING"
    assert fields[0]["input_mode"] == "FREETEXT"
    assert fields[0]["allowed_values"] == []

    assert fields[1]["name"] == "Type"
    assert fields[1]["input_mode"] == "SELECT"
    assert fields[1]["allowed_values"] == ["Shirt", "Pants"]

@patch('services.category_detail_generator.GeminiRestClient')
@patch('services.category_detail_generator.EBayCategoryService')
def test_generate_questions(mock_ebay_service, mock_gemini_client):
    generator = CategoryDetailGenerator()
    generator.category_service.get_category_aspects.return_value = {
        "required": [
            {"name": "Brand"},
            {"name": "Type", "mode": "SELECT", "values": ["A", "B"]},
            {"name": "Size"},
            {"name": "Color"}
        ]
    }

    # All fields missing
    questions = generator.generate_questions("123", {"item_name": "Test Item"})
    assert len(questions) == 3 # Should limit to 3
    assert questions[0]["field"] == "Brand"
    assert questions[0]["input_type"] == "text"
    assert questions[1]["field"] == "Type"
    assert questions[1]["input_type"] == "select"
    assert questions[1]["options"] == ["A", "B"]
    assert questions[2]["field"] == "Size"

    # Some fields known
    questions = generator.generate_questions("123", {"item_name": "Test Item", "brand": "Nike"})
    assert len(questions) == 3
    assert questions[0]["field"] == "Type"

    # Case insensitivity test
    questions = generator.generate_questions("123", {"item_name": "Test Item", "BRAND": "Nike", "type": "A"})
    assert len(questions) == 2
    assert questions[0]["field"] == "Size"
    assert questions[1]["field"] == "Color"


@patch('services.category_detail_generator.GeminiRestClient')
@patch('services.category_detail_generator.EBayCategoryService')
def test_create_question(mock_ebay_service, mock_gemini_client):
    generator = CategoryDetailGenerator()

    assert generator._create_question({"name": "Brand"}, {"item_name": "shoe"}) == "What brand is shoe?"
    assert generator._create_question({"name": "Type"}, {"item_name": "shirt"}) == "What type is shirt?"
    assert generator._create_question({"name": "Size"}, {}) == "What size is this item?"
    assert generator._create_question({"name": "Color"}, {"item_name": "hat"}) == "What color is hat?"
    assert generator._create_question({"name": "Condition"}, {"item_name": "book"}) == "What condition is book in?"

    # Fallback
    assert generator._create_question({"name": "Material"}, {"item_name": "table"}) == "What is the Material for table?"
    assert generator._create_question({"name": "Material"}, {}) == "What is the Material for this item?"

@patch('services.category_detail_generator.GeminiRestClient')
@patch('services.category_detail_generator.EBayCategoryService')
def test_validate_data(mock_ebay_service, mock_gemini_client):
    generator = CategoryDetailGenerator()
    generator.category_service.get_category_aspects.return_value = {
        "required": [
            {"name": "Brand"},
            {"name": "Type", "mode": "SELECT", "values": ["A", "B"]}
        ]
    }

    # Valid
    res = generator.validate_data("123", {"Brand": "Nike", "Type": "A"})
    assert res["valid"] is True
    assert len(res["missing"]) == 0
    assert len(res["invalid"]) == 0

    # Missing field
    res = generator.validate_data("123", {"Type": "A"})
    assert res["valid"] is False
    assert res["missing"] == ["Brand"]
    assert len(res["invalid"]) == 0

    # Empty field (counts as missing)
    res = generator.validate_data("123", {"Brand": "", "Type": "A"})
    assert res["valid"] is False
    assert res["missing"] == ["Brand"]

    # Invalid select option
    res = generator.validate_data("123", {"Brand": "Nike", "Type": "C"})
    assert res["valid"] is False
    assert len(res["missing"]) == 0
    assert len(res["invalid"]) == 1
    assert res["invalid"][0]["field"] == "Type"
    assert res["invalid"][0]["value"] == "C"
    assert res["invalid"][0]["allowed"] == ["A", "B"]

@patch('services.category_detail_generator.GeminiRestClient')
@patch('services.category_detail_generator.EBayCategoryService')
def test_suggest_category_from_data(mock_ebay_service, mock_gemini_client):
    generator = CategoryDetailGenerator()

    res = generator.suggest_category_from_data({"item_name": "iPhone 12"})
    assert res[0]["category_id"] == "293"
    assert res[0]["confidence"] == 0.8

    res = generator.suggest_category_from_data({"item_name": "Blue Cotton Shirt"})
    assert res[0]["category_id"] == "1059"
    assert res[0]["confidence"] == 0.7

    res = generator.suggest_category_from_data({"item_name": "Vintage Clock"})
    assert res[0]["category_id"] == "20081"
    assert res[0]["confidence"] == 0.6

    res = generator.suggest_category_from_data({"item_name": "Car Engine part"})
    assert res[0]["category_id"] == "6024"
    assert res[0]["confidence"] == 0.7

    res = generator.suggest_category_from_data({"item_name": "Random item"})
    assert res[0]["category_id"] == "293"
    assert res[0]["confidence"] == 0.3
