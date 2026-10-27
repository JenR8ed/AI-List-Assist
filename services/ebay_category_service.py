"""
eBay Category Specifics Service
Handles category-specific item aspects and mapping from AI valuation
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from services.ebay_token_manager import EBayTokenManager

logger = logging.getLogger(__name__)


class EBayCategoryService:
    """Service for handling eBay category-specific item aspects."""

    def __init__(self, access_token: Optional[str] = None, category_tree_id: Optional[str] = None, use_sandbox: bool = True):
        self.use_sandbox = use_sandbox
        self.token_manager = EBayTokenManager(use_sandbox=use_sandbox)
        # Avoid blocking network calls in __init__; token is refreshed on demand in get_category_aspects()
        self.access_token = access_token or os.getenv("EBAY_ACCESS_TOKEN") or "sandbox_token"
        self.cache = {}
        self.cache_expiry = {}

        if self.use_sandbox:
            self.base_url = "https://api.sandbox.ebay.com/commerce/taxonomy/v1/category_tree"
        else:
            self.base_url = "https://api.ebay.com/commerce/taxonomy/v1/category_tree"

        self.category_tree_id = category_tree_id or os.getenv("EBAY_CATEGORY_TREE_ID", "0")

        # Mock data for testing when API unavailable
        self.mock_aspects = {
            "293": {  # Electronics
                "required": [
                    {"name": "Brand", "mode": "FREETEXT", "values": []},
                    {"name": "Type", "mode": "SELECT", "values": ["Headphones", "Speakers", "Phone", "Computer"]},
                ],
                "recommended": [
                    {"name": "Color", "mode": "FREETEXT", "values": []},
                    {"name": "Features", "mode": "FREETEXT", "values": []},
                ],
            },
            "1059": {  # Men's Clothing
                "required": [
                    {"name": "Size", "mode": "SELECT", "values": ["S", "M", "L", "XL", "XXL"]},
                    {"name": "Brand", "mode": "FREETEXT", "values": []},
                ],
                "recommended": [
                    {"name": "Color", "mode": "FREETEXT", "values": []},
                    {"name": "Material", "mode": "FREETEXT", "values": []},
                ],
            },
            "20081": {  # Collectibles
                "required": [
                    {"name": "Type", "mode": "SELECT", "values": ["Vintage", "Antique", "Modern"]},
                    {"name": "Era", "mode": "SELECT", "values": ["1970s", "1980s", "1990s", "2000s"]},
                ],
                "recommended": [
                    {"name": "Brand", "mode": "FREETEXT", "values": []},
                ],
            },
        }

    def get_category_aspects(self, category_id: str) -> Dict:
        """Get required and recommended aspects for a category."""
        # Check cache
        if category_id in self.cache:
            if datetime.now() < self.cache_expiry.get(category_id, datetime.now()):
                logger.info(f"Using cached aspects for category {category_id}")
                return self.cache[category_id]

        # Refresh token if needed
        self.access_token = self.token_manager.get_valid_token() or self.access_token or "sandbox_token"

        # Try real API first, fallback to mock
        try:
            if self.access_token and self.access_token != "sandbox_token":
                aspects = self._fetch_from_api(category_id)
            else:
                logger.warning(f"No valid token, using mock data for category {category_id}")
                aspects = self._get_mock_aspects(category_id)
        except Exception:
            logger.warning("API failed, using mock data", exc_info=True)
            aspects = self._get_mock_aspects(category_id)

        # Cache for 24 hours
        self.cache[category_id] = aspects
        self.cache_expiry[category_id] = datetime.now() + timedelta(hours=24)

        return aspects

    def _fetch_from_api(self, category_id: str) -> Dict:
        """Fetch aspects from eBay Taxonomy API."""
        url = f"{self.base_url}/{self.category_tree_id}/get_item_aspects_for_category"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        params = {"category_id": category_id}

        logger.info(f"Fetching aspects for category {category_id} from eBay API...")
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 401:
            logger.warning("eBay API authentication failed, using mock data")
            raise RuntimeError("Authentication failed")

        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched {len(data.get('aspects', []))} aspects")

        return self._organize_aspects(data.get("aspects", []))

    def _get_mock_aspects(self, category_id: str) -> Dict:
        """Get mock aspects for testing."""
        return self.mock_aspects.get(
            category_id,
            {
                "required": [{"name": "Brand", "mode": "FREETEXT", "values": []}],
                "recommended": [],
            },
        )

    def _organize_aspects(self, aspects: List[Dict]) -> Dict:
        """Organize aspects by requirement level."""
        organized = {"required": [], "recommended": []}

        for aspect in aspects:
            aspect_info = {
                "name": aspect.get("localizedAspectName"),
                "mode": aspect.get("aspectConstraint", {}).get("aspectMode", "FREETEXT"),
                "values": [],
            }

            # Extract allowed values for SELECT mode
            if aspect_info["mode"] == "SELECT":
                constraint = aspect.get("aspectConstraint", {})
                aspect_info["values"] = [
                    v.get("localizedValue")
                    for v in constraint.get("aspectValues", [])
                ]

            # Categorize by requirement
            if aspect.get("required"):
                organized["required"].append(aspect_info)
            else:
                organized["recommended"].append(aspect_info)

        return organized

    def map_valuation_to_aspects(self, valuation: Dict, category_id: str) -> Dict:
        """Map AI valuation to category-specific aspects."""
        aspects_def = self.get_category_aspects(category_id)
        mapped = {}

        for aspect in aspects_def.get("required", []) + aspects_def.get("recommended", []):
            name = aspect["name"]
            value = self._map_single_aspect(name, valuation)
            if value:
                mapped[name] = value

        return mapped

    def _map_single_aspect(self, name: str, valuation: Dict) -> Optional[str]:
        """Map a single aspect name to a value from valuation."""
        name_lower = name.lower()

        if "brand" in name_lower:
            return valuation.get("brand")
        elif "type" in name_lower or "category" in name_lower:
            return valuation.get("probable_category") or valuation.get("item_name")
        elif "era" in name_lower or "age" in name_lower:
            age = valuation.get("estimated_age") or ""
            if "1980" in age or "80s" in age:
                return "1980s"
            elif "1990" in age or "90s" in age:
                return "1990s"
            elif "vintage" in age.lower():
                return "1970s"
            return None
        elif "color" in name_lower:
            factors = valuation.get("key_factors") or []
            colors = ["black", "white", "red", "blue", "green", "silver", "gold"]
            for factor in factors:
                for color in colors:
                    if color in factor.lower():
                        return color.title()
            return None
        elif "features" in name_lower:
            factors = valuation.get("key_factors") or []
            return ", ".join(factors[:3]) if factors else None

        return None

    def validate_aspects(self, aspects: Dict, category_id: str) -> Dict:
        """Validate aspects against category requirements."""
        aspects_def = self.get_category_aspects(category_id)
        validated = {}
        errors = []

        # Check required aspects
        for aspect in aspects_def.get("required", []):
            name = aspect["name"]
            value = aspects.get(name)

            if not value:
                errors.append(f"Required aspect '{name}' is missing")
                continue

            # Validate SELECT mode values
            if aspect["mode"] == "SELECT" and aspect["values"]:
                if value not in aspect["values"]:
                    # Try case-insensitive match
                    matched = False
                    for allowed in aspect["values"]:
                        if allowed.lower() == str(value).lower():
                            validated[name] = allowed
                            matched = True
                            break

                    if not matched:
                        errors.append(f"Invalid value '{value}' for {name}. Allowed: {aspect['values'][:3]}")
                        validated[name] = aspect["values"][0]  # Use first as fallback
                else:
                    validated[name] = value
            else:
                validated[name] = value

        # Add recommended aspects
        for aspect in aspects_def.get("recommended", []):
            name = aspect["name"]
            if name in aspects:
                validated[name] = aspects[name]

        return {"aspects": validated, "errors": errors}
