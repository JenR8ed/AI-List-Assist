💡 **What:**
Removed leftover `print()` statements used for debugging and deleted temporary scratch scripts (`patch_*` and `test_*` in the root).

🎯 **Why:**
Leaving debugging prints litters standard output and logs in production, leading to messy observability. Using the standard `logging` module provides proper leveling (e.g. `logger.debug`, `logger.error`). Temporary scripts left in the root directory increase tech debt and confuse maintainers regarding the actual architecture.

📊 **Result:**
A cleaner, more professional codebase. Production logs will no longer be spammed by arbitrary `print()` calls, and the root directory accurately reflects the project structure without leftover sandbox artifacts.
