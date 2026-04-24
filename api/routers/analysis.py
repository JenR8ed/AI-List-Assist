import uuid
import base64
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from core.database import get_session
from core.security import verify_api_key

# We import the legacy services directly for now.
# In the future, these should be converted to FastAPI dependencies.
from services.vision_service import VisionService
from services.valuation_service import ValuationService

router = APIRouter(prefix="/api/analyze", tags=["Analysis"])

# Instantiate locally for the router
vision_service = VisionService()
valuation_service = ValuationService(use_sandbox=True)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("")
async def analyze_image(
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
    api_key: str = Depends(verify_api_key)
):
    """Analyze image: detect items, value them, and determine if worth listing."""
    if not image.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    try:
        # Read async
        image_data = await image.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Save file asynchronously using AnyIO/FastAPI standards
        safe_filename = image.filename.replace(" ", "_")
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_filename}"
        filepath = UPLOAD_DIR / filename
        filepath.write_bytes(image_data)

        session_id = str(uuid.uuid4())

        # Call vision service natively
        content_type = image.content_type or 'image/jpeg'
        detected_items = await vision_service.detect_items_async(image_base64, content_type)

        # Placeholder return to prove architectural connection
        # TODO: Port the rest of the valuation loop and DB saves from app_enhanced.py
        return {
            "success": True,
            "session_id": session_id,
            "detected_items": len(detected_items),
            "image_url": f"/uploads/{filename}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
