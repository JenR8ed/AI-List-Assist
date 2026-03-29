# CLAUDE.md — ai-list-assist

## Project Overview

FastAPI application that generates real estate / marketplace listings using an
OpenAI-compatible LLM backend (NVIDIA NIM serverless or local Ollama for dev).
Deployed via GitLab CI. No GPU infra in the app container.

---

## Figma MCP Integration Rules

### Required Flow (do not skip)

1. Run `get_design_context` for the target node
2. Run `get_screenshot` for visual reference
3. Translate output into this project's conventions (Jinja2 templates or plain HTML)
4. Validate 1:1 against Figma screenshot before marking complete

### Asset Handling

- IMPORTANT: Use localhost sources from Figma MCP directly — do not add placeholder images
- IMPORTANT: DO NOT install new icon packages; use assets from the Figma payload
- Static assets → `app/static/`

---

## Project Structure
```
app/
  main.py          # FastAPI app entrypoint
  llm_client.py    # Swappable OpenAI-compat client (NIM / Ollama / OpenAI)
  listing.py       # Listing generation logic
  routers/         # FastAPI routers
  templates/       # Jinja2 HTML templates (if UI exists)
  static/          # CSS, JS, images
scripts/
  smoke_nim.py     # CI smoke test against NIM endpoint
tests/
  test_listing.py  # Unit tests — LLM client always mocked
.gitlab-ci.yml
Dockerfile         # CPU-only, ~200MB
```

---

## LLM Client Rules

- IMPORTANT: ALL model calls go through `app/llm_client.py` — never instantiate
  `openai.AsyncOpenAI` directly elsewhere
- Backend is controlled entirely by env vars — no code changes to swap providers:

| Var | Dev | CI/Prod |
|-----|-----|---------|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | `https://integrate.api.nvidia.com/v1` |
| `LLM_API_KEY` | `ollama` | `nvapi-...` (GitLab CI secret) |
| `LLM_MODEL` | `llama3.2` | `meta/llama-3.1-70b-instruct` |

- Use `AsyncOpenAI` (async) throughout — this is a FastAPI async app
- Default model: `meta/llama-3.1-70b-instruct` (NIM) / `glm-4.7-flash` (local DGX)

---

## Styling / Templates

- Styling approach: [update once Figma designs confirmed — Tailwind or plain CSS]
- IMPORTANT: Never hardcode hex colors — use CSS variables or Tailwind tokens
- Templates live in `app/templates/`; components in `app/templates/components/`

---

## GitLab CI Pipeline

Stages: `lint → test → smoke → build → deploy`

- `test` stage: unit tests only — LLM client is always mocked, never hits real API
- `smoke` stage: `scripts/smoke_nim.py` — validates NIM endpoint reachability
  (runs on `main` branch only, requires `LLM_BASE_URL` + `LLM_API_KEY` CI vars)
- `build` stage: builds CPU-only Docker image — no GPU base image, no model weights
- IMPORTANT: Never bake model weights or API keys into the Docker image

---

## Testing Rules

- Mock `app.llm_client.get_client` in all unit tests — never hit real LLM in `test` stage
- Test file location: `tests/`
- Use `pytest` + `pytest-asyncio`

---

## Code Quality

- IMPORTANT: Never hardcode API keys, base URLs, or model names — always use `os.environ`
- Prompt templates live in `app/prompts/` (or as constants in `listing.py` for small projects)
- Keep listing generation logic in `app/listing.py`, not in routers

---

## Resources

- [NVIDIA NIM API](https://integrate.api.nvidia.com/v1) — `nvapi-` key from build.nvidia.com
- [Figma MCP Server Docs](https://developers.figma.com/docs/figma-mcp-server/)
- [Ollama + Claude Code guide](https://ollama.com/blog/claude)
