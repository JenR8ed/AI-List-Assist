"""
Database service for tracking valuations and eBay submissions
"""

import json
import logging
import os
import sqlite3
import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from shared.models import ItemValuation

try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class ValuationDatabase:
    """Database service for tracking all valuations and eBay submissions."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = os.getenv("DATA_DIR")
            db_path = os.path.join(data_dir, "valuations.db") if data_dir else "valuations.db"
        self.db_path = db_path
        self._local = threading.local()

        # Cache setup
        self._stats_cache = None
        self._stats_cache_time = 0
        self.cache_ttl = 300  # 5 minutes

        # Redis setup
        self.redis_client = None
        if redis is not None:
            redis_host = os.environ.get("REDIS_HOST")
            if redis_host:
                try:
                    self.redis_client = redis.Redis(
                        host=redis_host,
                        port=int(os.environ.get("REDIS_PORT", 6379)),
                        db=0,
                        decode_responses=True,
                    )
                    self.redis_client.ping()
                except Exception as e:
                    logger.warning(f"Failed to connect to Redis for valuation caching: {e}")
                    self.redis_client = None

        self.init_database()

    @property
    def conn(self) -> sqlite3.Connection:
        """Get per-thread database connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            try:
                self._local.conn.execute("PRAGMA journal_mode=WAL")
            except sqlite3.OperationalError:
                pass
            self._local.conn.execute("PRAGMA busy_timeout=5000")
        return self._local.conn

    def _invalidate_stats_cache(self) -> None:
        """Invalidate both local and Redis stats caches on write mutations."""
        self._stats_cache = None
        self._stats_cache_time = 0
        if getattr(self, "redis_client", None):
            try:
                self.redis_client.delete("valuation_stats")
            except Exception:
                pass

    def init_database(self) -> None:
        """Initialize database schema."""
        conn = self.conn
        c = conn.cursor()

        c.execute('''
        CREATE TABLE IF NOT EXISTS valuations (
            id TEXT PRIMARY KEY,
            image_filename TEXT,
            image_hash TEXT,
            item_name TEXT,
            brand TEXT,
            estimated_value REAL,
            condition_score INTEGER,
            profitability TEXT,
            worth_listing INTEGER,
            confidence REAL,
            valuation_data TEXT,
            status TEXT DEFAULT 'analyzed',
            upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS ebay_submissions (
            id TEXT PRIMARY KEY,
            valuation_id TEXT,
            submission_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ebay_listing_id TEXT,
            status TEXT,
            ebay_response TEXT,
            FOREIGN KEY (valuation_id) REFERENCES valuations (id)
        )
        ''')

        conn.commit()

    def save_valuation(self, image_filename: str, image_hash: str, valuation: ItemValuation) -> str:
        """Save a new valuation to database."""
        valuation_id = str(uuid.uuid4())

        conn = self.conn
        c = conn.cursor()

        c.execute('''
        INSERT INTO valuations (
            id, image_filename, image_hash, item_name, brand,
            estimated_value, condition_score, profitability,
            worth_listing, confidence, valuation_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            valuation_id,
            image_filename,
            image_hash,
            valuation.item_name,
            valuation.brand,
            valuation.estimated_value,
            valuation.condition_score,
            valuation.profitability.value if hasattr(valuation.profitability, "value") else valuation.profitability,
            valuation.worth_listing,
            valuation.confidence,
            json.dumps(valuation.to_dict()) if hasattr(valuation, "to_dict") else json.dumps(valuation),
        ))

        conn.commit()
        self._invalidate_stats_cache()
        return valuation_id

    def save_valuations(self, image_filename: str, image_hash: str, valuations: List[ItemValuation]) -> List[str]:
        """Save multiple valuations to database using bulk insert."""
        if not valuations:
            return []

        conn = self.conn
        c = conn.cursor()

        valuation_ids = [str(uuid.uuid4()) for _ in valuations]

        params = [
            (
                vid,
                image_filename,
                image_hash,
                v.item_name,
                v.brand,
                v.estimated_value,
                v.condition_score,
                v.profitability.value if hasattr(v.profitability, "value") else v.profitability,
                v.worth_listing,
                v.confidence,
                json.dumps(v.to_dict()) if hasattr(v, "to_dict") else json.dumps(v),
            )
            for vid, v in zip(valuation_ids, valuations)
        ]

        c.executemany('''
        INSERT INTO valuations (
            id, image_filename, image_hash, item_name, brand,
            estimated_value, condition_score, profitability,
            worth_listing, confidence, valuation_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', params)

        conn.commit()
        self._invalidate_stats_cache()
        return valuation_ids

    def get_valuation_by_id(self, valuation_id: str) -> Optional[Dict[str, Any]]:
        """Get a single valuation's JSON data by ID."""
        conn = self.conn
        c = conn.cursor()
        c.execute("SELECT valuation_data FROM valuations WHERE id = ?", (valuation_id,))
        row = c.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return None

    def get_recent_valuations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent valuations ordered by timestamp."""
        conn = self.conn
        c = conn.cursor()

        c.execute('''
        SELECT id, image_filename, upload_timestamp, item_name, brand,
               estimated_value, condition_score, profitability, worth_listing, status
        FROM valuations
        ORDER BY upload_timestamp DESC
        LIMIT ?
        ''', (limit,))

        rows = c.fetchall()

        return [
            {
                "id": row[0],
                "image_filename": row[1],
                "upload_timestamp": row[2],
                "timestamp": row[2],
                "item_name": row[3],
                "brand": row[4],
                "estimated_value": row[5],
                "condition_score": row[6],
                "profitability": row[7],
                "worth_listing": bool(row[8]),
                "status": row[9],
            }
            for row in rows
        ]

    def get_approved_valuations(self) -> List[Dict[str, Any]]:
        """Get valuations approved for eBay listing."""
        conn = self.conn
        c = conn.cursor()

        c.execute('''
        SELECT id, image_filename, upload_timestamp, item_name, brand,
               estimated_value, condition_score, profitability, status
        FROM valuations
        WHERE status IN ('approved', 'submitted', 'listed')
        ORDER BY upload_timestamp DESC
        ''')

        rows = c.fetchall()

        return [
            {
                "id": row[0],
                "image_filename": row[1],
                "upload_timestamp": row[2],
                "item_name": row[3],
                "brand": row[4],
                "estimated_value": row[5],
                "condition_score": row[6],
                "profitability": row[7],
                "status": row[8],
            }
            for row in rows
        ]

    def update_status(self, valuation_id: str, status: str) -> bool:
        """Update valuation status."""
        conn = self.conn
        c = conn.cursor()
        c.execute("UPDATE valuations SET status = ? WHERE id = ?", (status, valuation_id))
        success = c.rowcount > 0
        conn.commit()
        if success:
            self._invalidate_stats_cache()
        return success

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated valuation statistics with caching."""
        now = time.time()
        if self._stats_cache and (now - self._stats_cache_time) < self.cache_ttl:
            return self._stats_cache

        if self.redis_client:
            try:
                cached = self.redis_client.get("valuation_stats")
                if cached:
                    self._stats_cache = json.loads(cached)
                    self._stats_cache_time = now
                    return self._stats_cache
            except Exception:
                pass

        conn = self.conn
        c = conn.cursor()

        c.execute("SELECT COUNT(*) FROM valuations")
        total = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM valuations WHERE worth_listing = 1")
        worth_listing = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM valuations WHERE status = 'draft'")
        drafts = c.fetchone()[0]

        c.execute("SELECT AVG(estimated_value) FROM valuations WHERE estimated_value > 0")
        avg_value = c.fetchone()[0] or 0.0

        stats = {
            "total_valuations": total,
            "worth_listing": worth_listing,
            "drafts": drafts,
            "average_value": round(avg_value, 2),
        }

        self._stats_cache = stats
        self._stats_cache_time = now

        if self.redis_client:
            try:
                self.redis_client.setex("valuation_stats", self.cache_ttl, json.dumps(stats))
            except Exception:
                pass

        return stats

    def create_draft_listing(self, valuation_id: str, listing_data: Dict[str, Any]) -> str:
        """Create draft listing from valuation."""
        listing_id = str(uuid.uuid4())

        conn = self.conn
        c = conn.cursor()

        c.execute("UPDATE valuations SET status = ? WHERE id = ?", ("draft", valuation_id))
        c.execute(
            "UPDATE valuations SET valuation_data = ? WHERE id = ?",
            (json.dumps(listing_data), valuation_id),
        )

        conn.commit()
        self._invalidate_stats_cache()
        return listing_id

    def get_draft_listings(self) -> List[Dict[str, Any]]:
        """Get draft listings ready for eBay submission."""
        conn = self.conn
        c = conn.cursor()

        c.execute('''
        SELECT id, image_filename, item_name, estimated_value, valuation_data, upload_timestamp
        FROM valuations WHERE status = 'draft'
        ORDER BY upload_timestamp DESC
        ''')

        rows = c.fetchall()

        return [
            {
                "id": row[0],
                "image_filename": row[1],
                "item_name": row[2],
                "estimated_value": row[3],
                "listing_data": json.loads(row[4]) if row[4] else {},
                "upload_timestamp": row[5],
            }
            for row in rows
        ]

    def update_draft_listing(self, listing_id: str, update_data: Dict[str, Any]) -> bool:
        """Update draft listing with new data."""
        conn = self.conn
        c = conn.cursor()

        c.execute("SELECT valuation_data FROM valuations WHERE id = ?", (listing_id,))
        row = c.fetchone()

        if not row:
            return False

        current_data = json.loads(row[0]) if row[0] else {}
        current_data.update(update_data)

        c.execute(
            "UPDATE valuations SET valuation_data = ? WHERE id = ?",
            (json.dumps(current_data), listing_id),
        )

        success = c.rowcount > 0
        conn.commit()
        if success:
            self._invalidate_stats_cache()
        return success

    def delete_draft_listing(self, listing_id: str) -> bool:
        """Revert a draft listing back to analyzed or remove it."""
        conn = self.conn
        c = conn.cursor()
        c.execute("UPDATE valuations SET status = 'analyzed' WHERE id = ? AND status = 'draft'", (listing_id,))
        success = c.rowcount > 0
        conn.commit()
        if success:
            self._invalidate_stats_cache()
        return success
