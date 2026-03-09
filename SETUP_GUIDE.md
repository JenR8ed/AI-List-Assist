# eBay Listing Assistant - Setup & Usage Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys
Your `.env` file is already configured with:
- ✅ Google API Key (for Gemini Vision)
- ✅ eBay Client ID & Secret

### 3. Run the Application
```bash
python app_enhanced.py
```

### 4. Open in Browser
Visit: **http://localhost:5000**

## 📱 How to Use

### Upload & Analyze Items
1. **Take a photo** of the item you want to sell
2. **Upload the image** using the web interface
3. **Click "Analyze Item"**
4. **Get instant valuation** with:
   - Estimated value
   - Condition assessment
   - Profitability rating
   - Selling recommendations

### Different Images = Different Results
The app provides varied valuations based on image content:
- **Electronics** → Higher values (~$180-320)
- **Collectibles** → Lower values (~$8-50)
- **Branded items** → Better profitability

## 🧪 Test with Sample Data

Use the provided test images in `test_data/`:
- `sony_headphones.jpg` → High-value electronics
- `vintage_mug.jpg` → Low-value collectible
- `iphone.jpg` → High-value phone

## 🔧 API Testing with Postman

### Import Collection
1. Import `eBay_Listing_Assistant_API.postman_collection.json`
2. Import `eBay_Listing_Assistant.postman_environment.json`
3. Select the environment in Postman

### Test Endpoints
- **GET** `/` → Web interface
- **POST** `/api/analyze` → Image analysis
- **POST** `/api/conversation/start` → Start listing conversation
- **POST** `/api/listing/create` → Generate listing

## 📊 Current Features

### ✅ Working Now
- Image upload and analysis
- Real eBay market scraping (sold comps & filters)
- **NEW**: Actual eBay Listing Creation (Inventory API Offer flow)
- **NEW**: "Send Offer" to Buyers (Negotiation API support)
- Web interface & Dashboard
- API endpoints
- Postman testing

### ⏳ Coming Soon (After eBay Approval)
- Real eBay market data
- Live sold price analysis
- Actual listing creation

## 🛠️ Technical Details

### Architecture
- **Frontend**: HTML/CSS/JavaScript
- **Backend**: Flask (Python)
- **Vision**: Gemini API (custom REST client)
- **Data**: Mock valuation service
- **Database**: SQLite

### File Structure
```
├── app_enhanced.py          # Main Flask application
├── services/
│   ├── vision_service.py    # Gemini vision API
│   ├── valuation_service.py # Item valuation logic
│   └── mock_valuation_service.py # Test data
├── templates/
│   └── index.html          # Web interface
├── test_data/              # Sample images
└── .env                    # API keys
```

## 🔑 API Keys Explained

### Google API Key
- **Purpose**: Powers Gemini vision analysis
- **Status**: ✅ Working
- **Used for**: Image recognition, text extraction

### eBay API Keys
- **Purpose**: Market data and listing creation
- **Status**: ⏳ Pending approval
- **Used for**: Real price data, listing to eBay

## 🐛 Troubleshooting

### App Won't Start
```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Run app
python app_enhanced.py
```

### No Valuation Results
- App uses mock data while eBay API is pending
- Different images should show different results
- Check browser console for errors

### API Errors
- Gemini API: Check `GOOGLE_API_KEY` in `.env`
- eBay API: Waiting for approval (expected to fail)

## 📈 Next Steps

1. **Test the current app** with sample images
2. **Wait for eBay API approval** (1-2 business days)
3. **Switch to real market data** when approved
4. **Deploy to production** when ready

## 💡 Tips

- **Use clear, well-lit photos** for best results
- **Include brand names/model numbers** in images
- **Test with different item types** to see varied valuations
- **Check the uploads/ folder** to see saved images

---

**Ready to start?** Run `python app_enhanced.py` and visit http://localhost:5000
