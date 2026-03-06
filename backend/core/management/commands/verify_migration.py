"""Management command to verify data migration integrity."""

from django.core.management.base import BaseCommand

from companies.models import Company
from roles.models import Role
from users.models import UserProfile


class Command(BaseCommand):
    help = "Verify data integrity after migration from AUTHinator"

    def handle(self, *args, **options):
        self.stdout.write("=== USERinator Migration Verification Report ===\n")

        # 1. User counts
        total_profiles = UserProfile.objects.count()
        active_profiles = UserProfile.objects.filter(is_active=True).count()
        inactive_profiles = total_profiles - active_profiles
        self.stdout.write(
            f"User Profiles: {total_profiles} total "
            f"({active_profiles} active, {inactive_profiles} inactive)"
        )

        # 2. Company counts
        total_companies = Company.objects.count()
        active_companies = Company.objects.filter(account_status="active").count()
        self.stdout.write(
            f"Companies: {total_companies} total ({active_companies} active)"
        )

        # 3. Role coverage
        roles = Role.objects.all()
        self.stdout.write(f"Roles defined: {roles.count()}")
        for role in roles:
            user_count = UserProfile.objects.filter(
                role_name=role.role_name, is_active=True
            ).count()
            system = " [system]" if role.is_system_role else ""
            self.stdout.write(
                f"  {role.role_name} (level={role.role_level}){system}: "
                f"{user_count} user(s)"
            )

        # 4. Orphan checks
        orphan_roles = (
            UserProfile.objects.filter(is_active=True)
            .exclude(role_name__in=roles.values_list("role_name", flat=True))
            .values_list("role_name", flat=True)
            .distinct()
        )
        if orphan_roles:
            self.stderr.write(
                self.style.WARNING(
                    f"Users with unrecognized roles: {list(orphan_roles)}"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("No orphan roles found."))

        # 5. Companies without users
        empty_companies = Company.objects.filter(account_status="active").exclude(
            id__in=UserProfile.objects.filter(is_active=True)
            .values_list("company_id", flat=True)
            .distinct()
        )
        if empty_companies.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"Active companies with no users: "
                    f"{list(empty_companies.values_list('name', flat=True))}"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("All active companies have users."))

        # 6. Duplicate email check
        from django.db.models import Count

        dupes = (
            UserProfile.objects.filter(is_active=True)
            .values("email")
            .annotate(count=Count("email"))
            .filter(count__gt=1)
        )
        if dupes.exists():
            self.stderr.write(
                self.style.ERROR(f"Duplicate emails: {[d['email'] for d in dupes]}")
            )
        else:
            self.stdout.write(self.style.SUCCESS("No duplicate emails found."))

        self.stdout.write("\n=== Verification Complete ===")
