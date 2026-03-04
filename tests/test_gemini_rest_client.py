import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock

# Mock out modules that might cause ImportErrors during testing
sys.modules['dotenv'] = MagicMock()
sys.modules['flask'] = MagicMock()

from services.gemini_rest_client import GeminiRestClient

def test_init_success(client):
    assert client.api_key == "test_key"
    assert client.model == "gemini-2.5-flash"

def test_init_missing_api_key():
    with pytest.raises(ValueError, match="api_key is required"):
        GeminiRestClient(api_key="")

@patch("services.gemini_rest_client.requests.Session.post")
def test_count_tokens_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"totalTokens": 42}
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    result = client.count_tokens("test prompt")

    assert result == {"totalTokens": 42}
    mock_post.assert_called_once()

    # check that inlineData is NOT sent
    args, kwargs = mock_post.call_args
    assert "inlineData" not in kwargs["json"]["contents"][0]["parts"][0]

def test_count_tokens_missing_mime():
    client = GeminiRestClient(api_key="test_key")
    with pytest.raises(ValueError, match="inline_image_mime_type is required when providing inline_image_base64"):
        client.count_tokens("test prompt", inline_image_base64="base64data")

@patch("services.gemini_rest_client.requests.Session.post")
def test_count_tokens_with_image(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"totalTokens": 84}
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    result = client.count_tokens(
        "test prompt",
        inline_image_base64="base64data",
        inline_image_mime_type="image/jpeg"
    )

    assert result == {"totalTokens": 84}
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    parts = kwargs["json"]["contents"][0]["parts"]
    assert len(parts) == 2
    assert parts[1]["inlineData"]["mimeType"] == "image/jpeg"
    assert parts[1]["inlineData"]["data"] == "base64data"

@pytest.mark.asyncio
@patch("services.gemini_rest_client.httpx.AsyncClient.post")
async def test_count_tokens_async_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"totalTokens": 42}
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    result = await client.count_tokens_async("test prompt")

    assert result == {"totalTokens": 42}
    mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_count_tokens_async_missing_mime():
    client = GeminiRestClient(api_key="test_key")
    with pytest.raises(ValueError, match="inline_image_mime_type is required when providing inline_image_base64"):
        await client.count_tokens_async("test prompt", inline_image_base64="base64data")

@pytest.mark.asyncio
@patch("services.gemini_rest_client.httpx.AsyncClient.post")
async def test_count_tokens_async_with_image(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"totalTokens": 84}
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    result = await client.count_tokens_async(
        "test prompt",
        inline_image_base64="base64data",
        inline_image_mime_type="image/jpeg"
    )

    assert result == {"totalTokens": 84}
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    parts = kwargs["json"]["contents"][0]["parts"]
    assert len(parts) == 2
    assert parts[1]["inlineData"]["mimeType"] == "image/jpeg"

@patch("services.gemini_rest_client.requests.Session.post")
def test_generate_content_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "usageMetadata": {"totalTokenCount": 10},
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello, world!"}]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    text, usage = client.generate_content("test prompt")

    assert text == "Hello, world!"
    assert usage == {"totalTokenCount": 10}
    mock_post.assert_called_once()

@patch("services.gemini_rest_client.requests.Session.post")
def test_generate_content_no_candidates(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    with pytest.raises(RuntimeError, match="No candidates in response"):
        client.generate_content("test prompt")

@patch("services.gemini_rest_client.requests.Session.post")
def test_generate_content_no_text_parts(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"other": "stuff"}]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    with pytest.raises(RuntimeError, match="No text parts in response"):
        client.generate_content("test prompt")

def test_generate_content_missing_mime():
    client = GeminiRestClient(api_key="test_key")
    with pytest.raises(ValueError, match="inline_image_mime_type is required when providing inline_image_base64"):
        client.generate_content("test prompt", inline_image_base64="base64data")

@patch("services.gemini_rest_client.requests.Session.post")
def test_generate_content_with_image(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "usageMetadata": {"totalTokenCount": 10},
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello, world from image!"}]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    text, usage = client.generate_content(
        "test prompt",
        inline_image_base64="base64data",
        inline_image_mime_type="image/png"
    )

    assert text == "Hello, world from image!"
    assert usage == {"totalTokenCount": 10}
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    parts = kwargs["json"]["contents"][0]["parts"]
    assert len(parts) == 2
    assert parts[1]["inlineData"]["mimeType"] == "image/png"


@pytest.mark.asyncio
@patch("services.gemini_rest_client.httpx.AsyncClient.post")
async def test_generate_content_async_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "usageMetadata": {"totalTokenCount": 10},
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello, world!"}]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    text, usage = await client.generate_content_async("test prompt")

    assert text == "Hello, world!"
    assert usage == {"totalTokenCount": 10}
    mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_generate_content_async_missing_mime():
    client = GeminiRestClient(api_key="test_key")
    with pytest.raises(ValueError, match="inline_image_mime_type is required when providing inline_image_base64"):
        await client.generate_content_async("test prompt", inline_image_base64="base64data")

@pytest.mark.asyncio
@patch("services.gemini_rest_client.httpx.AsyncClient.post")
async def test_generate_content_async_with_image(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "usageMetadata": {"totalTokenCount": 10},
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello, world!"}]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    text, usage = await client.generate_content_async(
        "test prompt",
        inline_image_base64="base64data",
        inline_image_mime_type="image/jpeg"
    )

    assert text == "Hello, world!"
    assert usage == {"totalTokenCount": 10}
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    parts = kwargs["json"]["contents"][0]["parts"]
    assert len(parts) == 2
    assert parts[1]["inlineData"]["mimeType"] == "image/jpeg"

@pytest.mark.asyncio
@patch("services.gemini_rest_client.httpx.AsyncClient.post")
async def test_generate_content_async_no_candidates(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {}
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    with pytest.raises(RuntimeError, match="No candidates in response"):
        await client.generate_content_async("test prompt")

@pytest.mark.asyncio
@patch("services.gemini_rest_client.httpx.AsyncClient.post")
async def test_generate_content_async_no_text_parts(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"other": "stuff"}]
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    client = GeminiRestClient(api_key="test_key")
    with pytest.raises(RuntimeError, match="No text parts in response"):
        await client.generate_content_async("test prompt")
