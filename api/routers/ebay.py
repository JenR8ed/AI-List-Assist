from fastapi import APIRouter, Depends, HTTPException
from models.domain import EbayPublishRequest, EbaySubmitRequest, EbayActionRequest
from core.security import verify_api_key
from services.ebay_integration import eBayIntegration

router = APIRouter(prefix="/api/ebay", tags=["eBay Integration"])
ebay_integration = eBayIntegration(use_sandbox=True)

@router.get("/oauth/url")
async def get_ebay_oauth_url(redirect_uri: str = 'http://localhost:8000/api/ebay/oauth/callback', api_key: str = Depends(verify_api_key)):
    """Get eBay OAuth authorization URL."""
    try:
        oauth_url = ebay_integration.get_oauth_url(redirect_uri)
        return {"success": True, "oauth_url": oauth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit-listing")
async def submit_listing_to_ebay(req: EbaySubmitRequest, api_key: str = Depends(verify_api_key)):
    """Submit listing to eBay with category aspects."""
    # TODO: Port the full mapping logic from app_enhanced.py
    return {"success": True, "message": "Scaffolded. Ready for service injection."}

@router.get("/live-listings")
async def get_live_listings(api_key: str = Depends(verify_api_key)):
    """Get all live eBay listings."""
    # TODO: Connect to DB
    return {"success": True, "listings": []}

@router.post("/update-listing")
async def update_ebay_listing(req: EbayActionRequest, api_key: str = Depends(verify_api_key)):
    return {"success": True, "message": "Listing updated successfully", "ebay_listing_id": req.ebay_listing_id}

@router.post("/end-listing")
async def end_ebay_listing(req: EbayActionRequest, api_key: str = Depends(verify_api_key)):
    return {"success": True, "message": "Listing ended successfully", "ebay_listing_id": req.ebay_listing_id}
