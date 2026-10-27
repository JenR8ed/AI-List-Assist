import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from services.vision_service import VisionService

@pytest.fixture
def vision_service():
    return VisionService(api_key="test_key")


async def test_close_before_async_use_does_not_create_client():
    with patch("services.vision_service.GeminiRestClient"), patch(
        "services.vision_service.httpx.AsyncClient"
    ) as client_factory:
        service = VisionService(api_key="test_key")
        await service.close_async()
        await service.close_async()
        client_factory.assert_not_called()


async def test_async_client_reuse_isolation_and_reopen():
    with patch("services.vision_service.GeminiRestClient"):
        first = VisionService(api_key="test_key")
        second = VisionService(api_key="test_key")

    try:
        first_client = first.async_client
        second_client = second.async_client
        assert isinstance(first_client, httpx.AsyncClient)
        assert first.async_client is first_client
        assert first_client is not second_client

        await first.close_async()
        await first.close_async()
        assert first_client.is_closed
        assert not second_client.is_closed
        assert second.async_client is second_client

        reopened_client = first.async_client
        assert reopened_client is not first_client
        assert not reopened_client.is_closed
        assert first.async_client is reopened_client
    finally:
        await first.close_async()
        await second.close_async()

def test_parse_gemini_response_valid_markdown_json(vision_service):
    response_text = """
    ```json
    {
        "items": [
            {
                "item_id": "item_1",
                "probable_category": "Electronics",
                "detected_text": ["Sony", "Walkman"],
                "brand": "Sony",
                "model": "WM-FX195"
            }
        ]
    }
    ```
    """
    items = vision_service._parse_gemini_response(response_text)
    assert len(items) == 1
    assert items[0].item_id == "item_1"
    assert items[0].probable_category == "Electronics"
    assert items[0].brand == "Sony"
    assert items[0].model == "WM-FX195"

def test_parse_gemini_response_valid_raw_json(vision_service):
    response_text = """
    {
        "items": [
            {
                "item_id": "test_id",
                "probable_category": "Clothing",
                "brand": "Nike"
            }
        ]
    }
    """
    items = vision_service._parse_gemini_response(response_text)
    assert len(items) == 1
    assert items[0].item_id == "test_id"
    assert items[0].probable_category == "Clothing"
    assert items[0].brand == "Nike"

def test_parse_gemini_response_invalid_json_format(vision_service):
    response_text = "This is not json."
    items = vision_service._parse_gemini_response(response_text)
    assert len(items) == 1
    assert items[0].probable_category == "Unknown"

@patch("services.vision_service.logger.error")
def test_parse_gemini_response_json_decode_error(mock_logger_error, vision_service):
    response_text = """
    {
        "items": [
            {
                "item_id": "item_1",
                "probable_category": "Electronics"
    }
    """
    items = vision_service._parse_gemini_response(response_text)
    assert len(items) == 1
    assert items[0].probable_category == "Unknown"
    mock_logger_error.assert_called_once()

@patch("services.vision_service.logger.error")
def test_detect_with_gemini_json_decode_error(mock_logger_error, vision_service):
    # Setup mock to return invalid JSON
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value = ("""
    {
        "items": [
            {
                "item_id": "item_1",
                "probable_category": "Electronics"
    }
    """, {})
    vision_service.gemini_client = mock_instance

    items = vision_service._detect_with_gemini("fake_base64", "image/jpeg")

    assert len(items) == 1
    assert items[0].probable_category == "Unknown"
    mock_logger_error.assert_called_once()

@patch("services.vision_service.logger.error")
async def test_detect_with_gemini_async_json_decode_error(mock_logger_error, vision_service):
    # Setup mock to return invalid JSON
    mock_instance = MagicMock()
    mock_instance.generate_content_async = AsyncMock(return_value=("""
    {
        "items": [
            {
                "item_id": "item_1",
                "probable_category": "Electronics"
    }
    """, {}))
    vision_service.gemini_client = mock_instance

    items = await vision_service._detect_with_gemini_async("fake_base64", "image/jpeg")

    assert len(items) == 1
    assert items[0].probable_category == "Unknown"
    mock_logger_error.assert_called_once()
