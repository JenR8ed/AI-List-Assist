# AI List Assist: Enterprise-Grade Reselling Orchestration

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Architecture](https://img.shields.io/badge/architecture-service--based-orange.svg)

**AI List Assist** is an advanced automation platform for professional online resellers. It transforms unstructured visual data (photos) into structured, category-specific marketplace listings using a **Hybrid AI** architecture (Google Gemini 1.5 Flash + Cloud Vision).

---

## 🛠️ How It Works: The Hybrid AI Pipeline

AI List Assist utilizes a sophisticated multi-stage pipeline to convert a single photo into a high-quality marketplace listing.

```text
   +-------------------+       +-------------------+       +-------------------+
   |  📸 Visual Input  | ----> |  🧠 Vision AI     | ----> |  💰 Market Value  |
   |  (Dashboard/Bot)  |       |  (OCR & Detection)|       |  (Trend Analysis) |
   +-------------------+       +-------------------+       +-------------------+
                                                                     |
                                                                     v
   +-------------------+       +-------------------+       +-------------------+
   |  🚀 Secure Pub.   | <---- |  ✍️ List Synthesis | <---- |  ⚖️ Decision Gate |
   |  (eBay REST API)  |       |  (SEO & Mapping)  |       |  (List/No-List)   |
   +-------------------+       +-------------------+       +-------------------+
```

---

## 🚀 The Reselling Problem: Solved

In high-volume reselling, the "Listing Bottleneck" is the primary barrier to scale. AI List Assist eliminates this by:
- **Instant Valuation**: Moving from manual research to data-backed "List/No-List" decisions in seconds.
- **Cognitive Automation**: Handling the complex mapping of eBay item specifics that humans often skip.
- **Operational Scalability**: Enabling a transition from individual sourcing to commercial-grade warehouse intake.

---

## ✨ Key Features

- **Hybrid AI Pipeline**: Combines Google Cloud Vision (OCR/Object Detection) with Gemini 1.5 Flash (Reasoning/Synthesis).
- **API Usage Tracker**: Real-time cost transparency and token monitoring directly in the dashboard.
- **Deterministic Analysis**: Uses SHA-256 image hashing to ensure consistent valuation results for identical items.
- **Secure Architecture**: Protected by HMAC-based API key verification and strict security headers.
- **Omnichannel Readiness**: Modular design ready to expand beyond eBay to Mercari, Poshmark, and more.

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

## 🏗️ System Architecture

The platform utilizes a modular, service-oriented architecture designed for reliability and speed.

### 📁 13 Specialized Services
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
11. **`ValuationDatabase`**: Persistent storage for analysis history and market trends (with 95% faster bulk inserts).
12. **`GeminiRestClient`**: Unified sync/async interface for direct Google AI REST calls, bypassing heavy SDK dependencies.
13. **`MockValuationService`**: High-fidelity environment for development and automated testing.

### 💾 Triple-DB Strategy
The system maintains data integrity and operational speed by separating concerns into three SQLite databases (with WAL enabled):
- **`valuations.db`**: Records analysis history, detection confidence, and market valuations.
- **`listings.db`**: Stores eBay inventory/offer states, draft data, and submission logs.
- **`consignment.db`**: Manages participant profiles (KYC), tax nexus codes, and asset tracking.

---

## 🔒 Security & Reliability

Data integrity and secure access are core pillars of the AI List Assist architecture.

- **HMAC API Protection**: Sensitive endpoints (analysis, publishing) are secured using HMAC-based signature verification against a server-side `API_KEY`.
- **Deterministic Hashing**: Every uploaded image is processed using SHA-256 hashing. This ensures that identical items receive consistent valuations and prevents redundant, costly AI processing.
- **Transactional Integrity**: All database operations utilize SQLite's Write-Ahead Logging (WAL) mode to ensure atomic, consistent, isolated, and durable (ACID) transactions even under high load.
- **Credential Safety**: Strict environment variable enforcement ensures no API secrets or tokens are ever persisted in the source code or build artifacts.

---

## 📱 Primary Interfaces

AI List Assist provides two primary entry points for item intake and valuation.

### 💻 Web Dashboard
The desktop-optimized central hub for bulk management, eBay publishing, and detailed analytics.
- **Studio Mode**: Batch image processing.
- **Reporting**: API usage tracking and profitability insights.

### 🤖 Telegram Valuator Bot
A mobile-first companion designed specifically for **Sourcing Mode**.
- **Field Appraisal**: Send a photo from a thrift store or estate sale for instant market analysis.
- **Real-time Notifications**: Get alerts when listings are published or items are sold.
- **Zero Latency**: Direct interaction with the Vision pipeline without opening a browser.

---

## 🔄 The Logic Pipeline: From Image to Listing

1.  **Visual Acquisition**: Upload photos via the **Web Dashboard** or the **Telegram Valuator Bot**.
2.  **Hybrid Analysis**: AI detects items, assesses condition, and extracts brand/model metadata using deterministic image hashing.
3.  **The Decision Gate**: Items are filtered based on 90-day sold history, supply, and demand.
4.  **Conversational Refinement**: The `ConversationOrchestrator` asks targeted questions to fill required eBay aspects.
5.  **Marketplace Synthesis**: Optimized titles and HTML descriptions are generated using [eBay Mapping Logic](EBAY_LISTING_MAPPING.md).
6.  **Secure Publishing**: Direct deployment to eBay via OAuth 2.0 and the Inventory API.

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.12+ (Developed on 3.12.12)
- Google Cloud API Key (Gemini + Vision)
- eBay Developer Account (Sandbox or Production)
- Telegram Bot Token (Optional, for mobile valuation)

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
- **Telegram Valuator Bot**: `python your_ebay_valuator_bot.py`
- **Database Init**: `python seed_db.py`

---

## 🧪 Verification & Testing

Ensure system integrity by running the test suite:
```bash
export PYTHONPATH=$PYTHONPATH:.
# Set dummy credentials for local testing
export SECRET_KEY=test EBAY_CLIENT_ID=test EBAY_CLIENT_SECRET=test GOOGLE_API_KEY=test API_KEY=test EBAY_CATEGORY_TREE_ID=0
python -m pytest tests/ -v
```

For detailed valuation testing, see the [Valuation Data Guide](VALUATION_DATA_GUIDE.md).

---

## 📅 Roadmap

- **Phase 1: Automation** (Complete) - Core Hybrid Vision and eBay REST integration.
- **Phase 2: Reporting** (In Progress) - Consignment dashboards and multi-item trend analysis.
- **Phase 3: Scale** (Planned) - Omnichannel support (Mercari, Poshmark integration).

---

## 📚 Specialized Documentation
- 📖 [Setup Guide](SETUP_GUIDE.md): Detailed installation and Postman testing instructions.
- 📊 [Valuation Guide](VALUATION_DATA_GUIDE.md): Deep dive into decision logic and price discovery.
- 🔄 [Mapping Guide](EBAY_LISTING_MAPPING.md): How AI data translates to eBay fields.
- 🤝 [Contributing](CONTRIBUTING.md): Guidelines for code standards and PR processes.

---

**AI List Assist** - Turning reselling into a science.
