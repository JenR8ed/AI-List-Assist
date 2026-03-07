"""
Vision & OCR Service
Detects multiple items in images using Google Cloud Vision API and Gemini Vision.
"""

import logging
import json
import os
from typing import List, Dict, Any, Optional
import httpx
from shared.models import DetectedItem, BoundingBox
from services.gemini_rest_client import GeminiRestClient
import requests
import httpx
import base64
import re

logger = logging.getLogger(__name__)

class VisionService:
    """Service for multi-item detection and OCR using Google Vision APIs."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize vision service with Google APIs."""
        if not api_key:
            api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not provided")

        self.api_key = api_key
        self.last_usage_metadata = {}
        self.session = requests.Session()
        
        # Initialize Gemini client
        try:
            self.gemini_client = GeminiRestClient(api_key=api_key, model="gemini-1.5-flash")
        except:
            self.gemini_client = GeminiRestClient(api_key=api_key, model="gemini-pro-vision")
    
    def detect_items(self, image_base64: str, media_type: str) -> List[DetectedItem]:
        """Detect items using Google Cloud Vision API first, fallback to Gemini."""
        
        # Try Google Cloud Vision API first
        try:
            return self._detect_with_cloud_vision(image_base64)
        except Exception as e:
            logger.warning(f"Cloud Vision failed: {e}, falling back to Gemini")
            return self._detect_with_gemini(image_base64, media_type)

    async def detect_items_async(self, image_base64: str, media_type: str) -> List[DetectedItem]:
        """Detect items using Google Cloud Vision API first, fallback to Gemini, asynchronously."""

        # Try Google Cloud Vision API first
        try:
            return await self._detect_with_cloud_vision_async(image_base64)
        except Exception as e:
            print(f"Cloud Vision failed: {e}, falling back to Gemini")
            return await self._detect_with_gemini_async(image_base64, media_type)
    
    def _detect_with_cloud_vision(self, image_base64: str) -> List[DetectedItem]:
        """Use Google Cloud Vision API for object detection."""
        
        url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
        
        payload = {
            "requests": [{
                "image": {"content": image_base64},
                "features": [
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                    {"type": "TEXT_DETECTION", "maxResults": 10},
                    {"type": "LABEL_DETECTION", "maxResults": 10}
                ]
            }]
        }
        
        response = self.session.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return self._parse_cloud_vision_response(data)

    async def _detect_with_cloud_vision_async(self, image_base64: str) -> List[DetectedItem]:
        """Use Google Cloud Vision API for object detection asynchronously."""

        url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"

        payload = {
            "requests": [{
                "image": {"content": image_base64},
                "features": [
                    {"type": "OBJECT_LOCALIZATION", "maxResults": 10},
                    {"type": "TEXT_DETECTION", "maxResults": 10},
                    {"type": "LABEL_DETECTION", "maxResults": 10}
                ]
            }]
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        return self._parse_cloud_vision_response(data)
    
    def _parse_cloud_vision_response(self, data: Dict) -> List[DetectedItem]:
        """Parse Google Cloud Vision API response."""
        
        items = []
        responses = data.get("responses", [{}])
        
        if not responses:
            return [self._create_default_item()]
        
        response = responses[0]
        
        # Get objects
        objects = response.get("localizedObjectAnnotations", [])
        texts = response.get("textAnnotations", [])
        labels = response.get("labelAnnotations", [])
        
        # Extract text for brand/model detection
        detected_texts = []
        if texts:
            detected_texts = [text["description"] for text in texts[1:]]  # Skip first (full text)
        
        # Create items from detected objects
        for idx, obj in enumerate(objects):
            vertices = obj.get("boundingPoly", {}).get("normalizedVertices", [])
            
            if vertices:
                # Convert normalized coordinates to pixel estimates (assuming 1000x1000)
                x = int(vertices[0].get("x", 0) * 1000)
                y = int(vertices[0].get("y", 0) * 1000)
                width = int((vertices[2].get("x", 1) - vertices[0].get("x", 0)) * 1000)
                height = int((vertices[2].get("y", 1) - vertices[0].get("y", 0)) * 1000)
            else:
                x = y = width = height = 0
            
            bbox = BoundingBox(x=x, y=y, width=width, height=height)
            
            item = DetectedItem(
                item_id=f"item_{idx + 1}",
                bbox=bbox,
                confidence=obj.get("score", 0.5),
                probable_category=obj.get("name", "Unknown"),
                detected_text=detected_texts,
                brand=self._extract_brand(detected_texts),
                model=self._extract_model(detected_texts)
            )
            items.append(item)
        
        # If no objects detected, create default item with available text/labels
        if not items:
            item = DetectedItem(
                item_id="item_1",
                bbox=BoundingBox(x=0, y=0, width=0, height=0),
                confidence=0.7,
                probable_category=labels[0]["description"] if labels else "Unknown",
                detected_text=detected_texts,
                brand=self._extract_brand(detected_texts),
                model=self._extract_model(detected_texts)
            )
            items.append(item)
        
        return items
    
    def _extract_brand(self, texts: List[str]) -> Optional[str]:
        """Extract brand from detected text."""
        common_brands = ["Sony", "Apple", "Samsung", "Nike", "Adidas", "Canon", "Nikon"]
        for text in texts:
            for brand in common_brands:
                if brand.lower() in text.lower():
                    return brand
        return None
    
    def _extract_model(self, texts: List[str]) -> Optional[str]:
        """Extract model from detected text."""
        for text in texts:
            # Look for model patterns (letters + numbers)
            model_match = re.search(r'[A-Z]{2,}[-\s]?\d{3,}', text)
            if model_match:
                return model_match.group()
        return None
    
    def _parse_gemini_response(self, response_text: str) -> List[DetectedItem]:
        """Parse Gemini JSON response."""
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            try:
                data = json.loads(json_str)
                items = []
                for idx, item_data in enumerate(data.get("items", [])):
                    item = DetectedItem(
                        item_id=item_data.get("item_id", f"item_{idx + 1}"),
                        bbox=BoundingBox(x=0, y=0, width=0, height=0),
                        confidence=0.7,
                        probable_category=item_data.get("probable_category"),
                        detected_text=item_data.get("detected_text", []),
                        brand=item_data.get("brand"),
                        model=item_data.get("model")
                    )
                    items.append(item)
                return items if items else [self._create_default_item()]
            except json.JSONDecodeError:
                pass

        return [self._create_default_item()]

    def _detect_with_gemini(self, image_base64: str, media_type: str) -> List[DetectedItem]:
        """Fallback to Gemini Vision API."""
        
        prompt = """Analyze this image and detect ALL distinct items visible.

For each item, provide:
1. Item category/type
2. Any visible text (brand names, model numbers)
3. Brand name if visible
4. Model number if visible

Return JSON: {"items": [{"item_id": "item_1", "probable_category": "Electronics", "detected_text": ["Sony"], "brand": "Sony", "model": "WH-1000XM4"}]}"""
        
        try:
            response_text, usage_metadata = self.gemini_client.generate_content(
                prompt,
                inline_image_base64=image_base64,
                inline_image_mime_type=media_type,
                temperature=0.2,
                max_output_tokens=1024,
            )
            
            # Store usage metadata for tracking
            self.last_usage_metadata = usage_metadata
            return self._parse_gemini_response(response_text)

        except Exception as e:
            print(f"Gemini Vision error: {e}")
            return [self._create_default_item()]

    async def _detect_with_gemini_async(self, image_base64: str, media_type: str) -> List[DetectedItem]:
        """Fallback to Gemini Vision API asynchronously."""

        prompt = """Analyze this image and detect ALL distinct items visible.

For each item, provide:
1. Item category/type
2. Any visible text (brand names, model numbers)
3. Brand name if visible
4. Model number if visible

Return JSON: {"items": [{"item_id": "item_1", "probable_category": "Electronics", "detected_text": ["Sony"], "brand": "Sony", "model": "WH-1000XM4"}]}"""

        try:
            response_text, usage_metadata = await self.gemini_client.generate_content_async(
                prompt,
                inline_image_base64=image_base64,
                inline_image_mime_type=media_type,
                temperature=0.2,
                max_output_tokens=1024,
            )
            
            # Store usage metadata for tracking
            self.last_usage_metadata = usage_metadata
            return self._parse_gemini_response(response_text)
        
        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            return [self._create_default_item()]

    async def _detect_with_gemini_async(self, image_base64: str, media_type: str) -> List[DetectedItem]:
        """Fallback to Gemini Vision API (async)."""

        prompt = """Analyze this image and detect ALL distinct items visible.

For each item, provide:
1. Item category/type
2. Any visible text (brand names, model numbers)
3. Brand name if visible
4. Model number if visible

Return JSON: {"items": [{"item_id": "item_1", "probable_category": "Electronics", "detected_text": ["Sony"], "brand": "Sony", "model": "WH-1000XM4"}]}"""

        try:
            response_text, usage_metadata = await self.gemini_client.generate_content_async(
                prompt,
                inline_image_base64=image_base64,
                inline_image_mime_type=media_type,
                temperature=0.2,
                max_output_tokens=1024,
            )

            # Store usage metadata for tracking
            self.last_usage_metadata = usage_metadata

            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                try:
                    data = json.loads(json_str)
                    items = []
                    for idx, item_data in enumerate(data.get("items", [])):
                        item = DetectedItem(
                            item_id=item_data.get("item_id", f"item_{idx + 1}"),
                            bbox=BoundingBox(x=0, y=0, width=0, height=0),
                            confidence=0.7,
                            probable_category=item_data.get("probable_category"),
                            detected_text=item_data.get("detected_text", []),
                            brand=item_data.get("brand"),
                            model=item_data.get("model")
                        )
                        items.append(item)
                    return items if items else [self._create_default_item()]
                except json.JSONDecodeError:
                    pass

            return [self._create_default_item()]

        except Exception as e:
            logger.error(f"Gemini Vision error: {e}")
            return [self._create_default_item()]
    
    def _create_default_item(self) -> DetectedItem:
        """Create a default item when detection fails."""
        return DetectedItem(
            item_id="item_1",
            bbox=BoundingBox(x=0, y=0, width=0, height=0),
            confidence=0.5,
            probable_category="Unknown"
        )
    
    def extract_text(self, image_base64: str, media_type: str) -> List[str]:
        """Extract text using Google Cloud Vision API."""
        
        try:
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
            
            payload = {
                "requests": [{
                    "image": {"content": image_base64},
                    "features": [{"type": "TEXT_DETECTION", "maxResults": 50}]
                }]
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            responses = data.get("responses", [{}])
            
            if responses and "textAnnotations" in responses[0]:
                texts = responses[0]["textAnnotations"]
                return [text["description"] for text in texts[1:]]  # Skip first (full text)
            
            return []
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return []
    def get_usage_metadata(self) -> Dict[str, Any]:
        """Get usage metadata from last Gemini call."""
        return self.last_usage_metadata