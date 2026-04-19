"""
shared/schemas/pricing_strategy.py

Defines the configuration for how we price items.
This separates the 'Business Logic' (math) from the 'Service Logic' (code).
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class PricingResult:
    list_price: float
    auto_accept_price: Optional[float] = None
    minimum_price: Optional[float] = None
    format: str = "FIXED_PRICE"  # or "AUCTION"

# --- STRATEGY CONFIGURATION ---

# The "Negotiation Buffer" (Source 9)
# We list 15% higher than value to allow for offers.
MARKUP_PERCENTAGE = 0.15

# The "Auto-Accept" Threshold (Source 8)
# We automatically accept offers that are 90% of our LIST price.
AUTO_ACCEPT_THRESHOLD = 0.90

# The "Floor" (Minimum)
# We never auto-accept below the original estimated value.
PROTECT_ESTIMATE_FLOOR = True

def calculate_smart_price(estimated_value: float) -> PricingResult:
    """
    Applies the schema rules to a raw value.

    Example:
    Input Value: $100.00

    Calculation:
    1. Markup: $100 * 1.15 = $115.00 (List Price)
    2. Auto-Accept: $115 * 0.90 = $103.50

    Result:
    List for $115. Accept anything over $103.50 automatically.
    """

    if estimated_value <= 0:
        return PricingResult(list_price=0.0)

    # 1. Apply Negotiation Buffer
    list_price = round(estimated_value * (1 + MARKUP_PERCENTAGE), 2)

    # 2. Calculate Best Offer logic
    auto_accept = round(list_price * AUTO_ACCEPT_THRESHOLD, 2)

    # 3. Safety Check: If auto-accept drops below original estimate, clamp it?
    # (Optional based on strategy. Here we allow it to follow the % rule strictly)

    return PricingResult(
        list_price=list_price,
        auto_accept_price=auto_accept,
        minimum_price=round(list_price * 0.80, 2), # Auto-decline lowballs
        format="FIXED_PRICE"
    )
