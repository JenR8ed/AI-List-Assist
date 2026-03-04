"""
Enhanced Flask App - End-to-End eBay Listing Assistant
Integrates all services: vision, valuation, conversation, listing synthesis, eBay API
"""

from flask import Flask
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable must be set")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure folders exist, skip during test discovery where config is mocked
if not getattr(app.config.get('UPLOAD_FOLDER', ''), '__class__', None).__name__ == 'MagicMock':
    try:
        Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create upload folder: {e}")

# Import dependencies initialized in extensions.py
from extensions import db

# Register Blueprints
from routes import (
    ui_bp,
    analysis_bp,
    listings_bp,
    ebay_bp,
    conversation_bp,
    categories_bp
)

app.register_blueprint(ui_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(listings_bp)
app.register_blueprint(ebay_bp)
app.register_blueprint(conversation_bp)
app.register_blueprint(categories_bp)

# ============================================================================
# DATABASE
# ============================================================================

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect('listings.db')
    c = conn.cursor()

    # Sessions table
    c.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT,
        session_data TEXT
    )
    ''')

    # Items table
    c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        item_id TEXT PRIMARY KEY,
        session_id TEXT,
        image_filename TEXT,
        valuation_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Listings table
    c.execute('''
    CREATE TABLE IF NOT EXISTS listings (
        listing_id TEXT PRIMARY KEY,
        item_id TEXT,
        title TEXT,
        price REAL,
        status TEXT,
        ebay_listing_id TEXT,
        draft_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == '__main__':
    init_db()
    print("Database initialized")
    print("Starting Enhanced eBay Listing Assistant")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
