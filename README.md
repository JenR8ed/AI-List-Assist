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
*   **Market Intelligence**: Real-time trend analysis and pricing data via integrated Perplexity AI insights.

---

## ✨ Key Features

*   **Hybrid AI Pipeline**: Combines Google Cloud Vision (OCR/Object Detection) with Gemini 1.5 Flash (Reasoning/Synthesis).
*   **Market Intelligence System**: Fetches real-time market trends via Perplexity AI (Sonar model), persisting data in PostgreSQL 15 and caching via Redis 7.
*   **Mobile-First Sourcing**: Includes a **Telegram Valuator Bot** for rapid field appraisals and instant valuations.
*   **API Usage Tracker**: Real-time cost transparency and token monitoring for AI services directly in the dashboard.
*   **Secure Architecture**: Protected by HMAC-based Bearer token verification, strict security headers (CSP, X-Frame-Options), and XSS-safe rendering.
*   **Progressive Questioning**: Intelligent dialogue flow to resolve missing item aspects via a state-machine orchestrator.

---

## 🏗️ System Architecture: The 13-Service Engine

The platform utilizes a modular, service-oriented architecture designed for reliability and extreme performance.

### 📁 Core Services
1.  **`VisionService`**: Hybrid OCR and multi-item object detection using Cloud Vision + Gemini.
2.  **`ValuationService`**: Market analysis and "Decision Gate" profitability logic using real-time eBay sold data.
3.  **`ConversationOrchestrator`**: AI-driven dialogue management to resolve missing item aspects.
4.  **`ListingSynthesisEngine`**: LLM-powered marketplace listing generation and SEO optimization.
5.  **`eBayIntegration`**: Direct interaction with modern eBay REST Inventory/Offer APIs.
6.  **`EBayCategoryService`**: Real-time interaction with the eBay Taxonomy API for metadata.
7.  **`EBayTokenManager`**: Centralized OAuth 2.0 lifecycle and refresh management.
8.  **`CategoryDetailGenerator`**: Optimized field requirement mapping and question generation.
9.  **`DraftImageManager`**: Lifecycle management for listing-specific image assets.
10. **`ConsignmentDatabase`**: Specialized tracking for participants, KYC, and asset provenance.
11. **`ValuationDatabase`**: Persistent storage for analysis history and market trends.
12. **`GeminiRestClient`**: Unified sync/async interface for Google AI REST calls.
13. **`MockValuationService`**: High-fidelity environment for development and automated testing.

### 💾 Triple-DB Strategy
The system ensures strict separation of concerns and data integrity by using three dedicated SQLite databases with **Write-Ahead Logging (WAL)** enabled:
*   **`valuations.db`**: Stores analysis history, detection confidence, and market valuations.
*   **`listings.db`**: Stores eBay inventory/offer states, draft data, and session tracking.
*   **`consignment.db`**: Manages participant profiles (KYC), tax nexus codes, and asset provenance.

### 📊 Market Intelligence Stack
For enterprise-grade market analysis, the system extends its capability via:
*   **PostgreSQL 15**: Dedicated storage for historical market trends (`market_trends` table).
*   **Redis 7**: High-speed caching for latest trend data.
*   **Perplexity AI Integration**: Uses the Sonar model to ingest real-time marketplace insights.

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

*   **HMAC Bearer Authentication**: Sensitive API endpoints require HMAC-based Bearer token verification.
*   **Content Security Policy**: Strict CSP headers prevent XSS and data injection attacks.
*   **XSS Protection**: Secure rendering logic ensures dynamic metadata is safely handled.
*   **Credential Integrity**: All credentials managed via environment variables; strict no-hardcode policy.

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
   (eBay REST API)         (LLM Optimization)         (Attribute Resolution)
```

---

## ⚙️ Setup & Installation

### Prerequisites
*   **Python 3.12+**
*   Google Cloud API Key (Gemini + Vision)
*   eBay Developer Account
*   Telegram Bot Token (Optional)
*   Docker & Docker Compose (for full Market Intelligence stack)

### Environment Configuration
Create a `.env` file based on the provided `.env.example`:
```env
SECRET_KEY=your_flask_secret_key
API_KEY=your_hmac_api_key
GOOGLE_API_KEY=your_google_cloud_api_key
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
EBAY_RU_NAME=your_ebay_runame
EBAY_CATEGORY_TREE_ID=0
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
PERPLEXITY_API_KEY=your_perplexity_key
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=ai_password
REDIS_HOST=localhost
```

### Quick Start (Local SQLite Mode)
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize databases
python3 -c "from app_enhanced import init_db; from services.consignment_database import init_db as init_consignment; init_db(); init_consignment()"

# Launch application
python3 app_enhanced.py
```

### Enterprise Start (Docker Stack)
```bash
# Launch Postgres & Redis
docker-compose -f docker-compose.db.yml up -d

# Seed market intelligence data
python3 seed_db.py

# Launch development environment
docker-compose -f docker-compose.dev.yml up --build
```

---

## 🧪 Verification & Testing

Ensure system integrity by running the test suite:
```bash
export SECRET_KEY=test EBAY_CLIENT_ID=test EBAY_CLIENT_SECRET=test GOOGLE_API_KEY=test API_KEY=test EBAY_CATEGORY_TREE_ID=0
PYTHONPATH=. pytest tests/ -v
```

---

## 📚 Specialized Documentation
*   📊 [Valuation Guide](VALUATION_DATA_GUIDE.md): Deep dive into decision logic and price discovery.
*   🔄 [Mapping Guide](EBAY_LISTING_MAPPING.md): How AI data translates to eBay fields.
*   🛠️ [Setup Guide](SETUP_GUIDE.md): Detailed installation and Postman testing instructions.
*   🤝 [Contributing](CONTRIBUTING.md): Guidelines for code standards and PR processes.

---

**AI List Assist** - Turning reselling into a science.
