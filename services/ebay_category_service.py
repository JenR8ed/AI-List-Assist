"""
eBay Category Specifics Service
Handles category-specific item aspects and mapping from AI valuation
"""

import requests
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from services.ebay_token_manager import EBayTokenManager

class EBayCategoryService:
    """Service for handling eBay category-specific item aspects."""
    
    def __init__(self, access_token: Optional[str] = None):
        self.token_manager = EBayTokenManager()
        self.access_token = access_token or self.token_manager.get_valid_token() or "sandbox_token"
        self.cache = {}
        self.cache_expiry = {}
        self.base_url = "https://api.ebay.com/commerce/taxonomy/v1/category_tree"
        self.category_tree_id = "100"  # US marketplace
        
        # Mock data for testing when API unavailable
        self.mock_aspects = {
            "293": {  # Electronics
                "required": [
                    {"name": "Brand", "mode": "FREETEXT", "values": []},
                    {"name": "Type", "mode": "SELECT", "values": ["Headphones", "Speakers", "Phone", "Computer"]}
                ],
                "recommended": [
                    {"name": "Color", "mode": "FREETEXT", "values": []},
                    {"name": "Features", "mode": "FREETEXT", "values": []}
                ]
            },
            "1059": {  # Men's Clothing
                "required": [
                    {"name": "Size", "mode": "SELECT", "values": ["S", "M", "L", "XL", "XXL"]},
                    {"name": "Brand", "mode": "FREETEXT", "values": []}
                ],
                "recommended": [
                    {"name": "Color", "mode": "FREETEXT", "values": []},
                    {"name": "Material", "mode": "FREETEXT", "values": []}
                ]
            },
            "20081": {  # Collectibles
                "required": [
                    {"name": "Type", "mode": "SELECT", "values": ["Vintage", "Antique", "Modern"]},
                    {"name": "Era", "mode": "SELECT", "values": ["1950s", "1960s", "1970s", "1980s", "1990s"]}
                ],
                "recommended": [
                    {"name": "Brand", "mode": "FREETEXT", "values": []},
                    {"name": "Features", "mode": "FREETEXT", "values": []}
                ]
            }
        }
    
    def get_category_aspects(self, category_id: str) -> Dict:
        """Get item aspects for a category with caching."""
        
        # Check cache first
        if category_id in self.cache:
            if datetime.now() < self.cache_expiry.get(category_id, datetime.now()):
                print(f"Using cached aspects for category {category_id}")
                return self.cache[category_id]
        
        # Refresh token if needed
        self.access_token = self.token_manager.get_valid_token() or "sandbox_token"
        
        # Try real API first, fallback to mock
        try:
            if self.access_token and self.access_token != "sandbox_token":
                aspects = self._fetch_from_api(category_id)
            else:
                print(f"No valid token, using mock data for category {category_id}")
                aspects = self._get_mock_aspects(category_id)
        except Exception as e:
            print(f"API failed ({e}), using mock data")
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
            "Content-Type": "application/json"
        }
        params = {"category_id": category_id}
        
        print(f"Fetching aspects for category {category_id} from eBay API...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 401:
            print("eBay API authentication failed, using mock data")
            raise Exception("Authentication failed")
        
        response.raise_for_status()
        data = response.json()
        print(f"Successfully fetched {len(data.get('aspects', []))} aspects")
        
        return self._organize_aspects(data.get("aspects", []))
    
    def _get_mock_aspects(self, category_id: str) -> Dict:
        """Get mock aspects for testing."""
        return self.mock_aspects.get(category_id, {
            "required": [{"name": "Brand", "mode": "FREETEXT", "values": []}],
            "recommended": []
        })
    
    def _organize_aspects(self, aspects: List[Dict]) -> Dict:
        """Organize aspects by requirement level."""
        organized = {"required": [], "recommended": []}
        
        for aspect in aspects:
            aspect_info = {
                "name": aspect.get("localizedAspectName"),
                "mode": aspect.get("aspectConstraint", {}).get("aspectMode", "FREETEXT"),
                "values": []
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
        mapped_aspects = {}
        
        # Map required aspects
        for aspect in aspects_def.get("required", []):
            value = self._map_aspect_value(aspect["name"], valuation, aspect)
            if value:
                mapped_aspects[aspect["name"]] = value
        
        # Map recommended aspects if data available
        for aspect in aspects_def.get("recommended", []):
            value = self._map_aspect_value(aspect["name"], valuation, aspect)
            if value:
                mapped_aspects[aspect["name"]] = value
        
        return mapped_aspects
    
    def _map_aspect_value(self, aspect_name: str, valuation: Dict, aspect_def: Dict) -> Optional[str]:
        """Map a single aspect from valuation data."""
        
        name_lower = aspect_name.lower()
        
        # Brand mapping
        if "brand" in name_lower:
            return valuation.get("brand")
        
        # Type mapping
        elif "type" in name_lower:
            item_name = valuation.get("item_name", "")
            if "headphones" in item_name.lower():
                return "Headphones"
            elif "phone" in item_name.lower():
                return "Phone"
            else:
                return item_name.split()[0] if item_name else None
        
        # Condition mapping
        elif "condition" in name_lower:
            score = valuation.get("condition_score", 5)
            condition_map = {10: "New", 9: "Like New", 8: "Excellent", 7: "Good", 6: "Fair", 5: "Poor"}
            return condition_map.get(score, "Good")
        
        # Size mapping (for clothing)
        elif "size" in name_lower:
            factors = valuation.get("key_factors", [])
            for factor in factors:
                if any(s in factor.lower() for s in ["small", "medium", "large", "xl"]):
                    return factor.title()
            return "M"  # Default
        
        # Era/Year mapping
        elif any(x in name_lower for x in ["era", "year"]):
            age = valuation.get("estimated_age", "")
            if "1980" in age or "80s" in age:
                return "1980s"
            elif "1990" in age or "90s" in age:
                return "1990s"
            elif "vintage" in age.lower():
                return "1970s"
            return None
        
        # Color mapping
        elif "color" in name_lower:
            factors = valuation.get("key_factors", [])
            colors = ["black", "white", "red", "blue", "green", "silver", "gold"]
            for factor in factors:
                for color in colors:
                    if color in factor.lower():
                        return color.title()
            return None
        
        # Features mapping
        elif "features" in name_lower:
            factors = valuation.get("key_factors", [])
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
                        if allowed.lower() == value.lower():
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