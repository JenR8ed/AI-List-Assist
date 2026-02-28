import base64
from services.mock_valuation_service import MockValuationService

def test_mock_val():
    service = MockValuationService()
    # Create fake base64 image
    with open('test_data/iphone.jpg', 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
    res = service.evaluate_item(img_b64, 'image/jpeg')
    print("Mock Valuation Result:")
    print(res.to_dict())

if __name__ == "__main__":
    test_mock_val()
