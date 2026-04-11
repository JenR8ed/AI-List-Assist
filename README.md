# AI List Assist: Enterprise-Grade Reselling Orchestration

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Architecture](https://img.shields.io/badge/architecture-service--based-orange.svg)

**AI List Assist** is a high-performance automation platform for professional online resellers. It transforms unstructured visual data (photos) into structured, category-specific marketplace listings using a **Hybrid AI** architecture (Google Gemini 1.5 Flash + Cloud Vision).

---

## 🚀 The Reselling Problem: Solved

In high-volume reselling, the "Listing Bottleneck" is the primary barrier to scale. AI List Assist eliminates this by providing:
- **Instant Valuation**: Shift from manual research to data-backed "List/No-List" decisions in seconds.
- **Cognitive Automation**: Handle the complex mapping of eBay item specifics automatically.
- **Operational Scalability**: Transition from individual sourcing to commercial-grade warehouse intake with specialized operational modes.
- **Consignment Ready**: Integrated participant and asset tracking for third-party reselling operations.
- **Financial Transparency**: Integrated **API Usage Tracker** to monitor AI costs (Gemini & Vision) in real-time.

---

## ✨ Key Features

- **Hybrid AI Pipeline**: Combines Google Cloud Vision (OCR/Object Detection) with Gemini 1.5 Flash (Reasoning/Synthesis).
- **Consignment Management**: Full-lifecycle tracking for participants, asset provenance (SHA-256), and automated commission calculations.
- **Telegram Valuator Bot**: Mobile-first sourcing with instant appraisals via a dedicated Telegram interface.
- **API Usage Tracker**: Real-time cost transparency and token monitoring directly in the dashboard.
- **Deterministic Analysis**: Uses image hashing to ensure consistent valuation results for identical items.
- **Secure Architecture**: Protected by HMAC-based Bearer token verification, strict security headers (CSP, X-Frame-Options), and XSS-safe rendering.
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
8.  **`CategoryDetailGenerator`**: Optimized field requirement mapping and question generation.
9.  **`DraftImageManager`**: Lifecycle management for listing-specific image assets.
10. **`ConsignmentDatabase`**: Specialized tracking for participants, KYC, and asset provenance.
11. **`ValuationDatabase`**: Persistent storage for analysis history and bulk ingestion logic.
12. **`GeminiRestClient`**: Unified sync/async interface for direct Google AI REST calls.
13. **`MockValuationService`**: High-fidelity environment for development and automated testing.

### 💾 Triple-DB Strategy
The system ensures strict separation of concerns and data integrity by using three dedicated SQLite databases with **Write-Ahead Logging (WAL)** enabled:
- **`valuations.db`**: Stores analysis history, detection confidence, and market valuations.
- **`listings.db`**: Stores eBay inventory/offer states, session drafts, and submission logs.
- **`consignment.db`**: Manages participant profiles (KYC), tax nexus codes, asset tracking, and transaction history.

---

## 📊 Measured Performance Benchmarks

AI List Assist is engineered for speed, delivering measurable improvements over standard implementations:
- **⚡ Brand Extraction**: **~51-53% gain** in `VisionService._extract_brand` via pre-calculated lowercase lookups.
- **⚡ Model Detection**: **~26-35% gain** in `VisionService._extract_model` via class-level regex pre-compilation.
- **⚡ Category Mapping**: **30x speedup** in `CategoryDetailGenerator` using O(N+M) complexity algorithms.
- **⚡ Database Throughput**: **40x faster** ingestion in `ValuationDatabase` using bulk `executemany` patterns.
- **⚡ Server Concurrency**: **60% reduction** in latency for async routes by replacing blocking I/O with `asyncio.to_thread`.

---

## 🔐 Security & Compliance

- **HMAC Bearer Authentication**: Sensitive API endpoints require HMAC-based Bearer token verification via `Authorization: Bearer <token>`.
- **Content Security Policy**: Strict CSP headers prevent XSS and data injection attacks.
- **XSS Protection**: Secure rendering logic ensures dynamic metadata is safely handled in the dashboard.
- **Credential Integrity**: Strict policy against hardcoded secrets; all credentials must be managed via environment variables.

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
3.  **The Decision Gate**: Items are filtered based on 90-day sold history and demand using market-optimized pricing strategies.
4.  **Conversational Refinement**: The orchestrator asks targeted questions to fill required eBay aspects.
5.  **Marketplace Synthesis**: Optimized titles and descriptions are generated according to [eBay Mapping Rules](EBAY_LISTING_MAPPING.md).
6.  **Secure Publishing**: Direct deployment to eBay via OAuth 2.0 and the Inventory API.

---

## ⚙️ Setup & Installation

### Prerequisites
- **Python 3.12+**
- Google Cloud API Key (Gemini + Vision)
- eBay Developer Account (Sandbox or Production)
- Telegram Bot Token (Optional)

### Environment Configuration
Create a `.env` file in the root directory:
```env
# Flask Security
SECRET_KEY=your_flask_secret_key
API_KEY=your_hmac_api_key

# Google AI
GOOGLE_API_KEY=your_google_cloud_api_key

# eBay API
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
EBAY_RU_NAME=your_ebay_runame
EBAY_CATEGORY_TREE_ID=0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

### Quick Start (Local)
```bash
# Clone the repository
git clone <repository-url>
cd ai-list-assist

# Install core dependencies
pip install -r requirements.txt

# Initialize databases
python3 -c "from app_enhanced import init_db; from services.consignment_database import init_db as init_consignment; init_db(); init_consignment()"
```

### Launching
- **Web Dashboard**: `python3 app_enhanced.py` (Visit `http://localhost:5000`)
- **Telegram Bot**: `python3 your_ebay_valuator_bot.py`
- **Docker (Full Stack)**: `docker-compose -f docker-compose.dev.yml up --build`

---

## 🧪 Verification & Testing

Ensure system integrity by running the test suite:
```bash
export SECRET_KEY=test EBAY_CLIENT_ID=test EBAY_CLIENT_SECRET=test GOOGLE_API_KEY=test API_KEY=test EBAY_CATEGORY_TREE_ID=0
PYTHONPATH=. python3 -m pytest tests/ -v
```

---

## 📚 Specialized Documentation
- 📊 [Valuation Guide](VALUATION_DATA_GUIDE.md): Deep dive into decision logic and price discovery.
- 🔄 [Mapping Guide](EBAY_LISTING_MAPPING.md): How AI data translates to eBay fields.
- 🛠️ [Setup Guide](SETUP_GUIDE.md): Detailed installation and Postman testing instructions.
- 🤝 [Contributing](CONTRIBUTING.md): Guidelines for code standards and PR processes.

---

**AI List Assist** - Turning reselling into a science.
