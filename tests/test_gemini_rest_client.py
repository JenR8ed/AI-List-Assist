import pytest
import os
os.environ['GOOGLE_API_KEY'] = 'test'
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

from services.gemini_rest_client import GeminiRestClient

# --- Dummy Data ---
SUCCESS_TOKEN_COUNT_RESPONSE = {
    "totalTokens": 42
}

SUCCESS_GENERATE_RESPONSE = {
    "usageMetadata": {"totalTokenCount": 10},
    "candidates": [
        {
            "content": {
                "parts": [{"text": "Hello, world!"}]
            }
        }
    ]
}

class TestGeminiRestClient:
    def test_init_success(self):
        client = GeminiRestClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.model == "gemini-2.5-flash"
        assert client.api_base == "https://generativelanguage.googleapis.com"
        assert client.api_version == "v1beta"

    def test_init_missing_api_key(self):
        with pytest.raises(ValueError, match="api_key is required"):
            GeminiRestClient(api_key="")

    @patch("services.gemini_rest_client.requests.Session.post")
    def test_count_tokens_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = SUCCESS_TOKEN_COUNT_RESPONSE
        mock_post.return_value = mock_response

        client = GeminiRestClient(api_key="test_key")
        token_count = client.count_tokens("test prompt")

        assert token_count.get('totalTokens') == 42 if isinstance(token_count, dict) else token_count == 42
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "models/gemini-2.5-flash:countTokens" in args[0]
        assert "test prompt" in kwargs["json"]["contents"][0]["parts"][0]["text"]

    @pytest.mark.parametrize("method_name", ["count_tokens", "count_tokens_async"])
    def test_count_tokens_missing_mime(self, method_name):
        client = GeminiRestClient(api_key="test_key")
        with pytest.raises(ValueError, match="inline_image_mime_type is required when providing inline_image_base64"):
            if method_name == "count_tokens":
                client.count_tokens("test", inline_image_base64="data")
            else:
                import asyncio
                asyncio.run(client.count_tokens_async("test", inline_image_base64="data"))

    @patch("services.gemini_rest_client.requests.Session.post")
    def test_count_tokens_with_image(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"totalTokens": 84}
        mock_post.return_value = mock_response

        client = GeminiRestClient(api_key="test_key")
        token_count = client.count_tokens(
            "test prompt",
            inline_image_base64="base64data",
            inline_image_mime_type="image/jpeg"
        )

        assert token_count.get('totalTokens') == 84 if isinstance(token_count, dict) else token_count == 84
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        parts = kwargs["json"]["contents"][0]["parts"]
        assert len(parts) == 2
        assert "inlineData" in parts[1]
        assert parts[1]["inlineData"]["mimeType"] == "image/jpeg"
        assert parts[1]["inlineData"]["data"] == "base64data"

    @pytest.mark.asyncio
    @patch("services.gemini_rest_client.httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_count_tokens_async_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = SUCCESS_TOKEN_COUNT_RESPONSE
        mock_post.return_value = mock_response

        client = GeminiRestClient(api_key="test_key")
        token_count = await client.count_tokens_async("test prompt")

        assert token_count.get('totalTokens') == 42 if isinstance(token_count, dict) else token_count == 42
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_tokens_async_missing_mime(self):
        client = GeminiRestClient(api_key="test_key")
        with pytest.raises(ValueError, match="inline_image_mime_type is required when providing inline_image_base64"):
            await client.count_tokens_async("test", inline_image_base64="data")

    @pytest.mark.asyncio
    @patch("services.gemini_rest_client.httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_count_tokens_async_with_image(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"totalTokens": 84}
        mock_post.return_value = mock_response

        client = GeminiRestClient(api_key="test_key")
        token_count = await client.count_tokens_async(
            "test prompt",
            inline_image_base64="base64data",
            inline_image_mime_type="image/jpeg"
        )

        assert token_count.get('totalTokens') == 84 if isinstance(token_count, dict) else token_count == 84
        mock_post.assert_called_once()

    @patch("services.gemini_rest_client.requests.Session.post")
    def test_generate_content_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = SUCCESS_GENERATE_RESPONSE
        mock_post.return_value = mock_response

        client = GeminiRestClient(api_key="test_key")
        text, usage = client.generate_content("test prompt")

        assert text == "Hello, world!"
        assert usage["totalTokenCount"] == 10
        mock_post.assert_called_once()

    @patch("services.gemini_rest_client.requests.Session.post")
    def test_generate_content_no_candidates(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        client = GeminiRestClient(api_key="test_key")
        with pytest.raises(RuntimeError, match="No candidates in response"):
            client.generate_content("test prompt")

    @patch("services.gemini_rest_client.requests.Session.post")
    def test_generate_content_no_text_parts(self, mock_post):
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

    def test_generate_content_missing_mime(self):
        client = GeminiRestClient(api_key="test_key")
        with pytest.raises(ValueError, match="inline_image_mime_type is required when providing inline_image_base64"):
            client.generate_content("test", inline_image_base64="data")

    @patch("services.gemini_rest_client.requests.Session.post")
    def test_generate_content_with_image(self, mock_post):
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
            inline_image_mime_type="image/jpeg"
        )

        assert text == "Hello, world from image!"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.gemini_rest_client.httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_generate_content_async_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = SUCCESS_GENERATE_RESPONSE
        mock_post.return_value = mock_response

        client = GeminiRestClient(api_key="test_key")
        text, usage = await client.generate_content_async("test prompt")

        assert text == "Hello, world!"
        assert usage["totalTokenCount"] == 10
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_content_async_missing_mime(self):
        client = GeminiRestClient(api_key="test_key")
        with pytest.raises(ValueError, match="inline_image_mime_type is required when providing inline_image_base64"):
            await client.generate_content_async("test", inline_image_base64="data")

    @pytest.mark.asyncio
    @patch("services.gemini_rest_client.httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_generate_content_async_with_image(self, mock_post):
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
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch("services.gemini_rest_client.httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_generate_content_async_no_candidates(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        client = GeminiRestClient(api_key="test_key")
        with pytest.raises(RuntimeError, match="No candidates in response"):
            await client.generate_content_async("test prompt")

    @pytest.mark.asyncio
    @patch("services.gemini_rest_client.httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_generate_content_async_no_text_parts(self, mock_post):
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
