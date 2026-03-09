"""
Enhanced Flask App - End-to-End eBay Listing Assistant
Integrates all services: vision, valuation, conversation, listing synthesis, eBay API
"""

from flask import Flask, render_template, request, jsonify
import base64
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import sqlite3
import uuid

# Import services
from services.vision_service import VisionService
from services.conversation_orchestrator import ConversationOrchestrator
from services.listing_synthesis import ListingSynthesisEngine
from services.ebay_integration import eBayIntegration
from services.valuation_database import ValuationDatabase
from services.valuation_service import ValuationService
from services.ebay_category_service import EBayCategoryService
from services.draft_image_manager import DraftImageManager
from services.category_detail_generator import CategoryDetailGenerator
from services.ebay_comp_scraper import EbayCompScraper

# Load environment variables
from dotenv import find_dotenv
load_dotenv(find_dotenv())

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-secret-key-12345')
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable must be set")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure folders exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

# Initialize services
try:
    vision_service = VisionService()
    print("Vision service initialized")
except Exception as e:
    print(f"Vision service failed: {e}")
    vision_service = None

# Initialize database and services
db = ValuationDatabase()
valuation_service = ValuationService()
category_service = EBayCategoryService()
category_generator = CategoryDetailGenerator()
draft_image_manager = DraftImageManager()
comp_scraper = EbayCompScraper()
print("Database and services initialized")

try:
    conversation_orchestrator = ConversationOrchestrator()
    listing_engine = ListingSynthesisEngine()
    ebay_integration = eBayIntegration(use_sandbox=True)
    print("Other services initialized")
except Exception as e:
    print(f"Other services warning: {e}")

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
def analyze_image():
    """
    Analyze image: detect items, value them, and determine if worth listing.
    """
    files = request.files.getlist('image')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "No images provided"}), 400

    try:
        filenames = []
        primary_image_base64 = None
        primary_content_type = None

        for i, file in enumerate(files):
            if file.filename == '':
                continue

            image_data = file.read()
            if i == 0:
                primary_image_base64 = base64.b64encode(image_data).decode('utf-8')
                primary_content_type = file.content_type or 'image/jpeg'

            # Save uploaded file
            safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}_{file.filename.replace(' ', '_')}"
            filepath = Path(app.config['UPLOAD_FOLDER']) / safe_filename
            with open(filepath, 'wb') as f:
                f.write(image_data)
            filenames.append(safe_filename)

        if not filenames:
            return jsonify({"error": "No valid files uploaded"}), 400

        # Get market filters from request
        condition_filter = request.form.get('condition')
        min_price = request.form.get('min_price')
        max_price = request.form.get('max_price')

        try:
            min_price = float(min_price) if min_price else None
            max_price = float(max_price) if max_price else None
        except ValueError:
            min_price = None
            max_price = None

        # Create session
        session_id = str(uuid.uuid4())

        # Step 1: Detect items (using primary image)
        print(f"DEBUG: Processing {len(filenames)} images, primary size: {len(primary_image_base64) if primary_image_base64 else 0} chars")
        if not vision_service:
            return jsonify({"error": "Vision service not available"}), 500

        vision_used = False
        gemini_used = False
        usage_metadata = {}

        try:
            detected_items = vision_service.detect_items(primary_image_base64, primary_content_type)

            # Check which APIs were used
            vision_used = True
            usage_metadata = vision_service.get_usage_metadata()
            if usage_metadata:
                gemini_used = True

            print(f"DEBUG: Detected {len(detected_items)} items")
        except Exception as vision_error:
            print(f"DEBUG: Vision service error: {vision_error}")
            return jsonify({"error": f"Vision service failed: {str(vision_error)}"}), 500

        # Step 2: Value each item
        valuations = []
        for item in detected_items:
            try:
                # Fetch real market comps before valuation
                query = f"{item.brand or ''} {item.probable_category or ''}".strip()
                if item.detected_text:
                    query += " " + " ".join(item.detected_text[:2])

                print(f"DEBUG: Fetching comps for query: {query}")
                sold_comps, seo_tokens = comp_scraper.scrape_comps(
                    query,
                    limit=5,
                    condition=condition_filter,
                    min_price=min_price,
                    max_price=max_price
                )

                valuation = valuation_service.evaluate_item(
                    primary_image_base64,
                    primary_content_type,
                    item.to_dict(),
                    sold_comps=sold_comps,
                    seo_tokens=seo_tokens
                )
                valuations.append(valuation)
                print(f"DEBUG: Valued item {item.item_id}: {valuation.item_name}")
            except Exception as val_error:
                print(f"DEBUG: Valuation error for {item.item_id}: {val_error}")

        # Step 3: Filter items worth listing
        worth_listing = [v for v in valuations if v.worth_listing]

        # Save valuations to database
        primary_filename = filenames[0]
        image_hash = str(hash(primary_image_base64))
        for valuation in valuations:
            valuation_id = db.save_valuation(primary_filename, image_hash, valuation)
            # Store full photo list in valuation data
            db.update_draft_listing(valuation_id, {"photos": filenames})

        # Save to database session
        conn = sqlite3.connect('listings.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO sessions (session_id, status, session_data)
            VALUES (?, ?, ?)
        ''', (session_id, "analyzed", json.dumps({
            "detected_items": [item.to_dict() for item in detected_items],
            "valuations": [v.to_dict() for v in valuations],
            "image_filename": primary_filename,
            "all_photos": filenames
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
            "items": [
                {
                    "item_id": v.item_id,
                    "item_name": v.item_name,
                    "estimated_value": v.estimated_value,
                    "worth_listing": v.worth_listing,
                    "profitability": v.profitability.value
                }
                for v in valuations
            ],
            "image_url": f"/uploads/{primary_filename}",
            "all_images": [f"/uploads/{f}" for f in filenames]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

@app.route('/api/conversation/start', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversation/answer', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/listing/create', methods=['POST'])
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
            INSERT INTO listings (listing_id, item_id, title, price, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            listing_draft.listing_id,
            item_id,
            listing_draft.title,
            listing_draft.price,
            "draft"
        ))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "listing": listing_draft.to_dict()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/listing/publish', methods=['POST'])
def publish_listing():
    """Publish listing to eBay."""
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
        c.execute('SELECT * FROM listings WHERE listing_id = ?', (listing_id,))
        row = c.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Listing not found"}), 404

        # In production, would reconstruct ListingDraft from DB
        # For now, return success
        return jsonify({
            "success": True,
            "message": "Listing published successfully",
            "listing_id": listing_id,
            "note": "eBay API integration requires OAuth setup"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/oauth/url', methods=['GET'])
def get_ebay_oauth_url():
    """Get eBay OAuth authorization URL."""
    redirect_uri = request.args.get('redirect_uri', 'http://localhost:5000/api/ebay/oauth/callback')

    try:
        oauth_url = ebay_integration.get_oauth_url(redirect_uri)
        return jsonify({
            "success": True,
            "oauth_url": oauth_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/valuations/recent', methods=['GET'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/valuations/approved', methods=['GET'])
def get_approved_valuations():
    """Get approved valuations ready for eBay."""
    try:
        valuations = db.get_approved_valuations()
        return jsonify({
            "success": True,
            "approved_valuations": valuations
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/valuations/<valuation_id>/approve', methods=['POST'])
def approve_valuation(valuation_id):
    """Approve a valuation for eBay listing."""
    try:
        success = db.approve_valuation(valuation_id)
        if success:
            return jsonify({"success": True, "message": "Valuation approved"})
        else:
            return jsonify({"error": "Valuation not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get valuation statistics."""
    try:
        stats = db.get_valuation_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/valuations/<valuation_id>', methods=['GET'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/category/<category_id>/aspects', methods=['GET'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/submit-listing', methods=['POST'])
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
        from shared.models import ListingDraft, ItemCondition

        # Map condition ID to ItemCondition enum (or just use the string if it matches)
        # This is a bit of a hack until condition mapping is formalized
        cond_str = data.get('condition', 'USED')
        try:
            cond_enum = ItemCondition[cond_str.upper()]
        except:
            cond_enum = ItemCondition.USED

        listing_draft = ListingDraft(
            listing_id=valuation_id, # Use valuation_id as SKU
            item_id=valuation_id,
            title=data.get('title'),
            description=data.get('description'),
            category_id=category_id,
            condition=cond_enum,
            price=float(data.get('price', 0)),
            item_specifics=validation["aspects"]
        )

        try:
            # Get valid token and call eBay
            from services.ebay_token_manager import EBayTokenManager
            token_manager = EBayTokenManager()
            token = token_manager.get_valid_token()

            if not token:
                raise Exception("No valid eBay token found. Please authenticate.")

            ebay_integration.access_token = token
            result = ebay_integration.create_listing(listing_draft)

            ebay_listing_id = result.get("listing_id")
            ebay_response = result

            print(f"DEBUG: Successfully published to eBay: {ebay_listing_id}")

        except Exception as ebay_error:
            print(f"DEBUG: eBay API error: {ebay_error}")
            # Fallback to simulation if token is dummy (for dev purposes)
            if "dummy" in str(os.getenv('EBAY_CLIENT_ID', '')).lower():
                ebay_listing_id = f"ebay_{valuation_id[:8]}"
                ebay_response = {"status": "success", "listing_id": ebay_listing_id, "note": "Simulated successful submission"}
            else:
                return jsonify({"error": f"eBay API failed: {str(ebay_error)}"}), 500

        # Record submission in database
        submission_id = db.submit_to_ebay(
            valuation_id=valuation_id,
            ebay_listing_id=ebay_listing_id,
            listing_title=data.get('title'),
            listing_price=data.get('price'),
            ebay_response=ebay_response
        )

        # Cleanup draft images after successful submission
        listing_id = data.get('listing_id')
        if listing_id:
            draft_image_manager.cleanup_draft_images(listing_id)

        return jsonify({
            "success": True,
            "ebay_listing_id": ebay_listing_id,
            "submission_id": submission_id,
            "listing_data": {
                "title": listing_draft.title,
                "price": listing_draft.price,
                "aspects": listing_draft.item_specifics
            },
            "message": "Listing published to eBay successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/listing/update-draft', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/listing/create-draft', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/listings/drafts', methods=['GET'])
def get_draft_listings():
    """Get draft listings ready for eBay submission."""
    try:
        drafts = db.get_draft_listings()
        return jsonify({"success": True, "drafts": drafts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/live-listings', methods=['GET'])
def get_live_listings():
    """Get all live eBay listings."""
    try:
        submissions = db.get_ebay_submissions()
        return jsonify({
            "success": True,
            "listings": submissions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/category/questions', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/category/suggest', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/category/<category_id>/fields', methods=['GET'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/token/status', methods=['GET'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/token/refresh', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/refresh-listings', methods=['POST'])
def refresh_live_listings():
    """Refresh live listings from eBay account."""
    try:
        # Mock eBay API call to get active listings
        active_listings = [
            {
                "ebay_listing_id": "123456789",
                "title": "Sony WH-1000XM4 Headphones",
                "price": 249.99,
                "status": "Active",
                "views": 45,
                "watchers": 3
            },
            {
                "ebay_listing_id": "987654321",
                "title": "Apple iPhone 13 Pro",
                "price": 899.99,
                "status": "Active",
                "views": 128,
                "watchers": 12
            }
        ]

        return jsonify({
            "success": True,
            "message": f"Refreshed {len(active_listings)} listings",
            "listings": active_listings
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/listing/<ebay_listing_id>', methods=['GET'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/update-listing', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/end-listing', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/ebay/listing/<ebay_listing_id>/send-offer', methods=['POST'])
def send_ebay_offer(ebay_listing_id):
    """Send negotiation offer to watchers."""
    data = request.json
    offer_price = data.get('offer_price')

    if not offer_price:
        return jsonify({"error": "offer_price is required"}), 400

    try:
        from services.ebay_token_manager import EBayTokenManager
        token_manager = EBayTokenManager()
        token = token_manager.get_valid_token()

        if not token:
             raise Exception("No valid eBay token found.")

        ebay_integration.access_token = token
        result = ebay_integration.send_negotiation_offer(ebay_listing_id, offer_price)

        return jsonify({
            "success": True,
            "message": "Offer sent successfully",
            "ebay_response": result
        })
    except Exception as e:
        print(f"DEBUG: Send offer error: {e}")
        # Simulation fallback
        if "dummy" in str(os.getenv('EBAY_CLIENT_ID', '')).lower():
            return jsonify({
                "success": True,
                "message": "Simulated offer sent successfully",
                "simulated": True
            })
        return jsonify({"error": str(e)}), 500

@app.route('/api/comps/scrape', methods=['GET'])
def scrape_ebay_comps():
    """Scrape exact comps and return popular title SEO tokens via eBay Insights API."""
    query = request.args.get('query')
    limit = request.args.get('limit', 10, type=int)
    condition = request.args.get('condition') # new, used, parts
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    if not query:
        return jsonify({"error": "query parameter is required"}), 400

    try:
        comps, seo_tokens = comp_scraper.scrape_comps(
            query,
            limit=limit,
            condition=condition,
            min_price=min_price,
            max_price=max_price
        )
        return jsonify({
            "success": True,
            "query": query,
            "filters": {
                "condition": condition,
                "min_price": min_price,
                "max_price": max_price
            },
            "comps_found": len(comps),
            "top_seo_tokens": seo_tokens,
            "comps": comps
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<filename>')
def download_file(filename):
    """Serve uploaded images."""
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == '__main__':
    init_db()
    print("Database initialized")
    print("Starting Enhanced eBay Listing Assistant")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
