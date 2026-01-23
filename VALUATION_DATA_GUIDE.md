# Item Valuation Data Structure Guide

## 📊 Core Valuation Data Model

### ItemValuation Object
```python
class ItemValuation:
    item_id: str                    # Unique identifier
    item_name: str                  # "Sony WH-1000XM4 Headphones"
    brand: str                      # "Sony", "Apple", "Nike"
    estimated_age: str              # "2-3 years", "Vintage (10+ years)"
    condition_score: int            # 1-10 scale
    condition_notes: str            # "Good condition, minor wear"
    is_complete: bool               # Has all original parts/accessories
    estimated_value: float          # $180.00
    value_range: dict               # {"low": 150.00, "high": 220.00}
    resale_score: int               # 1-10 market demand
    profitability: Profitability    # HIGH/MEDIUM/LOW/NOT_RECOMMENDED
    recommended_platforms: list     # ["eBay", "Amazon", "Mercari"]
    key_factors: list               # ["Popular brand", "High demand"]
    risks: list                     # ["Market saturation", "New model released"]
    listing_tips: list              # ["Include original box", "Highlight features"]
    worth_listing: bool             # Final recommendation
    confidence: float               # 0.0-1.0 AI confidence level
```

## 🎯 Decision Logic Flow

### 1. Image Analysis → Item Recognition
```
Photo Input → Vision API → Extract:
├── Item Category (Electronics, Clothing, etc.)
├── Brand Name (from text/logos)
├── Model Number (from labels)
├── Condition Assessment (visual inspection)
└── Completeness Check (missing parts?)
```

### 2. Market Research → Price Discovery
```
Item Keywords → eBay API → Analyze:
├── Sold Listings (last 90 days)
├── Active Listings (current competition)
├── Price Trends (going up/down?)
└── Sell-Through Rate (demand vs supply)
```

### 3. Profitability Calculation
```python
# Decision Gate Logic
if estimated_value >= $50 and sell_through_rate >= 30%:
    profitability = "HIGH"
elif estimated_value >= $20 and sell_through_rate >= 20%:
    profitability = "MEDIUM"
elif estimated_value >= $10:
    profitability = "LOW"
else:
    profitability = "NOT_RECOMMENDED"
```

## 📈 Sample Data Examples

### High-Value Electronics
```json
{
    "item_name": "Sony WH-1000XM4 Headphones",
    "brand": "Sony",
    "estimated_value": 180.00,
    "value_range": {"low": 150.00, "high": 220.00},
    "condition_score": 8,
    "resale_score": 9,
    "profitability": "HIGH",
    "worth_listing": true,
    "key_factors": ["Popular brand", "High demand", "Good condition"],
    "risks": ["Market saturation"],
    "listing_tips": ["Include original box", "Highlight noise cancellation"]
}
```

### Low-Value Collectible
```json
{
    "item_name": "Vintage Ceramic Mug",
    "brand": "Unknown",
    "estimated_value": 8.50,
    "value_range": {"low": 5.00, "high": 12.00},
    "condition_score": 6,
    "resale_score": 4,
    "profitability": "LOW",
    "worth_listing": false,
    "key_factors": ["Vintage appeal"],
    "risks": ["Low demand", "Shipping fragility"],
    "listing_tips": ["Pack carefully", "Market as vintage"]
}
```

## 🔍 Key Metrics Explained

### Condition Score (1-10)
- **10**: Brand new, perfect condition
- **8-9**: Excellent, minor wear
- **6-7**: Good, noticeable wear but functional
- **4-5**: Fair, significant wear
- **1-3**: Poor, major damage

### Resale Score (1-10)
- **9-10**: High demand, sells quickly
- **7-8**: Good demand, steady sales
- **5-6**: Moderate demand
- **3-4**: Low demand, slow sales
- **1-2**: Very low demand

### Profitability Levels
- **HIGH**: $50+ value, 30%+ sell-through rate
- **MEDIUM**: $20+ value, 20%+ sell-through rate  
- **LOW**: $10+ value, any sell-through rate
- **NOT_RECOMMENDED**: Under $10 or very low demand

## 🎲 Mock Data Generation

### How Different Images Get Different Results
```python
# Image hash determines which mock item to return
image_hash = hash(image_base64) % 3

mock_items = [
    sony_headphones,    # Hash 0 → Electronics
    vintage_mug,        # Hash 1 → Collectible
    iphone_12_pro       # Hash 2 → Phone
]

return mock_items[image_hash]
```

### Why This Works
- **Consistent**: Same image always gets same result
- **Varied**: Different images get different valuations
- **Realistic**: Based on actual market data patterns

## 🚀 Real API Integration

### When eBay API is Approved
```python
# Replace mock data with real market analysis
sold_listings = ebay_api.search_sold_items(keywords)
active_listings = ebay_api.search_active_items(keywords)

avg_price = calculate_average(sold_listings)
sell_through_rate = len(sold_listings) / (len(sold_listings) + len(active_listings))

# Real-time market-based valuation
estimated_value = avg_price
worth_listing = avg_price >= 15.0 and sell_through_rate >= 0.15
```

## 💡 Understanding the Output

### What Each Field Tells You
- **estimated_value**: What you can expect to sell for
- **value_range**: Price fluctuation range
- **worth_listing**: Final yes/no recommendation
- **profitability**: Profit potential level
- **key_factors**: Why it's valuable (or not)
- **risks**: What could go wrong
- **listing_tips**: How to maximize sale price

### Business Logic
The system answers: **"Should I spend time listing this item?"**
- Considers listing effort vs. potential profit
- Factors in market competition
- Accounts for eBay fees and shipping costs
- Provides actionable recommendations

This data structure captures everything needed to make informed reselling decisions!