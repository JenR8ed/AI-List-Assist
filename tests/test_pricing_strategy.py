import pytest
from shared.schemas.pricing_strategy import calculate_smart_price, PricingResult

@pytest.mark.parametrize("invalid_value", [
    0,
    0.0,
    -1,
    -10.5,
    -1000,
])
def test_calculate_smart_price_zero_or_negative(invalid_value):
    """
    Test that calculating a smart price with zero or negative estimated value
    returns a PricingResult with a list_price of 0.0 and defaults for other fields.
    """
    result = calculate_smart_price(invalid_value)

    assert isinstance(result, PricingResult)
    assert result.list_price == 0.0
    assert result.auto_accept_price is None
    assert result.minimum_price is None
    assert result.format == "FIXED_PRICE"
