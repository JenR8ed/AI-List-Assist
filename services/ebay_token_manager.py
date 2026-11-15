"""
eBay Token Manager - Auto-refresh tokens with App vs User scope separation
and atomic 0o600 credential persistence.
"""

import base64
from datetime import datetime, timedelta
import json
import logging
import os
import tempfile
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import requests

logger = logging.getLogger(__name__)


class EBayTokenManager:
    def __init__(self, client_id=None, client_secret=None, use_sandbox=True, token_file=None):
        load_dotenv()
        self.client_id = client_id or os.getenv("EBAY_CLIENT_ID") or os.getenv("EBAY_APP_ID")
        self.client_secret = client_secret or os.getenv("EBAY_CLIENT_SECRET") or os.getenv("EBAY_CERT_ID")
        self.use_sandbox = use_sandbox
        data_dir = os.getenv("DATA_DIR")
        default_token_file = os.path.join(data_dir, ".ebay_token.json") if data_dir else ".ebay_token.json"
        self.token_file = token_file or default_token_file
        self.base_url = "https://api.sandbox.ebay.com" if use_sandbox else "https://api.ebay.com"
        self._cached_token_data: Optional[Dict[str, Any]] = None
        self._cached_app_token_data: Optional[Dict[str, Any]] = None

    def get_valid_token(self) -> Optional[str]:
        """Get valid token, refresh if needed."""
        if self._cached_token_data and not self._is_expired(self._cached_token_data):
            return self._cached_token_data.get("access_token")

        token_data = self._load_token()

        if not token_data or self._is_expired(token_data):
            token_data = self._refresh_token()

        self._cached_token_data = token_data
        return token_data.get("access_token") if token_data else None

    def get_app_token(self) -> Optional[str]:
        """
        Get an Application OAuth token (client_credentials grant) suitable for
        read-only eBay Taxonomy and Browse APIs.
        """
        if self._cached_app_token_data and not self._is_expired(self._cached_app_token_data):
            return self._cached_app_token_data.get("access_token")

        token_data = self._request_client_credentials_token()
        if token_data:
            expires_at = datetime.now() + timedelta(seconds=token_data.get("expires_in", 7200))
            token_data["expires_at"] = expires_at.isoformat()
            token_data["token_type_flow"] = "application"
            self._cached_app_token_data = token_data
            return token_data.get("access_token")
        return None

    def get_user_token(self) -> Optional[str]:
        """
        Get a User-delegated OAuth token (authorization_code / refresh_token grant)
        required for eBay Sell Inventory, Offer, and Account APIs.
        Returns None if only an application token is available without a refresh_token.
        """
        token_data = self._cached_token_data or self._load_token()
        if token_data and token_data.get("refresh_token"):
            if not self._is_expired(token_data):
                return token_data.get("access_token")
            refreshed = self._refresh_token()
            if refreshed and refreshed.get("refresh_token"):
                return refreshed.get("access_token")
        return os.getenv("EBAY_ACCESS_TOKEN") or None

    def _load_token(self) -> Optional[Dict[str, Any]]:
        """Load token from file."""
        try:
            with open(self.token_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _save_token(self, token_data: Dict[str, Any]) -> None:
        """Atomically save token to file with 0o600 permissions."""
        expires_at = datetime.now() + timedelta(seconds=token_data.get("expires_in", 7200))
        token_data["expires_at"] = expires_at.isoformat()
        self._cached_token_data = token_data

        try:
            target_dir = os.path.dirname(os.path.abspath(self.token_file)) or "."
            os.makedirs(target_dir, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(dir=target_dir, prefix=".ebay_token_", suffix=".tmp")
            try:
                os.chmod(tmp_path, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(token_data, f)
                os.replace(tmp_path, self.token_file)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise
        except OSError as e:
            logger.warning(f"Could not persist token file {self.token_file}: {e}")

    def _is_expired(self, token_data: Dict[str, Any]) -> bool:
        """Check if token is expired."""
        try:
            expires_at = datetime.fromisoformat(token_data["expires_at"])
            return datetime.now() >= expires_at - timedelta(minutes=5)
        except Exception:
            return True

    def _encode_basic_auth(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    def _request_client_credentials_token(self) -> Optional[Dict[str, Any]]:
        if not self.client_id or not self.client_secret:
            return None
        encoded = self._encode_basic_auth()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded}",
        }
        data = {"grant_type": "client_credentials"}
        token_url = f"{self.base_url}/identity/v1/oauth2/token"
        try:
            response = requests.post(token_url, headers=headers, data=data)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logging.error(f"Error refreshing token: {e}")
        return None

    def exchange_code_for_token(self, auth_code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens."""
        if not self.client_id or not self.client_secret:
            return None

        encoded = self._encode_basic_auth()
        token_url = f"{self.base_url}/identity/v1/oauth2/token"

        try:
            response = requests.post(
                token_url,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {encoded}",
                },
                data={
                    "grant_type": "authorization_code",
                    "code": auth_code,
                    "redirect_uri": redirect_uri,
                },
            )

            if response.status_code == 200:
                token_data = response.json()
                self._save_token(token_data)
                return token_data
            else:
                try:
                    error_data = response.json()
                    error_desc = error_data.get("error_description", "No description")
                    logger.error(f"Token exchange failed: {response.status_code} - {error_desc}")
                except Exception:
                    logger.error(f"Token exchange failed: {response.status_code} - [REDACTED]")
        except Exception:
            logger.exception("Error exchanging code")

        return None

    def _refresh_token(self) -> Optional[Dict[str, Any]]:
        """Get new token from eBay."""
        if not self.client_id or not self.client_secret:
            return None

        token_data = self._load_token()
        refresh_token = token_data.get("refresh_token") if token_data else None

        encoded = self._encode_basic_auth()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded}",
        }

        if refresh_token:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": " ".join([
                    "https://api.ebay.com/oauth/api_scope/sell.inventory",
                    "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
                ]),
            }
        else:
            data = {"grant_type": "client_credentials"}

        token_url = f"{self.base_url}/identity/v1/oauth2/token"

        try:
            response = requests.post(
                token_url,
                headers=headers,
                data=data,
            )

            if response.status_code == 200:
                new_token_data = response.json()
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
