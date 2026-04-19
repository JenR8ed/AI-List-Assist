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

@pytest.mark.parametrize("value, expected_list, expected_auto, expected_min", [
    (100.0, 115.0, 103.5, 92.0),
    (50.0, 57.5, 51.75, 46.0),
    (0.01, 0.01, 0.01, 0.01),
])
def test_calculate_smart_price_positive_values(value, expected_list, expected_auto, expected_min):
    """
    Test that calculating a smart price with positive values returns
    the correctly calculated PricingResult.
    """
    result = calculate_smart_price(value)

    assert isinstance(result, PricingResult)
    assert result.list_price == pytest.approx(expected_list)
    assert result.auto_accept_price == pytest.approx(expected_auto)
    assert result.minimum_price == pytest.approx(expected_min)
    assert result.format == "FIXED_PRICE"
