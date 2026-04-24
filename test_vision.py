"""
Test Google Vision API integration
"""

import os
import base64
from services.vision_service import VisionService
from dotenv import load_dotenv

load_dotenv()

def test_vision_service():
    """Test the vision service with a sample image."""
    
    # Check if we have an API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ No GOOGLE_API_KEY found in .env file")
        return
    
    print(f"✅ API Key found: [REDACTED]")
    
    try:
        # Initialize vision service
        vision_service = VisionService()
        print("✅ Vision service initialized")
        
        # Test with a sample image (if available)
        test_images = [
            'test_data/iphone.jpg',
            'test_data/sony_headphones.jpg',
            'uploads/20260122_230200_iphone.jpg'
        ]
        
        for image_path in test_images:
            if os.path.exists(image_path):
                print(f"\n🔍 Testing with {image_path}")
                
                # Read and encode image
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # Test detection
                items = vision_service.detect_items(image_base64, 'image/jpeg')
                print(f"✅ Detected {len(items)} items:")
                
                for item in items:
                    print(f"  - {item.item_id}: {item.probable_category}")
                    if item.brand:
                        print(f"    Brand: {item.brand}")
                    if item.model:
                        print(f"    Model: {item.model}")
                    if item.detected_text:
                        print(f"    Text: {item.detected_text[:3]}")
                
                # Test text extraction
                texts = vision_service.extract_text(image_base64, 'image/jpeg')
                print(f"✅ Extracted {len(texts)} text elements:")
                for text in texts[:5]:  # Show first 5
                    print(f"  - {text}")
                
                break
        else:
            print("⚠️ No test images found")
            
    except Exception as e:
        print(f"❌ Error testing vision service: {e}")

if __name__ == "__main__":
    test_vision_service()