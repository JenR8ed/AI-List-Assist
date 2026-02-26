# AI List Assist: Enterprise-Grade Reselling Orchestration

**AI List Assist** is an advanced, end-to-end automation platform for online resellers. It bridges the gap between unstructured visual data (photos) and structured marketplace requirements (eBay listings) using a **Hybrid AI** architecture (Google Gemini 1.5 Flash + Cloud Vision).

---

## 🚀 System Overview

AI List Assist is an enterprise-grade orchestration layer designed to transform unstructured visual data into optimized e-commerce assets. By bridging the gap between raw photos and structured marketplace requirements, it eliminates the manual friction of reselling.

From the moment you source an item at a thrift store or manage a high-volume consignment intake, the system orchestrates the entire lifecycle: **Detection, Valuation, Taxonomy Validation, and Automated Submission.**

### 🌟 Key Features

*   **🤖 Multi-Item Hybrid Vision**: Snap one photo of multiple items; our Vision Service (Google Cloud Vision + Gemini 1.5 Flash) identifies and separates them automatically, extracting brand, model, and condition.
*   **⚖️ Decision Gate Valuation Engine**: Instant market analysis providing estimated values, resale scores (1-10), and a "Worth Listing" recommendation based on real-time profitability metrics.
*   **💬 Conversational Listing Assistant**: An AI-driven state machine that guides you through filling in missing eBay item specifics, resolving ambiguities through natural dialogue.
*   **🔌 Direct eBay Publishing**: Secure OAuth 2.0 integration with eBay’s modern **Inventory and Offer APIs** for seamless one-click publishing and active listing management.
*   **📱 Omnichannel Interfaces**:
    *   **Professional Dashboard**: A rich web interface for bulk management, live listing updates, and performance tracking.
    *   **Mobile Valuator Bot**: A dedicated Telegram bot (`your_ebay_valuator_bot.py`) for on-the-go sourcing. Snap a photo in the field to get instant Brand, Model, and Category identification.
*   **📦 Consignment & Asset Tracking**: A professional-grade system (`services/consignment_database.py`) for managing reselling at scale. Tracks participants (with KYC status and tax nexus codes), assets, commissions, and document provenance (GSA-compliant filenames).
*   **💰 API Usage & Cost Tracker**: Real-time monitoring of Vision, Gemini, and eBay API calls with accurate cost estimation for transparent operations.

---

## 🔄 Core Workflow

```mermaid
graph TD
    A[Capture Image] --> B{Vision Service}
    B -->|Object Detection| C[Identify Items]
    B -->|OCR| D[Extract Brand/Model]
    C & D --> E{Decision Gate}
    E -->|Analyze Market| F[Valuation Report]
    F -->|Worth Listing?| G[Conversational Refinement]
    G -->|User Feedback| H[Listing Synthesis]
    H -->|Submit| I[eBay Marketplace]
    I --> J[Live Management]
```

1.  **Visual Acquisition**: Upload photos via the Web Dashboard or Telegram Bot.
2.  **Hybrid Analysis**: AI detects items, extracts text, and evaluates market potential.
3.  **The Decision Gate**: Filters high-potential items based on a 90-day sold history and demand.
4.  **Guided Refinement**: The Conversational Orchestrator ensures all required eBay aspects (e.g., Size, Color, Material) are met.
5.  **Marketplace Synthesis**: Automated generation and publishing of SEO-optimized eBay listings.
6.  **Live Management**: Update or end active listings directly from the dashboard.

---

## ⚖️ The "Decision Gate" Logic

Maximize ROI by calculating profitability before spending time on the listing process.

| Profitability | Criteria | Recommendation |
| :--- | :--- | :--- |
| **🚀 High** | >$50 value, >30% sell-through | **List Immediately** |
| **✅ Medium** | >$20 value, >20% sell-through | **Worth Listing** |
| **📦 Low** | >$10 value | **Consider Bundling** |
| **♻️ None** | <$10 or no demand | **Donate/Discard** |

---

## 🏗️ Technical Architecture

AI List Assist uses a service-oriented architecture designed for scale and resilience.

### 📁 Project Structure

```text
ai-list-assist/
├── app_enhanced.py           # Main Flask application & Web API
├── your_ebay_valuator_bot.py # Telegram bot interface (Mobile)
├── services/                 # Core Business Logic
│   ├── vision_service.py     # Multi-item detection & OCR (Gemini + Vision)
│   ├── valuation_service.py  # Market analysis & Decision Gate logic
│   ├── listing_synthesis.py  # eBay listing generation engine
│   ├── ebay_integration.py   # eBay API client (Inventory/Offer/Account)
│   ├── consignment_database.py # Consignment & Asset management
│   ├── ebay_token_manager.py # OAuth 2.0 lifecycle management
│   ├── valuation_database.py # Persistent storage for analysis history
│   ├── ebay_category_service.py # eBay taxonomy & category-specific aspects
│   ├── conversation_orchestrator.py # Multi-turn dialogue for listing refinement
│   ├── category_detail_generator.py # AI-driven required field identification
│   ├── draft_image_manager.py # Management of listing draft photos
│   └── gemini_rest_client.py  # Direct REST interface for Google Gemini
├── shared/                   # Shared data models (ListingDraft, ItemValuation)
├── templates/                # Professional Web UI (Dashboard)
├── tests/                    # Comprehensive test suite
└── ebayCategories/           # Category-specific mapping data & documentation
```

### 🛠️ Tech Stack
- **Backend**: Python 3.12+ / Flask
- **AI Stack**: Google Cloud Vision & Gemini 1.5 Flash (direct REST integration)
- **Marketplace**: eBay Sell APIs (Inventory, Taxonomy, Account, Analytics)
- **Persistence**: SQLite (Dual-DB strategy: `valuations.db` and `listings.db`)
- **Mobile**: Python Telegram Bot API (async)

---

## 🛠️ Getting Started

### 1. Prerequisites
- **Python 3.12 - 3.14.2**: The core stack is tested on 3.12, while utilizing async features optimized for the upcoming 3.14 lifecycle.
- Google Cloud Project (Vision and Gemini APIs enabled).
- eBay Developer Account (Sandbox or Production).
- Telegram Bot Token (from @BotFather).

### 2. Installation

#### Standard Setup
```bash
# Clone the repository
git clone <repository-url>
cd ai-list-assist

# Install dependencies
pip install -r requirements.txt
```

#### Quick Start with Docker
The project includes a multi-container Docker setup for development.
```bash
# Build and start all services (App + Redis + DBs)
docker-compose -f docker-compose.dev.yml up --build
```
This will launch the Flask app on port 5000 and ensure all persistence layers are correctly initialized.

### 3. Configuration
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_flask_secret_key
GOOGLE_API_KEY=your_google_api_key
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
EBAY_RU_NAME=your_ebay_redirect_uri_name
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
EBAY_USE_SANDBOX=True
```

### 4. Launching
```bash
# Start the Dashboard
python app_enhanced.py

# Start the Telegram Bot
python your_ebay_valuator_bot.py
```
Access the dashboard at: **http://localhost:5000**

---

## 📱 How to Use

### Web Dashboard
1.  **Analyze**: Upload an image. The Hybrid Vision service detects items and provides valuations.
2.  **Review**: See API usage costs in real-time via the built-in tracker.
3.  **Refine**: Enter the conversational flow to provide missing eBay specifics.
4.  **Publish**: Review the synthesized listing and publish to eBay.
5.  **Manage**: Use the "Live Listings" tab to edit or end active listings.

### Telegram Bot
1.  **Start**: Send `/start` to your bot.
2.  **Snap**: Send a photo of an item while sourcing.
3.  **Evaluate**: Receive instant Brand, Model, and Category identification on your phone.

---

## 📅 Project Roadmap

### Phase 1: Automation & Refinement (Current)
- [x] **Project Refactor**: Transitioned to modular service architecture.
- [x] **Business Policy Integration**: Dynamic shipping and return policy handling.
- [ ] **Return Window Lock**: Automated logic to prevent ending listings within active return windows.

### Phase 2: Professional Reporting & Analytics
- [ ] **Consignment Payout Dashboard**: Automated commission calculation and reporting for partners.
- [ ] **Market Trend Analysis**: Historical sold data visualization.

### Phase 3: Scaling & Omnichannel Expansion
- [ ] **Multi-Marketplace Support**: Pushing listings to Mercari and Poshmark.
- [ ] **Studio Mode**: High-speed bulk photo intake for commercial warehouses.

---

## 🧪 Development & Testing

We maintain high code quality through automated testing.

```bash
# Run the full test suite
export PYTHONPATH=$PYTHONPATH:/path/to/extra/packages
export SECRET_KEY=test_secret EBAY_CLIENT_ID=test EBAY_CLIENT_SECRET=test GOOGLE_API_KEY=test
python -m unittest discover tests
```

### 🔒 Operational Boundaries
- **Strict Credential Policy**: Never hardcode secrets. All credentials must be in `.env`.
- **Modern APIs**: Always use the eBay REST/JSON Inventory API over legacy Trading APIs.
- **Data Integrity**: Analysis is stored in `valuations.db`; listing state in `listings.db`.

---

## 📄 Documentation
- [Setup Guide](SETUP_GUIDE.md)
- [Valuation Data Guide](VALUATION_DATA_GUIDE.md)
- [eBay Listing Mapping](EBAY_LISTING_MAPPING.md)
- [Agent Guidelines](AGENTS.md)
