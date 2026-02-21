"""
eBay API Integration Layer
Handles OAuth, listing creation, and eBay Sell APIs.
"""

from typing import Dict, Any, Optional, List
import os
import requests
from shared.models import ListingDraft, ItemCondition
from services.ebay_token_manager import EBayTokenManager


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
        # Support both naming conventions for environment variables
        self.app_id = app_id or os.getenv('EBAY_APP_ID') or os.getenv('EBAY_CLIENT_ID')
        self.cert_id = cert_id or os.getenv('EBAY_CERT_ID') or os.getenv('EBAY_CLIENT_SECRET')
        self.dev_id = dev_id or os.getenv('EBAY_DEV_ID')
        self.use_sandbox = use_sandbox

        self.base_url = self.SANDBOX_BASE_URL if use_sandbox else self.PRODUCTION_BASE_URL

        # Initialize token manager for persistence and lifecycle handling
        self.token_manager = EBayTokenManager(
            client_id=self.app_id,
            client_secret=self.cert_id,
            use_sandbox=use_sandbox
        )

        # Load initial tokens if available
        self.access_token: Optional[str] = os.getenv('EBAY_ACCESS_TOKEN')
        self.refresh_token: Optional[str] = os.getenv('EBAY_REFRESH_TOKEN')

    def authenticate(self, auth_code: str, redirect_uri: str) -> bool:
        """
        Authenticate with eBay using OAuth 2.0 authorization code.

        Args:
            auth_code: Authorization code from OAuth callback
            redirect_uri: Redirect URI used in OAuth flow

        Returns:
            True if authentication successful
        """
        token_data = self.token_manager.exchange_code_for_token(auth_code, redirect_uri)
        if token_data:
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            return True
        return False

    def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.

        Returns:
            True if refresh successful
        """
        # The token manager handles the refresh logic internally using stored refresh token
        token_data = self.token_manager._refresh_token()
        if token_data:
            self.access_token = token_data.get("access_token")
            if token_data.get("refresh_token"):
                self.refresh_token = token_data.get("refresh_token")
            return True
        return False

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
        """Create inventory item via eBay Inventory API."""
        url = f"{self.base_url}/sell/inventory/v1/inventory_item"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        # Placeholder - would make actual API call
        return {
            "sku": inventory_item["sku"],
            "status": "created"
        }

    def _create_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Create offer via eBay Offer API."""
        url = f"{self.base_url}/sell/offer/v1/offer"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        # Placeholder - would make actual API call
        return {
            "offerId": f"offer_{offer['sku']}",
            "status": "created"
        }

    def _publish_listing(self, offer_id: str) -> Dict[str, Any]:
        """Publish listing via eBay Offer API."""
        url = f"{self.base_url}/sell/offer/v1/offer/{offer_id}/publish"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        # Placeholder - would make actual API call
        return {
            "listingId": f"listing_{offer_id}",
            "status": "published"
        }

    def get_active_listings(self) -> List[Dict[str, Any]]:
        """
        Fetch active listings from the eBay seller account.

        Returns:
            List of active listing dicts with basic details.
        """
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")

        url = f"{self.base_url}/sell/inventory/v1/inventory_item"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        try:
            response = requests.get(url, headers=headers, params={"limit": 200})
            response.raise_for_status()
            data = response.json()
            items = data.get("inventoryItems", [])
            return [
                {
                    "sku": item.get("sku"),
                    "title": item.get("product", {}).get("title"),
                    "condition": item.get("condition"),
                    "quantity": item.get("availability", {})
                              .get("shipToLocationAvailability", {})
                              .get("quantity")
                }
                for item in items
            ]
        except requests.HTTPError as e:
            raise RuntimeError(f"eBay API error fetching listings: {e.response.text}") from e

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
                "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly"
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
