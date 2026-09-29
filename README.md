# AI List Assist — marketplace listing workflow

AI List Assist is Jennifer McKinley's applied AI engineering project for product intake, valuation, listing drafts, and marketplace integration. It is an active build; publishing routes are disabled in this slice.

> **Current state:** The checked-in entry point is `app_enhanced.py`, a Flask application with Jinja templates and SQLite persistence. FastAPI, Pydantic/SQLModel, PostgreSQL, and React/Next.js are migration goals, not the current runnable stack.

## Current local verification

For the local fixture journey, start the Flask app with `LOCAL_DRAFT_MODE=1 python app_enhanced.py` and open `http://127.0.0.1:5000/local` (also linked from `/` and `/simple`). Select the example item, inspect the persisted structured record, create a draft, enter a description and price, save, and explicitly approve it. The page uses a signed local browser session and CSRF token; no provider key, API key in browser code, image analysis, external API, or marketplace credential is needed. Publishing remains disabled even after approval. This fixture path makes no claim that an uploaded image was analyzed or a market price was measured.

From a fresh, disposable clone with Python 3.12+, install the checked-in dependencies and run the offline smoke tests:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests/test_smoke.py -q
```

The tests set sentinel environment values, initialize local SQLite files, and may remove `listings.db`, `valuations.db`, and `consignment.db` in their teardown. Run them only in a disposable checkout without valuable files under those names or a local `.env`. `tests/test_local_fixture_journey.py` covers the fixture journey through API and HTML forms with network access blocked; the smoke test covers boot and basic auth. Neither establishes external API, OAuth, or publishing readiness.

## Core workflow

```
Product intake → Vision/Gemini analysis → structured item data
→ valuation/profitability → category/aspect mapping
→ listing synthesis → human review → eBay workflow
```

## Current engineering focus

- Multimodal image/OCR analysis and structured extraction
- Valuation, market intelligence, and profitability decision support
- eBay taxonomy, Inventory/Offer, OAuth, and listing workflows
- Typed validation around probabilistic AI output
- Regression and edge-case testing
- Performance optimization, including recent valuation-stat query batching/caching
- Human-in-the-loop approval boundaries
- Security and secrets hygiene

## Target architecture

| Layer | Direction |
|---|---|
| Backend | FastAPI |
| Contracts / ORM | Pydantic + SQLModel |
| Database | PostgreSQL / managed Postgres |
| Frontend | React / Next.js + TailwindCSS |
| Async work | native async/await + Redis-backed jobs |
| AI | Gemini + Google Cloud Vision |
| Marketplace | eBay APIs |
| Dev environment | WSL2 / Linux |

## Migration roadmap

1. Stabilize legacy workflow and regression coverage.
2. Move Flask routes to FastAPI routers.
3. Convert legacy persistence/models to Pydantic + SQLModel/PostgreSQL.
4. Replace Jinja/vanilla UI with React/Next.js.
5. Move external I/O to native async and expensive work to Redis-backed workers.
6. Add reusable AI evaluation datasets, model/prompt comparisons, regression suites, confidence thresholds, and measurable workflow-quality signals.

## Reliability / evaluation

The project is being developed as an applied AI reliability lab: model output is treated as a candidate, then validated, enriched, transformed, and gated by deterministic application logic. The goal is reproducible, measurable AI behavior rather than prompt-only demos.

## Security boundary

The application reads integration configuration from its environment. Both marketplace publishing routes fail closed in this slice, while other legacy integration paths remain subject to separate security review before any deployment or credential-based test. The offline tests do not establish production readiness.

## Related JenR8ed work

- jenr8ed-deploy-kit — deployment/governance layer
- [Engineering portfolio](https://jenr8edai.com/) — primary public destination

**Jennifer McKinley / JenR8ed — AI Engineer · SDET Architect · Agentic Systems Builder**
