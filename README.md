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

## 🔄 The Logic Pipeline: From Image to Listing

The system orchestrates a multi-stage pipeline combining deterministic vision and generative reasoning:

```text
[ SOURCE ]          [ HYBRID AI ANALYSIS ]          [ DECISION GATE ]          [ PUBLISHING ]
   |                    |                               |                       |
   |-- Web Dashboard    |-- Cloud Vision (OCR/Detect)   |-- Market Comparison   |-- SEO Title Gen
   |-- Telegram Bot ----|-- Gemini 1.5 (Reasoning)      |-- Profitability Calc  |-- Aspect Mapping
   |-- API Upload       |-- Deterministic Hashing       |-- "List/No-List"      |-- eBay REST API
   |                    |                               |                       |
[ IMAGE ] ----------> [ METADATA ] ----------------> [ VALUATION ] ----------> [ LIVE LISTING ]
```

---

## ✨ Key Features

- **Hybrid AI Pipeline**: Combines Google Cloud Vision (OCR/Object Detection) with Gemini 1.5 Flash (Reasoning/Synthesis).
- **Secure by Design**: All sensitive API endpoints are protected by HMAC-based signature verification.
- **Mobile Valuator Bot**: Real-time sourcing via Telegram for rapid field appraisal.
- **API Usage Tracker**: Real-time cost transparency and token monitoring directly in the dashboard.
- **Deterministic Analysis**: Uses SHA-256 image hashing to ensure consistent results and prevent redundant API costs.
- **Omnichannel Readiness**: Modular design ready to expand beyond eBay to Mercari, Poshmark, and more.

---

## 🏗️ System Architecture: The 13-Service Engine

The platform utilizes a modular, service-oriented architecture designed for reliability and extreme performance.

### 📁 Core Services
1.  **`VisionService`**: Hybrid OCR and multi-item object detection using Cloud Vision + Gemini.
2.  **`ValuationService`**: Market analysis and "Decision Gate" profitability logic.
3.  **`ConversationOrchestrator`**: AI-driven dialogue management to resolve missing item aspects.
4.  **`ListingSynthesisEngine`**: SEO-optimized marketplace listing generation.
5.  **`eBayIntegration`**: Direct interaction with modern eBay REST Inventory/Offer APIs.
6.  **`EBayCategoryService`**: Real-time interaction with the eBay Taxonomy API for metadata.
7.  **`EBayTokenManager`**: Centralized OAuth 2.0 lifecycle and refresh management.
8.  **`CategoryDetailGenerator`**: Optimized question generation (~30x speedup via O(N+M) mapping).
9.  **`DraftImageManager`**: Lifecycle management for listing-specific image assets.
10. **`ConsignmentDatabase`**: Specialized tracking for participants, KYC, and asset provenance.
11. **`ValuationDatabase`**: Persistent storage for analysis history (95% faster via bulk `executemany` inserts).
12. **`GeminiRestClient`**: Unified sync/async interface for direct Google AI REST calls.
13. **`MockValuationService`**: High-fidelity environment for development and automated testing.

### 💾 Triple-DB Strategy
The system ensures strict separation of concerns and data integrity by using three dedicated SQLite databases (with WAL enabled):
- **`valuations.db`**: Stores analysis history, detection confidence, and market valuations.
- **`listings.db`**: Stores eBay inventory/offer states, draft data, and submission logs.
- **`consignment.db`**: Manages participant profiles (KYC), tax nexus codes, and asset tracking.

---

## 🎮 Operational Modes

AI List Assist adapts to your specific workflow through four dedicated operational modes:

| Mode | Purpose | Key Benefit |
| :--- | :--- | :--- |
| **🏠 Locker Mode** | Personal collection management. | High-fidelity asset tracking for enthusiasts. |
| **🔍 Sourcing Mode** | Mobile-first field appraisal. | Instant "Buy/Don't Buy" signals for thrift hunters. |
| **🤝 Consignment** | Third-party asset management. | Automated commission splits and KYC compliance. |
| **🏬 Studio Mode** | High-speed, bulk intake. | Optimized for commercial-grade photography setups. |

---

## 🔐 Security & Authentication

The application implements enterprise-grade security for its API surface:

- **HMAC Verification**: Sensitive routes (e.g., `/api/analyze`, `/api/listing/publish`) require a `Bearer` token that is verified via `hmac.compare_digest` against the server's `API_KEY`.
- **Global Headers**: The system automatically injects security headers (`X-Frame-Options`, `Content-Security-Policy`, `X-Content-Type-Options`).
- **Secret Management**: All credentials (Google, eBay, HMAC keys) are managed exclusively through environment variables; never hardcoded.

---

## 🤖 Mobile-First Integration (Telegram Bot)

For field sourcing, use the **eBay Valuator Bot** (`your_ebay_valuator_bot.py`):
1. **Instant Valuation**: Snap a photo in a thrift store and receive immediate brand, category, and model detection.
2. **Setup**:
   - Obtain a bot token from [@BotFather](https://t.me/BotFather).
   - Set `TELEGRAM_BOT_TOKEN` in your `.env`.
   - Run `python your_ebay_valuator_bot.py`.
3. **Usage**: Simply send a photo to the bot to trigger the Hybrid AI analysis pipeline.

---

## 💰 Integrated API Usage Tracker

The dashboard includes a real-time **API Usage Tracker** that calculates costs for:
- **Google Cloud Vision**: Tracks free tier vs. paid calls.
- **Gemini 1.5 Flash**: Tracks input/output tokens and associated costs.
- **eBay API**: Monitors handshake and inventory calls.

This ensures reselling margins are protected from unexpected AI infrastructure costs.

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.12+
- Google Cloud API Key (Gemini + Vision)
- eBay Developer Account (Sandbox or Production)

### Docker Deployment (Recommended)
The easiest way to launch the full stack is using Docker Compose:
```bash
# Start the database and application containers
docker-compose -f docker-compose.dev.yml up --build
```

### Manual Installation
```bash
# Clone and install dependencies
git clone <repository-url>
cd ai-list-assist
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Update with your API keys:
# GOOGLE_API_KEY, EBAY_CLIENT_ID, EBAY_CLIENT_SECRET,
# SECRET_KEY, API_KEY, TELEGRAM_BOT_TOKEN

# Initialize and Seed Market Trends (Optional)
python seed_db.py
```

### Launching
- **Web Dashboard**: `python app_enhanced.py` (Visit `http://localhost:5000`)
- **Telegram Bot**: `python your_ebay_valuator_bot.py`

---

## 🧪 Verification & Testing

Ensure system integrity by running the test suite:
```bash
export PYTHONPATH=$PYTHONPATH:.
# Set dummy credentials for local testing
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
