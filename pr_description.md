🧹 [remove unused import `random` in `mock_valuation_service.py`]

🎯 **What:** Removed an unused `import random` statement from `services/mock_valuation_service.py`.
💡 **Why:** To improve code cleanliness and maintainability by eliminating unnecessary module imports.
✅ **Verification:** Verified by compiling the python file (`python -m py_compile services/mock_valuation_service.py`) and running the test suite to ensure no logic regressions occurred as a result.
✨ **Result:** A slightly cleaner file without unused dependencies.
