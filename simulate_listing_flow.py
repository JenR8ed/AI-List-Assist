import os
from datetime import datetime
from services.ebay_integration import eBayIntegration
from shared.models import ListingDraft, ItemCondition

def simulate_flow():
    # Set mock env variables for eBay credentials if not present
    os.environ.setdefault("EBAY_APP_ID", "mock_app_id")
    os.environ.setdefault("EBAY_CERT_ID", "mock_cert_id")
    os.environ.setdefault("EBAY_ACCESS_TOKEN", "mock_access_token_value_abc123")

    # Initialize the integration
    integration = eBayIntegration(use_sandbox=True)

    # Verify the mock token is set
    integration.access_token = os.getenv("EBAY_ACCESS_TOKEN")

    print("--- Starting Simulator ---")
    mock_draft = ListingDraft(
        listing_id="sim_list_xyz890",
        item_id="item_001",
        title="Vintage Leather Jacket",
        description="Great condition vintage jacket.",
        price=149.99,
        category_id="293",
        condition=ItemCondition.USED,
        images=["http://example.com/img1.jpg"],
        item_specifics={"Brand": ["Vintage"], "Size": ["L"]},
        created_at=datetime.now()
    )

    try:
        # We catch the exception because the HTTP error will be raised by raise_for_status()
        # since it's a mock token being sent to the real Sandbox API.
        integration.create_listing(mock_draft)
    except Exception as e:
        print(f"\\nExpected API Error caught: {e}")
    print("--- Simulation Complete ---")

if __name__ == "__main__":
    simulate_flow()
