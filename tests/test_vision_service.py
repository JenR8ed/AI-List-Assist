import sys
import unittest
from unittest.mock import MagicMock, patch
import asyncio
import json

class TestVisionService(unittest.TestCase):
    def setUp(self):
        # Apply patch to sys.modules specifically for the duration of the test run to avoid breaking other tests
        self.modules_patcher = patch.dict(sys.modules, {
            'dotenv': MagicMock(),
            'google.generativeai': MagicMock(),
            'google': MagicMock(),
            'httpx': MagicMock(),
            'PIL': MagicMock(),
            'PIL.Image': MagicMock(),
            'flask': MagicMock(),
            'requests': MagicMock()
        })
        self.modules_patcher.start()

        # Import VisionService AFTER the dependencies are mocked
        from services.vision_service import VisionService
        self.vision_service = VisionService(api_key="test_key")

    def tearDown(self):
        self.modules_patcher.stop()

    def test_gemini_json_decode_error(self):
        # Mocking the gemini client generate_content to return malformed json
        self.vision_service.gemini_client = MagicMock()

        # This response contains malformed json missing a quote
        malformed_json_response = """
        Here is the detected item:
        {
            "items": [
                {
                    "item_id": "item_1",
                    "probable_category": Electronics",
                    "detected_text": ["Sony"],
                    "brand": "Sony",
                    "model": "WH-1000XM4"
                }
            ]
        }
        """
        # In VisionService, the call is: response_text, usage_metadata = self.gemini_client.generate_content(...)
        self.vision_service.gemini_client.generate_content.return_value = (malformed_json_response, {})

        result = self.vision_service._detect_with_gemini("fake_base64", "image/jpeg")

        # Due to malformed JSON, we expect it to fallback to the default item
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].item_id, "item_1")
        self.assertEqual(result[0].probable_category, "Unknown")
        self.assertEqual(result[0].confidence, 0.5)

    def test_gemini_no_json(self):
        self.vision_service.gemini_client = MagicMock()

        # This response contains no json
        no_json_response = "I couldn't detect any items in this image."
        self.vision_service.gemini_client.generate_content.return_value = (no_json_response, {})

        result = self.vision_service._detect_with_gemini("fake_base64", "image/jpeg")

        # No JSON found, we expect it to fallback to the default item
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].item_id, "item_1")
        self.assertEqual(result[0].probable_category, "Unknown")
        self.assertEqual(result[0].confidence, 0.5)

    def test_gemini_async_json_decode_error(self):
        # Setting up for async test
        self.vision_service.gemini_client = MagicMock()

        malformed_json_response = """
        {
            "items": [
                {
                    "item_id": "item_1",
                    "probable_category": Electronics",
                    "detected_text": ["Sony"]
                }
            ]
        }
        """

        async def mock_generate_content_async(*args, **kwargs):
            return (malformed_json_response, {})

        self.vision_service.gemini_client.generate_content_async = mock_generate_content_async

        result = asyncio.run(self.vision_service._detect_with_gemini_async("fake_base64", "image/jpeg"))

        # Expecting default item fallback
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].item_id, "item_1")
        self.assertEqual(result[0].probable_category, "Unknown")
        self.assertEqual(result[0].confidence, 0.5)

if __name__ == '__main__':
    unittest.main()
