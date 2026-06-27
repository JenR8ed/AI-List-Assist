🎯 **What:** The hardcoded fallback 'mock_key_if_missing' was removed from the PERPLEXITY_API_KEY environment variable fetch in seed_db.py.
⚠️ **Risk:** Hardcoded pseudocredentials can be a security risk and confuse operators if environment variables are missing. It circumvents secure secret management.
🛡️ **Solution:** Modified os.environ.get to remove the hardcoded fallback and updated the subsequent if condition to check for a truthy perplexity_key. The corresponding test test_seed_db_security.py was also updated to use 'test_key' instead of the mock value.
