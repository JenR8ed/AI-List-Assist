"""AI List Assist FastAPI entrypoint for Cloud Run."""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("ai-list-assist")

app = FastAPI(title="AI List Assist", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

SYSTEM = """You are the listing synthesis engine for AI List Assist, a tool used by professional online resellers.
Analyze the product photo and return a single JSON object for an eBay-ready draft.
Be conservative: if a brand/model is not clearly readable, say Unbranded / unknown rather than guessing a luxury house.
Titles must be <= 80 characters, no promotional spam, no ALL CAPS except acronyms.
Prices are USD, realistic sold-comp ranges for a US eBay listing in 2026, not MSRP.
Gate rules:
- LIST: identifiable item, estimated value >= 20, condition not "For parts" unless parts value is high
- CAUTION: missing brand, untested electronics/cameras, or thin comps
- NO_LIST: unidentifiable junk, estimated value < 12, or clearly damaged beyond parts value
Return JSON only."""


class AnalyzeRequest(BaseModel):
    image_data_url: str = Field(min_length=32, max_length=2_500_000)
    notes: str = Field(default="", max_length=800)


class HealthResponse(BaseModel):
    status: str
    service: str = "ai-list-assist"
    version: str = "1.0.0"


def _inference_key() -> tuple[str, str] | None:
    xai = os.getenv("XAI_API_KEY")
    if xai:
        return ("xai", xai)
    gemini = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gemini:
        return ("gemini", gemini)
    return None


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    response.headers["x-request-id"] = request_id
    log.info(
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": elapsed_ms,
        },
    )
    return response


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/ready")
def ready() -> dict[str, Any]:
    provider = _inference_key()
    return {
        "status": "ok" if provider else "degraded",
        "inference": bool(provider),
        "provider": provider[0] if provider else None,
    }


def _user_prompt(notes: str) -> str:
    extra = notes.strip() or "No extra seller notes."
    return f"""Extract a marketplace listing from this product photo.
Seller notes to incorporate: {extra}

Return this exact JSON shape:
{{
  "item_name": "string",
  "brand": "string",
  "model": "string",
  "probable_category": "eBay breadcrumb",
  "category_id": "numeric string if known, else empty",
  "detected_text": ["visible words"],
  "visual_condition": "one sentence",
  "condition": "New | New other (see details) | New with defects | Manufacturer refurbished | Seller refurbished | Used | For parts or not working",
  "condition_score": 1-10,
  "confidence": 0-1,
  "titles": ["title1", "title2", "title3"],
  "description": "plain text with line breaks, no HTML",
  "item_specifics": {{"Brand": "", "Model": "", "Color": "", "Type": ""}},
  "estimated_value": 0,
  "value_low": 0,
  "value_high": 0,
  "list_price": 0,
  "profitability": "HIGH | MEDIUM | LOW",
  "gate": "LIST | CAUTION | NO_LIST",
  "gate_reason": "one sentence",
  "fees_estimate": 0,
  "missing_required_specifics": ["field"],
  "key_factors": ["..."],
  "risks": ["..."],
  "listing_tips": ["..."]
}}"""


def _extract_json(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    body = fenced.group(1) if fenced else text
    start = body.find("{")
    end = body.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Model did not return JSON")
    parsed = json.loads(body[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Model JSON was not an object")
    return parsed


async def _call_xai(api_key: str, image_data_url: str, notes: str) -> dict[str, Any]:
    payload = {
        "model": os.getenv("XAI_MODEL", "grok-4.5"),
        "temperature": 0.25,
        "max_tokens": 1600,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url, "detail": "high"}},
                    {"type": "text", "text": _user_prompt(notes)},
                ],
            },
        ],
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json=payload,
        )
    if res.status_code >= 400:
        log.warning("xai_error status=%s", res.status_code)
        raise HTTPException(status_code=502, detail="Vision request failed")
    body = res.json()
    text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    return _extract_json(text)


async def _call_gemini(api_key: str, image_data_url: str, notes: str) -> dict[str, Any]:
    header, _, b64 = image_data_url.partition(",")
    mime = "image/jpeg"
    if "image/png" in header:
        mime = "image/png"
    elif "image/webp" in header:
        mime = "image/webp"
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM}\n\n{_user_prompt(notes)}"},
                    {"inline_data": {"mime_type": mime, "data": b64}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.25, "maxOutputTokens": 1600},
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        res = await client.post(url, json=payload)
    if res.status_code >= 400:
        log.warning("gemini_error status=%s", res.status_code)
        raise HTTPException(status_code=502, detail="Vision request failed")
    body = res.json()
    parts = body.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts)
    return _extract_json(text)


@app.post("/v1/listings/analyze")
async def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    provider = _inference_key()
    if not provider:
        raise HTTPException(status_code=503, detail="Inference is unavailable")
    name, key = provider
    if not payload.image_data_url.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="image_data_url must be a data URL")
    try:
        if name == "xai":
            analysis = await _call_xai(key, payload.image_data_url, payload.notes)
        else:
            analysis = await _call_gemini(key, payload.image_data_url, payload.notes)
    except HTTPException:
        raise
    except Exception:
        log.exception("analyze_failed")
        raise HTTPException(status_code=502, detail="Could not parse the listing") from None
    return {"ok": True, "analysis": analysis, "provider": name}
