from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from models.domain import CategoryQuestionsRequest
from core.security import verify_api_key
from services.ebay_category_service import EBayCategoryService
from services.category_detail_generator import CategoryDetailGenerator

router = APIRouter(prefix="/api/category", tags=["Categories"])
category_service = EBayCategoryService()
category_generator = CategoryDetailGenerator()

@router.get("/{category_id}/aspects")
async def get_category_aspects(category_id: str, api_key: str = Depends(verify_api_key)):
    try:
        aspects = category_service.get_category_aspects(category_id)
        return {"success": True, "category_id": category_id, "aspects": aspects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/questions")
async def get_category_questions(req: CategoryQuestionsRequest, api_key: str = Depends(verify_api_key)):
    try:
        required_fields = category_generator.get_required_fields(req.category_id)
        questions = category_generator.generate_questions(req.category_id, req.known_data)
        validation = category_generator.validate_data(req.category_id, req.known_data)
        return {
            "success": True,
            "category_id": req.category_id,
            "required_fields": required_fields,
            "questions": questions,
            "validation": validation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest")
async def suggest_category(data: Dict[str, Any], api_key: str = Depends(verify_api_key)):
    try:
        suggestions = category_generator.suggest_category_from_data(data)
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
