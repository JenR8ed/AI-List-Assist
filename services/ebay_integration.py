"""
eBay API Integration Layer
Handles OAuth, listing creation, and eBay Sell APIs.
"""

from typing import Dict, Any, Optional, List
import os
import requests
from shared.models import ListingDraft, ItemCondition


class eBayIntegration:
    """Integration layer for eBay Sell APIs."""

    # eBay API endpoints (Sandbox)
    SANDBOX_BASE_URL = "https://api.sandbox.ebay.com"
    PRODUCTION_BASE_URL = "https://api.ebay.com"

    def __init__(
        self,
        app_id: Optional[str] = None,
        cert_id: Optional[str] = None,
        dev_id: Optional[str] = None,
        use_sandbox: bool = True
    ):
        """
        Initialize eBay integration.

        Args:
            app_id: eBay App ID (Client ID)
            cert_id: eBay Certificate ID (Client Secret)
            dev_id: eBay Developer ID
            use_sandbox: Use sandbox environment
        """
        self.app_id = app_id or os.getenv('EBAY_APP_ID')
        self.cert_id = cert_id or os.getenv('EBAY_CERT_ID')
        self.dev_id = dev_id or os.getenv('EBAY_DEV_ID')
        self.use_sandbox = use_sandbox

        self.base_url = self.SANDBOX_BASE_URL if use_sandbox else self.PRODUCTION_BASE_URL
        self.access_token: Optional[str] = None

    def authenticate(self, auth_code: str, redirect_uri: str) -> bool:
        """
        Authenticate with eBay using OAuth 2.0 authorization code.

        Args:
            auth_code: Authorization code from OAuth callback
            redirect_uri: Redirect URI used in OAuth flow

        Returns:
            True if authentication successful
        """
        # This is a placeholder - full OAuth implementation would go here
        # For now, we'll use a token-based approach
        token_url = f"{self.base_url}/identity/v1/oauth2/token"

        # In production, this would exchange auth_code for access_token
        # For now, we'll assume token is provided via environment variable
        self.access_token = os.getenv('EBAY_ACCESS_TOKEN')

        return self.access_token is not None

    def create_listing(self, listing_draft: ListingDraft) -> Dict[str, Any]:
        """
        Create an eBay listing from a draft.

        Args:
            listing_draft: ListingDraft object

        Returns:
            API response with listing details
        """
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")

        # Map to eBay Inventory API format
        inventory_item = self._map_to_ebay_inventory(listing_draft)

        # Create inventory item
        inventory_response = self._create_inventory_item(inventory_item)

        # Create offer
        offer = self._map_to_ebay_offer(listing_draft, inventory_response)
        offer_response = self._create_offer(offer)

        # Publish listing
        publish_response = self._publish_listing(offer_response.get("offerId"))

        return {
            "listing_id": publish_response.get("listingId"),
            "status": "published",
            "url": f"https://www.ebay.com/itm/{publish_response.get('listingId')}"
        }

    def _map_to_ebay_inventory(self, draft: ListingDraft) -> Dict[str, Any]:
        """Map ListingDraft to eBay Inventory API format."""
        return {
            "sku": draft.listing_id,
            "product": {
                "title": draft.title,
                "description": draft.description,
                "aspects": draft.item_specifics,
                "imageUrls": draft.images
            },
            "condition": draft.condition.value,
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": 1
                }
            }
        }

    def _map_to_ebay_offer(self, draft: ListingDraft, inventory_response: Dict) -> Dict[str, Any]:
        """Map ListingDraft to eBay Offer API format."""
        return {
            "sku": draft.listing_id,
            "marketplaceId": "EBAY_US",  # Default to US marketplace
            "format": "FIXED_PRICE",
            "pricingSummary": {
                "price": {
                    "value": str(draft.price),
                    "currency": "USD"
                }
            },
            "categoryId": draft.category_id or "267",  # Default category
            "listingPolicies": {
                "fulfillmentPolicyId": "default",
                "paymentPolicyId": "default",
                "returnPolicyId": "default"
            }
        }

    def _create_inventory_item(self, inventory_item: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update inventory item via eBay Inventory API (PUT)."""
        sku = inventory_item["sku"]
        url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US"
        }

        print(f"DEBUG: Creating inventory item in eBay: {sku}")
        response = requests.put(url, headers=headers, json=inventory_item, timeout=10)

        if response.status_code not in [200, 204]:
            print(f"DEBUG: eBay Inventory Item error: {response.status_code} - {response.text}")
            raise Exception(f"Failed to create inventory item: {response.text}")

        return {"sku": sku, "status": "success"}

    def _create_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Create offer via eBay Inventory API (POST)."""
        url = f"{self.base_url}/sell/inventory/v1/offer"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US"
        }

        print(f"DEBUG: Creating eBay offer for SKU: {offer['sku']}")
        response = requests.post(url, headers=headers, json=offer, timeout=10)

        if response.status_code not in [200, 201]:
            print(f"DEBUG: eBay Offer error: {response.status_code} - {response.text}")
            raise Exception(f"Failed to create offer: {response.text}")

        return response.json()

    def _publish_listing(self, offer_id: str) -> Dict[str, Any]:
        """Publish listing via eBay Inventory API (POST)."""
        url = f"{self.base_url}/sell/inventory/v1/offer/{offer_id}/publish"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Language": "en-US"
        }

        print(f"DEBUG: Publishing eBay offer: {offer_id}")
        response = requests.post(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"DEBUG: eBay Publish error: {response.status_code} - {response.text}")
            raise Exception(f"Failed to publish listing: {response.text}")

        return response.json()

    def send_negotiation_offer(self, ebay_listing_id: str, offer_price: float) -> Dict[str, Any]:
        """Send offer to interested buyers via eBay Negotiation API."""
        if not self.access_token:
            raise ValueError("Not authenticated")

        url = f"{self.base_url}/sell/negotiation/v1/send_offer_to_interested_buyers"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        # We need to find the "interested_buyers" first in a real scenario,
        # but for this endpoint we can attempt to send to all eligible for the listing.
        payload = {
            "offeredItems": [
                {
                    "listingId": ebay_listing_id,
                    "discountPercentage": 0, # Not used since we provide fixed price
                    "price": {
                        "value": str(offer_price),
                        "currency": "USD"
                    }
                }
            ],
            "message": "Special offer for watchers!"
        }

        print(f"DEBUG: Sending eBay offer for listing {ebay_listing_id}: ${offer_price}")
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code not in [200, 201, 204, 207]:
            print(f"DEBUG: eBay Negotiation error: {response.status_code} - {response.text}")
            raise Exception(f"Failed to send offer: {response.text}")

        return response.json() if response.text else {"success": True}

    def get_oauth_url(self, redirect_uri: str, scopes: List[str] = None) -> str:
        """
        Generate eBay OAuth authorization URL.

        Args:
            redirect_uri: Redirect URI after authorization
            scopes: List of OAuth scopes

        Returns:
            OAuth authorization URL
        """
        if scopes is None:
            scopes = [
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
                "https://api.ebay.com/oauth/api_scope/sell.marketing"
            ]

        base_url = "https://auth.sandbox.ebay.com" if self.use_sandbox else "https://auth.ebay.com"

        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes)
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}/oauth2/authorize?{query_string}"
