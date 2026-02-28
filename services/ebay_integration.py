"""
eBay API Integration Layer
Handles OAuth, listing creation, and eBay Sell APIs.
"""

from typing import Dict, Any, Optional, List
import os
import requests
from datetime import datetime
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
        sku = inventory_item.get("sku")
        url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"
        headers = {
            "Authorization": f"Bearer [REDACTED]",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
        print(f"DEBUG: HTTP POST {url} \\nHeaders: {headers} \\nPayload: {inventory_item}")

        # Real headers with actual token
        real_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        response = requests.post(url, headers=real_headers, json=inventory_item)
        response.raise_for_status()

        return {
            "sku": sku,
            "status": "created"
        }

    def _create_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Create offer via eBay Offer API."""
        url = f"{self.base_url}/sell/offer/v1/offer"
        headers = {
            "Authorization": f"Bearer [REDACTED]",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
        print(f"DEBUG: HTTP POST {url} \\nHeaders: {headers} \\nPayload: {offer}")

        real_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        response = requests.post(url, headers=real_headers, json=offer)
        response.raise_for_status()

        return response.json()

    def _publish_listing(self, offer_id: str) -> Dict[str, Any]:
        """Publish listing via eBay Offer API."""
        url = f"{self.base_url}/sell/offer/v1/offer/{offer_id}/publish"
        headers = {
            "Authorization": f"Bearer [REDACTED]",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
        print(f"DEBUG: HTTP POST {url} \\nHeaders: {headers} \\nPayload: <empty>")

        real_headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        response = requests.post(url, headers=real_headers)
        response.raise_for_status()

        return response.json()

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
            try:
                error_msg = e.response.json().get('errors', [{}])[0].get('message', 'Unknown error')
                raise RuntimeError(f"eBay API error fetching listings: {e.response.status_code} - {error_msg}") from e
            except:
                raise RuntimeError(f"eBay API error fetching listings: {e.response.status_code} - [REDACTED]") from e

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

    def get_active_listings(self) -> List[Dict[str, Any]]:
        """
        Fetch active listings (published offers) from eBay.

        Returns:
            List of dictionaries containing listing details
        """
        if not self.access_token:
            # Try to get valid token from token manager
            self.access_token = self.token_manager.get_valid_token()

        if not self.access_token:
            print("Warning: No access token available for eBay API")
            return []

        url = f"{self.base_url}/sell/inventory/v1/offer"
        params = {
            "marketplace_id": "EBAY_US",
            "limit": 100
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 401:
                # Token might have expired, try to refresh once
                if self.refresh_access_token():
                    # Retry with new token
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                return self._parse_ebay_offers(response.json())
            else:
                try:
                    error_msg = response.json().get('errors', [{}])[0].get('message', 'Unknown error')
                    print(f"Error fetching eBay listings: {response.status_code} - {error_msg}")
                except:
                    print(f"Error fetching eBay listings: {response.status_code} - [REDACTED]")
                return []
        except Exception as e:
            print(f"Exception fetching eBay listings: {e}")
            return []

    def _parse_ebay_offers(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse eBay Inventory API offers response into application format."""
        offers = data.get("offers", [])
        active_listings = []

        for offer in offers:
            # Only include published offers (active listings)
            if offer.get("status") == "PUBLISHED":
                title = offer.get("listing", {}).get("title") or offer.get("sku")
                price = float(offer.get("pricingSummary", {}).get("price", {}).get("value", 0))

                active_listings.append({
                    "ebay_listing_id": offer.get("listingId"),
                    "title": title,                   # Original mock field
                    "listing_title": title,           # Frontend expected field
                    "price": price,                   # Original mock field
                    "listing_price": price,           # Frontend expected field
                    "status": "Active",               # Original mock field
                    "listing_status": "active",       # Frontend expected field
                    "submission_timestamp": datetime.now().isoformat(),
                    "image_filename": "",             # Placeholder
                    "views": 0,
                    "watchers": 0
                })
        return active_listings

    def update_listing(self, sku: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing eBay listing.

        Args:
            sku: The SKU of the item to update
            update_data: Dictionary containing fields to update (title, price, description, aspects, images, policies)

        Returns:
            Dictionary with results and warnings
        """
        if not self.access_token:
            self.access_token = self.token_manager.get_valid_token()

        if not self.access_token:
            raise ValueError("No access token available for eBay API")

        results = {"success": True, "warnings": []}

        # 1. Update Inventory Item if product details changed
        inventory_fields = ['title', 'description', 'aspects', 'images', 'condition']
        if any(k in update_data for k in inventory_fields):
            try:
                current_item = self._get_inventory_item(sku)

                # Merge product data
                if 'title' in update_data: current_item["product"]["title"] = update_data['title']
                if 'description' in update_data: current_item["product"]["description"] = update_data['description']

                if 'aspects' in update_data:
                    if "aspects" not in current_item["product"]:
                        current_item["product"]["aspects"] = {}
                    current_item["product"]["aspects"].update(update_data['aspects'])

                if 'images' in update_data: current_item["product"]["imageUrls"] = update_data['images']
                if 'condition' in update_data: current_item["condition"] = update_data['condition']

                # SKU must not be in the body for the PUT
                if "sku" in current_item: del current_item["sku"]

                self._update_inventory_item(sku, current_item)
            except Exception as e:
                results["success"] = False
                results["error"] = f"Inventory update failed: {str(e)}"
                return results

        # 2. Update Offer if price or policies changed
        offer_fields = ['price', 'fulfillmentPolicyId', 'paymentPolicyId', 'returnPolicyId']
        if any(k in update_data for k in offer_fields):
            offer_id = self._get_offer_id_by_sku(sku)
            if not offer_id:
                results["success"] = False
                results["error"] = f"Could not find offer for SKU: {sku}"
                return results

            try:
                current_offer = self._get_offer(offer_id)

                if 'price' in update_data:
                    current_offer["pricingSummary"]["price"] = {
                        "value": str(update_data['price']),
                        "currency": "USD"
                    }

                if any(k in update_data for k in ['fulfillmentPolicyId', 'paymentPolicyId', 'returnPolicyId']):
                    if "listingPolicies" not in current_offer:
                        current_offer["listingPolicies"] = {}

                    if 'fulfillmentPolicyId' in update_data:
                        current_offer['listingPolicies']['fulfillmentPolicyId'] = update_data['fulfillmentPolicyId']
                    if 'paymentPolicyId' in update_data:
                        current_offer['listingPolicies']['paymentPolicyId'] = update_data['paymentPolicyId']
                    if 'returnPolicyId' in update_data:
                        current_offer['listingPolicies']['returnPolicyId'] = update_data['returnPolicyId']

                # Remove read-only fields
                # The Inventory API PUT offer documentation says we need to provide the full offer.
                # Remove fields that the API doesn't accept in the PUT body.
                read_only_fields = ['listingId', 'offerId', 'status']
                body = {k: v for k, v in current_offer.items() if k not in read_only_fields}

                offer_response = self._update_offer(offer_id, body)
                if offer_response and 'warnings' in offer_response:
                    results["warnings"].extend(offer_response['warnings'])
            except Exception as e:
                results["success"] = False
                results["error"] = f"Offer update failed: {str(e)}"
                return results

        return results

    def _get_inventory_item(self, sku: str) -> Dict[str, Any]:
        """Fetch inventory item details."""
        url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def _update_inventory_item(self, sku: str, inventory_item: Dict[str, Any]) -> bool:
        """Update inventory item via eBay Inventory API (PUT)."""
        url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
        response = requests.put(url, headers=headers, json=inventory_item)
        response.raise_for_status()
        return True

    def _get_offer(self, offer_id: str) -> Dict[str, Any]:
        """Fetch offer details."""
        url = f"{self.base_url}/sell/offer/v1/offer/{offer_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    def _update_offer(self, offer_id: str, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Update offer via eBay Offer API (PUT)."""
        url = f"{self.base_url}/sell/offer/v1/offer/{offer_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US"
        }
        response = requests.put(url, headers=headers, json=offer)
        response.raise_for_status()
        return response.json() if response.content else {}

    def _get_offer_id_by_sku(self, sku: str) -> Optional[str]:
        """Get offer ID for a given SKU."""
        url = f"{self.base_url}/sell/inventory/v1/offer"
        params = {"sku": sku, "marketplace_id": "EBAY_US"}
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        offers = data.get("offers", [])
        if offers:
            return offers[0].get("offerId")
        return None
