from flask import Blueprint, request, jsonify
import logging

from extensions import db, conversation_orchestrator

conversation_bp = Blueprint('conversation', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@conversation_bp.route('/conversation/start', methods=['POST'])
def start_conversation():
    """Start a new data collection conversation."""
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

        conversation_id, initial_message = conversation_orchestrator.start_conversation(
            valuation_id, valuation_data
        )

        return jsonify({
            "success": True,
            "conversation_id": conversation_id,
            "message": initial_message
        })
    except Exception as e:
        logger.exception(f"Error starting conversation: {e}")
        return jsonify({"error": str(e)}), 500

@conversation_bp.route('/conversation/answer', methods=['POST'])
def answer_question():
    """Provide an answer to the current conversation question."""
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    conversation_id = data.get('conversation_id')
    answer = data.get('answer')

    if not conversation_id or not answer:
        return jsonify({"error": "conversation_id and answer required"}), 400

    try:
        response = conversation_orchestrator.process_answer(conversation_id, answer)

        # Ensure response has is_complete flag even if it wasn't returned
        if 'is_complete' not in response:
            response['is_complete'] = False

        return jsonify({
            "success": True,
            **response
        })
    except Exception as e:
        logger.exception(f"Error processing answer: {e}")
        return jsonify({"error": str(e)}), 500
