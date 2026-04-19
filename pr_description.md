🎯 **What:** Removed the unused `ItemCondition` import from `services/ebay_integration.py`.

💡 **Why:** The `ItemCondition` class was imported from `shared.models` but never referenced within the `eBayIntegration` class or the file's logic. Removing it cleans up the namespace, adheres to Python linting best practices, and improves overall code maintainability by eliminating dead code.

✅ **Verification:**
1. Verified via `grep` that `ItemCondition` is not used anywhere else in the file.
2. Successfully executed the full test suite (`pytest tests/ -v`). The changes caused no regressions. Existing failures related to mocked external dependencies were unaffected.
3. Code review completed without issues.

✨ **Result:** A cleaner `services/ebay_integration.py` file with unnecessary dependencies removed, slightly reducing module load overhead and preventing potential confusion for future contributors.
