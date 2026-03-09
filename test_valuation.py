import base64
from dotenv import load_dotenv

load_dotenv()
from services.valuation_service import ValuationService

def test_valuation():
    service = ValuationService()
    # Create fake base64 image
    with open('test_data/iphone.jpg', 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode('utf-8')
    res = service.evaluate_item(img_b64, 'image/jpeg')
    print("Valuation Result:")
    print(res.to_dict())

if __name__ == "__main__":
    test_valuation()
