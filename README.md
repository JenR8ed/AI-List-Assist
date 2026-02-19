# AI List Assist: AI-Powered eBay Listing System

AI List Assist is a comprehensive, end-to-end system designed to automate the lifecycle of online reselling. By leveraging Google's Gemini Vision and eBay's Sell APIs, the system transforms unstructured photos into structured, marketplace-ready listings with accurate valuations.

---

## 🎯 Key Features

### 🤖 Smart Analysis & Valuation
- **Multi-Item Detection**: Automatically identifies multiple items within a single photograph using Google Vision.
- **AI-Powered OCR**: Extracts brands, model numbers, and specific item details from labels and packaging.
- **Decision Gate Valuation**: Provides instant market value estimates, condition assessments (1-10), and profitability ratings (High/Medium/Low) to help you decide what's worth listing.

### 💬 Conversational Listing Assistant
- **Progressive Questioning**: A guided web interface that asks only the necessary questions to fill in missing details for an eBay listing.
- **Natural Language Processing**: Context-aware interactions to refine item specifics.

### 🔌 Robust eBay Integration
- **OAuth 2.0 Security**: Full implementation of eBay's OAuth 2.0 lifecycle for secure user authentication.
- **Category-Specific Aspects**: Automatically maps AI-detected data to eBay's required and recommended item specifics using the Taxonomy API.
- **Direct Publishing**: Publish listings directly to eBay via the modern Inventory and Offer APIs.
- **Live Management**: View and manage active listings directly from the dashboard.

### 📱 Telegram Valuator Bot
- **On-the-Go Valuations**: Send a photo to the dedicated Telegram bot for instant valuation results while sourcing items in the field.

---

## 🏗️ Architecture & Tech Stack

- **Backend**: Python 3.12 / Flask
- **Frontend**: Responsive Dashboard (HTML5, JavaScript, Tailwind-style CSS)
- **AI Services**: Google Vision API & Gemini 1.5 Pro/Flash (via REST)
- **Marketplace**: eBay Sell APIs (Inventory, Taxonomy, Account, Analytics)
- **Persistence**: Dual SQLite strategy (`valuations.db` for analysis history, `listings.db` for workflow state)
- **Asynchronous Processing**: `httpx` for non-blocking API interactions

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- Google Cloud Project with Vision and Gemini APIs enabled
- eBay Developer Account

### 2. Installation
```bash
# Clone the repository
git clone <repository-url>
cd ai-list-assist

# Install dependencies
pip install -r requirements.txt
# Note: httpx is also required for async features
pip install httpx
```

### 3. Configuration
Create a `.env` file in the root directory and add your credentials:
```env
# Flask Configuration
SECRET_KEY=your_flask_secret_key

# Google AI Keys
GOOGLE_API_KEY=your_google_api_key

# eBay API Keys
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
EBAY_RU_NAME=your_ebay_redirect_uri_name

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### 4. Running the Application
```bash
# Start the main web application
python app_enhanced.py

# Start the Telegram bot (in a separate terminal)
python valuator_bot.py
```
Visit: **http://localhost:5000**

---

## 📁 Project Structure

```
ai-list-assist/
├── app_enhanced.py           # Main Flask application & API
├── your_ebay_valuator_bot.py # Telegram bot interface
├── services/                 # Core business logic
│   ├── vision_service.py     # Multi-item detection & OCR
│   ├── valuation_database.py # Persistent storage for analysis
│   ├── listing_synthesis.py  # Listing generation engine
│   ├── ebay_integration.py   # eBay API client
│   └── ...                   # Other specialized services
├── shared/                   # Shared data models
│   ├── models.py             # Dataclasses (ListingDraft, ItemValuation)
│   └── schemas/              # Validation schemas
├── templates/                # Web UI components
├── tests/                    # Comprehensive test suite
├── ebayCategories/           # Category-specific mapping data
├── SETUP_GUIDE.md            # Environment and API setup guide
├── VALUATION_DATA_GUIDE.md   # AI valuation logic guide
└── EBAY_LISTING_MAPPING.md   # eBay field mapping guide
```

---

## 📊 Workflow

1. **Capture**: Take a photo of one or more items.
2. **Analyze**: AI detects items and generates a valuation report.
3. **Decide**: The "Decision Gate" highlights items with high resale potential.
4. **Refine**: Answer guided questions to complete the listing details.
5. **Publish**: One-click publishing to your eBay store.

---

## 🧪 Testing

The system includes a suite of unit and integration tests.
```bash
python -m unittest discover tests
```

---

## 📖 Related Documentation

- **[Setup Guide](SETUP_GUIDE.md)**: Detailed environment and API setup.
- **[Valuation Guide](VALUATION_DATA_GUIDE.md)**: Deep dive into the AI valuation logic.
- **[eBay Mapping](EBAY_LISTING_MAPPING.md)**: How data translates to eBay fields.

---

## 📄 License
This project is licensed under the terms specified in the repository.
