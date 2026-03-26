"""Management command to create default system roles."""

from django.core.management.base import BaseCommand

from roles.models import Role

# Platform roles (level >= 60) are company-independent — no company association.
# Company roles (level < 60) require a company.
DEFAULT_ROLES = [
    {
        "role_name": "PLATFORM_ADMIN",
        "role_level": 100,
        "description": "Platform administrator with full read/write access across all companies. No company association.",
        "is_system_role": True,
    },
    {
        "role_name": "PLATFORM_MANAGER",
        "role_level": 75,
        "description": "Platform manager with cross-company read access and limited write permissions. No company association.",
        "is_system_role": True,
    },
    {
        "role_name": "PLATFORM_MEMBER",
        "role_level": 60,
        "description": "Platform member with cross-company read-only access. No company association.",
        "is_system_role": True,
    },
    {
        "role_name": "COMPANY_ADMIN",
        "role_level": 50,
        "description": "Company administrator with elevated company access. Can manage managers and members, approve invitations, deactivate users up to manager level.",
        "is_system_role": True,
    },
    {
        "role_name": "COMPANY_MANAGER",
        "role_level": 30,
        "description": "Company manager with team management access within their company. Can manage members and approve invitations.",
        "is_system_role": True,
    },
    {
        "role_name": "COMPANY_MEMBER",
        "role_level": 10,
        "description": "Standard company member with read access to their company's data.",
        "is_system_role": True,
    },
]

# Minimum role level for platform (company-independent) users
PLATFORM_ROLE_THRESHOLD = 60


class Command(BaseCommand):
    help = "Create/update system roles: PLATFORM_ADMIN=100, PLATFORM_MANAGER=75, PLATFORM_MEMBER=60, COMPANY_MANAGER=30, COMPANY_MEMBER=10"

    def handle(self, *args, **options):
        """Upsert roles by level so that old names (ADMIN, MANAGER, MEMBER) get
        renamed to the new canonical names on re-run."""
        from users.models import UserProfile

        created_count = 0
        updated_count = 0

        for role_data in DEFAULT_ROLES:
            role, created = Role.objects.get_or_create(
                role_level=role_data["role_level"],
                defaults=role_data,
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  Created: {role.role_name} (level {role.role_level})")
                )
            elif role.role_name != role_data["role_name"]:
                old_name = role.role_name
                # Rename the Role record
                role.role_name = role_data["role_name"]
                role.description = role_data["description"]
                role.is_system_role = True
                role.save()
                # Update all UserProfile records using the old name
                updated = UserProfile.objects.filter(role_name=old_name).update(
                    role_name=role_data["role_name"]
                )
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Renamed: {old_name} → {role.role_name} "
                        f"(updated {updated} user profiles)"
                    )
                )
            else:
                self.stdout.write(f"  OK: {role.role_name} (level {role.role_level})")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone. Created {created_count} new, updated {updated_count} renamed role(s)."
            )
        )
