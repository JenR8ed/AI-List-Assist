# AI List Assist: Enterprise-Grade Reselling Orchestration

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Architecture](https://img.shields.io/badge/architecture-service--based-orange.svg)

**AI List Assist** is an advanced automation platform for professional online resellers. It transforms unstructured visual data (photos) into structured, category-specific marketplace listings using a **Hybrid AI** architecture (Google Gemini 1.5 Flash + Cloud Vision).

---

## 🚀 The Reselling Problem: Solved

In high-volume reselling, the "Listing Bottleneck" is the primary barrier to scale. AI List Assist eliminates this by:
- **Instant Valuation**: Moving from manual research to data-backed "List/No-List" decisions in seconds.
- **Cognitive Automation**: Handling the complex mapping of eBay item specifics that humans often skip.
- **Operational Scalability**: Enabling a transition from individual sourcing to commercial-grade warehouse intake.

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
10. **`ConsignmentDatabase`**: specialized tracking for participants, KYC, and asset provenance.
11. **`ValuationDatabase`**: Persistent storage for analysis history and market trends.
12. **`GeminiRestClient`**: Unified sync/async interface for direct Google AI REST calls.
13. **`MockValuationService`**: High-fidelity environment for development and automated testing.

### 💾 Triple-DB Strategy
The system maintains data integrity and operational speed by separating concerns into three SQLite databases (with WAL enabled):
- **`valuations.db`**: Records analysis history, detection confidence, and market valuations.
- **`listings.db`**: Stores eBay inventory/offer states, draft data, and submission logs.
- **`consignment.db`**: Manages participant profiles (KYC), tax nexus codes, and asset tracking.

---

## 🔄 The Logic Pipeline: From Image to Listing

1.  **Visual Acquisition**: Upload photos via the **Dashboard** or the **Telegram Valuator Bot**.
2.  **Hybrid Analysis**: AI detects items, assesses condition, and extracts brand/model metadata.
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

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd ai-list-assist

# Install core dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Update with your API keys
```

### Launching
- **Web Dashboard**: `python app_enhanced.py` (Visit `http://localhost:5000`)
- **Telegram Bot**: `python your_ebay_valuator_bot.py`
- **Database Init**: `python seed_db.py`

---

## 🧪 Verification & Testing

Ensure system integrity by running the test suite:
```bash
export PYTHONPATH=$PYTHONPATH:.
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
