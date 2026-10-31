"""
shared/schemas/pricing_strategy.py

Defines the configuration for how we price items and calculate net profit after eBay fees.
This separates the 'Business Logic' (math) from the 'Service Logic' (code).
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class PricingResult:
    list_price: float
    auto_accept_price: Optional[float] = None
    minimum_price: Optional[float] = None
    format: str = "FIXED_PRICE"  # or "AUCTION"


@dataclass
class ProfitBreakdown:
    list_price: float
    ebay_fee_rate: float
    ebay_fixed_fee: float
    ebay_total_fee: float
    shipping_cost: float
    cogs: float
    net_profit: float
    net_margin_pct: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "list_price": self.list_price,
            "ebay_fee_rate": self.ebay_fee_rate,
            "ebay_fixed_fee": self.ebay_fixed_fee,
            "ebay_total_fee": self.ebay_total_fee,
            "shipping_cost": self.shipping_cost,
            "cogs": self.cogs,
            "net_profit": self.net_profit,
            "net_margin_pct": self.net_margin_pct,
        }


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

# Standard eBay Final Value Fee (13.25% + $0.30 per order)
EBAY_FINAL_VALUE_FEE_RATE = 0.1325
EBAY_PER_ORDER_FIXED_FEE = 0.30


def calculate_smart_price(estimated_value: float) -> PricingResult:
    """
    Applies the schema rules to a raw value.
    """
    if estimated_value <= 0:
        return PricingResult(list_price=0.0)

    list_price = round(estimated_value * (1 + MARKUP_PERCENTAGE), 2)
    auto_accept = round(list_price * AUTO_ACCEPT_THRESHOLD, 2)

    return PricingResult(
        list_price=list_price,
        auto_accept_price=auto_accept,
        minimum_price=round(list_price * 0.80, 2),
        format="FIXED_PRICE",
    )


def calculate_net_profit(
    sale_price: float,
    shipping_cost: float = 0.0,
    cogs: float = 0.0,
    fee_rate: float = EBAY_FINAL_VALUE_FEE_RATE,
    fixed_fee: float = EBAY_PER_ORDER_FIXED_FEE,
) -> ProfitBreakdown:
    """
    Calculate net seller profit and margin after eBay Final Value Fees, shipping, and COGS.
    """
    if sale_price <= 0:
        return ProfitBreakdown(
            list_price=0.0,
            ebay_fee_rate=fee_rate,
            ebay_fixed_fee=0.0,
            ebay_total_fee=0.0,
            shipping_cost=round(max(0.0, shipping_cost), 2),
            cogs=round(max(0.0, cogs), 2),
            net_profit=round(-(max(0.0, shipping_cost) + max(0.0, cogs)), 2),
            net_margin_pct=0.0,
        )

    total_fee = round(sale_price * fee_rate + fixed_fee, 2)
    net_profit = round(sale_price - total_fee - max(0.0, shipping_cost) - max(0.0, cogs), 2)
    margin_pct = round((net_profit / sale_price) * 100.0, 1)

    return ProfitBreakdown(
        list_price=round(sale_price, 2),
        ebay_fee_rate=fee_rate,
        ebay_fixed_fee=fixed_fee,
        ebay_total_fee=total_fee,
        shipping_cost=round(max(0.0, shipping_cost), 2),
        cogs=round(max(0.0, cogs), 2),
        net_profit=net_profit,
        net_margin_pct=margin_pct,
    )
