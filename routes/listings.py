from flask import Blueprint, request, jsonify, current_app
import logging
import sqlite3
import json
import os

from extensions import db, listing_engine, conversation_orchestrator, draft_image_manager

listings_bp = Blueprint('listings', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@listings_bp.route('/listing/create', methods=['POST'])
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
        if session_row and session_row[0]:
            session_data = json.loads(session_row[0])
            image_filename = session_data.get('image_filename')
            if image_filename:
                original_images = [os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)]

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
        logger.exception(f"Error in create_listing: {e}")
        return jsonify({"error": str(e)}), 500

@listings_bp.route('/listing/publish', methods=['POST'])
def publish_listing():
    """Publish listing to eBay."""
    from extensions import ebay_integration

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
            return jsonify({"error": "Listing draft not found"}), 404

        from shared.models import ListingDraft, ItemCondition
        from datetime import datetime
        draft_dict = json.loads(row[0])

        # Handle datetime conversion
        if 'created_at' in draft_dict:
            draft_dict['created_at'] = datetime.fromisoformat(draft_dict['created_at'])

        # Handle condition Enum conversion
        if 'condition' in draft_dict:
            draft_dict['condition'] = ItemCondition(draft_dict['condition'])

        draft = ListingDraft(**draft_dict)

        # Publish to eBay
        from services.ebay_token_manager import EBayTokenManager
        token_manager = EBayTokenManager()
        token = token_manager.get_valid_token()
        if not token:
             return jsonify({
                "error": "eBay authentication required",
                "auth_url": "/api/ebay/oauth/url"
             }), 401

        # Mock actual API call for tests when not fully configured
        result = ebay_integration.create_listing(draft)

        if result.get("status") == "published" or result.get("status") == "success":
            # Update database
            conn = sqlite3.connect('listings.db')
            c = conn.cursor()
            c.execute('''
                UPDATE listings
                SET status = 'published', ebay_listing_id = ?
                WHERE listing_id = ?
            ''', (result.get('listing_id'), listing_id))
            conn.commit()
            conn.close()

            # Cleanup images
            draft_image_manager.cleanup_draft_images(listing_id)

            return jsonify({
                "success": True,
                "ebay_listing_id": result.get('listing_id'),
                "message": "Listing published successfully",
                "url": result.get('url', f"https://sandbox.ebay.com/itm/{result.get('listing_id')}")
            })
        else:
            return jsonify({
                "error": "Failed to publish to eBay",
                "details": result
            }), 500

    except Exception as e:
        logger.exception(f"Error in publish_listing: {e}")
        return jsonify({"error": str(e)}), 500

@listings_bp.route('/listing/update-draft', methods=['POST'])
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

@listings_bp.route('/listing/create-draft', methods=['POST'])
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

@listings_bp.route('/listings/drafts', methods=['GET'])
def get_draft_listings():
    """Get draft listings ready for eBay submission."""
    try:
        drafts = db.get_draft_listings()
        return jsonify({"success": True, "drafts": drafts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
