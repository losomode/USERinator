"""Management command to register USERinator with AUTHinator service registry."""

import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Register USERinator with AUTHinator service registry"

    def handle(self, *args, **options):
        service_data = {
            "name": "USERinator",
            "description": "User & Company Management",
            "base_url": "http://localhost:8004",
            "api_prefix": "/api/users",
            "ui_url": "http://localhost:8080/users",
            "health_url": "http://localhost:8004/api/users/health/",
            "icon": "👤",
            "service_key": settings.SERVICE_REGISTRATION_KEY,
        }

        # Update URLs if DEPLOY_DOMAIN is set
        if settings.DEPLOY_DOMAIN:
            scheme = settings.DEPLOY_SCHEME
            domain = settings.DEPLOY_DOMAIN
            service_data["ui_url"] = f"{scheme}://{domain}/users"
            service_data["health_url"] = f"{scheme}://{domain}/api/users/health/"

        try:
            response = requests.post(
                settings.SERVICE_REGISTRY_URL,
                json=service_data,
                timeout=10,
            )
            if response.status_code in (200, 201):
                self.stdout.write(
                    self.style.SUCCESS("Successfully registered USERinator.")
                )
                logger.info("USERinator registered with AUTHinator")
            else:
                self.stderr.write(
                    self.style.ERROR(
                        f"Registration failed ({response.status_code}): "
                        f"{response.text[:200]}"
                    )
                )
                logger.error("Failed to register USERinator: %s", response.text)
        except requests.RequestException as e:
            self.stderr.write(
                self.style.ERROR(f"Could not reach service registry: {e}")
            )
            logger.error("Error registering USERinator: %s", e)
