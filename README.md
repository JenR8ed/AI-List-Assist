# AI List Assist: Enterprise-Grade Reselling Orchestration

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Architecture](https://img.shields.io/badge/architecture-service--based-orange.svg)

**AI List Assist** is a high-performance automation platform for professional online resellers. It transforms unstructured visual data (photos) into structured, category-specific marketplace listings using a **Hybrid AI** architecture (Google Gemini 1.5 Flash + Cloud Vision).

---

## 🚀 The Reselling Problem: Solved

In high-volume reselling, the "Listing Bottleneck" is the primary barrier to scale. AI List Assist eliminates this by providing:
- **Instant Valuation**: Shift from manual research to data-backed "List/No-List" decisions in seconds using real-time eBay market data.
- **Cognitive Automation**: Handle the complex mapping of eBay item specifics automatically through AI-driven attribute extraction.
- **Operational Scalability**: Transition from individual sourcing to commercial-grade warehouse intake with specialized operational modes.
- **Financial Transparency**: Integrated **API Usage Tracker** to monitor AI costs (Gemini & Vision) and eBay API calls in real-time.

---

## ✨ Key Features

- **Hybrid AI Pipeline**: Combines Google Cloud Vision (OCR/Object Detection) with Gemini 1.5 Flash (Reasoning/Synthesis) for superior accuracy.
- **API Usage Tracker**: Real-time cost transparency and token monitoring directly in the dashboard, protecting your margins.
- **Deterministic Analysis**: Uses SHA-256 image hashing to ensure consistent valuation results and prevent duplicate processing.
- **Secure Architecture**: Protected by HMAC-based API key verification, strict security headers (CSP, X-Frame-Options), and XSS-safe rendering.
- **Market-Driven Logic**: Uses the eBay Browse API to calculate 90-day moving averages for "List/No-List" decision gates.
- **Mobile-First Sourcing**: Includes a **Telegram Valuator Bot** for rapid field appraisals and on-the-go sourcing.

---

## 🏗️ System Architecture: The 13-Service Engine

The platform utilizes a modular, service-oriented architecture designed for reliability and extreme performance.

### 📁 Core Services
1.  **`VisionService`**: Multi-item detection and OCR using Cloud Vision + Gemini. Optimized brand extraction (~32% gain).
2.  **`ValuationService`**: Real market analysis using the eBay Browse API to calculate dynamic pricing based on sold items.
3.  **`ConversationOrchestrator`**: AI-driven dialogue management to resolve missing item aspects through progressive questioning.
4.  **`ListingSynthesisEngine`**: SEO-optimized marketplace listing generation, mapping extracted data to eBay schemas.
5.  **`eBayIntegration`**: Direct interaction with modern eBay REST Inventory and Offer APIs.
6.  **`EBayCategoryService`**: Real-time interaction with the eBay Taxonomy API for category-specific metadata and aspects.
7.  **`EBayTokenManager`**: Centralized OAuth 2.0 lifecycle and auto-refresh management for eBay tokens.
8.  **`CategoryDetailGenerator`**: Generates targeted questions for missing required fields (~30x speedup via O(N+M) mapping).
9.  **`DraftImageManager`**: Lifecycle management for listing-specific image assets using deterministic storage.
10. **`ConsignmentDatabase`**: Specialized tracking for participants (KYC), asset provenance, and commission calculations.
11. **`ValuationDatabase`**: Persistent storage for analysis history (95% faster via bulk `executemany` inserts).
12. **`GeminiRestClient`**: Unified sync/async interface for direct Google AI REST calls, avoiding heavy dependencies.
13. **`MockValuationService`**: High-fidelity environment for development and isolated automated testing.

### 💾 Triple-DB Strategy
The system ensures strict separation of concerns and data integrity by using three dedicated SQLite databases (with **Write-Ahead Logging (WAL)** and `busy_timeout` enabled for concurrent performance):
- **`valuations.db`**: Stores analysis history, detection confidence, and market valuations.
- **`listings.db`**: Stores eBay inventory/offer states, draft data, and submission logs.
- **`consignment.db`**: Manages participant profiles (KYC), tax nexus codes, and asset tracking.

---

## 🔐 Security & Compliance

- **HMAC Authentication**: Sensitive API endpoints require HMAC-based signature verification via `Authorization: Bearer <token>`.
- **Content Security Policy**: Strict CSP headers prevent XSS and data injection attacks.
- **Secure Handling**: No hardcoded credentials; all secrets are managed via environment variables.
- **Data Privacy**: Local persistence of valuation data with deterministic hashing for privacy and consistency.

---

## 🎮 Operational Modes

AI List Assist adapts to your specific workflow through four dedicated operational modes:

| Mode | Purpose | Target User |
| :--- | :--- | :--- |
| **🏠 Locker Mode** | Secure inventory management for personal collections. | Casual Resellers |
| **🔍 Sourcing Mode** | Mobile-first valuation and market analysis in the field via Telegram. | Thrift/Estate Hunters |
| **🤝 Consignment** | Tracking third-party assets, commissions, and KYC requirements. | Consignment Businesses |
| **🏬 Studio Mode** | High-speed, bulk photo intake and batch processing. | Commercial Warehouses |

---

## 🔄 The Logic Pipeline: From Image to Listing

```text
[ PHOTO ACQUISITION ] --> [ HYBRID AI ANALYSIS ] --> [ PROFITABILITY GATE ]
      (Web/Bot)             (Vision + Gemini)         (Market Price Scan)
                                     |                         |
                                     V                         V
[ SECURE PUBLISHING ] <-- [ LISTING SYNTHESIS ] <--- [ CONVERSATIONAL FLOW ]
   (eBay REST API)         (SEO Optimization)         (Attribute Resolution)
```

1.  **Visual Acquisition**: Upload photos via the **Web Dashboard** or the **Telegram Valuator Bot**.
2.  **Hybrid Analysis**: AI detects items, assesses condition, and extracts brand/model metadata.
3.  **The Decision Gate**: Items are filtered based on real-time 90-day sold history, supply, and demand.
4.  **Conversational Refinement**: The orchestrator asks targeted questions to fill required eBay aspects.
5.  **Marketplace Synthesis**: Optimized titles and HTML descriptions are generated via [Mapping Logic](EBAY_LISTING_MAPPING.md).
6.  **Secure Publishing**: Direct deployment to eBay via OAuth 2.0 and the modern Inventory API.

---

## 💰 Integrated API Usage Tracker

The dashboard includes a real-time **API Usage Tracker** that calculates costs for:
- **Google Cloud Vision**: Tracks free tier vs. paid calls.
- **Gemini 1.5 Flash**: Tracks input/output tokens and associated costs ($0.075/$0.30 per 1M tokens).
- **eBay API**: Monitors handshake, taxonomy, and inventory calls.

This ensures reselling margins are protected from unexpected AI infrastructure costs.

---

## ⚙️ Setup & Installation

### Prerequisites
- **Python 3.12+** (Developed and tested on 3.12.13)
- Google Cloud API Key (Gemini + Vision)
- eBay Developer Account (Sandbox or Production)

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd ai-list-assist

# Install core dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Update with your API keys:
# GOOGLE_API_KEY, EBAY_CLIENT_ID, EBAY_CLIENT_SECRET,
# SECRET_KEY, API_KEY, EBAY_CATEGORY_TREE_ID=0
```

### Launching
- **Web Dashboard**: `python app_enhanced.py` (Visit `http://localhost:5000`)
- **Telegram Bot**: `python your_ebay_valuator_bot.py`
- **Docker (Full Stack)**: `docker-compose -f docker-compose.dev.yml up --build`

---

## 🧪 Verification & Testing

Ensure system integrity by running the test suite:
```bash
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
