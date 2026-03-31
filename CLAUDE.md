# CLAUDE.md — AI List Assist

## Project Overview

Flask-based enterprise automation platform for eBay reselling. It uses a Hybrid AI architecture (Google Gemini 1.5 Flash + Google Cloud Vision) to transform item photos into structured marketplace listings.

---

## Architecture & Tech Stack

- **Backend**: Flask 3.1.3 (Python 3.12+)
- **AI Engine**: Hybrid (Cloud Vision for OCR/Detection + Gemini 1.5 Flash for reasoning)
- **Databases**: SQLite (Triple-DB strategy with WAL enabled: `valuations.db`, `listings.db`, `consignment.db`)
- **Integration**: eBay REST APIs (Inventory, Offer, Taxonomy, Account)
- **Interfaces**: Web Dashboard (Jinja2) + Telegram Valuator Bot

---

## Development Rules

### Coding Standards
- **Strict Credential Policy**: NEVER hardcode API keys or secrets. Use environment variables.
- **Service-Oriented**: Core logic resides in the `services/` directory. `app_enhanced.py` orchestrates these services.
- **Type Safety**: Use Python dataclasses (defined in `shared/models.py`) and type hints for all public methods.
- **Security**: All sensitive endpoints must use the `@require_api_key` decorator (HMAC Bearer token comparison).

### External API Rules
- **eBay**: Always use modern REST APIs (not legacy Trading API).
- **Gemini**: All calls must go through `services/gemini_rest_client.py`.
- **Vision**: All calls must go through `services/vision_service.py`.

---

## Project Structure
```
services/              # Core service layer (13 services)
  vision_service.py    # Hybrid OCR and detection
  valuation_service.py # Market analysis and pricing logic
  ebay_integration.py  # eBay REST API client
  ...
shared/
  models.py            # Dataclasses and Enums
templates/             # Flask Jinja2 templates
tests/                 # Pytest suite
app_enhanced.py        # Main Flask application entrypoint
your_ebay_valuator_bot.py # Telegram bot entrypoint
Dockerfile             # Python 3.12-slim base
docker-compose.dev.yml # Development stack configuration
```

---

## Testing Protocols

- **Execution**: Run `python -m pytest tests/ -v`.
- **Requirements**: Requires `SECRET_KEY`, `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`, `GOOGLE_API_KEY`, `API_KEY`, and `EBAY_CATEGORY_TREE_ID` env vars (can be dummy values for unit tests).
- **Mocking**: Use `@patch` or localized mocks. Avoid global `sys.modules` mocking.

---

## Deployment & Setup

- **Local**: `pip install -r requirements.txt && python app_enhanced.py`
- **Docker**: `docker-compose -f docker-compose.dev.yml up --build`
- **Environment**: Configuration via `.env` file (copied from `.env.example`).
- **OAuth**: Handles eBay OAuth 2.0 via a local callback routed through ngrok/tunneling.

---

## Resources

- [eBay Developer Portal](https://developer.ebay.com/)
- [Google AI Studio (Gemini)](https://aistudio.google.com/)
- [Google Cloud Vision AI](https://cloud.google.com/vision)
