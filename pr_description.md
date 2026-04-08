🧹 [Remove unused imports in Telegram bot]

🎯 **What:** Removed unused `import asyncio` and `from services.mock_valuation_service import MockValuationService` from `your_ebay_valuator_bot.py`.
💡 **Why:** These imports were not being used anywhere in the file. Removing dead code improves maintainability and readability by reducing clutter and potential confusion for future developers reading the file.
✅ **Verification:** Verified that the removed imports were not used in the file using `grep`. Tested syntax with `python -m py_compile your_ebay_valuator_bot.py` and `python test_syntax.py`. Ran the full test suite (`python -m pytest tests`), ensuring no new regressions were introduced (existing failures are related to missing env variables).
✨ **Result:** A cleaner `your_ebay_valuator_bot.py` file with unnecessary dependencies removed, slightly improving code health.
