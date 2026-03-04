from flask import Blueprint, request, jsonify
import logging

from extensions import db, listing_engine

listings_bp = Blueprint('listings', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@listings_bp.route('/listing/create', methods=['POST'])
def create_listing():
    """Create a synthesized listing from valuation data."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    valuation_id = data.get('valuation_id')
    if not valuation_id:
        return jsonify({"error": "valuation_id required"}), 400

    try:
        valuation_data = db.get_valuation(valuation_id)
        if not valuation_data:
            return jsonify({"error": "Valuation not found"}), 404

        listing_data = listing_engine.synthesize_listing(valuation_data)

        return jsonify({
            "success": True,
            "listing": listing_data
        })
    except Exception as e:
        logger.exception(f"Error in create_listing: {e}")
        return jsonify({"error": str(e)}), 500

@listings_bp.route('/listing/publish', methods=['POST'])
def publish_listing():
    """Publish a draft listing to eBay."""
    from extensions import draft_image_manager

    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    valuation_id = data.get('valuation_id')
    if not valuation_id:
        return jsonify({"error": "valuation_id required"}), 400

    try:
        # Get category validation data
        validation = data.get('validation', {})

        listing_data = {
            "title": data.get('title'),
            "description": data.get('description'),
            "price": data.get('price'),
            "condition": data.get('condition', 'USED_EXCELLENT'),
            "category_id": data.get('category_id'),
            "aspects": validation.get("aspects", {}),
            "validation_errors": validation.get("errors", [])
        }

        # For now, simulate eBay submission
        ebay_listing_id = f"ebay_{valuation_id[:8]}"

        # Record submission in database
        submission_id = db.submit_to_ebay(
            valuation_id=valuation_id,
            ebay_listing_id=ebay_listing_id,
            listing_title=data.get('title'),
            listing_price=data.get('price'),
            ebay_response={"status": "success", "listing_id": ebay_listing_id}
        )

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
