import logging
logger = logging.getLogger(__name__)

from typing import Dict, Any, Optional
import requests
import os
from shared.models import ItemValuation, Profitability

class ValuationService:
    """Optional Browse API asking-price comparison, never sold-price history."""

    # Use Production API base for Browse API (OAuth typically scoped here or sandbox)
    BROWSE_API_URL = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"

    def __init__(self, use_sandbox: bool = True):
        self.use_sandbox = use_sandbox
        self.offline = os.getenv('LOCAL_DRAFT_MODE') == '1'
        self.base_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search" if use_sandbox else "https://api.ebay.com/buy/browse/v1/item_summary/search"
        from services.ebay_token_manager import EBayTokenManager
        self.token_manager = EBayTokenManager(use_sandbox=self.use_sandbox)

        # Performance optimization: reuse TCP connections via a Session
        self.session = requests.Session()

        # Increase the connection pool size if this service is used concurrently (e.g. ThreadPoolExecutor)
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get_access_token(self) -> Optional[str]:
        # Utilizing the TokenManager or env vars directly as per setup
        # For this service, we assume the environment has an active token, or we pull from token manager
        return self.token_manager.get_valid_token()

    def evaluate_item(self, image_base64: str, content_type: str, item_data: Dict[str, Any]) -> ItemValuation:
        """
        Compare visible fixed-price asking prices when the Browse API is available.
        A missing token, failed request or empty result leaves pricing unavailable.
        """
        # Formulate search query from item data
        brand = item_data.get("brand", "")
        item_name = item_data.get("item_name", "Unknown Item")
        # Ensure we have a valid keyword
        keywords = f"{brand} {item_name}".strip()

        estimated_value = None

        token = None if self.offline else self._get_access_token()
        if token and keywords:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
            }
            # Browse item summaries are current offers, not completed sales.
            params = {
                "q": keywords,
                "limit": "10",
                "filter": "buyingOptions:{FIXED_PRICE}"
            }
            try:
                response = self.session.get(self.base_url, headers=headers, params=params, timeout=10)
                logger.debug(f"DEBUG VALUATION: [{response.status_code}]")
                if response.status_code == 200:
                    data = response.json()
                    summaries = data.get("itemSummaries", [])
                    logger.debug(f"DEBUG VALUATION: Found {len(summaries)} summaries for '{keywords}'")
                    if summaries:
                        total_price = 0.0
                        count = 0
                        for item in summaries:
                            price_val = item.get("price", {}).get("value")
                            try:
                                price = float(price_val)
                                if price > 0:
                                    total_price += price
                                    count += 1
                            except (TypeError, ValueError):
                                continue
                        if count > 0:
                            estimated_value = round((total_price / count), 2)
                            logger.debug("Calculated mean asking price for %s", keywords)
            except Exception as e:
                logger.exception("Valuation exception")

        available = estimated_value is not None
        profitability = self._determine_profitability(estimated_value) if available else Profitability.NOT_RECOMMENDED

        return ItemValuation(
            item_id=item_data.get("item_id", "unknown"),
            item_name=item_name,
            brand=item_data.get("brand"),
            estimated_value=estimated_value,
            estimated_age=None,
            is_complete=True,
            value_range={},  # Browse results do not establish a defensible resale range.
            condition_score=7,
            profitability=profitability,
            resale_score=0,
            recommended_platforms=[],
            confidence=0.0,
            worth_listing=available and estimated_value > 10.0,
            key_factors=["Mean of current fixed-price asking prices; not sold-price history"] if available else [],
            risks=[],
            listing_tips=[],
            condition_notes="Condition not assessed from market data",
            source="live" if token else "simulated",
            status="available" if available else "unavailable"
        )

    def _determine_profitability(self, value: float) -> Profitability:
        if value < 15.0:
            return Profitability.LOW
        elif value < 50.0:
            return Profitability.MEDIUM
        else:
            return Profitability.HIGH
