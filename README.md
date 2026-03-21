# AI List Assist: Enterprise-Grade Reselling Orchestration

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.1.3-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Architecture](https://img.shields.io/badge/architecture-service--based-orange.svg)

**AI List Assist** is a high-performance automation platform for professional online resellers. It transforms unstructured visual data (photos) into structured, category-specific marketplace listings using a **Hybrid AI** architecture (Google Gemini 1.5 Flash + Cloud Vision).

---

## 🚀 The Reselling Problem: Solved

In high-volume reselling, the "Listing Bottleneck" is the primary barrier to scale. AI List Assist eliminates this by providing:
- **Instant Valuation**: Shift from manual research to data-backed "List/No-List" decisions in seconds.
- **Cognitive Automation**: Handle the complex mapping of eBay item specifics automatically.
- **Operational Scalability**: Transition from individual sourcing to commercial-grade warehouse intake with specialized operational modes.
- **Financial Transparency**: Integrated **API Usage Tracker** to monitor AI costs (Gemini & Vision) in real-time.

---

## ✨ Key Features

- **Hybrid AI Pipeline**: Combines Google Cloud Vision (OCR/Object Detection) with Gemini 1.5 Flash (Reasoning/Synthesis).
- **API Usage Tracker**: Real-time cost transparency and token monitoring directly in the dashboard.
- **Deterministic Analysis**: Uses SHA-256 image hashing to ensure consistent valuation results for identical items.
- **Secure Architecture**: Protected by HMAC-based API key verification and strict security headers.
- **Omnichannel Readiness**: Modular design ready to expand beyond eBay to Mercari, Poshmark, and more.

---

## 🏗️ System Architecture: The 13-Service Engine

The platform utilizes a modular, service-oriented architecture designed for reliability and extreme performance.

### 🛠️ Service Catalog
| Service | Purpose | Key Tech |
| :--- | :--- | :--- |
| **`VisionService`** | Hybrid OCR and multi-item object detection. | Cloud Vision, Gemini |
| **`ValuationService`** | Market analysis and "Decision Gate" profitability logic. | Internal Market Model |
| **`ConversationOrchestrator`** | AI-driven dialogue to resolve missing item aspects. | Gemini 1.5 Flash |
| **`ListingSynthesisEngine`** | SEO-optimized marketplace listing generation. | Markdown, HTML |
| **`eBayIntegration`** | Direct interaction with eBay REST Inventory/Offer APIs. | OAuth 2.0, REST |
| **`EBayCategoryService`** | Real-time interaction with eBay Taxonomy API metadata. | eBay SDK, JSON |
| **`EBayTokenManager`** | Centralized OAuth 2.0 lifecycle and refresh management. | HMAC, SQLite |
| **`CategoryDetailGenerator`** | Optimized question generation (~30x speedup via O(N+M)). | Python |
| **`DraftImageManager`** | Lifecycle management for listing-specific image assets. | `shutil.copy2` |
| **`ConsignmentDatabase`** | Tracking for participants, KYC, and asset provenance. | SQLite (consignment.db) |
| **`ValuationDatabase`** | Persistent analysis history (95% faster via bulk inserts). | SQLite (valuations.db) |
| **`GeminiRestClient`** | Unified sync/async interface for direct Google AI REST calls. | `httpx` |
| **`MockValuationService`** | High-fidelity environment for development and testing. | Deterministic Mocking |

### 💾 Triple-DB Strategy
The system ensures strict separation of concerns and data integrity by using three dedicated SQLite databases (with **Write-Ahead Logging (WAL)** enabled):
- **`valuations.db`**: Stores analysis history, detection confidence, and market valuations.
- **`listings.db`**: Stores eBay inventory/offer states, draft data, and submission logs.
- **`consignment.db`**: Manages participant profiles (KYC), tax nexus codes, and asset tracking.

---

## 🔒 Security & Authentication

AI List Assist implements a multi-layer security model to protect sensitive API data and inventory records:
- **HMAC Signature Verification**: All sensitive API routes (`/api/analyze`, `/api/listing/publish`) are protected by a custom `@require_api_key` decorator.
- **Bearer Token Auth**: Clients must provide a valid `API_KEY` via an `Authorization: Bearer <token>` header.
- **Global Security Headers**: The backend implements `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict `Content-Security-Policy`.
- **Credential Management**: No secrets are hardcoded; all configuration is handled via environment variables and `.env` files.

---

## 🎮 Operational Modes

AI List Assist adapts to your specific workflow through four dedicated operational modes:

| Mode | Purpose | Target User |
| :--- | :--- | :--- |
| **🏠 Locker Mode** | Secure inventory management for personal collections. | Casual Resellers |
| **🔍 Sourcing Mode** | Mobile-first valuation and market analysis in the field. | Thrift/Estate Hunters |
| **🤝 Consignment** | Tracking third-party assets, commissions, and KYC. | Consignment Businesses |
| **🏬 Studio Mode** | High-speed, bulk photo intake and batch processing. | Commercial Warehouses |

---

## 🔄 The Logic Pipeline: From Image to Listing

1.  **Visual Acquisition**: Upload photos via the **Web Dashboard** or the **Telegram Valuator Bot**.
2.  **Hybrid Analysis**: AI detects items, assesses condition, and extracts brand/model metadata.
3.  **The Decision Gate**: Items are filtered based on 90-day sold history, supply, and demand.
4.  **Conversational Refinement**: The orchestrator asks targeted questions to fill required eBay aspects.
5.  **Marketplace Synthesis**: Optimized titles and HTML descriptions are generated via [Mapping Logic](EBAY_LISTING_MAPPING.md).
6.  **Secure Publishing**: Direct deployment to eBay via OAuth 2.0 and the Inventory API.

---

## 💰 Integrated API Usage Tracker

The dashboard includes a real-time **API Usage Tracker** that calculates costs for:
- **Google Cloud Vision**: Tracks free tier vs. paid calls.
- **Gemini 1.5 Flash**: Tracks input/output tokens and associated costs ($0.075/$0.30 per 1M tokens).
- **eBay API**: Monitors handshake and inventory calls.

This ensures reselling margins are protected from unexpected AI infrastructure costs.

---

## ⚙️ Setup & Installation

### Prerequisites
- **Python 3.12+**
- **Google Cloud API Key** (Gemini + Vision)
- **eBay Developer Account** (Sandbox or Production)
- **Telegram Bot Token** (Optional, for field appraisal)

### Configuration (Environment Variables)
Create a `.env` file in the root directory with the following keys:
```env
SECRET_KEY=your_flask_secret_key
API_KEY=your_hmac_api_key_for_clients
GOOGLE_API_KEY=your_google_cloud_api_key
EBAY_CLIENT_ID=your_ebay_app_id
EBAY_CLIENT_SECRET=your_ebay_cert_id
EBAY_CATEGORY_TREE_ID=0  # Default is 0 for US
TELEGRAM_BOT_TOKEN=your_bot_token  # Optional
```

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd ai-list-assist

# Install core dependencies
pip install -r requirements.txt

# Launching Web Dashboard
python app_enhanced.py

# Launching Telegram Bot
python your_ebay_valuator_bot.py
```

---

## 🧪 Verification & Testing

Ensure system integrity by running the test suite:
```bash
# Set dummy credentials for isolated testing
export SECRET_KEY=test EBAY_CLIENT_ID=test EBAY_CLIENT_SECRET=test GOOGLE_API_KEY=test API_KEY=test EBAY_CATEGORY_TREE_ID=0
python -m pytest tests/ -v
```

---

## 📅 Roadmap

- **Phase 1: Automation** (Complete) - Core Hybrid Vision and eBay REST integration.
- **Phase 2: Reporting** (In Progress) - Consignment dashboards and multi-item trend analysis.
- **Phase 3: Scale** (Planned) - Omnichannel support (Mercari, Poshmark integration).

---

## 📚 Specialized Documentation
- 📊 [Valuation Guide](VALUATION_DATA_GUIDE.md): Deep dive into decision logic and price discovery.
- 🔄 [Mapping Guide](EBAY_LISTING_MAPPING.md): How AI data translates to eBay fields.
- 🛠️ [Setup Guide](SETUP_GUIDE.md): Detailed installation and Postman testing instructions.
- 🤝 [Contributing](CONTRIBUTING.md): Guidelines for code standards and PR processes.

---

**AI List Assist** - Turning reselling into a science.
