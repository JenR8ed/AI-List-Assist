# AI List Assist: Enterprise-Grade Reselling Orchestration

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Architecture](https://img.shields.io/badge/architecture-service--based-orange.svg)

**AI List Assist** is a high-performance automation platform designed for professional online resellers. It transforms unstructured visual data into structured, category-specific marketplace listings using a sophisticated **Hybrid AI** architecture (Google Gemini 1.5 Flash + Cloud Vision).

---

## 🚀 The Reselling Problem: Solved

In high-volume reselling, the "Listing Bottleneck" is the primary barrier to scale. AI List Assist eliminates this by providing:

*   **Instant Valuation**: Shift from manual research to data-backed "List/No-List" decisions in seconds.
*   **Cognitive Automation**: Handle the complex mapping of eBay item specifics automatically.
*   **Operational Scalability**: Transition from individual sourcing to commercial-grade warehouse intake with specialized operational modes.
*   **Financial Transparency**: Integrated **API Usage Tracker** to monitor AI costs (Gemini & Vision) in real-time.

---

## ✨ Key Features

*   **Hybrid AI Pipeline**: Combines Google Cloud Vision (OCR/Object Detection) with Gemini 1.5 Flash (Reasoning/Synthesis).
*   **API Usage Tracker**: Real-time cost transparency and token monitoring directly in the dashboard.
*   **Deterministic Analysis**: Uses image hashing (SHA-256) to ensure consistent valuation results for identical items across sessions.
*   **Secure Architecture**: Protected by HMAC-based Bearer token verification, strict security headers (CSP, X-Frame-Options), and XSS-safe rendering.
*   **Mobile-First Sourcing**: Includes a **Telegram Valuator Bot** for rapid field appraisals.
*   **Progressive Questioning**: Intelligent dialogue flow to resolve missing item aspects via a state-machine orchestrator.

---

## 🏗️ System Architecture: The 13-Service Engine

The platform utilizes a modular, service-oriented architecture designed for reliability and extreme performance.

### 📁 Core Services Deep Dive
1.  **`VisionService`**: Implements a hybrid OCR and multi-item object detection pipeline. It utilizes Google Cloud Vision for initial detection and Gemini 1.5 Flash for high-level reasoning and verification.
2.  **`ValuationService`**: The "Decision Gate" of the system. It analyzes market trends and "Sold" data to calculate profitability, factoring in commissions and shipping estimates.
3.  **`ConversationOrchestrator`**: A state-machine driven service that manages AI-led dialogues with the user to collect missing, category-required item specifics.
4.  **`ListingSynthesisEngine`**: A specialized LLM engine that generates SEO-optimized titles, rich descriptions, and maps AI-detected attributes to marketplace-specific schemas.
5.  **`eBayIntegration`**: A robust client for the modern eBay REST APIs (Inventory and Offer), replacing legacy Trading API calls.
6.  **`EBayCategoryService`**: Interacts with the eBay Taxonomy API to retrieve real-time metadata and aspect requirements for thousands of categories.
7.  **`EBayTokenManager`**: Handles the full OAuth 2.0 lifecycle, including secure token storage and background refresh logic.
8.  **`CategoryDetailGenerator`**: Optimized field requirement mapping that reduces O(N^2) lookups to O(N+M) complexity for rapid UI rendering.
9.  **`DraftImageManager`**: Manages the lifecycle of temporary listing images, including secure storage, hashing, and automatic cleanup after submission.
10. **`ConsignmentDatabase`**: A specialized service for managing high-trust transactions, participant KYC, tax nexus codes, and asset provenance tracking.
11. **`ValuationDatabase`**: Persistent storage layer for analysis history, detection confidence, and localized market trend snapshots.
12. **Market Intelligence System**: A sophisticated sub-system utilizing **Perplexity AI (Sonar model)** to fetch real-time trends, persisted in **PostgreSQL 15** and cached in **Redis 7** for sub-millisecond retrieval.
13. **`GeminiRestClient`**: A unified, high-performance interface for both synchronous and asynchronous communication with the Google Generative Language REST API.

### 💾 Triple-DB Strategy
The system ensures strict separation of concerns and data integrity by using three dedicated SQLite databases with **Write-Ahead Logging (WAL)** enabled:
*   **`valuations.db`**: Stores analysis history, detection confidence, and market valuations.
*   **`listings.db`**: Stores eBay inventory/offer states, draft data, and session tracking.
*   **`consignment.db`**: Manages participant profiles (KYC), tax nexus codes, and asset provenance.

---

## 📊 Measured Performance Benchmarks

AI List Assist is engineered for speed, delivering measurable improvements over standard implementations:

*   **⚡ Brand Extraction**: **~51-53% gain** in `VisionService` via pre-calculated lowercase lookups.
*   **⚡ Model Detection**: **~26-35% gain** via class-level regex pre-compilation.
*   **⚡ Category Mapping**: **~30x speedup** in `CategoryDetailGenerator` using O(N+M) complexity algorithms.
*   **⚡ Database Throughput**: **~40x faster** ingestion in `ValuationDatabase` using bulk `executemany` patterns.
*   **⚡ Server Concurrency**: **~60% reduction** in latency for the `analyze_image` route by delegating blocking I/O to threads.

---

## 🔐 Security & Compliance

*   **HMAC Bearer Authentication**: All sensitive API endpoints are secured using HMAC-based Bearer token verification against a server-side `API_KEY`.
*   **Content Security Policy (CSP)**: Strict headers restrict script, style, and image sources to prevent XSS and data injection.
*   **XSS Protection**: Secure rendering logic via Jinja2 and explicit sanitization ensuring dynamic metadata is safely handled.
*   **Credential Integrity**: Strict "Zero-Hardcoding" policy; all credentials (eBay, Google, Postgres) are managed via environment variables.

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

## 🤖 Telegram Valuator Bot

For field work, the integrated Telegram Bot (`your_ebay_valuator_bot.py`) provides:
*   **Instant Photo Analysis**: Send a photo, get an AI-driven valuation in seconds.
*   **Field Appraisals**: Determine "Worth Listing" status while sourcing at thrift stores or estate sales.
*   **Markdown Reports**: Clean, readable reports on detected brand, model, and category.

---

## 🛠️ Development & Environment

### Prerequisites
*   **Python 3.12+**
*   **Docker & Docker Compose** (for Market Intelligence stack)
*   Google Cloud API Key (Gemini + Vision)
*   eBay Developer Account (Client ID, Secret, RuName)
*   Perplexity API Key (for Market Trends)

### Environment Configuration
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_flask_secret_key
API_KEY=your_hmac_bearer_api_key
GOOGLE_API_KEY=your_google_cloud_api_key
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
EBAY_RU_NAME=your_ebay_runame
EBAY_CATEGORY_TREE_ID=0
PERPLEXITY_API_KEY=your_perplexity_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Market Intelligence (Docker)
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=ai_password
POSTGRES_DB=ebay_market_data
REDIS_HOST=localhost
```

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Start Market Intelligence stack (Postgres + Redis)
docker-compose -f docker-compose.db.yml up -d

# Initialize databases
python3 -c "from app_enhanced import init_db; from services.consignment_database import init_db as init_consignment; init_db(); init_consignment()"

# Seed Market Trends
python3 seed_db.py

# Launch application
python3 app_enhanced.py
```

### 🧪 Testing Protocols
The system includes a comprehensive test suite covering all services.

**Run full test suite:**
```bash
export SECRET_KEY=test EBAY_CLIENT_ID=test EBAY_CLIENT_SECRET=test GOOGLE_API_KEY=test API_KEY=test EBAY_CATEGORY_TREE_ID=0
PYTHONPATH=. pytest tests/ -v
```

**Run specific service tests:**
```bash
PYTHONPATH=. pytest tests/test_vision_service.py -v
PYTHONPATH=. pytest tests/test_ebay_get_listings.py -v
```

---

## 🔄 The Logic Pipeline: From Image to Listing

```text
[ PHOTO ACQUISITION ] --> [ HYBRID AI ANALYSIS ] --> [ PROFITABILITY GATE ]
      (Web/Bot)             (Vision + Gemini)         (Market Price Scan)
                                     |                         |
                                     V                         V
[ SECURE PUBLISHING ] <-- [ LISTING SYNTHESIS ] <--- [ CONVERSATIONAL FLOW ]
   (eBay REST API)         (LLM Optimization)         (Attribute Resolution)
```

---

## 📚 Specialized Documentation
*   📊 [Valuation Guide](VALUATION_DATA_GUIDE.md): Deep dive into decision logic and price discovery.
*   🔄 [Mapping Guide](EBAY_LISTING_MAPPING.md): How AI data translates to eBay fields.
*   🛠️ [Setup Guide](SETUP_GUIDE.md): Detailed installation and Postman testing instructions.
*   🤝 [Contributing](CONTRIBUTING.md): Guidelines for code standards and PR processes.

---

**AI List Assist** - Turning reselling into a science.
