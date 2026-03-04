from flask import Blueprint, request, jsonify
import logging

from extensions import db, ebay_integration, draft_image_manager

ebay_bp = Blueprint('ebay', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@ebay_bp.route('/ebay/oauth/url', methods=['GET'])
def get_ebay_oauth_url():
    """Get the eBay OAuth consent URL."""
    try:
        if not ebay_integration:
            return jsonify({"error": "eBay integration not initialized"}), 500

        url = ebay_integration.get_user_consent_url()
        return jsonify({
            "success": True,
            "url": url
        })
    except Exception as e:
        logger.exception(f"Error getting OAuth URL: {e}")
        return jsonify({"error": str(e)}), 500

@ebay_bp.route('/ebay/submit-listing', methods=['POST'])
def submit_listing_to_ebay():
    """Real eBay listing submission via API."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    valuation_id = data.get('valuation_id')
    if not valuation_id:
        return jsonify({"error": "valuation_id required"}), 400

    try:
        if not ebay_integration:
            return jsonify({"error": "eBay integration not initialized"}), 500

        validation = data.get('validation', {})
        listing_data = {
            "title": data.get('title'),
            "description": data.get('description'),
            "price": data.get('price'),
            "condition": data.get('condition', 'USED_EXCELLENT'),
            "category_id": data.get('category_id'),
            "aspects": validation.get("aspects", {}),
        }

        # Real eBay API call
        ebay_response = ebay_integration.create_listing(listing_data)
        ebay_listing_id = ebay_response.get("listing_id")

        if ebay_response.get("status") == "success":
            # Record submission in database
            submission_id = db.submit_to_ebay(
                valuation_id=valuation_id,
                ebay_listing_id=ebay_listing_id,
                listing_title=listing_data['title'],
                listing_price=listing_data['price'],
                ebay_response=ebay_response
            )

            # Cleanup draft images
            listing_id = data.get('listing_id')
            if listing_id:
                draft_image_manager.cleanup_draft_images(listing_id)

            return jsonify({
                "success": True,
                "ebay_listing_id": ebay_listing_id,
                "submission_id": submission_id,
                "listing_data": listing_data,
                "message": "Listing published successfully to eBay"
            })
        else:
            return jsonify({
                "error": "Failed to publish to eBay",
                "details": ebay_response
            }), 400

    except Exception as e:
        logger.exception(f"Error in submit_listing_to_ebay: {e}")
        return jsonify({"error": str(e)}), 500

@ebay_bp.route('/ebay/live-listings', methods=['GET'])
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

@ebay_bp.route('/ebay/token/status', methods=['GET'])
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

@ebay_bp.route('/ebay/token/refresh', methods=['POST'])
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

@ebay_bp.route('/ebay/refresh-listings', methods=['POST'])
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
        return jsonify({"error": str(e)}), 500

@ebay_bp.route('/ebay/listing/<ebay_listing_id>', methods=['GET'])
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

@ebay_bp.route('/ebay/update-listing', methods=['POST'])
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

@ebay_bp.route('/ebay/end-listing', methods=['POST'])
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
