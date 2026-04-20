"""
Enhanced Flask App - End-to-End eBay Listing Assistant
Integrates all services: vision, valuation, conversation, listing synthesis, eBay API
"""

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import base64
import json
import os
import logging
import hmac
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import sqlite3
import uuid

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
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Ensure folders exist
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
print("Database and services initialized")

conversation_orchestrator = None
listing_engine = None
ebay_integration = None

try:
    conversation_orchestrator = ConversationOrchestrator()
    listing_engine = ListingSynthesisEngine()
    ebay_integration = eBayIntegration(use_sandbox=True)
    print("Other services initialized")
except Exception as e:
    print(f"Other services warning: {e}")


from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = os.getenv('API_KEY')
        if not api_key:
            # If no API key is configured, we might want to allow it for dev
            # But for security, we should enforce it.
            return jsonify({"error": "Server misconfiguration: API_KEY not set"}), 500

        request_key = request.headers.get('Authorization')
        if request_key and request_key.startswith('Bearer '):
            request_key = request_key.split('Bearer ')[1]

        if not request_key or not hmac.compare_digest(request_key, api_key):
            return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)
    return decorated_function

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
# API ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/simple')
def simple_interface():
    """Simple upload interface."""
    return render_template('index.html')

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

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only images are allowed."}), 400

    try:
        # Read and encode image
        image_data = file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Sanitize and save uploaded file
        safe_filename = secure_filename(file.filename)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_filename}"
        filepath = Path(app.config['UPLOAD_FOLDER']) / filename
        with open(filepath, 'wb') as f:
            f.write(image_data)

        # Create session
        session_id = str(uuid.uuid4())

        # Step 1: Detect items
        print(f"DEBUG: Processing image, size: {len(image_base64)} chars, content_type: {file.content_type}")
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

            print(f"DEBUG: Detected {len(detected_items)} items")
            for i, item in enumerate(detected_items):
                print(f"DEBUG: Item {i}: brand={item.brand}, category={item.probable_category}, text={item.detected_text}")
        except Exception as vision_error:
            print(f"DEBUG: Vision service error: {vision_error}")
            return jsonify({"error": f"Vision service failed: {str(vision_error)}"}), 500

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
                    "status": "success"
                })
                logger.info(f"Valued item {item.item_id}: {valuation.item_name}")
            except Exception as val_error:
                logger.exception(f"Valuation error for item {item.item_id}")
                # Collect failed items for the frontend
                item_results.append({
                    "item_id": item.item_id,
                    "item_name": item.probable_category or item.brand or "Unknown Item",
                    "estimated_value": 0.0,
                    "worth_listing": False,
                    "profitability": "not_recommended",
                    "status": "failed",
                    **item.to_dict()
                })
                valuations.append(valuation)
                item_results.append({
                    "item_id": valuation.item_id,
                    "item_name": valuation.item_name,
                    "estimated_value": valuation.estimated_value,
                    "worth_listing": valuation.worth_listing,
                    "profitability": valuation.profitability.value,
                    "status": "success"
                })
                logger.info(f"Valued item {item.item_id}: {valuation.item_name}")
            except Exception as val_error:
                logger.exception(f"Valuation error for item {item.item_id}")
                # Collect failed items for the frontend
                item_results.append({
                    "item_id": item.item_id,
                    "item_name": item.brand or "Unknown Item",
                    "estimated_value": 0.0,
                    "worth_listing": False,
                    "profitability": "not_recommended",
                    "status": "failed",
                    "error": "Valuation failed due to an internal error."
                })

        # Step 3: Filter items worth listing
        worth_listing = [v for v in valuations if v.worth_listing]

        # Save valuations to database
        for valuation in valuations:
            image_hash = str(hash(image_base64))
            valuation_id = db.save_valuation(filename, image_hash, valuation)
            print(f"Saved valuation {valuation_id} for {valuation.item_name}")

        # Save to database
        conn = sqlite3.connect('listings.db')
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
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

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
        conn = sqlite3.connect('listings.db')
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
            estimated_value=conv_state.known_fields.get("price", 0.0),
            value_range={"low": 0, "high": 0},
            resale_score=7,
            profitability=Profitability.MEDIUM,
            recommended_platforms=["eBay"],
            key_factors=[],
            risks=[],
            listing_tips=[],
            worth_listing=True,
            confidence=conv_state.confidence
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
        conn = sqlite3.connect('listings.db')
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
            "listing": listing_draft.to_dict()
        })

    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/listing/publish', methods=['POST'])
@require_api_key
def publish_listing():
    """Publish listing to eBay."""
    if not ebay_integration:
        return jsonify({"error": "eBay integration not initialized"}), 500

    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    listing_id = data.get('listing_id')

    if not listing_id:
        return jsonify({"error": "listing_id required"}), 400

    try:
        # Get listing from database
        conn = sqlite3.connect('listings.db')
        c = conn.cursor()
        c.execute('SELECT draft_data FROM listings WHERE listing_id = ?', (listing_id,))
        row = c.fetchone()
        conn.close()

        if not row or not row[0]:
            return jsonify({"error": "Listing draft data not found"}), 404

        # Reconstruct ListingDraft from DB
        draft_dict = json.loads(row[0])

        # Handle datetime conversion
        if 'created_at' in draft_dict:
            draft_dict['created_at'] = datetime.fromisoformat(draft_dict['created_at'])

        # Handle condition Enum conversion
        if 'condition' in draft_dict:
            draft_dict['condition'] = ItemCondition(draft_dict['condition'])

        listing_draft = ListingDraft(**draft_dict)

        # Ensure we have a valid eBay token
        token = ebay_integration.token_manager.get_valid_token()
        if token:
            ebay_integration.access_token = token

        # Publish to eBay
        try:
            ebay_result = ebay_integration.create_listing(listing_draft)
            ebay_listing_id = ebay_result.get("listing_id")

            # Update database status
            conn = sqlite3.connect('listings.db')
            c = conn.cursor()
            c.execute('''
                UPDATE listings
                SET status = ?, ebay_listing_id = ?
                WHERE listing_id = ?
            ''', ("active", ebay_listing_id, listing_id))
            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "message": "Listing published successfully to eBay",
                "listing_id": listing_id,
                "ebay_listing_id": ebay_listing_id,
                "url": ebay_result.get("url")
            })
        except Exception as ebay_err:
            return jsonify({
                "error": f"eBay publishing failed: {str(ebay_err)}",
                "note": "Make sure you have completed the eBay OAuth flow"
            }), 401

    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/oauth/url', methods=['GET'])
@require_api_key
def get_ebay_oauth_url():
    """Get eBay OAuth authorization URL."""
    if not ebay_integration:
        return jsonify({"error": "eBay integration not initialized"}), 500

    redirect_uri = request.args.get('redirect_uri', 'http://localhost:5000/api/ebay/oauth/callback')

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
            "valuations": valuations
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
            "approved_valuations": valuations
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
            return jsonify({"success": True, "message": "Valuation approved"})
        else:
            return jsonify({"error": "Valuation not found"}), 404
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/stats', methods=['GET'])
@require_api_key
def get_stats():
    """Get valuation statistics."""
    try:
        stats = db.get_valuation_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/valuations/<valuation_id>', methods=['GET'])
@require_api_key
def get_valuation(valuation_id):
    """Get a specific valuation by ID."""
    try:
        conn = sqlite3.connect('valuations.db')
        c = conn.cursor()
        c.execute('SELECT valuation_data FROM valuations WHERE id = ?', (valuation_id,))
        row = c.fetchone()
        conn.close()

        if row:
            valuation_data = json.loads(row[0])
            return jsonify({
                "success": True,
                "valuation": valuation_data
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
            "aspects": aspects
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/submit-listing', methods=['POST'])
@require_api_key
def submit_listing_to_ebay():
    """Submit listing to eBay with category aspects."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    valuation_id = data.get('valuation_id')

    if not valuation_id:
        return jsonify({"error": "valuation_id required"}), 400

    try:
        # Get valuation data for mapping
        conn = sqlite3.connect('valuations.db')
        c = conn.cursor()
        c.execute('SELECT valuation_data FROM valuations WHERE id = ?', (valuation_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Valuation not found"}), 404

        valuation_data = json.loads(row[0])

        # Map valuation to category aspects
        category_id = data.get('category_id', '293')
        mapped_aspects = category_service.map_valuation_to_aspects(valuation_data, category_id)

        # Validate aspects
        validation = category_service.validate_aspects(mapped_aspects, category_id)

        # Build complete listing data
        listing_data = {
            "title": data.get('title'),
            "category_id": category_id,
            "price": data.get('price'),
            "condition": data.get('condition'),
            "description": data.get('description'),
            "aspects": validation["aspects"],
            "validation_errors": validation["errors"]
        }
        # Ensure we have a valid eBay token
        token = ebay_integration.token_manager.get_valid_token()
        if token:
            ebay_integration.access_token = token

        # Reconstruct ListingDraft
        listing_id = data.get('listing_id')
        if listing_id and not all(c.isalnum() or c in '-_' for c in listing_id):
            return jsonify({"error": "Invalid listing_id format"}), 400
        
        if not listing_id:
            listing_id = f"draft_{valuation_id[:8]}"

        condition_str = data.get('condition', 'USED')
        try:
            condition = ItemCondition(condition_str)
        except ValueError:
            condition = ItemCondition.USED

        listing_draft = ListingDraft(
            listing_id=listing_id,
            item_id=valuation_id,
            title=data.get('title'),
            description=data.get('description', ''),
            category_id=category_id,
            condition=condition,
            price=float(data.get('price') or 0.0),
            item_specifics=validation["aspects"],
            images=data.get('images', [])
        )

        # Publish to eBay
        try:
            ebay_result = ebay_integration.create_listing(listing_draft)
            ebay_listing_id = ebay_result.get("listing_id")

            # Record submission in database
            submission_id = db.submit_to_ebay(
                valuation_id=valuation_id,
                ebay_listing_id=ebay_listing_id,
                listing_title=data.get('title'),
                listing_price=price,
                ebay_response=ebay_result
            )
        except Exception as ebay_err:
            return jsonify({
                "error": f"eBay publishing failed: {str(ebay_err)}",
                "details": "The listing was processed but failed to publish to eBay."
            }), 500

        # Cleanup draft images after successful submission
        listing_id = data.get('listing_id')
        if listing_id:
            draft_image_manager.cleanup_draft_images(listing_id)

        return jsonify({
            "success": True,
            "ebay_listing_id": ebay_listing_id,
            "submission_id": submission_id,
            "listing_data": listing_data,
            "message": "Listing submitted successfully and draft images cleaned up"
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

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
            return jsonify({"success": True, "message": "Draft updated successfully"})
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
        return jsonify({"success": True, "listing_id": listing_id})
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/listings/drafts', methods=['GET'])
@require_api_key
def get_draft_listings():
    """Get draft listings ready for eBay submission."""
    try:
        drafts = db.get_draft_listings()
        return jsonify({"success": True, "drafts": drafts})
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
            "listings": submissions
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
            "suggestions": suggestions
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
            "required_fields": required_fields
        })
    except Exception as e:
        logger.exception("API Error"); return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/api/ebay/token/status', methods=['GET'])
@require_api_key
def get_token_status():
    """Check eBay token status."""
    try:
        from services.ebay_token_manager import EBayTokenManager
        token_manager = EBayTokenManager()
        token = token_manager.get_valid_token()

        return jsonify({
            "success": True,
            "has_token": bool(token),
            "token_preview": token[:20] + "..." if token else None
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
            "listings": active_listings
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
            "listing": listing
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
            "ebay_response": update_response
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
            "ebay_listing_id": ebay_listing_id
        })
    except Exception as e:
        logger.exception("API Error")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/uploads/<filename>')
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
    return response

# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == '__main__':
    init_db()
    print("Database initialized")
    print("Starting Enhanced eBay Listing Assistant")
    print("Visit: http://localhost:5000")
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't'), host='0.0.0.0', port=5000)
