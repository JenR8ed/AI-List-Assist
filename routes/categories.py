from flask import Blueprint, request, jsonify
import logging

from extensions import category_generator

categories_bp = Blueprint('categories', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@categories_bp.route('/category/<category_id>/aspects', methods=['GET'])
def get_category_aspects(category_id):
    """Get required item specifics for an eBay category."""
    try:
        from extensions import category_service
        aspects = category_service.get_category_specifics(category_id)
        return jsonify({
            "success": True,
            "category_id": category_id,
            "aspects": aspects
        })
    except Exception as e:
        logger.exception(f"Error getting category aspects: {e}")
        return jsonify({"error": str(e)}), 500

@categories_bp.route('/category/questions', methods=['POST'])
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

@categories_bp.route('/category/suggest', methods=['POST'])
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

@categories_bp.route('/category/<category_id>/fields', methods=['GET'])
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
