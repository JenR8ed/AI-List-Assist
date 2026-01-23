"""
Database service for tracking valuations and eBay submissions
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from shared.models import ItemValuation

class ValuationDatabase:
    """Database service for tracking all valuations and eBay submissions."""
    
    def __init__(self, db_path: str = "valuations.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Valuations table - tracks all image analyses
        c.execute('''
        CREATE TABLE IF NOT EXISTS valuations (
            id TEXT PRIMARY KEY,
            image_filename TEXT NOT NULL,
            image_hash TEXT NOT NULL,
            upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            item_name TEXT,
            brand TEXT,
            estimated_value REAL,
            condition_score INTEGER,
            profitability TEXT,
            worth_listing BOOLEAN,
            confidence REAL,
            valuation_data TEXT,  -- Full JSON of ItemValuation
            status TEXT DEFAULT 'analyzed'  -- analyzed, approved, submitted, listed
        )
        ''')
        
        # eBay submissions table - tracks listings sent to eBay
        c.execute('''
        CREATE TABLE IF NOT EXISTS ebay_submissions (
            id TEXT PRIMARY KEY,
            valuation_id TEXT,
            ebay_listing_id TEXT,
            submission_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            listing_title TEXT,
            listing_price REAL,
            listing_status TEXT,  -- draft, active, sold, ended
            ebay_response TEXT,   -- JSON response from eBay API
            FOREIGN KEY (valuation_id) REFERENCES valuations (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_valuation(self, image_filename: str, image_hash: str, valuation: ItemValuation) -> str:
        """Save a new valuation to database."""
        valuation_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
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
            valuation.profitability.value,
            valuation.worth_listing,
            valuation.confidence,
            json.dumps(valuation.to_dict())
        ))
        
        conn.commit()
        conn.close()
        
        return valuation_id
    
    def get_recent_valuations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent valuations ordered by timestamp."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        SELECT id, image_filename, upload_timestamp, item_name, brand,
               estimated_value, condition_score, profitability, worth_listing, status
        FROM valuations 
        ORDER BY upload_timestamp DESC 
        LIMIT ?
        ''', (limit,))
        
        rows = c.fetchall()
        conn.close()
        
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
                "worth_listing": bool(row[8]),
                "status": row[9]
            }
            for row in rows
        ]
    
    def get_approved_valuations(self) -> List[Dict[str, Any]]:
        """Get valuations approved for eBay listing."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        SELECT id, image_filename, upload_timestamp, item_name, brand,
               estimated_value, condition_score, profitability, status
        FROM valuations 
        WHERE status IN ('approved', 'submitted', 'listed')
        ORDER BY upload_timestamp DESC
        ''')
        
        rows = c.fetchall()
        conn.close()
        
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
                "status": row[8]
            }
            for row in rows
        ]
    
    def approve_valuation(self, valuation_id: str) -> bool:
        """Mark valuation as approved for eBay listing."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        UPDATE valuations 
        SET status = 'approved' 
        WHERE id = ?
        ''', (valuation_id,))
        
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def submit_to_ebay(self, valuation_id: str, ebay_listing_id: str, 
                      listing_title: str, listing_price: float, 
                      ebay_response: Dict[str, Any]) -> str:
        """Record eBay submission."""
        submission_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Update valuation status
        c.execute('''
        UPDATE valuations 
        SET status = 'submitted' 
        WHERE id = ?
        ''', (valuation_id,))
        
        # Record eBay submission
        c.execute('''
        INSERT INTO ebay_submissions (
            id, valuation_id, ebay_listing_id, listing_title, 
            listing_price, listing_status, ebay_response
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission_id,
            valuation_id,
            ebay_listing_id,
            listing_title,
            listing_price,
            'active',
            json.dumps(ebay_response)
        ))
        
        conn.commit()
        conn.close()
        
        return submission_id
    
    def get_ebay_submissions(self) -> List[Dict[str, Any]]:
        """Get all eBay submissions with valuation data."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        SELECT e.id, e.ebay_listing_id, e.submission_timestamp, 
               e.listing_title, e.listing_price, e.listing_status,
               v.item_name, v.image_filename, v.estimated_value
        FROM ebay_submissions e
        JOIN valuations v ON e.valuation_id = v.id
        ORDER BY e.submission_timestamp DESC
        ''')
        
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                "submission_id": row[0],
                "ebay_listing_id": row[1],
                "submission_timestamp": row[2],
                "listing_title": row[3],
                "listing_price": row[4],
                "listing_status": row[5],
                "item_name": row[6],
                "image_filename": row[7],
                "estimated_value": row[8]
            }
            for row in rows
        ]
    
    def get_valuation_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Total valuations
        c.execute('SELECT COUNT(*) FROM valuations')
        total_valuations = c.fetchone()[0]
        
        # Worth listing count
        c.execute('SELECT COUNT(*) FROM valuations WHERE worth_listing = 1')
        worth_listing = c.fetchone()[0]
        
        # Average value
        c.execute('SELECT AVG(estimated_value) FROM valuations WHERE estimated_value > 0')
        avg_value = c.fetchone()[0] or 0
        
        # Approved count
        c.execute('SELECT COUNT(*) FROM valuations WHERE status IN ("approved", "submitted", "listed")')
        approved_count = c.fetchone()[0]
        
        # eBay submissions
        c.execute('SELECT COUNT(*) FROM ebay_submissions')
        ebay_submissions = c.fetchone()[0]
        
        conn.close()
        
        return {
            "total_valuations": total_valuations,
            "worth_listing": worth_listing,
            "average_value": round(avg_value, 2),
            "approved_count": approved_count,
            "ebay_submissions": ebay_submissions,
            "approval_rate": round((approved_count / total_valuations * 100) if total_valuations > 0 else 0, 1)
        }
    
    def create_draft_listing(self, valuation_id: str, listing_data: Dict[str, Any]) -> str:
        """Create draft listing from valuation."""
        listing_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Update valuation status
        c.execute('UPDATE valuations SET status = ? WHERE id = ?', ('draft', valuation_id))
        
        # Store listing data in valuation_data field
        c.execute('UPDATE valuations SET valuation_data = ? WHERE id = ?', 
                  (json.dumps(listing_data), valuation_id))
        
        conn.commit()
        conn.close()
        return listing_id
    
    def get_draft_listings(self) -> List[Dict[str, Any]]:
        """Get draft listings ready for eBay submission."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        SELECT id, image_filename, item_name, estimated_value, valuation_data, upload_timestamp
        FROM valuations WHERE status = 'draft'
        ORDER BY upload_timestamp DESC
        ''')
        
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0], 
                "image_filename": row[1], 
                "item_name": row[2], 
                "estimated_value": row[3], 
                "listing_data": json.loads(row[4]) if row[4] else {},
                "upload_timestamp": row[5]
            } 
            for row in rows
        ]
    
    def update_draft_listing(self, listing_id: str, update_data: Dict[str, Any]) -> bool:
        """Update draft listing with new data."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get current listing data
        c.execute('SELECT valuation_data FROM valuations WHERE id = ?', (listing_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return False
        
        # Merge update data with existing data
        current_data = json.loads(row[0]) if row[0] else {}
        current_data.update(update_data)
        
        # Update the record
        c.execute('UPDATE valuations SET valuation_data = ? WHERE id = ?', 
                  (json.dumps(current_data), listing_id))
        
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        
        return success