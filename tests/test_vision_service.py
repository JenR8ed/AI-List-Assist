from typing import Any, List
import json
import logging
import pytest
from unittest.mock import AsyncMock
from services.vision_service import VisionService

logger = logging.getLogger(__name__)
INVALID_JSON = "{invalid json"

@pytest.fixture
def mock_gemini_client(mocker):
    client = mocker.Mock()
    client.generate_content.return_value = (INVALID_JSON, {})
    client.generate_content_async = AsyncMock(return_value=(INVALID_JSON, {}))
    return client

@pytest.fixture
def mock_async_gemini_client(mocker):
    client = mocker.Mock()
    client.generate_content_async = AsyncMock(return_value=(INVALID_JSON, {}))
    return client

@pytest.fixture
def vision_service(mock_gemini_client, mock_async_gemini_client) -> VisionService:
    service = VisionService(
        api_key="test_key"
    )
    service.gemini_client = mock_gemini_client
    service.async_gemini_client = mock_async_gemini_client
    return service

def _assert_invalid_json_handled(result: List[Any], caplog, suffix: str) -> None:
    assert result == []
    assert any(
        rec.levelno == logging.WARNING
        and f"Gemini returned invalid JSON in {suffix}" in rec.getMessage()
        for rec in caplog.records
    )

def test_detect_with_gemini_json_decode_error(vision_service: VisionService, mock_gemini_client, caplog):
    with caplog.at_level(logging.WARNING):
        result = vision_service._detect_with_gemini("dummy_base64", "image/jpeg")

    mock_gemini_client.generate_content.assert_called_once_with(
        vision_service.GEMINI_PROMPT,
        inline_image_base64="dummy_base64",
        inline_image_mime_type="image/jpeg",
        temperature=0.2,
        max_output_tokens=1024
    )
    _assert_invalid_json_handled(result, caplog, "detect")

@pytest.mark.asyncio
async def test_detect_with_gemini_async_json_decode_error(vision_service: VisionService, mock_async_gemini_client, caplog):
    vision_service.gemini_client = mock_async_gemini_client

    with caplog.at_level(logging.WARNING):
        result = await vision_service._detect_with_gemini_async("dummy_base64", "image/jpeg")

    mock_async_gemini_client.generate_content_async.assert_awaited_once_with(
        vision_service.GEMINI_PROMPT,
        inline_image_base64="dummy_base64",
        inline_image_mime_type="image/jpeg",
        temperature=0.2,
        max_output_tokens=1024
    )
    _assert_invalid_json_handled(result, caplog, "detect_async")
