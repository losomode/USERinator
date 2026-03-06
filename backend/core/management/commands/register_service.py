"""Management command to register USERinator with AUTHinator service registry."""

import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

SERVICE_METADATA = {
    "name": "USERinator",
    "description": "User & company management",
    "ui_url": "http://localhost:8080/users",
    "icon": "users",
    "port": 8004,
    "health_url": "http://localhost:8004/api/users/health/",
}


class Command(BaseCommand):
    help = "Register USERinator with AUTHinator service registry"

    def handle(self, *args, **options):
        url = settings.SERVICE_REGISTRY_URL
        key = settings.SERVICE_REGISTRATION_KEY

        # Update ui_url if DEPLOY_DOMAIN is set
        metadata = SERVICE_METADATA.copy()
        if settings.DEPLOY_DOMAIN:
            scheme = settings.DEPLOY_SCHEME
            metadata["ui_url"] = f"{scheme}://{settings.DEPLOY_DOMAIN}/users"
            metadata["health_url"] = (
                f"{scheme}://{settings.DEPLOY_DOMAIN}/api/users/health/"
            )

        try:
            response = requests.post(
                url,
                json=metadata,
                headers={"X-Service-Key": key},
                timeout=10,
            )
            if response.status_code in (200, 201):
                self.stdout.write(
                    self.style.SUCCESS("Successfully registered USERinator.")
                )
            else:
                self.stderr.write(
                    self.style.ERROR(
                        f"Registration failed ({response.status_code}): "
                        f"{response.text[:200]}"
                    )
                )
        except requests.RequestException as e:
            self.stderr.write(
                self.style.ERROR(f"Could not reach service registry: {e}")
            )
