⚡ [performance] Optimize database connections in seed_db.py

💡 **What:** Replaced the hard-coded `time.sleep(15)` at the start of `seed_db.py` with an active retry mechanism for both Redis and PostgreSQL. The script now pings Redis up to 15 times with 1s intervals, and connects to Postgres up to 15 times with 1s intervals, rather than waiting a full 15 seconds unconditionally.
🎯 **Why:** The hardcoded `time.sleep(15)` was unnecessary and blocking. Often times the database is already running, which means 15 seconds are completely wasted. By replacing this with an active retry approach, the script continues running exactly when the databases are ready.
📊 **Measured Improvement:** In a local benchmark test (`measure_baseline.py`), where the databases are immediately ready (mocked), the script's execution time went from 15.3 seconds to 0.3 seconds. This provides a roughly 50x speed up for cases where databases are fast to spin up or are already available.
