🎯 **What:** Removed unused `Dict` import from `shared/schemas/pricing_strategy.py`.

💡 **Why:** Reduces noise and improves code maintainability. `Dict` was imported but never utilized within the file.

✅ **Verification:** Verified that `pytest tests/test_pricing_strategy.py` completes successfully and checked syntax. No functional changes made.

✨ **Result:** Cleaned up unused import, leading to better readability and maintainability.
