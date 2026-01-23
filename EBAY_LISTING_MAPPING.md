# Valuation Data to eBay Listing Field Mapping

## 📊 Core Data Flow

```
Image Upload → AI Analysis → Valuation Data → eBay Listing Fields → Published Listing
```

## 🔄 Field Mapping Table

| Valuation Field | eBay Listing Field | Transformation | Example |
|----------------|-------------------|----------------|---------|
| `item_name` | **Title** | Optimize for 80 char limit | "Sony WH-1000XM4 Wireless Noise Canceling Headphones - Black" |
| `brand` | **Brand** (Item Specific) | Direct mapping | "Sony" |
| `estimated_value` | **Starting Price** | Apply pricing strategy | $180.00 → $179.99 |
| `condition_score` | **Condition** | Score to eBay condition | 8/10 → "Used - Excellent" |
| `condition_notes` | **Condition Description** | Detailed description | "Minor wear on ear cups, fully functional" |
| `key_factors` | **Description** (highlights) | Bullet points | "• Popular brand\n• High demand\n• Good condition" |
| `listing_tips` | **Description** (selling points) | Marketing copy | "Include original box if available" |
| `risks` | **Description** (disclaimers) | Transparency notes | "Some market competition" |
| `probable_category` | **Category ID** | Category mapping | "Electronics" → "293" |
| `recommended_platforms` | **Listing Format** | Platform optimization | ["eBay"] → "Auction" or "Buy It Now" |

## 🏷️ eBay Listing Structure

### Required Fields
```json
{
  "title": "Sony WH-1000XM4 Wireless Noise Canceling Headphones - Black",
  "categoryId": "293",
  "condition": "USED_EXCELLENT", 
  "conditionDescription": "Minor wear on ear cups, fully functional",
  "startPrice": 179.99,
  "listingType": "FIXED_PRICE",
  "duration": "DAYS_7"
}
```

### Item Specifics (Key-Value Pairs)
```json
{
  "Brand": "Sony",
  "Model": "WH-1000XM4", 
  "Color": "Black",
  "Connectivity": "Wireless",
  "Features": "Noise Canceling"
}
```

### Description (HTML)
```html
<h2>Sony WH-1000XM4 Wireless Headphones</h2>
<ul>
  <li>Popular brand with high demand</li>
  <li>Excellent condition (8/10)</li>
  <li>Fully functional with minor cosmetic wear</li>
</ul>
<p><strong>Condition Notes:</strong> Minor wear on ear cups, all functions work perfectly.</p>
```

## 🎯 Condition Score Mapping

| Valuation Score | eBay Condition | Description |
|----------------|----------------|-------------|
| 10 | `NEW` | Brand new, never used |
| 9 | `NEW_OTHER` | New but opened/displayed |
| 7-8 | `USED_EXCELLENT` | Minimal wear, works perfectly |
| 5-6 | `USED_GOOD` | Some wear, fully functional |
| 3-4 | `USED_ACCEPTABLE` | Significant wear, works |
| 1-2 | `FOR_PARTS` | Major damage, may not work |

## 💰 Pricing Strategy

### Base Price Calculation
```python
# From valuation data
estimated_value = 180.00
value_range = {"low": 150.00, "high": 220.00}
profitability = "HIGH"

# eBay pricing strategy
if profitability == "HIGH":
    starting_price = estimated_value * 0.95  # Start slightly below estimate
elif profitability == "MEDIUM": 
    starting_price = estimated_value * 0.90  # More aggressive pricing
else:
    starting_price = value_range["low"]      # Start at low end

# Final price: $179.99 (psychological pricing)
```

### Listing Format Decision
```python
if estimated_value >= 100 and profitability == "HIGH":
    listing_type = "FIXED_PRICE"  # Buy It Now
    duration = "DAYS_30"          # Longer exposure
else:
    listing_type = "AUCTION"      # Let market decide
    duration = "DAYS_7"           # Quick sale
```

## 📝 Title Optimization

### Title Generation Logic
```python
def generate_title(valuation):
    components = []
    
    # Brand (if known)
    if valuation.brand:
        components.append(valuation.brand)
    
    # Model/Product name
    components.append(valuation.item_name)
    
    # Key selling points from key_factors
    for factor in valuation.key_factors[:2]:  # Top 2 factors
        if len(" ".join(components + [factor])) <= 75:
            components.append(factor)
    
    # Condition hint
    if valuation.condition_score >= 8:
        components.append("Excellent")
    
    return " ".join(components)[:80]  # eBay 80 char limit
```

### Example Titles
- **Electronics**: "Sony WH-1000XM4 Wireless Noise Canceling Headphones Black Excellent"
- **Collectibles**: "Vintage 1990s Ceramic Coffee Mug Retro Kitchen Decor"
- **Phones**: "Apple iPhone 12 Pro 128GB Unlocked Smartphone Good Condition"

## 🏪 Category Mapping

### Category Decision Tree
```python
category_map = {
    "Electronics": {
        "headphones": "293",
        "phones": "9355", 
        "computers": "58058"
    },
    "Clothing": {
        "men": "1059",
        "women": "15724",
        "shoes": "93427"
    },
    "Collectibles": {
        "vintage": "20081",
        "antiques": "20081"
    }
}

def get_category_id(probable_category, item_name):
    # Use AI analysis + keyword matching
    category = category_map.get(probable_category, {})
    
    for keyword, cat_id in category.items():
        if keyword.lower() in item_name.lower():
            return cat_id
    
    return "1"  # Default: Collectibles
```

## 🚀 Complete Listing Generation

### From Valuation to eBay API Call
```python
def create_ebay_listing(valuation):
    return {
        "title": generate_title(valuation),
        "categoryId": get_category_id(valuation.probable_category, valuation.item_name),
        "condition": map_condition(valuation.condition_score),
        "conditionDescription": valuation.condition_notes,
        "startPrice": calculate_price(valuation),
        "listingType": get_listing_type(valuation),
        "duration": get_duration(valuation),
        "description": generate_description(valuation),
        "itemSpecifics": extract_specifics(valuation),
        "shippingDetails": get_shipping_options(valuation),
        "images": [valuation.image_url]
    }
```

## 📈 Success Metrics

### Listing Quality Score
```python
def calculate_listing_quality(valuation):
    score = 0
    
    # Title optimization (0-25 points)
    if len(title) >= 60: score += 25
    
    # Description completeness (0-25 points) 
    if len(valuation.key_factors) >= 3: score += 25
    
    # Pricing competitiveness (0-25 points)
    if valuation.profitability in ["HIGH", "MEDIUM"]: score += 25
    
    # Image quality (0-25 points)
    if valuation.confidence >= 0.8: score += 25
    
    return score  # 0-100 quality score
```

This mapping ensures every piece of valuation data translates into optimized eBay listing fields for maximum selling potential!