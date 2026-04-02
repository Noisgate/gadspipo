"""
Google OAuth2 handler.
"""

import requests
from urllib.parse import urlencode
from config import settings
import logging

logger = logging.getLogger(__name__)

class GoogleOAuth:
    """Google OAuth2 client."""

    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.scopes = [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/adwords",  # Google Ads API
        ]

    def get_authorization_url(self, state: str) -> str:
        """Get Google authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        
        query_string = urlencode(params)
        return f"{self.auth_url}?{query_string}"

    def exchange_code_for_tokens(self, code: str) -> dict | None:
        """Exchange authorization code for tokens."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }

        try:
            response = requests.post(self.token_url, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            # Log response details for debugging
            try:
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Google response: {e.response.text}")
                    logger.error(f"Status code: {e.response.status_code}")
            except:
                pass
            return None

    def get_user_info(self, access_token: str) -> dict | None:
        """Get user information from Google."""
        headers = {"Authorization": f"Bearer {access_token}"}
        
        try:
            response = requests.get(self.userinfo_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None

# Global instance
google_oauth = GoogleOAuth()
