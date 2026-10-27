"""Security regression tests for local UI sessions and draft publishing gates."""
import json
import os
import sqlite3
from unittest.mock import patch

import pytest

os.environ.setdefault("SECRET_KEY", "test-only-secret")
os.environ.setdefault("API_KEY", "test-only-api-key")
os.environ.setdefault("EBAY_CLIENT_ID", "test-only-ebay")
os.environ.setdefault("EBAY_CLIENT_SECRET", "test-only-ebay")

from app_enhanced import app, init_db  # noqa: E402
from shared.models import ListingDraft, ItemCondition  # noqa: E402


@pytest.fixture
def security_client(tmp_path, monkeypatch):
    # Keep test databases and uploads away from the checkout.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("API_KEY", "test-only-api-key")
    app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
    with app.app_context():
        init_db()
    with app.test_client() as client:
        yield client


def _draft(listing_id="draft-one", *, ready=True):
    return ListingDraft(
        listing_id=listing_id,
        item_id="item-one",
        title="Test Camera",
        description="An accurately described used camera.",
        category_id="293",
        condition=ItemCondition.USED,
        price=45.0,
        ready_for_api=ready,
    )


def _insert_draft(draft, status="draft"):
    conn = sqlite3.connect("listings.db")
    try:
        conn.execute(
            "INSERT INTO listings (listing_id,item_id,title,price,status,draft_data) VALUES (?,?,?,?,?,?)",
            (draft.listing_id, draft.item_id, draft.title, draft.price, status, json.dumps(draft.to_dict())),
        )
        conn.commit()
    finally:
        conn.close()


def test_login_requires_configured_password(security_client, monkeypatch):
    monkeypatch.delenv("LOCAL_UI_PASSWORD", raising=False)
    assert security_client.get("/login").status_code == 503


def test_session_auth_and_csrf(security_client, monkeypatch):
    monkeypatch.setenv("LOCAL_UI_PASSWORD", "test-local-password")
    page = security_client.get("/login")
    assert page.status_code == 200
    with security_client.session_transaction() as state:
        token = state["csrf_token"]
    wrong = security_client.post("/login", data={"password": "wrong", "csrf_token": token})
    assert wrong.status_code == 401
    response = security_client.post(
        "/login", data={"password": "test-local-password", "csrf_token": token}
    )
    assert response.status_code == 302
    assert security_client.get("/api/listings/drafts").status_code == 200
    assert security_client.post("/api/category/suggest", json={"item_name": "camera"}).status_code == 403
    with security_client.session_transaction() as state:
        token = state["csrf_token"]
    authorized = security_client.post(
        "/api/category/suggest",
        json={"item_name": "camera"},
        headers={"X-CSRF-Token": token},
    )
    assert authorized.status_code == 200


def test_publish_disabled_even_with_valid_server_key(security_client, monkeypatch):
    monkeypatch.delenv("ENABLE_EBAY_PUBLISHING", raising=False)
    with patch("app_enhanced.ebay_integration") as ebay:
        response = security_client.post(
            "/api/listing/publish",
            json={"listing_id": "anything"},
            headers={"Authorization": "Bearer test-only-api-key"},
        )
        assert response.status_code == 403
        ebay.create_listing.assert_not_called()


def test_approval_requires_valid_stored_draft(security_client):
    _insert_draft(_draft(ready=False))
    response = security_client.post(
        "/api/listing/draft-one/approve",
        headers={"Authorization": "Bearer test-only-api-key"},
    )
    assert response.status_code == 422
    conn = sqlite3.connect("listings.db")
    try:
        assert conn.execute("SELECT status FROM listings WHERE listing_id='draft-one'").fetchone()[0] == "draft"
    finally:
        conn.close()


def test_unapproved_draft_rejected_with_publish_flag(security_client, monkeypatch):
    _insert_draft(_draft(), status="draft")
    monkeypatch.setenv("ENABLE_EBAY_PUBLISHING", "1")
    with patch("app_enhanced.ebay_integration") as ebay:
        response = security_client.post(
            "/api/listing/publish",
            json={"listing_id": "draft-one"},
            headers={"Authorization": "Bearer test-only-api-key"},
        )
        assert response.status_code == 409
        ebay.create_listing.assert_not_called()


def test_legacy_direct_publish_disabled(security_client):
    response = security_client.post(
        "/api/ebay/submit-listing",
        json={"valuation_id": "item-one"},
        headers={"Authorization": "Bearer test-only-api-key"},
    )
    assert response.status_code == 410
