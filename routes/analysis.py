from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import base64
import os
import logging
from datetime import datetime

from extensions import db, vision_service, valuation_service, category_service, draft_image_manager

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@analysis_bp.route('/analyze', methods=['POST'])
def analyze_image():
    """
    Analyze image: detect items, value them, and determine if worth listing.
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Only images allowed."}), 400

    if not vision_service:
        return jsonify({"error": "Vision service not initialized"}), 500

    try:
        # Save original upload
        filename = secure_filename(file.filename)
        # Prepend timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # 1. Vision Analysis (Detect Items)
        with open(filepath, "rb") as image_file:
            image_bytes = image_file.read()

        logger.info(f"Analyzing image {unique_filename}")
        vision_result = vision_service.analyze_image(image_bytes)

        if not vision_result or "items" not in vision_result:
            return jsonify({
                "error": "Failed to analyze image",
                "details": "Vision service returned invalid format"
            }), 500

        # Create session
        session_id = db.create_session("analysis_started")
        results = []

        # 2. Process each detected item
        for item in vision_result["items"]:
            try:
                # Enhance item with eBay category
                category_data = category_service.suggest_category(
                    item.get("brand", ""),
                    item.get("model", "")
                )
                item["category_id"] = category_data["category_id"]
                item["category_name"] = category_data["category_name"]

                # Get valuation
                valuation = valuation_service.evaluate_item(item)

                # Store item and draft image
                item_id = db.add_item(session_id, unique_filename, valuation)
                draft_image_manager.save_draft_image(item_id, image_bytes, f"draft_{unique_filename}")

                results.append({
                    "item_id": item_id,
                    "status": "success",
                    "item": item,
                    "valuation": valuation
                })
            except Exception as item_error:
                logger.exception(f"Error processing item: {item_error}")
                results.append({
                    "status": "failed",
                    "item": item,
                    "error": str(item_error)
                })

        db.update_session_status(session_id, "analysis_complete", {"results": results})

        return jsonify({
            "success": True,
            "session_id": session_id,
            "image_url": f"/uploads/{unique_filename}",
            "items": results
        })

    except Exception as e:
        logger.exception(f"Unexpected error in analyze_image: {e}")
        return jsonify({"error": str(e)}), 500

@analysis_bp.route('/valuations/recent', methods=['GET'])
def get_recent_valuations():
    """Get recently analyzed items."""
    try:
        items = db.get_recent_items(limit=20)
        return jsonify({
            "success": True,
            "items": items
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analysis_bp.route('/valuations/approved', methods=['GET'])
def get_approved_valuations():
    """Get valuations approved for listing."""
    try:
        items = db.get_approved_valuations()
        return jsonify({
            "success": True,
            "items": items
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analysis_bp.route('/valuations/<valuation_id>/approve', methods=['POST'])
def approve_valuation(valuation_id):
    """Mark a valuation as approved for listing."""
    try:
        success = db.approve_valuation(valuation_id)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Valuation not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analysis_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get overall dashboard stats."""
    try:
        stats = db.get_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@analysis_bp.route('/valuations/<valuation_id>', methods=['GET'])
def get_valuation(valuation_id):
    """Get a specific valuation by ID."""
    try:
        valuation = db.get_valuation(valuation_id)
        if valuation:
            return jsonify({"success": True, "valuation": valuation})
        else:
            return jsonify({"error": "Valuation not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
