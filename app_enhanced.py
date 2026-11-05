"""
Enhanced Flask App - End-to-End eBay Listing Assistant
Integrates all services: vision, valuation, conversation, listing synthesis, eBay API
"""

import asyncio
import base64
from datetime import datetime
from functools import wraps
import hmac
import json
import logging
import os
from pathlib import Path
import sqlite3
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

# Import services
from shared.models import ItemCondition, ItemValuation, ListingDraft, Profitability
from services.category_detail_generator import CategoryDetailGenerator
from services.conversation_orchestrator import ConversationOrchestrator
from services.draft_image_manager import DraftImageManager
from services.ebay_category_service import EBayCategoryService
from services.ebay_integration import eBayIntegration
from services.ebay_token_manager import EBayTokenManager
from services.listing_synthesis import ListingSynthesisEngine
from services.valuation_database import ValuationDatabase
from services.valuation_service import ValuationService
from services.vision_service import VisionService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DATA_DIR = os.getenv("DATA_DIR")
LISTINGS_DB_PATH = os.path.join(DATA_DIR, "listings.db") if DATA_DIR else "listings.db"
VALUATIONS_DB_PATH = os.path.join(DATA_DIR, "valuations.db") if DATA_DIR else "valuations.db"
DEFAULT_UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads") if DATA_DIR else "uploads"
DEFAULT_DRAFTS_FOLDER = os.path.join(DATA_DIR, "drafts") if DATA_DIR else "drafts"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise ValueError("SECRET_KEY environment variable must be set")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
app.config["UPLOAD_FOLDER"] = DEFAULT_UPLOAD_FOLDER

# Ensure folders exist
if "MagicMock" not in str(app.config.get("UPLOAD_FOLDER", "")):
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

# Initialize services
try:
    vision_service = VisionService()
    logger.info("Vision service initialized")
except Exception as e:
    logger.exception(f"Vision service failed: {e}")
    vision_service = None

# Initialize database and services
db = ValuationDatabase(db_path=VALUATIONS_DB_PATH)
valuation_service = ValuationService(use_sandbox=True)
category_service = EBayCategoryService()
category_generator = CategoryDetailGenerator()
draft_image_manager = DraftImageManager(drafts_folder=DEFAULT_DRAFTS_FOLDER)
logger.info("Database and services initialized")

conversation_orchestrator = None
listing_engine = None
ebay_integration = None

try:
    conversation_orchestrator = ConversationOrchestrator()
    listing_engine = ListingSynthesisEngine()
    ebay_integration = eBayIntegration(use_sandbox=True)
    logger.info("Other services initialized")
except Exception as e:
    logger.warning(f"Other services warning: {e}")


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = os.getenv("API_KEY")
        if not api_key:
            return jsonify({"error": "Server misconfiguration: API_KEY not set"}), 500

        request_key = request.headers.get("Authorization")
        if request_key and request_key.startswith("Bearer "):
            request_key = request_key.split("Bearer ", 1)[1]
        elif not request_key:
            request_key = request.headers.get("X-API-Key")

        if not request_key or not hmac.compare_digest(request_key, api_key):
            return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# DATABASE
# ============================================================================

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(LISTINGS_DB_PATH, check_same_thread=False)
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT,
        session_data TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        item_id TEXT PRIMARY KEY,
        session_id TEXT,
        image_filename TEXT,
        valuation_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

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
# API ROUTES
# ============================================================================

@app.route("/health", methods=["GET"])
def health_check():
    """Lightweight health check endpoint for CI and monitoring."""
    return jsonify({"status": "ok", "service": "ai-list-assist"}), 200


@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("dashboard.html")


@app.route("/simple")
def simple_interface():
    """Simple upload interface."""
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
@require_api_key
async def analyze_image():
    """Analyze image: detect items, value them, and determine if worth listing."""
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        raw_image_data = file.read()
        image_data, sanitized_mime = VisionService.sanitize_and_downscale_image(raw_image_data)
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        safe_filename = secure_filename(file.filename)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_filename}"
        filepath = Path(app.config["UPLOAD_FOLDER"]) / filename
        await asyncio.to_thread(filepath.write_bytes, image_data)

        session_id = str(uuid.uuid4())

        if not vision_service:
            return jsonify({"error": "Vision service not available"}), 500

        vision_used = False
        gemini_used = False
        usage_metadata = {}

        try:
            content_type = file.content_type or "image/jpeg"
            detected_items = await vision_service.detect_items_async(image_base64, content_type)

            vision_used = True
            usage_metadata = vision_service.get_usage_metadata()
            if usage_metadata:
                gemini_used = True
        except Exception:
            logger.exception("Vision service error")
            return jsonify({"error": "Vision service failed to process the image."}), 500

        valuations = []
        item_results = []
        for item in detected_items:
            try:
                valuation = await asyncio.to_thread(
                    valuation_service.evaluate_item,
                    image_base64,
                    content_type,
                    item.to_dict(),
                )
                valuations.append(valuation)
                item_results.append({
                    "item_id": valuation.item_id,
                    "item_name": valuation.item_name,
                    "estimated_value": valuation.estimated_value,
                    "worth_listing": valuation.worth_listing,
                    "profitability": valuation.profitability.value if hasattr(valuation.profitability, "value") else valuation.profitability,
                    "status": "success",
                })
            except Exception:
                logger.exception(f"Valuation error for item {item.item_id}")
                item_results.append({
                    "item_id": item.item_id,
                    "item_name": item.probable_category or item.brand or "Unknown Item",
                    "estimated_value": 0.0,
                    "worth_listing": False,
                    "profitability": "not_recommended",
                    "status": "failed",
                })

        worth_listing = [v for v in valuations if v.worth_listing]
        image_hash = str(hash(image_base64))
        valuation_ids = db.save_valuations(filename, image_hash, valuations)

        def save_session_to_db():
            conn = sqlite3.connect(LISTINGS_DB_PATH, check_same_thread=False)
            c = conn.cursor()
            c.execute(
                "INSERT INTO sessions (session_id, status, session_data) VALUES (?, ?, ?)",
                (
                    session_id,
                    "analyzed",
                    json.dumps({
                        "detected_items": [item.to_dict() for item in detected_items],
                        "valuations": [v.to_dict() for v in valuations],
                        "valuation_ids": valuation_ids,
                        "image_filename": filename,
                    }),
                ),
            )
            conn.commit()
            conn.close()

        await asyncio.to_thread(save_session_to_db)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "detected_items": len(detected_items),
            "worth_listing": len(worth_listing),
            "vision_used": vision_used,
            "gemini_used": gemini_used,
            "usage_metadata": usage_metadata,
            "items": item_results,
            "image_url": f"/uploads/{filename}",
        })

    except Exception:
        logger.exception("Error processing image")
        return jsonify({"error": "An internal error occurred while processing the image."}), 500


@app.route("/api/conversation/start", methods=["POST"])
@require_api_key
def start_conversation():
    """Start conversation for gathering listing details."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    item_id = data.get("item_id")
    initial_data = data.get("initial_data", {})

    if not item_id:
        return jsonify({"error": "item_id required"}), 400

    try:
        state = conversation_orchestrator.start_conversation(item_id, initial_data)
        return jsonify({
            "success": True,
            "session_id": state.session_id,
            "question": state.current_question,
            "confidence": state.confidence,
            "is_complete": state.is_complete,
        })
    except Exception:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route("/api/conversation/answer", methods=["POST"])
@require_api_key
def answer_question():
    """Process user's answer and get next question."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    session_id = data.get("session_id")
    answer = data.get("answer")

    if not session_id or not answer:
        return jsonify({"error": "session_id and answer required"}), 400

    try:
        state = conversation_orchestrator.process_answer(session_id, answer)
        return jsonify({
            "success": True,
            "question": state.current_question,
            "confidence": state.confidence,
            "is_complete": state.is_complete,
            "known_fields": state.known_fields,
        })
    except Exception:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route("/api/listing/create", methods=["POST"])
@require_api_key
def create_listing():
    """Create listing draft from conversation data."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    item_id = data.get("item_id")
    session_id = data.get("session_id")

    if not item_id or not session_id:
        return jsonify({"error": "item_id and session_id required"}), 400

    try:
        conv_state = conversation_orchestrator.get_state(session_id)
        if not conv_state:
            return jsonify({"error": "Conversation session not found"}), 404

        conn = sqlite3.connect(LISTINGS_DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT session_data FROM sessions WHERE session_id = ?", (session_id,))
        session_row = c.fetchone()
        conn.close()

        original_images = []
        if session_row:
            session_data = json.loads(session_row[0])
            image_filename = session_data.get("image_filename")
            if image_filename:
                original_images = [os.path.join(app.config["UPLOAD_FOLDER"], image_filename)]

        valuation = ItemValuation(
            item_id=item_id,
            item_name=conv_state.known_fields.get("item_name", "Item"),
            brand=conv_state.known_fields.get("brand"),
            estimated_age=None,
            condition_score=7,
            condition_notes="",
            is_complete=conv_state.known_fields.get("is_complete", True),
            estimated_value=float(conv_state.known_fields.get("price", 0.0) or 0.0),
            value_range={"low": 0, "high": 0},
            resale_score=7,
            profitability=Profitability.MEDIUM,
            recommended_platforms=["eBay"],
            key_factors=[],
            risks=[],
            listing_tips=[],
            worth_listing=True,
            confidence=conv_state.confidence,
        )

        listing_draft = listing_engine.create_listing_draft(
            item_id=item_id,
            valuation=valuation,
            conversation_state=conv_state,
            images=original_images,
        )

        if original_images:
            draft_images = draft_image_manager.save_draft_images(
                listing_draft.listing_id,
                original_images,
            )
            listing_draft.images = draft_images

        conn = sqlite3.connect(LISTINGS_DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            """INSERT INTO listings (listing_id, item_id, title, price, status, draft_data)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                listing_draft.listing_id,
                item_id,
                listing_draft.title,
                listing_draft.price,
                "draft",
                json.dumps(listing_draft.to_dict()),
            ),
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True, "listing": listing_draft.to_dict()})

    except Exception:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route("/api/listing/publish", methods=["POST"])
@require_api_key
def publish_listing():
    """Publish listing to eBay."""
    if not ebay_integration:
        return jsonify({"error": "eBay integration not initialized"}), 500

    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    listing_id = data.get("listing_id")
    if not listing_id:
        return jsonify({"error": "listing_id required"}), 400

    try:
        conn = sqlite3.connect(LISTINGS_DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute("SELECT draft_data FROM listings WHERE listing_id = ?", (listing_id,))
        row = c.fetchone()
        conn.close()

        if not row or not row[0]:
            return jsonify({"error": "Listing not found"}), 404

        draft_dict = json.loads(row[0])
        draft = ListingDraft.model_validate(draft_dict)

        sku = draft.listing_id
        ebay_integration.create_inventory_item(draft, sku=sku)
        offer = ebay_integration.create_offer(sku, draft)
        offer_id = offer.get("offerId")
        if offer_id:
            result = ebay_integration.publish_offer(offer_id)
        else:
            result = offer

        conn = sqlite3.connect(LISTINGS_DB_PATH, check_same_thread=False)
        c = conn.cursor()
        c.execute(
            "UPDATE listings SET status = ?, ebay_listing_id = ? WHERE listing_id = ?",
            ("published", result.get("listingId") or offer_id, listing_id),
        )
        conn.commit()
        conn.close()

        return jsonify({"success": True, "result": result})

    except Exception:
        logger.exception("Publish error")
        return jsonify({"error": "Failed to publish listing."}), 500


@app.route("/api/stats", methods=["GET"])
@require_api_key
def get_stats():
    """Return valuation statistics."""
    return jsonify({"success": True, "stats": db.get_stats()})


@app.route("/api/pricing/preview", methods=["POST"])
@require_api_key
def pricing_preview():
    """Preview smart pricing and net profit."""
    data = request.json or {}
    estimated_value = float(data.get("estimated_value") or 0.0)
    shipping_cost = float(data.get("shipping_cost") or 0.0)
    cogs = float(data.get("cogs") or 0.0)

    from shared.schemas.pricing_strategy import calculate_net_profit, calculate_smart_price
    smart = calculate_smart_price(estimated_value)
    sale_price = float(data.get("sale_price") or smart.list_price or estimated_value)
    profit = calculate_net_profit(sale_price, shipping_cost=shipping_cost, cogs=cogs)

    return jsonify({
        "success": True,
        "smart_pricing": {
            "list_price": smart.list_price,
            "auto_accept_price": smart.auto_accept_price,
            "minimum_price": smart.minimum_price,
            "format": smart.format,
        },
        "profit_breakdown": profit.to_dict(),
    })


@app.route("/api/ebay/policies", methods=["GET"])
@require_api_key
def get_ebay_business_policies():
    """Get configured or Account API business policies for eBay Offer creation."""
    if not ebay_integration:
        return jsonify({"error": "eBay integration not initialized"}), 500
    marketplace_id = request.args.get("marketplace_id", "EBAY_US")
    policies = ebay_integration._get_business_policies()
    return jsonify({"success": True, "marketplace_id": marketplace_id, "policies": policies})


@app.route("/uploads/<filename>")
def download_file(filename):
    """Serve uploaded images."""
    from flask import send_from_directory
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    )
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    init_db()
    logger.info("Database initialized")
    logger.info("Starting Enhanced eBay Listing Assistant")
    logger.info("Visit: http://localhost:5000")
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "t"),
        host="0.0.0.0",
        port=5000,
    )
