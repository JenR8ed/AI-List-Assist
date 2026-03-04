"""
eBay Token Manager - Auto-refresh tokens
"""

import requests
import base64
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

class EBayTokenManager:
    def __init__(self, client_id=None, client_secret=None, use_sandbox=True):
        load_dotenv()
        self.client_id = client_id or os.getenv('EBAY_CLIENT_ID') or os.getenv('EBAY_APP_ID')
        self.client_secret = client_secret or os.getenv('EBAY_CLIENT_SECRET') or os.getenv('EBAY_CERT_ID')
        self.use_sandbox = use_sandbox
        self.token_file = '.ebay_token.json'
        self.base_url = "https://api.sandbox.ebay.com" if use_sandbox else "https://api.ebay.com"
        self._cached_token_data = None

    def get_valid_token(self):
        """Get valid token, refresh if needed."""
        if self._cached_token_data and not self._is_expired(self._cached_token_data):
            return self._cached_token_data.get('access_token')

        token_data = self._load_token()

        if not token_data or self._is_expired(token_data):
            token_data = self._refresh_token()

        self._cached_token_data = token_data
        return token_data.get('access_token') if token_data else None
    
    def _load_token(self):
        """Load token from file."""
        try:
            with open(self.token_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def _save_token(self, token_data):
        """Save token to file."""
        expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 7200))
        token_data['expires_at'] = expires_at.isoformat()
        
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f)
        self._cached_token_data = token_data
    
    def _is_expired(self, token_data):
        """Check if token is expired."""
        try:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            return datetime.now() >= expires_at - timedelta(minutes=5)  # 5min buffer
        except:
            return True
    
    def exchange_code_for_token(self, auth_code, redirect_uri):
        """Exchange authorization code for tokens."""
        if not self.client_id or not self.client_secret:
            return None
            
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        token_url = f"{self.base_url}/identity/v1/oauth2/token"

        try:
            response = requests.post(
                token_url,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {encoded}"
                },
                data={
                    "grant_type": "authorization_code",
                    "code": auth_code,
                    "redirect_uri": redirect_uri
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self._save_token(token_data)
                return token_data
            else:
                try:
                    error_data = response.json()
                    error_desc = error_data.get('error_description', 'No description')
                    print(f"Token exchange failed: {response.status_code} - {error_desc}")
                except:
                    print(f"Token exchange failed: {response.status_code} - [REDACTED]")
        except Exception as e:
            print(f"Error exchanging code: {e}")

        return None

    def _refresh_token(self):
        """Get new token from eBay."""
        if not self.client_id or not self.client_secret:
            return None

        token_data = self._load_token()
        refresh_token = token_data.get('refresh_token') if token_data else None

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded}"
        }

        if refresh_token:
            # Use refresh token if available (User-delegated flow)
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": " ".join([
                    "https://api.ebay.com/oauth/api_scope/sell.inventory",
                    "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly"
                ])
            }
        else:
            # Fallback to client_credentials (Application flow)
            data = {"grant_type": "client_credentials"}

        token_url = f"{self.base_url}/identity/v1/oauth2/token"

        try:
            response = requests.post(
                token_url,
                headers=headers,
                data=data
            )

            if response.status_code == 200:
                new_token_data = response.json()
                # If we used a refresh token, the response might not include a new refresh token
                # so we should preserve the old one if needed, but eBay usually returns the same one
                # or a new one. Let's merge with old data to be safe.
                if token_data:
                    for key, value in new_token_data.items():
                        token_data[key] = value
                else:
                    token_data = new_token_data

                self._save_token(token_data)
                return token_data
        except Exception as e:
            logging.error(f"Error refreshing token: {e}")
            
        return None
    
