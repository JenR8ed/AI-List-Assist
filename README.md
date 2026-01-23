# eBay Listing Assistant - AI-Powered Listing System

> **End-to-end AI-assisted eBay listing creation system** optimized for Pixel 9 Pro XL and designed to progressively gather information to create eBay listings via Sell APIs.

---

## 🎯 What This Does

This system helps you:
- 📸 **Capture items** with your Pixel 9 Pro XL
- 🤖 **AI analyzes** images to detect and value items
- 💬 **Smart questions** gather missing details progressively
- 📝 **Auto-generates** eBay listings
- 🚀 **Publishes** directly to eBay via Sell APIs

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `.env.example` to `.env` and add your keys:
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### 3. Run the Application
```bash
# Original app
python app.py

# Enhanced app (with all new features)
python app_enhanced.py
```

Visit: **http://localhost:5000**

---

## 📁 Project Structure

```
ebay-listing-assistant/
├── app.py                    # Original Flask app
├── app_enhanced.py           # Enhanced app with all services
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore rules
│
├── services/                # Core services
│   ├── vision_service.py           # Multi-item detection & OCR
│   ├── valuation_service.py        # Enhanced valuation with decision gate
│   ├── conversation_orchestrator.py # Progressive questioning
│   ├── listing_synthesis.py        # Listing generation
│   └── ebay_integration.py         # eBay API client
│
├── shared/                  # Shared components
│   └── models.py            # Data models & schemas
│
├── templates/               # Web UI
│   └── index.html          # Main interface
│
├── scripts/                 # Utility scripts
│   ├── item_valuation.py   # CLI valuation tool
│   └── test_setup.py       # Setup verification
│
└── docs/                    # Documentation
    ├── README.md           # This file
    ├── SETUP.md            # Setup guide
    ├── QUICKSTART.md       # Quick start
    ├── ARCHITECTURE.md     # System architecture
    ├── IMPLEMENTATION_PLAN.md
    ├── ASSESSMENT_SUMMARY.md
    ├── PIXEL_INTEGRATION.md
    ├── gemini-item-valuation-setup.md
    └── QUICK_REFERENCE.md  # API reference
```

---

## ✨ Key Features

### 🤖 AI-Powered Analysis
- **Multi-item detection** - Identifies all items in a single photo
- **Smart valuation** - Determines if items are worth listing
- **Decision gate** - Automatically filters low-value items

### 💬 Progressive Questioning
- **Only asks necessary questions** - No overwhelming forms
- **Natural language** - Human-friendly conversation
- **Smart prioritization** - Asks most important questions first

### 📝 Listing Generation
- **Auto-generated titles** - Optimized for eBay (80 char limit)
- **Rich descriptions** - HTML formatted with all details
- **Item specifics** - Automatically extracted and formatted

### 🔌 eBay Integration
- **OAuth 2.0** - Secure authentication
- **Sell APIs** - Direct listing creation
- **Sandbox support** - Test before going live

---

## 📖 Documentation

All documentation is in the `docs/` folder:

- **[SETUP.md](docs/SETUP.md)** - Detailed setup instructions
- **[QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute quick start
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)** - API endpoints
- **[PIXEL_INTEGRATION.md](docs/PIXEL_INTEGRATION.md)** - Mobile setup

---

## 🔧 Usage Examples

### Analyze Image (Multi-Item Detection)
```bash
POST /api/analyze
Content-Type: multipart/form-data
Body: image file
```

### Start Conversation
```bash
POST /api/conversation/start
{
  "item_id": "item_1",
  "initial_data": {"item_name": "Headphones", "brand": "Sony"}
}
```

### Create Listing
```bash
POST /api/listing/create
{
  "item_id": "item_1",
  "session_id": "..."
}
```

See [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) for complete API documentation.

---

## 🛠️ Development

### Running Tests
```bash
python scripts/test_setup.py
```

### CLI Tool
```bash
python scripts/item_valuation.py photo.jpg --save
```

---

## 📊 System Requirements

- Python 3.8+
- Google Gemini API key
- eBay Developer account (for full integration)
- Flask web server

---

## 🔐 Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional (for eBay integration)
EBAY_APP_ID=your_ebay_app_id
EBAY_CERT_ID=your_ebay_cert_id
EBAY_DEV_ID=your_ebay_dev_id
EBAY_ACCESS_TOKEN=your_ebay_token
```

---

## 🎯 Workflow

```
1. Capture photo with Pixel 9 Pro XL
   ↓
2. Upload to web app
   ↓
3. AI detects and values all items
   ↓
4. Decision gate filters worth listing
   ↓
5. Progressive questioning gathers details
   ↓
6. Listing auto-generated
   ↓
7. Review and publish to eBay
```

---

## 💡 Key Concepts

- **Decision Gate**: Automatically filters items not worth listing
- **Progressive Questioning**: Only asks necessary questions
- **Canonical Format**: Marketplace-agnostic listing structure
- **Multi-Item Support**: Process multiple items from one photo

---

## 🐛 Troubleshooting

See [SETUP.md](docs/SETUP.md) for troubleshooting guide.

Common issues:
- API key not found → Create `.env` file
- Module not found → Run `pip install -r requirements.txt`
- Port in use → Change port in `app.py`

---

## 📈 Cost Estimates

- **Gemini API**: ~$0.0005-0.001 per image analysis
- **Per listing**: ~$0.001-0.002 total
- **Very affordable** at scale!

---

## 🤝 Contributing

This is a modular system designed for extension:
- Add new marketplaces (Etsy, FB Marketplace)
- Customize decision gate thresholds
- Enhance conversation logic
- Add new AI models

---

## 📄 License

See individual files for license information.

---

## 🎉 Getting Started

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Create `.env` with `GOOGLE_API_KEY`
3. ✅ Run: `python app_enhanced.py`
4. ✅ Visit: http://localhost:5000
5. ✅ Upload a photo and start listing!

---

**For detailed documentation, see the [docs/](docs/) folder.**
