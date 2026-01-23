# Handling eBay Item Specifics by Category

## 🎯 The Core Challenge

**The Problem:**
Each eBay category has **different required, recommended, and optional item specifics** (also called "aspects").

```
Vintage BB Gun (Category 12576)
├─ Type (required)
├─ Brand (required)
├─ Condition (required)
├─ Features (optional)
└─ Year (optional)

Doll Clothes (Category 26568)
├─ Size (required)
├─ Material (required)
├─ Color (optional)
├─ Doll Type (optional)
└─ Features (optional)

Auto Parts (Category 6024)
├─ Make (required)
├─ Model (required)
├─ Year (required)
├─ Fitment Type (required)
└─ Engine Type (optional)
```

**Your Challenge:** You need to detect the category, get the correct specifics, fill them in from your AI valuation, and send to eBay.

---

## 📊 Understanding the Three Levels

### 1. **Required Item Specifics**
- ✅ **MUST be provided** for listing to be published
- Category-specific (different for each category)
- Buyers use these to filter search results
- Examples: "Brand", "Type", "Make", "Model", "Year"

### 2. **Recommended Item Specifics**
- ⭐ **Should be provided** (improves searchability)
- Helps buyers find your listing
- Not required but strongly encouraged
- Examples: "Features", "Color", "Size", "Condition"

### 3. **Optional Item Specifics**
- ℹ️ **Nice to have** (improves listing quality)
- Adds detail without being required
- Examples: "Style", "Grade", "Era", "Authenticity"

---

## 🔍 Step 1: Get Category-Specific Item Specifics

### Using the Taxonomy API

**Endpoint:**
```
GET https://api.ebay.com/commerce/taxonomy/v1/category_tree/{category_tree_id}/get_item_aspects_for_category?category_id={categoryId}
```

**Category Tree IDs:**
- `100` = eBay US
- `3` = eBay UK
- `77` = eBay Germany
- `181` = eBay Italy
- `205` = eBay Spain

**Example Request:**
```bash
curl -X GET "https://api.ebay.com/commerce/taxonomy/v1/category_tree/100/get_item_aspects_for_category?category_id=12576" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response (Vintage Toys Category 12576):**
```json
{
  "aspects": [
    {
      "localizedAspectName": "Type",
      "required": true,
      "aspectConstraint": {
        "aspectDataType": "STRING",
        "aspectMode": "SELECT",
        "aspectValues": [
          {
            "localizedValue": "Action Figure",
            "value": "Action Figure"
          },
          {
            "localizedValue": "Air Gun",
            "value": "Air Gun"
          },
          {
            "localizedValue": "BB Gun",
            "value": "BB Gun"
          }
        ]
      }
    },
    {
      "localizedAspectName": "Brand",
      "required": true,
      "aspectConstraint": {
        "aspectDataType": "STRING",
        "aspectMode": "FREETEXT"
      }
    },
    {
      "localizedAspectName": "Year",
      "required": false,
      "aspectConstraint": {
        "aspectDataType": "STRING",
        "aspectMode": "SELECT",
        "aspectValues": [...]
      }
    }
  ]
}
```

---

## 🐍 Python Implementation

### Step 1: Fetch Category Specifics (Cache This!)

```python
import requests
import json
from typing import Dict, List
from datetime import datetime, timedelta

class EBayCategorySpecifics:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.cache = {}
        self.cache_expiry = {}
        self.base_url = "https://api.ebay.com/commerce/taxonomy/v1/category_tree"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.category_tree_id = "100"  # US marketplace
    
    def get_item_aspects_for_category(self, category_id: str) -> Dict:
        """
        Get all item aspects (required, recommended, optional) for a category.
        Results are cached for 24 hours.
        
        Args:
            category_id: eBay category ID (e.g., "12576")
        
        Returns:
            Dict with required, recommended, optional specifics
        """
        # Check cache
        if category_id in self.cache:
            if datetime.now() < self.cache_expiry.get(category_id, datetime.now()):
                print(f"✅ Using cached data for category {category_id}")
                return self.cache[category_id]
        
        # Fetch from API
        url = f"{self.base_url}/{self.category_tree_id}/get_item_aspects_for_category"
        params = {"category_id": category_id}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Organize by requirement level
            organized = {
                "required": [],
                "recommended": [],
                "optional": []
            }
            
            for aspect in data.get("aspects", []):
                aspect_info = {
                    "name": aspect.get("localizedAspectName"),
                    "dataType": aspect.get("aspectConstraint", {}).get("aspectDataType"),
                    "mode": aspect.get("aspectConstraint", {}).get("aspectMode"),
                    "values": []
                }
                
                # Extract allowed values if SELECT mode
                if aspect.get("aspectConstraint", {}).get("aspectMode") == "SELECT":
                    aspect_info["values"] = [
                        v.get("localizedValue") 
                        for v in aspect.get("aspectConstraint", {}).get("aspectValues", [])
                    ]
                
                # Categorize by requirement
                if aspect.get("required"):
                    organized["required"].append(aspect_info)
                else:
                    # Check if eBay recommends it
                    if aspect.get("recommended"):
                        organized["recommended"].append(aspect_info)
                    else:
                        organized["optional"].append(aspect_info)
            
            # Cache for 24 hours
            self.cache[category_id] = organized
            self.cache_expiry[category_id] = datetime.now() + timedelta(hours=24)
            
            print(f"✅ Fetched aspects for category {category_id}")
            print(f"   Required: {len(organized['required'])}")
            print(f"   Recommended: {len(organized['recommended'])}")
            print(f"   Optional: {len(organized['optional'])}")
            
            return organized
        
        except Exception as e:
            print(f"❌ Error fetching aspects: {e}")
            return {"required": [], "recommended": [], "optional": []}
    
    def display_aspects(self, category_id: str):
        """Pretty print category specifics"""
        aspects = self.get_item_aspects_for_category(category_id)
        
        print(f"\n📋 Item Specifics for Category {category_id}")
        print("="*60)
        
        if aspects.get("required"):
            print("\n✅ REQUIRED:")
            for asp in aspects["required"]:
                print(f"  • {asp['name']} ({asp['dataType']}, {asp['mode']})")
                if asp['values']:
                    print(f"    Allowed values: {', '.join(asp['values'][:5])}")
        
        if aspects.get("recommended"):
            print("\n⭐ RECOMMENDED:")
            for asp in aspects["recommended"]:
                print(f"  • {asp['name']}")
        
        if aspects.get("optional"):
            print("\n ℹ️  OPTIONAL:")
            for asp in aspects["optional"]:
                print(f"  • {asp['name']}")


# Usage
category_api = EBayCategorySpecifics(access_token)
category_api.display_aspects("12576")  # Vintage Toys
```

---

### Step 2: Map AI Valuation to Category Specifics

```python
def map_ai_to_category_specifics(
    valuation: dict,
    category_id: str,
    category_specifics: dict
) -> dict:
    """
    Map AI valuation fields to eBay category-specific item aspects.
    
    Args:
        valuation: AI valuation dict from Gemini
        category_id: eBay category ID
        category_specifics: Dict from get_item_aspects_for_category()
    
    Returns:
        Dict with mapped aspects ready for eBay API
    """
    
    aspects = {}
    
    # Get all required aspects for this category
    all_required = category_specifics.get("required", [])
    
    # Map based on aspect name
    for aspect_def in all_required:
        aspect_name = aspect_def["name"]
        value = None
        
        # Type mappings based on common aspect names
        if aspect_name.lower() in ["type", "item type"]:
            value = valuation.get("item_name", "").split()[0]  # First word
        
        elif aspect_name.lower() == "brand":
            value = valuation.get("brand")
        
        elif aspect_name.lower() == "condition":
            condition_map = {
                10: "New",
                9: "Like New",
                8: "Excellent",
                7: "Good",
                6: "Fair",
                5: "Poor"
            }
            value = condition_map.get(valuation.get("condition_score", 5), "Good")
        
        elif aspect_name.lower() == "year":
            # Extract from estimated_age if available
            age_str = valuation.get("estimated_age", "")
            if "19" in age_str or "20" in age_str:
                # Try to extract year
                import re
                years = re.findall(r"19\d{2}|20\d{2}", age_str)
                if years:
                    value = years[0]
        
        elif aspect_name.lower() in ["color", "colour"]:
            # Could come from key_factors
            factors = valuation.get("key_factors", [])
            for factor in factors:
                if any(c in factor.lower() for c in ["red", "blue", "black", "white", "green"]):
                    value = factor.split()[0]
                    break
        
        elif aspect_name.lower() == "size":
            factors = valuation.get("key_factors", [])
            for factor in factors:
                if any(s in factor.lower() for s in ["large", "medium", "small", "xl", "lg"]):
                    value = factor
                    break
        
        elif aspect_name.lower() in ["features", "material"]:
            # Use key_factors
            factors = valuation.get("key_factors", [])
            if factors:
                value = ", ".join(factors[:3])
        
        # Validate against allowed values if SELECT mode
        if value and aspect_def.get("mode") == "SELECT" and aspect_def.get("values"):
            allowed = aspect_def["values"]
            # Try exact match
            if value not in allowed:
                # Try case-insensitive
                for allowed_val in allowed:
                    if allowed_val.lower() == value.lower():
                        value = allowed_val
                        break
                else:
                    # No match - use first allowed value as fallback
                    print(f"⚠️  Value '{value}' not in allowed values for {aspect_name}")
                    value = allowed[0]
        
        # Add to aspects if we found a value
        if value:
            aspects[aspect_name] = value
            print(f"✅ {aspect_name}: {value}")
        else:
            print(f"⚠️  Could not map {aspect_name}")
    
    return aspects
```

---

## 🎯 Complete End-to-End Flow

```python
def create_ebay_listing_with_category_specifics(
    access_token: str,
    valuation: dict,
    category_id: str,
    sku: str
):
    """Complete flow: Get specifics → Map AI → Create inventory → Publish"""
    
    # Step 1: Get category-specific aspects
    category_api = EBayCategorySpecifics(access_token)
    category_specifics = category_api.get_item_aspects_for_category(category_id)
    
    # Step 2: Map AI valuation to category specifics
    aspects = map_ai_to_category_specifics(valuation, category_id, category_specifics)
    
    # Step 3: Build inventory item with aspects
    inventory_item = {
        "product": {
            "title": valuation.get("item_name"),
            "brand": valuation.get("brand"),
            "aspects": aspects  # ← Your mapped specifics
        },
        "condition": "USED_EXCELLENT",
        "quantity": 1
    }
    
    # Step 4: Send to eBay API
    print(f"\n📤 Inventory Item:")
    print(json.dumps(inventory_item, indent=2))
    
    # Make API call here...


# Usage
valuation = {
    "item_name": "Vintage Crosman BB Gun Model 760",
    "brand": "Crosman",
    "condition_score": 8,
    "estimated_age": "1980s",
    "key_factors": ["All original parts", "Fully functional", "Vintage collectible"],
}

create_ebay_listing_with_category_specifics(
    access_token="YOUR_TOKEN",
    valuation=valuation,
    category_id="12576",  # Vintage Toys
    sku="CROSMAN_001"
)
```

---

## 🚨 Common Category-Specific Issues

### For Vintage Collectibles (12576)
```
Required:
  • Type: [Air Gun, Action Figure, Doll, Toy Vehicle, etc.]
  • Brand: Free text
  
Recommended:
  • Year: [1950s, 1960s, 1970s, 1980s, 1990s, etc.]
  • Features: Free text (vinyl, plastic, original box, etc.)
```

### For Doll Clothes (26568)
```
Required:
  • Size: [Fits dolls 18 inch, Fits dolls 16 inch, etc.]
  • Material: [Cotton, Polyester, Vinyl, Wool, etc.]
  
Recommended:
  • Color: Free text
  • Doll Type: [Barbie, American Girl, Generic, etc.]
```

### For Auto Parts (6024)
```
Required:
  • Make: [Automotive brand]
  • Model: [Car model]
  • Year: [2020, 2019, 2018, etc.]
  • Fitment Type: [Direct replacement, Universal, etc.]
  
Recommended:
  • Engine Type: [V4, V6, V8, etc.]
```

---

## ✅ Strategy: Smart Defaults

Since your AI doesn't know the category ahead of time, use this strategy:

```python
def smart_aspect_mapping(valuation: dict, category_specifics: dict) -> dict:
    """
    Use best-effort mapping with smart fallbacks.
    """
    
    aspects = {}
    
    # Always try to fill required aspects
    for aspect in category_specifics.get("required", []):
        name = aspect["name"].lower()
        
        # Priority order for each aspect type
        if "brand" in name:
            aspects[aspect["name"]] = valuation.get("brand", "Unknown")
        
        elif "type" in name or "category" in name:
            # Use first word or category guess
            aspects[aspect["name"]] = valuation.get("item_type", "Collectible")
        
        elif "year" in name or "era" in name:
            # Try to extract from estimated_age
            aspects[aspect["name"]] = valuation.get("estimated_age", "Unknown")
        
        elif "condition" in name:
            # Use our standard mapping
            condition_score = valuation.get("condition_score", 5)
            aspects[aspect["name"]] = ["Poor", "Fair", "Good", "Very Good", "Excellent"][condition_score // 2]
        
        else:
            # For unknown aspects, use key_factors as fallback
            factors = valuation.get("key_factors", [])
            if factors:
                aspects[aspect["name"]] = factors[0]
    
    return aspects
```

---

## 📋 Quick Checklist

Before sending to eBay API:

- ✅ Call `get_item_aspects_for_category` for your category
- ✅ Identify all **required** aspects
- ✅ Map each required aspect from AI valuation
- ✅ Validate against allowed values (if SELECT mode)
- ✅ For unmapped required aspects, use smart defaults
- ✅ Include recommended aspects if data available
- ✅ Include aspects in `product.aspects` field
- ✅ Do NOT include aspects from different categories

---

## 🔗 eBay API References

**Taxonomy API:**
- [getItemAspectsForCategory](https://developer.ebay.com/api-docs/commerce/taxonomy/resources/category_tree/methods/getItemAspectsForCategory)
- [Category Tree Overview](https://developer.ebay.com/api-docs/commerce/taxonomy/overview.html)

**Inventory API:**
- [Product Type Definition](https://developer.ebay.com/api-docs/sell/inventory/types/slr:Product)
- [createOrReplaceInventoryItem](https://developer.ebay.com/api-docs/sell/inventory/resources/inventory_item/methods/createOrReplaceInventoryItem)

**Key Resources:**
- [Item Specifics Guide](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/item-specifics.html)
- [Metadata API](https://developer.ebay.com/api-docs/sell/metadata/overview.html)

---

**Bottom Line:** Always fetch category-specific aspects first, then map intelligently from your AI valuation. Cache results for 24 hours to avoid API rate limits! 🚀
