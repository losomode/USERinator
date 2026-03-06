"""Management command to migrate user data from AUTHinator to USERinator."""

import logging

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from companies.models import Company
from roles.models import Role
from users.models import UserProfile

logger = logging.getLogger(__name__)

# Default role mapping from AUTHinator role names → USERinator role levels
ROLE_MAP = {
    "ADMIN": 100,
    "MANAGER": 30,
    "MEMBER": 10,
    "USER": 10,  # AUTHinator may use "USER" instead of "MEMBER"
}


class Command(BaseCommand):
    help = "Migrate users from AUTHinator to USERinator"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without making changes",
        )
        parser.add_argument(
            "--default-company",
            type=str,
            default="Default Company",
            help="Name of the default company for users without one",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        default_company_name = options["default_company"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — no changes will be made\n"))

        # Fetch users from AUTHinator
        users_data = self._fetch_authinator_users()
        if users_data is None:
            self.stderr.write(
                self.style.ERROR("Failed to fetch users from AUTHinator.")
            )
            return

        self.stdout.write(f"Found {len(users_data)} user(s) in AUTHinator.\n")

        # Load role definitions
        roles = {r.role_name: r for r in Role.objects.all()}
        if not roles:
            self.stderr.write(
                self.style.ERROR(
                    "No roles found. Run 'manage.py create_default_roles' first."
                )
            )
            return

        created = 0
        skipped = 0
        errors = 0

        for user_data in users_data:
            user_id = user_data.get("id")
            username = user_data.get("username", "")
            email = user_data.get("email", "")

            if not user_id:
                self.stderr.write(f"  Skipping user with no id: {user_data}")
                errors += 1
                continue

            # Check if already migrated
            if UserProfile.objects.filter(user_id=user_id).exists():
                self.stdout.write(f"  Skipped (exists): {username} (id={user_id})")
                skipped += 1
                continue

            # Determine company
            company_name = (
                user_data.get("company", {}).get("name")
                if user_data.get("company")
                else default_company_name
            )

            # Determine role
            role_name = user_data.get("role", "MEMBER").upper()
            role_level = ROLE_MAP.get(role_name, 10)

            if dry_run:
                self.stdout.write(
                    f"  Would create: {username} (id={user_id}) "
                    f"→ company={company_name}, role={role_name}({role_level})"
                )
                created += 1
                continue

            try:
                with transaction.atomic():
                    company, _ = Company.objects.get_or_create(
                        name=company_name,
                        defaults={"account_status": "active"},
                    )

                    UserProfile.objects.create(
                        user_id=user_id,
                        username=username,
                        email=email,
                        company=company,
                        display_name=user_data.get("display_name", username),
                        role_name=role_name,
                        role_level=role_level,
                    )
                    created += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Created: {username} (id={user_id}) "
                            f"→ company={company_name}, role={role_name}({role_level})"
                        )
                    )
            except Exception as e:
                errors += 1
                self.stderr.write(
                    self.style.ERROR(f"  Error migrating {username}: {e}")
                )

        self.stdout.write(
            f"\nDone. Created={created}, Skipped={skipped}, Errors={errors}"
        )

    def _fetch_authinator_users(self):
        """Fetch all users from AUTHinator API."""
        api_url = settings.AUTHINATOR_API_URL
        try:
            response = requests.get(
                f"{api_url}users/",
                headers={
                    "X-Service-Key": settings.SERVICE_REGISTRATION_KEY,
                },
                verify=settings.AUTHINATOR_VERIFY_SSL,
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("results", data) if isinstance(data, dict) else data
            else:
                logger.error(
                    "AUTHinator returned %s: %s",
                    response.status_code,
                    response.text[:200],
                )
                return None
        except requests.RequestException as e:
            logger.error("Failed to connect to AUTHinator: %s", e)
            return None
