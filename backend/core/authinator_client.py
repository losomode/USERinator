"""
Client for communicating with AUTHinator service.

Validates JWT tokens and fetches user information from AUTHinator.
USERinator-specific: also extracts role_level and company_id.
"""

import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AuthinatorClient:
    """Client for interacting with AUTHinator API."""

    def __init__(self):
        self.api_url = settings.AUTHINATOR_API_URL
        self.verify_ssl = settings.AUTHINATOR_VERIFY_SSL

    def get_user_from_token(self, token):
        """
        Validate JWT token and retrieve user information from AUTHinator.

        Args:
            token: JWT access token string.

        Returns:
            dict with user info (id, username, email, role, role_level, etc.)
            or None if token is invalid.
        """
        # Check cache first (5 minute TTL)
        cache_key = f"authinator_user_{token[:20]}"
        cached_user = cache.get(cache_key)
        if cached_user:
            return cached_user

        try:
            response = requests.get(
                f"{self.api_url}me/",
                headers={"Authorization": f"Bearer {token}"},
                verify=self.verify_ssl,
                timeout=5,
            )

            if response.status_code == 200:
                user_data = response.json()

                user_info = {
                    "id": user_data.get("id"),
                    "username": user_data.get("username"),
                    "email": user_data.get("email", ""),
                    "role": user_data.get("role", ""),
                    "role_level": user_data.get("role_level", 10),
                    "company_id": (
                        user_data.get("company", {}).get("id")
                        if user_data.get("company")
                        else None
                    ),
                    "company_name": (
                        user_data.get("company", {}).get("name")
                        if user_data.get("company")
                        else None
                    ),
                    "is_verified": user_data.get("is_verified", False),
                    "is_active": user_data.get("is_active", True),
                }

                cache.set(cache_key, user_info, 300)  # 5 minutes
                return user_info
            else:
                logger.warning(
                    "Failed to validate token with AUTHinator: %s",
                    response.status_code,
                )
                return None

        except requests.RequestException as e:
            logger.error("Error connecting to AUTHinator: %s", e)
            return None

    def verify_token(self, token):
        """Check if a JWT token is valid."""
        return self.get_user_from_token(token) is not None


# Singleton instance
authinator_client = AuthinatorClient()
