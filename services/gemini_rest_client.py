"""
Gemini REST Client (no google-generativeai dependency)

Uses Google Generative Language REST API via `requests` and `httpx`, avoiding protobuf issues on Python 3.14.
Supports native structured outputs (`responseMimeType` + `responseSchema`) and `x-goog-api-key` headers.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import httpx
import requests


class GeminiRestClient:
    """
    Minimal client for Gemini `generateContent` endpoint with native structured output support.

    Docs: https://ai.google.dev/
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        api_base: str = "https://generativelanguage.googleapis.com",
        api_version: str = "v1beta",
        timeout_s: int = 60,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.api_version = api_version
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update({"x-goog-api-key": self.api_key})
        self.async_client = httpx.AsyncClient(
            timeout=self.timeout_s,
            headers={"x-goog-api-key": self.api_key},
        )

    def _build_headers(self) -> Dict[str, str]:
        return {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def _prepare_payload(
        self,
        prompt: str,
        inline_image_base64: Optional[str] = None,
        inline_image_mime_type: Optional[str] = None,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        parts: List[Dict[str, Any]] = [{"text": prompt}]
        if inline_image_base64:
            if not inline_image_mime_type:
                raise ValueError("inline_image_mime_type is required when providing inline_image_base64")
            parts.append(
                {
                    "inlineData": {
                        "mimeType": inline_image_mime_type,
                        "data": inline_image_base64,
                    }
                }
            )

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": parts,
                }
            ]
        }
        if generation_config:
            payload["generationConfig"] = generation_config
        return payload

    def _build_generation_config(
        self,
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
        response_mime_type: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config: Dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_output_tokens,
        }
        if response_mime_type:
            config["responseMimeType"] = response_mime_type
        elif response_schema:
            config["responseMimeType"] = "application/json"
        if response_schema:
            config["responseSchema"] = response_schema
        return config

    def _parse_generate_content_response(self, data: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        usage_metadata = data.get("usageMetadata", {})

        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError(f"No candidates in response: {json.dumps(data)[:2000]}")

        content = candidates[0].get("content") or {}
        parts_out = content.get("parts") or []
        texts = []
        for p in parts_out:
            t = p.get("text")
            if t:
                texts.append(t)
        if not texts:
            raise RuntimeError(f"No text parts in response: {json.dumps(data)[:2000]}")

        return "\n".join(texts), usage_metadata

    def count_tokens(
        self,
        prompt: str,
        *,
        inline_image_base64: Optional[str] = None,
        inline_image_mime_type: Optional[str] = None,
    ) -> Dict[str, int]:
        """Count tokens for content before making request."""
        url = f"{self.api_base}/{self.api_version}/models/{self.model}:countTokens"
        payload = self._prepare_payload(prompt, inline_image_base64, inline_image_mime_type)

        resp = self.session.post(url, json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()

        return {"totalTokens": data.get("totalTokens", 0)}

    async def count_tokens_async(
        self,
        prompt: str,
        *,
        inline_image_base64: Optional[str] = None,
        inline_image_mime_type: Optional[str] = None,
    ) -> Dict[str, int]:
        """Count tokens for content before making request asynchronously."""
        url = f"{self.api_base}/{self.api_version}/models/{self.model}:countTokens"
        payload = self._prepare_payload(prompt, inline_image_base64, inline_image_mime_type)

        resp = await self.async_client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        return {"totalTokens": data.get("totalTokens", 0)}

    def generate_content(
        self,
        prompt: str,
        *,
        inline_image_base64: Optional[str] = None,
        inline_image_mime_type: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
        response_mime_type: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, Dict[str, Any]]:
        url = f"{self.api_base}/{self.api_version}/models/{self.model}:generateContent"
        generation_config = self._build_generation_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type=response_mime_type,
            response_schema=response_schema,
        )
        payload = self._prepare_payload(prompt, inline_image_base64, inline_image_mime_type, generation_config)

        resp = self.session.post(url, json=payload, timeout=self.timeout_s)
        resp.raise_for_status()
        data = resp.json()

        return self._parse_generate_content_response(data)

    async def generate_content_async(
        self,
        prompt: str,
        *,
        inline_image_base64: Optional[str] = None,
        inline_image_mime_type: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 1024,
        response_mime_type: Optional[str] = None,
        response_schema: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, Dict[str, Any]]:
        """Async version of generate_content."""
        url = f"{self.api_base}/{self.api_version}/models/{self.model}:generateContent"
        generation_config = self._build_generation_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type=response_mime_type,
            response_schema=response_schema,
        )
        payload = self._prepare_payload(prompt, inline_image_base64, inline_image_mime_type, generation_config)

        resp = await self.async_client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

        return self._parse_generate_content_response(data)
