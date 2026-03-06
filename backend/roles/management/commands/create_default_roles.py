"""Management command to create default system roles."""

from django.core.management.base import BaseCommand

from roles.models import Role

DEFAULT_ROLES = [
    {
        "role_name": "ADMIN",
        "role_level": 100,
        "description": "Platform administrator with full access",
        "is_system_role": True,
    },
    {
        "role_name": "MANAGER",
        "role_level": 30,
        "description": "Company manager with team management access",
        "is_system_role": True,
    },
    {
        "role_name": "MEMBER",
        "role_level": 10,
        "description": "Standard company member",
        "is_system_role": True,
    },
]


class Command(BaseCommand):
    help = "Create default system roles (ADMIN=100, MANAGER=30, MEMBER=10)"

    def handle(self, *args, **options):
        created_count = 0
        for role_data in DEFAULT_ROLES:
            role, created = Role.objects.get_or_create(
                role_name=role_data["role_name"],
                defaults=role_data,
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created role: {role.role_name} (level {role.role_level})"
                    )
                )
            else:
                self.stdout.write(
                    f"  Role already exists: {role.role_name} (level {role.role_level})"
                )

        self.stdout.write(
            self.style.SUCCESS(f"\nDone. Created {created_count} new role(s).")
        )
