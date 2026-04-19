"""
Consignment Database Service
Manages participants, assets, transactions, and documentation for the
consignment & return protocol system.
Schema version: 1.0.0
"""

import sqlite3
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pathlib import Path


DB_PATH = "consignment.db"


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS participants (
    participant_id      TEXT PRIMARY KEY,
    display_name        TEXT,
    email               TEXT,
    kyc_status          TEXT NOT NULL DEFAULT 'PENDING',   -- PENDING | VERIFIED | REJECTED
    tax_nexus_code      TEXT,                              -- ISO-3166-2, e.g. US-CA
    payout_method_type  TEXT,
    last_verification_utc TEXT,
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    asset_id            TEXT PRIMARY KEY,
    participant_id      TEXT NOT NULL REFERENCES participants(participant_id),
    provenance_hash     TEXT,                              -- SHA-256 of identifying data
    basis_value         REAL NOT NULL DEFAULT 0.0,
    condition_state     TEXT NOT NULL DEFAULT 'GOOD',      -- MINT | GOOD | DAMAGED | INAD
    current_status      TEXT NOT NULL DEFAULT 'RECEIVED',  -- RECEIVED | LISTED | SOLD | RETURN_PENDING | CLOSED
    ebay_listing_id     TEXT,
    sale_price          REAL,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id      TEXT PRIMARY KEY,
    asset_id            TEXT NOT NULL REFERENCES assets(asset_id),
    call_type           TEXT NOT NULL,  -- LISTING_SUBMISSION | SALE_RECORD | RETURN_CLAIM | DISPUTE_RESOLUTION
    commission_multiplier REAL NOT NULL DEFAULT 0.15,
    timestamp_iso8601   TEXT NOT NULL,
    carrier_trace_id    TEXT,
    notes               TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    document_id         TEXT PRIMARY KEY,
    asset_id            TEXT NOT NULL REFERENCES assets(asset_id),
    gsa_file_name       TEXT NOT NULL,
    persistent_url      TEXT,
    mime_type           TEXT NOT NULL DEFAULT 'application/pdf',
    document_category   TEXT NOT NULL,  -- VALUATION | DAMAGE_PROOF | SHIP_LABEL
    created_at          TEXT NOT NULL
);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    with _get_conn() as conn:
        conn.executescript(SCHEMA_SQL)
    print(f"Consignment DB initialised at {DB_PATH}")


# ---------------------------------------------------------------------------
# Participants
# ---------------------------------------------------------------------------

def create_participant(
    display_name: str,
    email: str,
    tax_nexus_code: Optional[str] = None,
    payout_method_type: Optional[str] = None,
) -> Dict[str, Any]:
    pid = f"P-{uuid.uuid4().hex[:10].upper()}"
    now = _now()
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO participants
               (participant_id, display_name, email, kyc_status,
                tax_nexus_code, payout_method_type, created_at)
               VALUES (?, ?, ?, 'PENDING', ?, ?, ?)""",
            (pid, display_name, email, tax_nexus_code, payout_method_type, now),
        )
    return get_participant(pid)


def get_participant(participant_id: str) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM participants WHERE participant_id = ?", (participant_id,)
        ).fetchone()
    return dict(row) if row else None


def list_participants(kyc_status: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM participants"
    params = []
    if kyc_status:
        sql += " WHERE kyc_status = ?"
        params.append(kyc_status)
    sql += " ORDER BY created_at DESC"
    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def update_participant_kyc(participant_id: str, kyc_status: str) -> Optional[Dict[str, Any]]:
    now = _now()
    with _get_conn() as conn:
        conn.execute(
            """UPDATE participants
               SET kyc_status = ?, last_verification_utc = ?
               WHERE participant_id = ?""",
            (kyc_status, now, participant_id),
        )
    return get_participant(participant_id)


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

def create_asset(
    participant_id: str,
    basis_value: float,
    condition_state: str = "GOOD",
    provenance_data: Optional[str] = None,
) -> Dict[str, Any]:
    asset_id = f"EB-{uuid.uuid4().int % 10**12:012d}"
    provenance_hash = (
        hashlib.sha256(provenance_data.encode()).hexdigest()
        if provenance_data
        else hashlib.sha256(asset_id.encode()).hexdigest()
    )
    now = _now()
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO assets
               (asset_id, participant_id, provenance_hash, basis_value,
                condition_state, current_status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'RECEIVED', ?, ?)""",
            (asset_id, participant_id, provenance_hash, basis_value, condition_state, now, now),
        )
    # Auto-log the intake transaction
    log_transaction(asset_id, "LISTING_SUBMISSION", notes="Asset received into consignment")
    return get_asset(asset_id)


def get_asset(asset_id: str) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM assets WHERE asset_id = ?", (asset_id,)
        ).fetchone()
    return dict(row) if row else None


def list_assets(
    participant_id: Optional[str] = None,
    current_status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM assets WHERE 1=1"
    params = []
    if participant_id:
        sql += " AND participant_id = ?"
        params.append(participant_id)
    if current_status:
        sql += " AND current_status = ?"
        params.append(current_status)
    sql += " ORDER BY created_at DESC"
    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def update_asset_status(
    asset_id: str,
    new_status: str,
    ebay_listing_id: Optional[str] = None,
    sale_price: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    now = _now()
    with _get_conn() as conn:
        conn.execute(
            """UPDATE assets
               SET current_status = ?, ebay_listing_id = COALESCE(?, ebay_listing_id),
                   sale_price = COALESCE(?, sale_price), updated_at = ?
               WHERE asset_id = ?""",
            (new_status, ebay_listing_id, sale_price, now, asset_id),
        )
    return get_asset(asset_id)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------

def log_transaction(
    asset_id: str,
    call_type: str,
    commission_multiplier: float = 0.15,
    carrier_trace_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    txn_id = str(uuid.uuid4())
    now = _now()
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO transactions
               (transaction_id, asset_id, call_type, commission_multiplier,
                timestamp_iso8601, carrier_trace_id, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (txn_id, asset_id, call_type, commission_multiplier, now, carrier_trace_id, notes),
        )
    return get_transaction(txn_id)


def get_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,)
        ).fetchone()
    return dict(row) if row else None


def list_transactions(asset_id: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM transactions"
    params = []
    if asset_id:
        sql += " WHERE asset_id = ?"
        params.append(asset_id)
    sql += " ORDER BY timestamp_iso8601 DESC"
    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def calculate_commission(asset_id: str) -> Dict[str, Any]:
    """Calculate commission owed for a sold asset."""
    asset = get_asset(asset_id)
    if not asset:
        return {"error": "Asset not found"}
    if asset["current_status"] != "SOLD":
        return {"error": "Asset is not yet SOLD"}
    txns = list_transactions(asset_id)
    # Use the most recent commission multiplier from SALE_RECORD if present
    sale_txns = [t for t in txns if t["call_type"] == "SALE_RECORD"]
    multiplier = sale_txns[0]["commission_multiplier"] if sale_txns else 0.15
    sale_price = asset.get("sale_price") or 0.0
    commission = round(sale_price * multiplier, 2)
    payout = round(sale_price - commission, 2)
    return {
        "asset_id": asset_id,
        "sale_price": sale_price,
        "commission_multiplier": multiplier,
        "commission_amount": commission,
        "participant_payout": payout,
    }


# ---------------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------------

def attach_document(
    asset_id: str,
    document_category: str,
    persistent_url: str,
    mime_type: str = "application/pdf",
    gsa_file_name: Optional[str] = None,
) -> Dict[str, Any]:
    doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    now = _now()
    if not gsa_file_name:
        # Auto-generate GSA-compliant file name: YYYYMMDD_ASSETID_CATEGORY
        date_str = datetime.now().strftime("%Y%m%d")
        gsa_file_name = f"{date_str}_{asset_id}_{document_category}"
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO documents
               (document_id, asset_id, gsa_file_name, persistent_url,
                mime_type, document_category, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (doc_id, asset_id, gsa_file_name, persistent_url, mime_type, document_category, now),
        )
    return get_document(doc_id)


def get_document(document_id: str) -> Optional[Dict[str, Any]]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE document_id = ?", (document_id,)
        ).fetchone()
    return dict(row) if row else None


def list_documents(asset_id: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM documents"
    params = []
    if asset_id:
        sql += " WHERE asset_id = ?"
        params.append(asset_id)
    sql += " ORDER BY created_at DESC"
    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
