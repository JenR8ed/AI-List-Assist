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
- **Secure Architecture**: Protected by HMAC-based Bearer token verification, strict security headers (CSP, X-Frame-Options), and XSS-safe rendering.
- **Omnichannel Readiness**: Modular design ready to expand beyond eBay to Mercari, Poshmark, and more.
- **Mobile-First Sourcing**: Includes a **Telegram Valuator Bot** for rapid field appraisals.

---

## 📊 Measured Performance Benchmarks

The platform is engineered for extreme throughput, achieving significant gains through targeted algorithmic optimizations:

- **⚡ Brand Extraction**: **~51-53% gain** in `VisionService._extract_brand` via pre-calculated lowercase lookups.
- **⚡ Title Generation**: **~50-60% gain** in `ListingSynthesisEngine._generate_title` using C-level null-byte delimited substring checks.
- **⚡ Model Extraction**: **~26-35% gain** in `VisionService._extract_model` via class-level regex pre-compilation.
- **⚡ Database Performance**: **95% faster** ingestion in `ValuationDatabase` using bulk `executemany` patterns.
- **⚡ Category Mapping**: **~30x speedup** in `CategoryDetailGenerator` using an O(N+M) complexity algorithm.
- **⚡ Server Concurrency**: **~60% reduction** in concurrent latency for the `analyze_image` route by replacing blocking I/O with `asyncio.to_thread`.

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
9.  **`DraftImageManager`**: Lifecycle management for listing-specific image assets within `drafts/`.
10. **`ConsignmentDatabase`**: Specialized tracking for participants, KYC, and asset provenance.
11. **`ValuationDatabase`**: Persistent storage for analysis history.
12. **`GeminiRestClient`**: Unified sync/async interface for direct Google AI REST calls.
13. **`MockValuationService`**: High-fidelity environment for development and automated testing.

### 💾 Triple-DB Strategy
The system ensures strict separation of concerns and data integrity by using three dedicated SQLite databases with **Write-Ahead Logging (WAL)** enabled:
- **`valuations.db`**: Stores analysis history, detection confidence, and market valuations.
- **`listings.db`**: Stores eBay inventory/offer states, draft data, and submission logs.
- **`consignment.db`**: Manages participant profiles (KYC), tax nexus codes, and asset tracking.

---

## 🔐 Security & Compliance

- **HMAC Bearer Authentication**: Sensitive API endpoints (e.g., `/api/analyze`, `/api/listing/publish`) require HMAC-based comparison against the `API_KEY` environment variable.
- **Security Headers**: Implements `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict `Content-Security-Policy`.
- **Error Sanitization**: Backend replaces raw exception strings in JSON responses with generic messages, logging full tracebacks internally to prevent information exposure.
- **Strict Credential Policy**: All API credentials and secrets must be fetched via environment variables and are never hardcoded.

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
3.  **The Decision Gate**: Items are filtered based on 90-day sold history, supply, and demand using market-optimized fractional pricing strategies.
4.  **Conversational Refinement**: The orchestrator asks targeted questions to fill required eBay aspects.
5.  **[Marketplace Synthesis](EBAY_LISTING_MAPPING.md)**: Optimized titles and HTML descriptions are generated.
6.  **Secure Publishing**: Direct deployment to eBay via OAuth 2.0 and the Inventory API.

---

## ⚙️ Setup & Installation

### Prerequisites
- **Python 3.12+** (Developed and tested on 3.12.13)
- Google Cloud API Key (Gemini + Vision)
- eBay Developer Account (Sandbox or Production)

### Quick Start (Local)
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

### Database Initialization
The system uses `seed_db.py` to initialize market trend data using Perplexity AI, PostgreSQL, and Redis.

```bash
python seed_db.py
```

### Launching
- **Web Dashboard**: `python app_enhanced.py` (Visit `http://localhost:5000`)
- **Telegram Bot**: `python your_ebay_valuator_bot.py`
- **Docker (Full Stack)**: `docker-compose -f docker-compose.dev.yml up --build`

---

## 🧪 Verification & Testing

Ensure system integrity by running the test suite:
```bash
export SECRET_KEY=test EBAY_CLIENT_ID=test EBAY_CLIENT_SECRET=test GOOGLE_API_KEY=test API_KEY=test EBAY_CATEGORY_TREE_ID=0
PYTHONPATH=. python3 -m pytest tests/ -v
```

Additionally, use `test_syntax.py` to verify the main application's integrity:
```bash
python test_syntax.py
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
