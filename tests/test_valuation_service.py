import pytest
from unittest.mock import patch

from services.valuation_service import ValuationService
from shared.models import Profitability

@pytest.fixture
def valuation_service():
    with patch('services.valuation_service.EBayTokenManager', create=True):
        return ValuationService()

@pytest.mark.parametrize("value, expected", [
    (0.0, Profitability.LOW),
    (10.0, Profitability.LOW),
    (14.99, Profitability.LOW),
    (15.0, Profitability.MEDIUM),
    (25.0, Profitability.MEDIUM),
    (49.99, Profitability.MEDIUM),
    (50.0, Profitability.HIGH),
    (50.01, Profitability.HIGH),
    (100.0, Profitability.HIGH),
    (-10.0, Profitability.LOW)
])
def test_determine_profitability(valuation_service, value, expected):
    """
    Test that ValuationService._determine_profitability returns the correct
    Profitability enum based on the provided value.
    """
    result = valuation_service._determine_profitability(value)
    assert result == expected
