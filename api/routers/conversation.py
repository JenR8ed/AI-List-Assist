from fastapi import APIRouter, Depends, HTTPException
from models.domain import ConversationStartRequest, ConversationAnswerRequest
from core.security import verify_api_key
from services.conversation_orchestrator import ConversationOrchestrator

router = APIRouter(prefix="/api/conversation", tags=["Conversation"])
orchestrator = ConversationOrchestrator()

@router.post("/start")
async def start_conversation(
    req: ConversationStartRequest,
    api_key: str = Depends(verify_api_key)
):
    """Start conversation for gathering listing details."""
    try:
        state = orchestrator.start_conversation(req.item_id, req.initial_data)
        return {
            "success": True,
            "session_id": state.session_id,
            "question": state.current_question,
            "confidence": state.confidence,
            "is_complete": state.is_complete
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/answer")
async def answer_question(
    req: ConversationAnswerRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process user's answer and get next question."""
    try:
        state = orchestrator.process_answer(req.session_id, req.answer)
        return {
            "success": True,
            "question": state.current_question,
            "confidence": state.confidence,
            "is_complete": state.is_complete,
            "known_fields": state.known_fields
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
