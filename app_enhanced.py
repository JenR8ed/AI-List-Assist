"""
Enhanced Flask App - End-to-End eBay Listing Assistant
Integrates all services: vision, valuation, conversation, listing synthesis, eBay API
"""

from flask import Flask, abort, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import base64
import json
import os
import logging
import hmac
import ipaddress
import secrets
from urllib.parse import urlsplit
from datetime import datetime
from pathlib import Path
from contextlib import closing
from dotenv import load_dotenv
import sqlite3
import uuid
import asyncio

# Import services
from shared.models import ListingDraft, ItemCondition
from services.vision_service import VisionService
from services.conversation_orchestrator import ConversationOrchestrator
from services.listing_synthesis import ListingSynthesisEngine
from services.ebay_integration import eBayIntegration
from services.valuation_database import ValuationDatabase
from services.valuation_service import ValuationService
from services.ebay_category_service import EBayCategoryService
from services.draft_image_manager import DraftImageManager
from services.category_detail_generator import CategoryDetailGenerator
from services.draft_review import validate_draft

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['LOCAL_DRAFT_MODE'] = os.getenv('LOCAL_DRAFT_MODE') == '1'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or (
    secrets.token_hex(32) if app.config['LOCAL_DRAFT_MODE'] else None
)
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable must be set")
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.config['SESSION_COOKIE_SECURE'] = not app.config['LOCAL_DRAFT_MODE']
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure folders exist
if 'MagicMock' not in str(app.config.get('UPLOAD_FOLDER', '')):
    Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

# Initialize services
try:
    vision_service = VisionService()
    logger.info("Vision service initialized")
except Exception as e:
    logger.exception(f"Vision service failed: {e}")
    vision_service = None

# Initialize database and services
db = ValuationDatabase()
valuation_service = ValuationService(use_sandbox=True)
category_service = EBayCategoryService()
category_generator = CategoryDetailGenerator()
draft_image_manager = DraftImageManager()
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


from functools import wraps

def _is_local_request():
    """Local mode is for a direct loopback browser, never a public host."""
    try:
        address = ipaddress.ip_address(request.remote_addr)
        hostname = urlsplit(f"http://{request.host}").hostname
        return address.is_loopback and hostname in ('localhost', '127.0.0.1', '::1')
    except ValueError:
        return False


def _render_local_ui(template):
    csrf_token = ''
    if app.config['LOCAL_DRAFT_MODE']:
        if not _is_local_request():
            abort(403)
        session['local_ui'] = True
        csrf_token = session.setdefault('csrf_token', secrets.token_urlsafe(32))
    return render_template(template, csrf_token=csrf_token)


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if app.config['LOCAL_DRAFT_MODE']:
            # No local UI request or server-to-server key can publish in draft mode.
            if request.path.startswith('/api/ebay/'):
                return jsonify({"error": "Marketplace integration disabled in local draft mode"}), 503
            if session.get('local_ui') and _is_local_request():
                if request.method not in ('GET', 'HEAD', 'OPTIONS'):
                    supplied = request.headers.get('X-CSRF-Token', '')
                    if not supplied or not hmac.compare_digest(supplied, session.get('csrf_token', '')):
                        return jsonify({"error": "Invalid CSRF token"}), 403
                return app.ensure_sync(f)(*args, **kwargs)

        api_key = os.getenv('API_KEY')
        if not api_key:
            if app.config['LOCAL_DRAFT_MODE']:
                return jsonify({"error": "Unauthorized"}), 401
            return jsonify({"error": "Server misconfiguration: API_KEY not set"}), 500

        request_key = request.headers.get('Authorization')
        if request_key and request_key.startswith('Bearer '):
            request_key = request_key.split('Bearer ')[1]

        if not request_key or not hmac.compare_digest(request_key, api_key):
            return jsonify({"error": "Unauthorized"}), 401

        return app.ensure_sync(f)(*args, **kwargs)
    return decorated_function

# ============================================================================
# DATABASE
# ============================================================================

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect('listings.db', check_same_thread=False)
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
# API ROUTES
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Lightweight health check endpoint for CI and monitoring."""
    return jsonify({'status': 'ok', 'service': 'ai-list-assist'}), 200


@app.route('/')
def index():
    """Main dashboard page."""
    return _render_local_ui('dashboard.html')

@app.route('/simple')
def simple_interface():
    """Simple upload interface."""
    return _render_local_ui('index.html')

@app.route('/api/analyze', methods=['POST'])
@require_api_key
async def analyze_image():
    """
    Analyze image: detect items, value them, and determine if worth listing.
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Read and encode image
        image_data = file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Sanitize and save uploaded file
        safe_filename = secure_filename(file.filename)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_filename}"
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        await asyncio.to_thread(filepath.write_bytes, image_data)

        # Create session
        session_id = str(uuid.uuid4())

        # Step 1: Detect items
        logger.debug(f"DEBUG: Processing image, size: {len(image_base64)} chars, content_type: {file.content_type}")
        if not vision_service:
            return jsonify({"error": "Vision service not available"}), 500

        vision_used = False
        gemini_used = False
        usage_metadata = {}

        try:
            content_type = file.content_type or 'image/jpeg'  # Default if None
            detected_items = await vision_service.detect_items_async(image_base64, content_type)

            # Check which APIs were used
            vision_used = True  # Cloud Vision always tried first
            usage_metadata = vision_service.get_usage_metadata()
            if usage_metadata:  # If we have Gemini usage data, it was used
                gemini_used = True

            logger.debug(f"DEBUG: Detected {len(detected_items)} items")
            for i, item in enumerate(detected_items):
                logger.debug(f"DEBUG: Item {i}: brand={item.brand}, category={item.probable_category}, text={item.detected_text}")
        except Exception as vision_error:
            logger.exception("Vision service error")
            return jsonify({"error": "Vision service failed to process the image."}), 500

        # Step 2: Value each item
        valuations = []
        item_results = []
        for item in detected_items:
            try:
                content_type = file.content_type or 'image/jpeg'  # Default if None
                valuation = await asyncio.to_thread(
                    valuation_service.evaluate_item,
                    image_base64,
                    content_type,
                    item.to_dict()
                )
                valuations.append(valuation)
                item_results.append({
                    "item_id": valuation.item_id,
                    "item_name": valuation.item_name,
                    "estimated_value": valuation.estimated_value,
                    "worth_listing": valuation.worth_listing,
                    "profitability": valuation.profitability.value,
                    "status": valuation.status,
                    "source": valuation.source
                })
                logger.info(f"Valued item {item.item_id}: {valuation.item_name}")
            except Exception as val_error:
                logger.exception(f"Valuation error for item {item.item_id}")
                # Collect failed items for the frontend
                item_results.append({
                    "item_id": item.item_id,
                    "item_name": item.probable_category or item.brand or "Unknown Item",
                    "estimated_value": None,
                    "worth_listing": False,
                    "profitability": "not_recommended",
                    "status": "unavailable",
                    "source": "simulated",
                    **item.to_dict()
                })

        # Step 3: Filter items worth listing
        worth_listing = [v for v in valuations if v.worth_listing]

        # Save valuations to database
        image_hash = str(hash(image_base64))
        valuation_ids = db.save_valuations(filename, image_hash, valuations)
        for val, v_id in zip(valuations, valuation_ids):
            logger.info(f"Saved valuation {v_id} for {val.item_name}")

        # Save to database
        def save_session_to_db():
            conn = sqlite3.connect('listings.db', check_same_thread=False)
            c = conn.cursor()
            c.execute('''
                INSERT INTO sessions (session_id, status, session_data)
                VALUES (?, ?, ?)
            ''', (session_id, "analyzed", json.dumps({
                "detected_items": [item.to_dict() for item in detected_items],
                "valuations": [v.to_dict() for v in valuations],
                "image_filename": filename
            })))
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
            "image_url": f"/uploads/{filename}"
        })

    except Exception as e:
        logger.exception("Error processing image")
        return jsonify({"error": "An internal error occurred while processing the image."}), 500

@app.route('/api/conversation/start', methods=['POST'])
@require_api_key
def start_conversation():
    """Start conversation for gathering listing details."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    item_id = data.get('item_id')
    initial_data = data.get('initial_data', {})

    if not item_id:
        return jsonify({"error": "item_id required"}), 400

    try:
        state = conversation_orchestrator.start_conversation(item_id, initial_data)
        return jsonify({
            "success": True,
            "session_id": state.session_id,
            "question": state.current_question,
            "confidence": state.confidence,
            "is_complete": state.is_complete
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/conversation/answer', methods=['POST'])
@require_api_key
def answer_question():
    """Process user's answer and get next question."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    session_id = data.get('session_id')
    answer = data.get('answer')

    if not session_id or not answer:
        return jsonify({"error": "session_id and answer required"}), 400

    try:
        state = conversation_orchestrator.process_answer(session_id, answer)
        return jsonify({
            "success": True,
            "question": state.current_question,
            "confidence": state.confidence,
            "is_complete": state.is_complete,
            "known_fields": state.known_fields
        })
    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/listing/create', methods=['POST'])
@require_api_key
def create_listing():
    """Create listing draft from conversation data."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    item_id = data.get('item_id')
    session_id = data.get('session_id')

    if not item_id or not session_id:
        return jsonify({"error": "item_id and session_id required"}), 400

    try:
        # Get conversation state
        conv_state = conversation_orchestrator.get_state(session_id)
        if not conv_state:
            return jsonify({"error": "Conversation session not found"}), 404

        # Get original image path from session
        conn = sqlite3.connect('listings.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT session_data FROM sessions WHERE session_id = ?', (session_id,))
        session_row = c.fetchone()
        conn.close()

        original_images = []
        if session_row:
            session_data = json.loads(session_row[0])
            image_filename = session_data.get('image_filename')
            if image_filename:
                original_images = [os.path.join(app.config['UPLOAD_FOLDER'], image_filename)]

        # Get valuation (would fetch from DB in production)
        # For now, create a basic valuation
        from shared.models import ItemValuation, Profitability
        valuation = ItemValuation(
            item_id=item_id,
            item_name=conv_state.known_fields.get("item_name", "Item"),
            brand=conv_state.known_fields.get("brand"),
            estimated_age=None,
            condition_score=7,
            condition_notes="",
            is_complete=conv_state.known_fields.get("is_complete", True),
            estimated_value=conv_state.known_fields.get("price"),
            value_range={"low": 0, "high": 0},
            resale_score=7,
            profitability=Profitability.MEDIUM,
            recommended_platforms=["eBay"],
            key_factors=[],
            risks=[],
            listing_tips=[],
            worth_listing=True,
            confidence=conv_state.confidence,
            source="simulated",
            status="available" if conv_state.known_fields.get("price") is not None else "unavailable"
        )

        # Create listing draft
        listing_draft = listing_engine.create_listing_draft(
            item_id=item_id,
            valuation=valuation,
            conversation_state=conv_state,
            images=original_images
        )

        # Save images to draft storage
        if original_images:
            draft_images = draft_image_manager.save_draft_images(
                listing_draft.listing_id,
                original_images
            )
            listing_draft.images = draft_images

        # Save to database
        conn = sqlite3.connect('listings.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''
            INSERT INTO listings (listing_id, item_id, title, price, status, draft_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            listing_draft.listing_id,
            item_id,
            listing_draft.title,
            listing_draft.price,
            "draft",
            json.dumps(listing_draft.to_dict())
        ))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "listing": listing_draft.to_dict(),
            "source": listing_draft.source
        })

    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

def _stored_listing(listing_id):
    with closing(sqlite3.connect('listings.db', check_same_thread=False)) as conn:
        row = conn.execute('SELECT status, draft_data FROM listings WHERE listing_id = ?', (listing_id,)).fetchone()
    return (row[0], json.loads(row[1])) if row and row[1] else None


@app.route('/api/listing/<listing_id>/validate', methods=['GET'])
@require_api_key
def validate_listing(listing_id):
    """Validate local review fields without approving or publishing."""
    stored = _stored_listing(listing_id)
    if not stored:
        return jsonify({"error": "Listing draft not found"}), 404
    status, draft = stored
    errors = validate_draft(draft)
    return jsonify({"listing_id": listing_id, "status": status, "valid": not errors, "errors": errors,
                    "source": draft.get('source', 'simulated')})


@app.route('/api/listing/<listing_id>/approve', methods=['POST'])
@require_api_key
def approve_listing(listing_id):
    """Record human approval only after the stored draft passes validation."""
    with closing(sqlite3.connect('listings.db', check_same_thread=False)) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT status, draft_data FROM listings WHERE listing_id = ?', (listing_id,)).fetchone()
        if not row or not row[1]:
            return jsonify({"error": "Listing draft not found"}), 404
        if row[0] not in ('draft', 'approved'):
            return jsonify({"error": "Listing is not a draft"}), 409
        errors = validate_draft(json.loads(row[1]))
        if errors:
            return jsonify({"error": "Draft incomplete", "errors": errors}), 422
        conn.execute("UPDATE listings SET status = 'approved' WHERE listing_id = ?", (listing_id,))
    return jsonify({"listing_id": listing_id, "status": "approved",
                    "source": json.loads(row[1]).get('source', 'simulated')})


@app.route('/api/listing/<listing_id>', methods=['PUT'])
@require_api_key
def edit_listing(listing_id):
    """Save review edits and revoke any previous approval."""
    changes = request.get_json(silent=True)
    editable = {'title', 'description', 'category_id', 'condition', 'price', 'item_specifics', 'images'}
    if not isinstance(changes, dict) or not changes or set(changes) - editable:
        return jsonify({"error": "Provide only editable draft fields"}), 400
    if any(not isinstance(changes[key], str) for key in changes.keys() &
           {'title', 'description', 'category_id', 'condition'}):
        return jsonify({"error": "Text draft fields must be strings"}), 400
    if 'price' in changes and (isinstance(changes['price'], bool) or
                               not isinstance(changes['price'], (int, float))):
        return jsonify({"error": "price must be a number"}), 400
    if ('item_specifics' in changes and not isinstance(changes['item_specifics'], dict) or
            'images' in changes and not isinstance(changes['images'], list)):
        return jsonify({"error": "Invalid draft field type"}), 400
    with closing(sqlite3.connect('listings.db', check_same_thread=False)) as conn, conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT status, draft_data FROM listings WHERE listing_id = ?', (listing_id,)).fetchone()
        if not row or not row[1]:
            return jsonify({"error": "Listing draft not found"}), 404
        if row[0] not in ('draft', 'approved'):
            return jsonify({"error": "Listing is not editable"}), 409
        draft = json.loads(row[1])
        draft.update(changes)
        conn.execute('UPDATE listings SET draft_data = ?, title = ?, price = ?, status = ? WHERE listing_id = ?',
                     (json.dumps(draft), draft.get('title'), draft.get('price'), 'draft', listing_id))
    return jsonify({"listing_id": listing_id, "status": "draft", "listing": draft,
                    "source": draft.get('source', 'simulated')})


@app.route('/api/listing/publish', methods=['POST'])
@require_api_key
def publish_listing():
    """Reject unapproved drafts; publishing remains disabled even after approval."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('listing_id'), str) or not data['listing_id']:
        return jsonify({"error": "listing_id required"}), 400
    stored = _stored_listing(data['listing_id'])
    if not stored:
        return jsonify({"error": "Listing draft not found"}), 404
    status, draft = stored
    errors = validate_draft(draft)
    if errors or status != 'approved':
        return jsonify({"error": "Draft must be complete and approved", "errors": errors,
                        "source": draft.get('source', 'simulated')}), 409
    return jsonify({"error": "Publishing is disabled in this slice", "code": "FEATURE_DISABLED",
                    "source": draft.get('source', 'simulated')}), 503

@app.route('/api/ebay/oauth/url', methods=['GET'])
@require_api_key
def get_ebay_oauth_url():
    """Get eBay OAuth authorization URL."""
    if not ebay_integration:
        return jsonify({"error": "eBay integration not initialized"}), 500

    redirect_uri = os.getenv('EBAY_RU_NAME', 'http://localhost:5000/api/ebay/oauth/callback')

    try:
        oauth_url = ebay_integration.get_oauth_url(redirect_uri)
        return jsonify({
            "success": True,
            "oauth_url": oauth_url
        })
    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/valuations/recent', methods=['GET'])
@require_api_key
def get_recent_valuations():
    """Get recent valuations."""
    limit = request.args.get('limit', 20, type=int)

    try:
        valuations = db.get_recent_valuations(limit)
        return jsonify({
            "success": True,
            "valuations": valuations,
            "source": valuations[0].get('source', 'simulated') if valuations and
                      all(v.get('source') == valuations[0].get('source') for v in valuations) else 'simulated'
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/valuations/approved', methods=['GET'])
@require_api_key
def get_approved_valuations():
    """Get approved valuations ready for eBay."""
    try:
        valuations = db.get_approved_valuations()
        return jsonify({
            "success": True,
            "approved_valuations": valuations,
            "source": valuations[0].get('source', 'simulated') if valuations and
                      all(v.get('source') == valuations[0].get('source') for v in valuations) else 'simulated'
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/valuations/<valuation_id>/approve', methods=['POST'])
@require_api_key
def approve_valuation(valuation_id):
    """Approve a valuation for eBay listing."""
    try:
        success = db.approve_valuation(valuation_id)
        if success:
            return jsonify({"success": True, "message": "Valuation approved", "source": "simulated"})
        else:
            return jsonify({"error": "Valuation not found"}), 404
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/stats', methods=['GET'])
@require_api_key
def get_stats():
    try:
        stats = ValuationDatabase().get_valuation_stats()
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/valuations/<valuation_id>', methods=['GET'])
@require_api_key
def get_valuation(valuation_id):
    """Get a specific valuation by ID."""
    try:
        conn = sqlite3.connect('valuations.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('SELECT valuation_data FROM valuations WHERE id = ?', (valuation_id,))
        row = c.fetchone()
        conn.close()

        if row:
            valuation_data = json.loads(row[0])
            valuation_data.setdefault('source', 'simulated')
            valuation_data.setdefault('status', 'available')
            return jsonify({
                "success": True,
                "valuation": valuation_data,
                "source": valuation_data.get('source', 'simulated')
            })
        else:
            return jsonify({"error": "Valuation not found"}), 404
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/category/<category_id>/aspects', methods=['GET'])
@require_api_key
def get_category_aspects(category_id):
    """Get eBay category-specific aspects."""
    try:
        aspects = category_service.get_category_aspects(category_id)
        return jsonify({
            "success": True,
            "category_id": category_id,
            "aspects": aspects,
            "source": aspects.get('source', 'simulated')
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/submit-listing', methods=['POST'])
@require_api_key
def submit_listing_to_ebay():
    """Legacy submission path cannot bypass draft review or the publish shutdown."""
    return jsonify({"error": "Publishing is disabled in this slice", "code": "FEATURE_DISABLED",
                    "source": "simulated"}), 503

@app.route('/api/listing/update-draft', methods=['POST'])
@require_api_key
def update_draft_listing():
    """Update draft listing with category and aspects."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    listing_id = data.get('listing_id')
    category_id = data.get('category_id')
    aspects = data.get('aspects', {})

    if not listing_id:
        return jsonify({"error": "listing_id required"}), 400

    try:
        success = db.update_draft_listing(listing_id, {
            'category_id': category_id,
            'aspects': aspects
        })

        if success:
            return jsonify({"success": True, "message": "Draft updated successfully", "source": "simulated"})
        else:
            return jsonify({"error": "Draft not found"}), 404
    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/listing/create-draft', methods=['POST'])
@require_api_key
def create_draft_listing():
    """Create draft listing from valuation."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    valuation_id = data.get('valuation_id')
    if not valuation_id:
        return jsonify({"error": "valuation_id required"}), 400

    listing_data = {
        "title": data.get('title'),
        "price": data.get('price'),
        "description": data.get('description'),
        "category_id": data.get('category_id'),
        "condition": data.get('condition'),
        "aspects": data.get('aspects', {})
    }

    try:
        listing_id = db.create_draft_listing(valuation_id, listing_data)
        return jsonify({"success": True, "listing_id": listing_id, "source": "simulated"})
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/listings/drafts', methods=['GET'])
@require_api_key
def get_draft_listings():
    """Get draft listings ready for eBay submission."""
    try:
        drafts = db.get_draft_listings()
        return jsonify({"success": True, "drafts": drafts, "source": "simulated"})
    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/live-listings', methods=['GET'])
@require_api_key
def get_live_listings():
    """Get all live eBay listings."""
    try:
        submissions = db.get_ebay_submissions()
        return jsonify({
            "success": True,
            "listings": submissions,
            "source": "simulated"
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/category/questions', methods=['POST'])
@require_api_key
def get_category_questions():
    """Get category-specific questions from eBay Taxonomy API."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    category_id = data.get('category_id', '293')
    known_data = data.get('known_data', {})

    try:
        # Get exact required fields from eBay API
        required_fields = category_generator.get_required_fields(category_id)
        questions = category_generator.generate_questions(category_id, known_data)
        validation = category_generator.validate_data(category_id, known_data)

        return jsonify({
            "success": True,
            "category_id": category_id,
            "source": required_fields[0].get('source', 'simulated') if required_fields else 'simulated',
            "required_fields": required_fields,
            "questions": questions,
            "validation": validation
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/category/suggest', methods=['POST'])
@require_api_key
def suggest_category():
    """Suggest eBay category based on item data."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    try:
        suggestions = category_generator.suggest_category_from_data(data)

        return jsonify({
            "success": True,
            "suggestions": suggestions,
            "source": "simulated"
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/category/<category_id>/fields', methods=['GET'])
@require_api_key
def get_required_fields(category_id):
    """Get exact required fields for a category from eBay Taxonomy API."""
    try:
        required_fields = category_generator.get_required_fields(category_id)
        return jsonify({
            "success": True,
            "category_id": category_id,
            "required_fields": required_fields,
            "source": required_fields[0].get('source', 'simulated') if required_fields else 'simulated'
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/token/status', methods=['GET'])
@require_api_key
def get_token_status():
    """Check stored token presence without exposing or refreshing it."""
    try:
        from services.ebay_token_manager import EBayTokenManager
        token_manager = EBayTokenManager()
        stored = token_manager._load_token()

        return jsonify({
            "success": True,
            "has_token": bool(stored and stored.get('access_token') and
                              not token_manager._is_expired(stored))
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/token/refresh', methods=['POST'])
@require_api_key
def refresh_token():
    """Force refresh eBay token."""
    try:
        from services.ebay_token_manager import EBayTokenManager
        token_manager = EBayTokenManager()
        token_data = token_manager._refresh_token()

        if token_data:
            return jsonify({
                "success": True,
                "message": "Token refreshed successfully",
                "expires_in": token_data.get('expires_in')
            })
        else:
            return jsonify({"error": "Failed to refresh token"}), 400
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/refresh-listings', methods=['POST'])
@require_api_key
def refresh_live_listings():
    """Refresh live listings from eBay account."""
    if not ebay_integration:
        return jsonify({"error": "eBay integration not initialized"}), 500

    try:
        # Real eBay API call to get active listings
        active_listings = ebay_integration.get_active_listings()

        return jsonify({
            "success": True,
            "message": f"Refreshed {len(active_listings)} listings",
            "listings": [{**listing, "source": "live"} for listing in active_listings],
            "source": "live"
        })
    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/listing/<ebay_listing_id>', methods=['GET'])
@require_api_key
def get_ebay_listing(ebay_listing_id):
    """Get specific eBay listing details."""
    try:
        # Mock listing data for now
        listing = {
            "title": "Sample eBay Listing",
            "price": 99.99,
            "description": "Sample description",
            "category_id": "293",
            "aspects": {"Brand": "Sony", "Type": "Headphones"}
        }
        return jsonify({
            "success": True,
            "listing": {**listing, "source": "simulated"},
            "source": "simulated"
        })
    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/update-listing', methods=['POST'])
@require_api_key
def update_ebay_listing():
    """Update eBay listing using ReviseItem API."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    ebay_listing_id = data.get('ebay_listing_id')

    if not ebay_listing_id:
        return jsonify({"error": "ebay_listing_id required"}), 400

    try:
        # Mock eBay API update call
        update_response = {
            "success": True,
            "ebay_listing_id": ebay_listing_id,
            "updated_fields": list(data.keys())
        }

        return jsonify({
            "success": True,
            "message": "Listing updated successfully",
            "ebay_response": update_response,
            "source": "simulated"
        })
    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/end-listing', methods=['POST'])
@require_api_key
def end_ebay_listing():
    """End eBay listing using EndItem API."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    ebay_listing_id = data.get('ebay_listing_id')

    if not ebay_listing_id:
        return jsonify({"error": "ebay_listing_id required"}), 400

    try:
        # Mock eBay API end listing call
        return jsonify({
            "success": True,
            "message": "Listing ended successfully",
            "ebay_listing_id": ebay_listing_id,
            "source": "simulated"
        })
    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/uploads/<filename>')
@require_api_key
def download_file(filename):
    """Serve uploaded images."""
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:;"
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == '__main__':
    init_db()
    logger.info("Database initialized")
    logger.info("Starting Enhanced eBay Listing Assistant")
    logger.info("Visit: http://localhost:5000")
    host = '127.0.0.1' if app.config['LOCAL_DRAFT_MODE'] else '0.0.0.0'
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't'), host=host, port=5000)
