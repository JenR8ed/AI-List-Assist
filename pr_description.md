🎯 **What:**
Fixed an Open Redirect vulnerability in the `get_ebay_oauth_url` endpoint (`app_enhanced.py:552`) by removing the reliance on user-provided input (`request.args.get('redirect_uri')`) for the OAuth callback URL construction.

⚠️ **Risk:**
If left unfixed, an attacker could supply an arbitrary domain (e.g., `?redirect_uri=https://evil.com/callback`). If the OAuth application validation isn't strictly configured, this could lead to the theft of the authorization code, allowing malicious actors to hijack user accounts or perform an Open Redirect attack directly from a trusted domain.

🛡️ **Solution:**
Replaced the dynamic request parameter extraction with a server-side configuration using the `EBAY_RU_NAME` environment variable:
`redirect_uri = os.getenv('EBAY_RU_NAME', 'http://localhost:5000/api/ebay/oauth/callback')`.
This strictly ensures that only authorized callbacks configured on the server can be utilized, completely mitigating the risk of user-controlled redirection. A unit test (`tests/test_security_oauth_redirect.py`) was also added to enforce this protection going forward.
