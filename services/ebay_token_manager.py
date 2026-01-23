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
    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv('EBAY_CLIENT_ID')
        self.client_secret = os.getenv('EBAY_CLIENT_SECRET')
        self.token_file = '.ebay_token.json'
        
    def get_valid_token(self):
        """Get valid token, refresh if needed."""
        token_data = self._load_token()
        
        if not token_data or self._is_expired(token_data):
            token_data = self._refresh_token()
            
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
    
    def _is_expired(self, token_data):
        """Check if token is expired."""
        try:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            return datetime.now() >= expires_at - timedelta(minutes=5)  # 5min buffer
        except:
            return True
    
    def _refresh_token(self):
        """Get new token from eBay."""
        if not self.client_id or not self.client_secret:
            return None
            
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        try:
            response = requests.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {encoded}"
                },
                data={"grant_type": "client_credentials"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self._save_token(token_data)
                self._update_env(token_data['access_token'])
                return token_data
        except:
            pass
            
        return None
    
    def _update_env(self, token):
        """Update .env file with new token."""
        try:
            with open('.env', 'r') as f:
                content = f.read()
            
            if 'EBAY_ACCESS_TOKEN=' in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('EBAY_ACCESS_TOKEN='):
                        lines[i] = f'EBAY_ACCESS_TOKEN={token}'
                content = '\n'.join(lines)
            else:
                content += f'\nEBAY_ACCESS_TOKEN={token}'
            
            with open('.env', 'w') as f:
                f.write(content)
        except:
            pass