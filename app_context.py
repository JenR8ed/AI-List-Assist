import os
import sqlite3
import logging
from pathlib import Path
from dotenv import load_dotenv

from services.vision_service import VisionService
from services.conversation_orchestrator import ConversationOrchestrator
from services.listing_synthesis import ListingSynthesisEngine
from services.ebay_integration import eBayIntegration
from services.valuation_database import ValuationDatabase
from services.valuation_service import ValuationService
from services.ebay_category_service import EBayCategoryService
from services.draft_image_manager import DraftImageManager
from services.category_detail_generator import CategoryDetailGenerator

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services (lazy or eager)
db = ValuationDatabase()
valuation_service = ValuationService(use_sandbox=True)
category_service = EBayCategoryService()
category_generator = CategoryDetailGenerator()
draft_image_manager = DraftImageManager()

try:
    vision_service = VisionService()
except Exception as e:
    logger.error(f"Vision service failed: {e}")
    vision_service = None

try:
    conversation_orchestrator = ConversationOrchestrator()
    listing_engine = ListingSynthesisEngine()
    ebay_integration = eBayIntegration(use_sandbox=True)
except Exception as e:
    logger.error(f"Other services warning: {e}")
    conversation_orchestrator = None
    listing_engine = None
    ebay_integration = None

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
