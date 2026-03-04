"""
eBay API Integration Layer
Handles OAuth, listing creation, and eBay Sell APIs.
"""

import logging
from typing import Dict, Any, Optional, List
import os
import requests
from datetime import datetime
from shared.models import ListingDraft, ItemCondition
from services.ebay_token_manager import EBayTokenManager

logger = logging.getLogger(__name__)

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
        """Create or update inventory item via eBay Inventory API (PUT)."""
        sku = inventory_item.get("sku")
        if not sku:
            raise ValueError("Inventory item must have a SKU")

        url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"
        headers = self._get_headers()

        try:
            response = requests.put(url, headers=headers, json=inventory_item)
            if response.status_code in [200, 201, 204]:
                return {
                    "sku": sku,
                    "status": "created"
                }
            else:
                self._handle_api_error(response, "create_inventory_item")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error creating inventory item: {str(e)}") from e

    def _get_headers(self) -> Dict[str, str]:
        """Helper to get standard eBay API headers, ensuring token is fresh."""
        self.access_token = self.token_manager.get_valid_token()

        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

    def _handle_api_error(self, response: requests.Response, context: str):
        """Handle eBay API errors with granular parsing."""
        try:
            error_data = response.json()
            errors = error_data.get('errors', [])
            if errors:
                main_error = errors[0]
                error_msg = main_error.get('message', 'Unknown error')
                error_id = main_error.get('errorId', 'Unknown ID')
                full_msg = f"eBay API error in {context}: {response.status_code} - {error_msg} (Error ID: {error_id})"
                logger.error(full_msg)
                raise RuntimeError(full_msg)
            else:
                raise RuntimeError(f"eBay API error in {context}: {response.status_code} - [REDACTED]")
        except (ValueError, KeyError):
            raise RuntimeError(f"eBay API error in {context}: {response.status_code} - [REDACTED]")

    def _create_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Create offer via eBay Offer API."""
        url = f"{self.base_url}/sell/offer/v1/offer"
        headers = self._get_headers()

        try:
            response = requests.post(url, headers=headers, json=offer)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                self._handle_api_error(response, "create_offer")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error creating offer: {str(e)}") from e

    def _publish_listing(self, offer_id: str) -> Dict[str, Any]:
        """Publish listing via eBay Offer API."""
        url = f"{self.base_url}/sell/offer/v1/offer/{offer_id}/publish"
        headers = self._get_headers()

        try:
            response = requests.post(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                self._handle_api_error(response, "publish_listing")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error publishing listing: {str(e)}") from e

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

    def end_listing(self, sku: str) -> Dict[str, Any]:
        """
        End an active eBay listing by withdrawing its offer.
        """
        headers = self._get_headers()
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")

        # 1. Get offers for the SKU
        offer_url = f"{self.base_url}/sell/inventory/v1/offer"
        params = {"sku": sku}

        try:
            offer_response = requests.get(offer_url, headers=headers, params=params)

            if offer_response.status_code == 401:
                if self.refresh_access_token():
                    headers = self._get_headers()
                    offer_response = requests.get(offer_url, headers=headers, params=params)

            if offer_response.status_code != 200:
                self._handle_api_error(offer_response, "end_listing_get_offers")

            offers_data = offer_response.json()
            offers = offers_data.get("offers", [])

            # Find the published offer
            published_offer = next((o for o in offers if o.get("status") == "PUBLISHED"), None)

            if not published_offer:
                raise RuntimeError(f"No published offer found for SKU {sku}")

            offer_id = published_offer.get("offerId")

            # 2. Withdraw the offer
            withdraw_url = f"{self.base_url}/sell/inventory/v1/offer/{offer_id}/withdraw"
            withdraw_response = requests.post(withdraw_url, headers=headers)

            if withdraw_response.status_code == 200:
                return withdraw_response.json()
            else:
                self._handle_api_error(withdraw_response, "end_listing_withdraw")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error ending listing: {str(e)}") from e

    def get_active_listings(self) -> List[Dict[str, Any]]:
        """
        Fetch active listings (published offers) from eBay, joined with inventory data.
        Handles pagination for both offers and inventory items.

        Returns:
            List of dictionaries containing listing details
        """
        headers = self._get_headers()
        if not headers.get("Authorization"):
            logger.warning("No access token available for eBay API")
            return []

        # 1. Fetch Offers (Active Listings) with Pagination
        published_offers = []
        offer_url = f"{self.base_url}/sell/inventory/v1/offer"
        offer_params = {"marketplace_id": "EBAY_US", "limit": 100}

        try:
            next_url = offer_url
            params = offer_params
            while next_url:
                offer_response = requests.get(next_url, headers=headers, params=params)
                if offer_response.status_code == 401:
                    if self.refresh_access_token():
                        headers = self._get_headers()
                        offer_response = requests.get(next_url, headers=headers, params=params)

                if offer_response.status_code != 200:
                    self._handle_api_error(offer_response, "get_active_listings_offers")
                    break

                offers_data = offer_response.json()
                published_offers.extend([o for o in offers_data.get("offers", []) if o.get("status") == "PUBLISHED"])

                next_url = offers_data.get("next")
                params = None  # Subsequent calls use full URL from 'next'

            if not published_offers:
                return []

            # 2. Fetch Inventory Items with Pagination to get images/details
            inventory_map = {}
            inventory_url = f"{self.base_url}/sell/inventory/v1/inventory_item"
            inventory_params = {"limit": 100}

            next_inv_url = inventory_url
            inv_params = inventory_params
            while next_inv_url:
                inventory_response = requests.get(next_inv_url, headers=headers, params=inv_params)
                if inventory_response.status_code == 200:
                    inv_data = inventory_response.json()
                    for item in inv_data.get("inventoryItems", []):
                        inventory_map[item.get("sku")] = item
                    next_inv_url = inv_data.get("next")
                    inv_params = None
                else:
                    logger.warning(f"Failed to fetch inventory page: {inventory_response.status_code}")
                    break

            # 3. Join and Map
            return self._join_offer_inventory(published_offers, inventory_map)

        except Exception as e:
            logger.exception(f"Exception fetching eBay listings: {str(e)}")
            return []

    def _join_offer_inventory(self, offers: List[Dict], inventory_map: Dict) -> List[Dict[str, Any]]:
        """Join offer data with inventory item data."""
        active_listings = []

        for offer in offers:
            sku = offer.get("sku")
            inventory_item = inventory_map.get(sku, {})
            product = inventory_item.get("product", {})
            image_urls = product.get("imageUrls", [])
            image_filename = image_urls[0] if image_urls else ""

            title = offer.get("listing", {}).get("title") or product.get("title") or sku
            price = float(offer.get("pricingSummary", {}).get("price", {}).get("value", 0))

            active_listings.append({
                "ebay_listing_id": offer.get("listingId"),
                "sku": sku,
                "title": title,
                "listing_title": title,
                "price": price,
                "listing_price": price,
                "status": "Active",
                "listing_status": "active",
                "submission_timestamp": datetime.now().isoformat(),
                "image_filename": image_filename,
                "views": 0,
                "watchers": 0
            })
        return active_listings
