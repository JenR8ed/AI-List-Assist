"""
Vision & OCR Service
Detects multiple items in images using Google Cloud Vision API and Gemini 2.5 Flash.
Includes Pillow EXIF stripping/downscaling, x-goog-api-key header hygiene, native
responseSchema structured outputs, and 2-stage Cloud Vision + Gemini fusion.
"""

import io
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx
from PIL import Image, UnidentifiedImageError
import requests
from shared.models import BoundingBox, DetectedItem
from shared.schemas.item_response import ITEM_DETECTION_SCHEMA
from services.gemini_rest_client import GeminiRestClient

logger = logging.getLogger(__name__)

_MODEL_PATTERN = re.compile(r"[A-Z]{2,}[-\s]?\d{3,}[A-Z0-9]*")


class VisionService:
    """Service for multi-item detection and OCR using Google Vision APIs."""

    _session = None

    _COMMON_BRANDS = ["Sony", "Apple", "Samsung", "Nike", "Adidas", "Canon", "Nikon"]
    _BRAND_DATA = [(brand.lower(), brand) for brand in _COMMON_BRANDS]
    _MODEL_PATTERN = re.compile(r"[A-Z]{2,}[-\s]?\d{3,}")

    GEMINI_PROMPT = """Analyze this image and detect ALL distinct items visible.

For each item, provide:
1. Item category/type
2. Any visible text (brand names, model numbers)
3. Brand name if visible
4. Model number if visible

Return JSON: {"items": [{"item_id": "item_1", "probable_category": "Electronics", "detected_text": ["Sony"], "brand": "Sony", "model": "WH-1000XM4"}]}"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize vision service with Google APIs."""
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not provided")

        self.api_key = api_key
        self.last_usage_metadata: Dict[str, Any] = {}

        if VisionService._session is None:
            VisionService._session = requests.Session()
        self.session = VisionService._session

        self._async_client: Optional[httpx.AsyncClient] = None

        try:
            self.gemini_client = GeminiRestClient(api_key=api_key, model="gemini-2.5-flash")
        except Exception:
            self.gemini_client = GeminiRestClient(api_key=api_key, model="gemini-1.5-flash")

    @staticmethod
    def sanitize_and_downscale_image(
        image_bytes: bytes,
        max_edge: int = 1536,
        quality: int = 85,
    ) -> Tuple[bytes, str]:
        """
        Validate image magic bytes with Pillow, strip EXIF metadata, and downscale
        large images to keep payload sizes reasonable for Vision/Gemini APIs.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.load()
        except UnidentifiedImageError as e:
            raise ValueError(f"Invalid image data: {e}") from e

        # Strip EXIF / orientation
        if hasattr(img, "_getexif") and img._getexif():
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

        # Convert to RGB if needed
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Downscale if necessary
        w, h = img.size
        if max(w, h) > max_edge:
            scale = max_edge / float(max(w, h))
            new_size = (int(w * scale), int(h * scale))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue(), "image/jpeg"

    def _vision_headers(self) -> Dict[str, str]:
        return {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    def detect_items(self, image_base64: str, media_type: str = "image/jpeg") -> List[DetectedItem]:
        """Synchronous multi-item detection (Cloud Vision + Gemini fusion)."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context - fall back to sync path
                return self._detect_items_sync(image_base64, media_type)
            return loop.run_until_complete(self.detect_items_async(image_base64, media_type))
        except RuntimeError:
            return self._detect_items_sync(image_base64, media_type)

    def _detect_items_sync(self, image_base64: str, media_type: str) -> List[DetectedItem]:
        """Sync implementation."""
        ocr_texts = self.extract_text(image_base64, media_type)
        items = self._detect_with_gemini(image_base64, media_type, ocr_texts)
        return items or [self._create_default_item()]

    async def detect_items_async(self, image_base64: str, media_type: str = "image/jpeg") -> List[DetectedItem]:
        """Async multi-item detection."""
        ocr_texts = self.extract_text(image_base64, media_type)
        items = await self._detect_with_gemini_async(image_base64, media_type, ocr_texts)
        return items or [self._create_default_item()]

    def _build_gemini_prompt(self, ocr_context: Optional[List[str]] = None) -> str:
        prompt = self.GEMINI_PROMPT
        if ocr_context:
            prompt += f"\n\nOCR context from Cloud Vision: {ocr_context[:20]}"
        return prompt

    def _detect_with_gemini(
        self,
        image_base64: str,
        media_type: str,
        ocr_context: Optional[List[str]] = None,
    ) -> List[DetectedItem]:
        """Gemini Vision path (sync)."""
        try:
            prompt = self._build_gemini_prompt(ocr_context)
            response_text, usage_metadata = self.gemini_client.generate_content(
                prompt,
                inline_image_base64=image_base64,
                inline_image_mime_type=media_type,
                temperature=0.2,
                max_output_tokens=1024,
                response_schema=ITEM_DETECTION_SCHEMA,
            )
            self.last_usage_metadata = usage_metadata
            return self._parse_gemini_response(response_text)
        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            return [self._create_default_item()]

    async def _detect_with_gemini_async(
        self,
        image_base64: str,
        media_type: str,
        ocr_context: Optional[List[str]] = None,
    ) -> List[DetectedItem]:
        """Fallback/enrichment via Gemini Vision API (async) with structured responseSchema."""
        try:
            prompt = self._build_gemini_prompt(ocr_context)
            response_text, usage_metadata = await self.gemini_client.generate_content_async(
                prompt,
                inline_image_base64=image_base64,
                inline_image_mime_type=media_type,
                temperature=0.2,
                max_output_tokens=1024,
                response_schema=ITEM_DETECTION_SCHEMA,
            )
            self.last_usage_metadata = usage_metadata
            return self._parse_gemini_response(response_text)
        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            return [self._create_default_item()]

    def _parse_gemini_response(self, response_text: str) -> List[DetectedItem]:
        """Parse Gemini JSON response into DetectedItem list."""
        try:
            clean = response_text
            json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", response_text, re.DOTALL)
            if json_match:
                clean = json_match.group(1)
            else:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start >= 0 and end > start:
                    clean = response_text[start:end]

            data = json.loads(clean)
            items_data = data.get("items", [])
            results = []
            for i, item in enumerate(items_data):
                results.append(
                    DetectedItem(
                        item_id=item.get("item_id", f"item_{i+1}"),
                        bbox=BoundingBox(x=0, y=0, width=0, height=0),
                        confidence=0.85,
                        probable_category=item.get("probable_category"),
                        detected_text=item.get("detected_text") or [],
                        brand=item.get("brand"),
                        model=item.get("model"),
                    )
                )
            return results or [self._create_default_item()]
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return [self._create_default_item()]

    def _create_default_item(self) -> DetectedItem:
        """Create a default item when detection fails."""
        return DetectedItem(
            item_id="item_1",
            bbox=BoundingBox(x=0, y=0, width=0, height=0),
            confidence=0.5,
            probable_category="Unknown",
        )

    def extract_text(self, image_base64: str, media_type: str) -> List[str]:
        """Extract text using Google Cloud Vision API with x-goog-api-key header."""
        try:
            url = "https://vision.googleapis.com/v1/images:annotate"
            payload = {
                "requests": [{
                    "image": {"content": image_base64},
                    "features": [{"type": "TEXT_DETECTION", "maxResults": 50}],
                }]
            }
            response = self.session.post(url, headers=self._vision_headers(), json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            responses = data.get("responses", [{}])
            if responses and "textAnnotations" in responses[0]:
                texts = responses[0]["textAnnotations"]
                return [text["description"] for text in texts[1:]]
            return []
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return []

    def get_usage_metadata(self) -> Dict[str, Any]:
        """Get usage metadata from last Gemini call."""
        return self.last_usage_metadata
