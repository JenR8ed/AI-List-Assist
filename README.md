# AI List Assist — AI-Powered Marketplace Workflow Engine

AI List Assist is Jennifer McKinley's flagship applied AI engineering project: a multimodal e-commerce workflow that turns product intake into structured valuation, category-aware listing data, and marketplace publishing workflows.

> **Current state:** Active build. The repository is migrating from its original Flask/SQLite/Jinja implementation toward a FastAPI + Pydantic/SQLModel + PostgreSQL + React/Next.js architecture. The legacy implementation remains migration material; the target architecture is documented in `llms.txt` and `.cursorrules`.

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

## Security

- No hardcoded credentials
- Environment/managed secret injection
- HMAC-protected sensitive routes
- Request/schema validation
- CSP/security headers
- Linux-first development paths
- Human approval for consequential publishing actions

## Related JenR8ed work

- JAIOS — agentic workspace architecture
- jaios-agentic-core — architecture nucleus
- jaios-notion-gateway — event ingress boundary
- jenr8ed-deploy-kit — deployment/governance layer
- AI-Agentic-Terminal-Portfolio — engineering portfolio
- Hermes — model-routing prototype

**Jennifer McKinley / JenR8ed — AI Engineer · SDET Architect · Agentic Systems Builder**