"""
eBay API Integration Layer
Handles OAuth, listing creation, Account API business policy lookup,
aspect normalization (Dict[str, List[str]] <= 65 chars), and condition enum mapping.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
import os
from typing import Any, Dict, List, Optional, Union
import requests
from shared.models import ItemCondition, ListingDraft
from services.ebay_token_manager import EBayTokenManager

logger = logging.getLogger(__name__)


INVENTORY_CONDITION_ENUM_MAP: Dict[str, str] = {
    "New": "NEW",
    "NEW": "NEW",
    "New other (see details)": "NEW_OTHER",
    "NEW_OTHER": "NEW_OTHER",
    "New with defects": "NEW_WITH_DEFECTS",
    "NEW_WITH_DEFECTS": "NEW_WITH_DEFECTS",
    "Manufacturer refurbished": "CERTIFIED_REFURBISHED",
    "MANUFACTURER_REFURBISHED": "CERTIFIED_REFURBISHED",
    "CERTIFIED_REFURBISHED": "CERTIFIED_REFURBISHED",
    "Seller refurbished": "SELLER_REFURBISHED",
    "SELLER_REFURBISHED": "SELLER_REFURBISHED",
    "Used": "USED_EXCELLENT",
    "USED": "USED_EXCELLENT",
    "USED_EXCELLENT": "USED_EXCELLENT",
    "USED_GOOD": "USED_GOOD",
    "USED_ACCEPTABLE": "USED_ACCEPTABLE",
    "For parts or not working": "FOR_PARTS_OR_NOT_WORKING",
    "FOR_PARTS": "FOR_PARTS_OR_NOT_WORKING",
    "FOR_PARTS_OR_NOT_WORKING": "FOR_PARTS_OR_NOT_WORKING",
}


class eBayIntegration:
    """Integration layer for eBay Sell APIs."""

    SANDBOX_BASE_URL = "https://api.sandbox.ebay.com"
    PRODUCTION_BASE_URL = "https://api.ebay.com"

    def __init__(
        self,
        app_id: Optional[str] = None,
        cert_id: Optional[str] = None,
        dev_id: Optional[str] = None,
        use_sandbox: bool = True,
    ):
        self.app_id = app_id or os.getenv("EBAY_APP_ID") or os.getenv("EBAY_CLIENT_ID")
        self.cert_id = cert_id or os.getenv("EBAY_CERT_ID") or os.getenv("EBAY_CLIENT_SECRET")
        self.dev_id = dev_id or os.getenv("EBAY_DEV_ID")
        self.use_sandbox = use_sandbox

        self.base_url = self.SANDBOX_BASE_URL if use_sandbox else self.PRODUCTION_BASE_URL

        self.token_manager = EBayTokenManager(
            client_id=self.app_id,
            client_secret=self.cert_id,
            use_sandbox=use_sandbox,
        )

        self.access_token: Optional[str] = os.getenv("EBAY_ACCESS_TOKEN")
        self.refresh_token: Optional[str] = os.getenv("EBAY_REFRESH_TOKEN")
        self._policy_cache: Dict[str, Dict[str, str]] = {}

    def _get_headers(self) -> Dict[str, str]:
        token = self.token_manager.get_user_token() or self.token_manager.get_valid_token() or self.access_token
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Content-Language": "en-US",
        }

    def _normalize_aspects(self, item_specifics: Dict[str, Union[str, List[str]]]) -> Dict[str, List[str]]:
        """Normalize aspects to Dict[str, List[str]] with values truncated to 65 chars."""
        normalized: Dict[str, List[str]] = {}
        for key, value in (item_specifics or {}).items():
            if isinstance(value, list):
                normalized[key] = [str(v)[:65] for v in value if v]
            elif value is not None:
                normalized[key] = [str(value)[:65]]
        return normalized

    def _map_condition(self, condition: Union[ItemCondition, str]) -> str:
        if isinstance(condition, ItemCondition):
            condition = condition.value
        return INVENTORY_CONDITION_ENUM_MAP.get(str(condition), "USED_EXCELLENT")

    def create_inventory_item(self, draft: ListingDraft, sku: Optional[str] = None) -> Dict[str, Any]:
        """Create or replace an inventory item from a ListingDraft."""
        sku = sku or draft.listing_id or draft.item_id
        url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"

        payload = {
            "availability": {"shipToLocationAvailability": {"quantity": 1}},
            "condition": self._map_condition(draft.condition),
            "product": {
                "title": draft.title[:80],
                "description": draft.description,
                "aspects": self._normalize_aspects(draft.item_specifics),
                "imageUrls": draft.images[:12] if draft.images else [],
            },
        }

        resp = requests.put(url, headers=self._get_headers(), json=payload, timeout=30)
        if resp.status_code not in (200, 201, 204):
            logger.error(f"create_inventory_item failed: {resp.status_code} {resp.text[:500]}")
            resp.raise_for_status()
        return {"sku": sku, "status": "created"}

    def create_offer(self, sku: str, draft: ListingDraft, category_id: Optional[str] = None) -> Dict[str, Any]:
        """Create an offer for an existing inventory item."""
        url = f"{self.base_url}/sell/inventory/v1/offer"

        policies = self._get_business_policies()

        payload = {
            "sku": sku,
            "marketplaceId": "EBAY_US",
            "format": "FIXED_PRICE",
            "availableQuantity": 1,
            "categoryId": category_id or draft.category_id,
            "listingDescription": draft.description,
            "listingPolicies": {
                "fulfillmentPolicyId": policies.get("fulfillmentPolicyId"),
                "paymentPolicyId": policies.get("paymentPolicyId"),
                "returnPolicyId": policies.get("returnPolicyId"),
            },
            "pricingSummary": {
                "price": {"value": str(draft.price), "currency": "USD"}
            },
        }

        resp = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
        if resp.status_code not in (200, 201):
            logger.error(f"create_offer failed: {resp.status_code} {resp.text[:500]}")
            resp.raise_for_status()
        return resp.json()

    def publish_offer(self, offer_id: str) -> Dict[str, Any]:
        """Publish an offer to make the listing live."""
        url = f"{self.base_url}/sell/inventory/v1/offer/{offer_id}/publish"
        resp = requests.post(url, headers=self._get_headers(), timeout=30)
        if resp.status_code not in (200, 201):
            logger.error(f"publish_offer failed: {resp.status_code} {resp.text[:500]}")
            resp.raise_for_status()
        return resp.json()

    def _get_business_policies(self) -> Dict[str, str]:
        """Fetch or return cached business policy IDs."""
        if self._policy_cache:
            return self._policy_cache

        # Prefer env overrides
        fulfillment = os.getenv("EBAY_FULFILLMENT_POLICY_ID")
        payment = os.getenv("EBAY_PAYMENT_POLICY_ID")
        return_policy = os.getenv("EBAY_RETURN_POLICY_ID")

        if fulfillment and payment and return_policy:
            self._policy_cache = {
                "fulfillmentPolicyId": fulfillment,
                "paymentPolicyId": payment,
                "returnPolicyId": return_policy,
            }
            return self._policy_cache

        # Fallback: attempt Account API lookup
        try:
            url = f"{self.base_url}/sell/account/v1/fulfillment_policy"
            resp = requests.get(url, headers=self._get_headers(), params={"marketplace_id": "EBAY_US"}, timeout=15)
            if resp.status_code == 200:
                policies = resp.json().get("fulfillmentPolicies", [])
                if policies:
                    fulfillment = policies[0].get("fulfillmentPolicyId")
            # Similar for payment / return would go here; keep simple for now
        except Exception as e:
            logger.warning(f"Policy lookup failed: {e}")

        self._policy_cache = {
            "fulfillmentPolicyId": fulfillment or "",
            "paymentPolicyId": payment or "",
            "returnPolicyId": return_policy or "",
        }
        return self._policy_cache

    def get_active_listings(self) -> List[Dict[str, Any]]:
        """Fetch active listings by joining offers + inventory items."""
        try:
            headers = self._get_headers()
            offers_url = f"{self.base_url}/sell/inventory/v1/offer"
            resp = requests.get(offers_url, headers=headers, params={"limit": 100}, timeout=30)
            if resp.status_code != 200:
                logger.warning(f"Failed to fetch offers: {resp.status_code}")
                return []

            data = resp.json()
            offers = data.get("offers", [])
            published_offers = [o for o in offers if o.get("status") == "PUBLISHED"]

            inventory_map: Dict[str, Dict] = {}
            inventory_url = f"{self.base_url}/sell/inventory/v1/inventory_item"

            # First page
            inv_resp = requests.get(inventory_url, headers=headers, params={"limit": 100}, timeout=30)
            if inv_resp.status_code == 200:
                inv_data = inv_resp.json()
                for item in inv_data.get("inventoryItems", []):
                    inventory_map[item.get("sku")] = item

                total = inv_data.get("total", 0)
                if total > 100:
                    def fetch_inventory_page(offset: int):
                        try:
                            r = requests.get(inventory_url, headers=headers, params={"limit": 100, "offset": offset}, timeout=30)
                            if r.status_code == 200:
                                return r.json().get("inventoryItems", [])
                        except Exception as e:
                            logger.error(f"Error fetching inventory page at offset {offset}: {e}")
                        return []

                    offsets = range(100, total, 100)
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = {executor.submit(fetch_inventory_page, off): off for off in offsets}
                        for future in as_completed(futures):
                            for item in future.result():
                                inventory_map[item.get("sku")] = item

            return self._join_offer_inventory(published_offers, inventory_map)

        except Exception as e:
            logger.exception(f"Exception fetching eBay listings: {e}")
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
                "watchers": 0,
            })
        return active_listings
