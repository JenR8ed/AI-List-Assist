from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "ai-list-assist"
    assert "x-request-id" in res.headers


def test_ready_degraded_without_keys(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    res = client.get("/ready")
    assert res.status_code == 200
    assert res.json()["inference"] is False


def test_analyze_rejects_without_keys(monkeypatch):
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    res = client.post(
        "/v1/listings/analyze",
        json={"image_data_url": "data:image/jpeg;base64," + ("A" * 40), "notes": ""},
    )
    assert res.status_code == 503
