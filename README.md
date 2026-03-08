# AI List Assist: Enterprise-Grade Reselling Orchestration

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)
![Architecture](https://img.shields.io/badge/architecture-service--based-orange.svg)

**AI List Assist** is an advanced, end-to-end automation platform for professional online resellers. It bridges the gap between unstructured visual data (photos) and structured marketplace requirements (eBay listings) using a **Hybrid AI** architecture (Google Gemini 1.5 Flash + Cloud Vision).

---

## 🚀 Why AI List Assist?

In the high-volume world of professional reselling, the "Listing Bottleneck" is the primary barrier to scale. AI List Assist eliminates this by:
- **Instant Valuation**: Moving from "What is this worth?" to a data-backed "List this now" in seconds.
- **Cognitive Automation**: Handling the tedious mapping of item specifics that humans often get wrong or skip.
- **Operational Scalability**: Transitioning from individual sourcing to commercial-grade warehouse intake.

---

## 🌟 Key Features

*   **🤖 Multi-Item Hybrid Vision**: Identify and separate multiple items from a single photo, extracting brand, model, and condition using Google Cloud Vision and Gemini 1.5 Flash.
*   **⚖️ Decision Gate Valuation Engine**: Instant market analysis providing estimated values, resale scores (1-10), and a "Worth Listing" recommendation based on real-time profitability metrics.
*   **💬 Conversational Listing Assistant**: An AI-driven state machine that guides users through filling in missing eBay item specifics, resolving ambiguities through natural dialogue.
*   **🔌 Direct eBay Publishing**: Secure OAuth 2.0 integration with eBay’s modern **Inventory and Offer APIs** for seamless one-click publishing and state reconciliation.
*   **🤝 Consignment & Asset Tracking**: Manage participants with KYC status, tax nexus codes, and commission tracking at scale via the `ConsignmentDatabase`.
*   **💰 API Usage & Cost Tracker**: Real-time monitoring of AI and marketplace API calls with accurate cost estimation for transparent operations.
*   **🎨 Palette UX**: ARIA-compliant dashboard with full keyboard navigation support (`tabindex="0"`) and responsive design.
*   **📱 Field Sourcing**: Mobile-first sourcing via the async Telegram Valuator Bot (`your_ebay_valuator_bot.py`).

---

## 🎮 Operational Modes

AI List Assist adapts to your specific reselling workflow through four dedicated modes:

| Mode | Purpose | Target User |
| :--- | :--- | :--- |
| **🏠 Locker Mode** | Secure storage and management of existing inventory. | Personal Resellers |
| **🔍 Sourcing Mode** | On-the-go valuation and market analysis in the field. | Thrift/Flea Market Hunters |
| **🤝 Consignment** | Tracking assets, commissions, and KYC for third-party sellers. | Consignment Businesses |
| **🏬 Studio Mode** | High-speed, bulk photo intake and batch processing. | Commercial Warehouses |

---

## 🏗️ Technical Architecture

### 🛠️ Tech Stack
- **Backend**: Python 3.12+ (Flask 3.0.0) with strict type hinting and dataclasses.
- **AI Stack**: Direct REST integration with Google Cloud Vision & Gemini 1.5 Flash (optimized for performance).
- **Marketplace**: eBay Sell APIs (Inventory, Taxonomy, Account, Analytics).
- **Persistence**: **Triple-DB Strategy** using SQLite with WAL enabled:
    - `valuations.db`: Tracks analysis history and market trends.
    - `listings.db`: Stores eBay inventory/offer state and draft data.
    - `consignment.db`: Manages participant data, KYC, and asset tracking.
- **Security**: Endpoint protection via `@require_api_key` (HMAC comparison) and strict file upload validation (MIME/Extension).
- **Infrastructure**: Docker-ready for multi-container deployments.

### 📁 Modular Service System
The platform is built on 13 specialized services:
1.  `VisionService`: Hybrid OCR and multi-item object detection.
2.  `ValuationService`: Market analysis and decision gate logic.
3.  `ConversationOrchestrator`: AI-driven dialogue management for item aspects.
4.  `ListingSynthesisEngine`: SEO-optimized marketplace listing generation.
5.  `eBayIntegration`: Modern REST Inventory/Offer API management.
6.  `EBayCategoryService`: Interaction with eBay Taxonomy API for metadata.
7.  `EBayTokenManager`: Centralized OAuth 2.0 lifecycle management.
8.  `CategoryDetailGenerator`: Optimized question generation (~30x speedup via O(N+M) mapping).
9.  `DraftImageManager`: Lifecycle management for listing images.
10. `ConsignmentDatabase`: Participant KYC and asset provenance tracking.
11. `ValuationDatabase`: History and trend analysis storage.
12. `GeminiRestClient`: Unified sync/async interface for Google AI.
13. `MockValuationService`: High-fidelity development and testing environment.

---

## 🔄 Core Workflow

1.  **Visual Acquisition**: Upload photos via the Web Dashboard or the Telegram Bot.
2.  **Hybrid Analysis**: AI detects items, extracts text, and evaluates market potential.
3.  **The Decision Gate**: Filters items based on 90-day sold history and demand.
4.  **Guided Refinement**: The Conversational Orchestrator resolves missing eBay aspects.
5.  **Marketplace Synthesis**: Automated generation of SEO-optimized eBay listings.
6.  **Secure Publishing**: Direct deployment to eBay via the Inventory API.

---

## ⚙️ Getting Started

### 1. Installation
```bash
# Clone and enter the repository
git clone <repository-url>
cd ai-list-assist

# Install core dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file from the following template:
```env
SECRET_KEY=...             # Flask secret key
API_KEY=...                # Custom API Key for Authorization: Bearer <token>
GOOGLE_API_KEY=...         # Google AI Studio API Key
EBAY_CLIENT_ID=...         # eBay Dev ID
EBAY_CLIENT_SECRET=...     # eBay Cert ID
EBAY_USE_SANDBOX=True      # Toggle for Sandbox/Production
EBAY_CATEGORY_TREE_ID=0    # Default eBay Category Tree (0 for US)
TELEGRAM_BOT_TOKEN=...     # For your_ebay_valuator_bot.py
```

### 3. Launching the System
```bash
# Start the Flask backend
python app_enhanced.py

# (Optional) Start the Telegram Bot for field sourcing
python your_ebay_valuator_bot.py
```

---

## 🧪 Testing
Run the comprehensive test suite (Unit + Integration):
```bash
export PYTHONPATH=$PYTHONPATH:.
python -m pytest tests/ -v
```

---

## 📅 Roadmap

- **Phase 1: Automation** (Complete) - Core Hybrid Vision and eBay REST integration.
- **Phase 2: Reporting & Analytics** (In Progress) - Consignment dashboards and trend analysis.
- **Phase 3: Scale** (Planned) - Omnichannel support (Mercari, Poshmark).

---

**AI List Assist** - Turning reselling into a science.
