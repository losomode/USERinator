"""Management command to create demo data for development."""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from companies.models import Company
from invitations.models import UserInvitation
from roles.models import Role
from users.models import UserProfile

DEMO_COMPANIES = [
    {
        "name": "Acme Corporation",
        "industry": "Technology",
        "company_size": "51-200",
        "website": "https://acme.example.com",
        "tags": ["enterprise", "vip"],
    },
    {
        "name": "Globex Industries",
        "industry": "Manufacturing",
        "company_size": "11-50",
        "website": "https://globex.example.com",
        "tags": ["manufacturing"],
    },
    {
        "name": "Initech LLC",
        "industry": "Consulting",
        "company_size": "1-10",
        "website": "https://initech.example.com",
        "tags": ["startup"],
    },
]

DEMO_USERS = [
    # (user_id, username, email, company_idx, role_name, display_name, job_title)
    (1, "admin", "admin@example.com", 0, "ADMIN", "Alice Admin", "System Administrator"),
    (
        101,
        "bob.manager",
        "bob@acme.example.com",
        0,
        "MANAGER",
        "Bob Manager",
        "Engineering Manager",
    ),
    (
        102,
        "carol",
        "carol@acme.example.com",
        0,
        "MEMBER",
        "Carol Chen",
        "Software Engineer",
    ),
    (103, "dave", "dave@acme.example.com", 0, "MEMBER", "Dave Davis", "QA Engineer"),
    (104, "globex.admin", "admin@globex.example.com", 1, "ADMIN", "Eve Globex", "CEO"),
    (
        105,
        "frank",
        "frank@globex.example.com",
        1,
        "MANAGER",
        "Frank Fisher",
        "Operations Manager",
    ),
    (
        106,
        "grace",
        "grace@globex.example.com",
        1,
        "MEMBER",
        "Grace Green",
        "Technician",
    ),
    (
        107,
        "initech.admin",
        "admin@initech.example.com",
        2,
        "ADMIN",
        "Henry Hart",
        "Founder",
    ),
    (108, "iris", "iris@initech.example.com", 2, "MEMBER", "Iris Irving", "Consultant"),
    (109, "jack", "jack@initech.example.com", 2, "MEMBER", "Jack Jones", "Analyst"),
]

DEMO_INVITATIONS = [
    # (email, company_idx, role_name, status, message)
    ("newuser@example.com", 0, "MEMBER", "PENDING", "I'd like to join Acme"),
    ("approved@example.com", 0, "MEMBER", "APPROVED", "Please add me"),
    ("rejected@example.com", 1, "MEMBER", "REJECTED", "Looking for work"),
]


class Command(BaseCommand):
    help = "Create demo data (3 companies, 10 users, sample invitations)"

    def handle(self, *args, **options):
        # Ensure default roles exist
        call_command("create_default_roles")
        self.stdout.write("")

        roles = {r.role_name: r for r in Role.objects.all()}

        # Create companies
        companies = []
        for comp_data in DEMO_COMPANIES:
            company, created = Company.objects.get_or_create(
                name=comp_data["name"],
                defaults=comp_data,
            )
            companies.append(company)
            status = "Created" if created else "Exists"
            self.stdout.write(f"  Company: {company.name} [{status}]")

        # Create user profiles
        for user_id, username, email, cidx, role_name, display, title in DEMO_USERS:
            role = roles.get(role_name, roles.get("MEMBER"))
            _, created = UserProfile.objects.get_or_create(
                user_id=user_id,
                defaults={
                    "username": username,
                    "email": email,
                    "company": companies[cidx],
                    "display_name": display,
                    "job_title": title,
                    "role_name": role.role_name,
                    "role_level": role.role_level,
                },
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  User: {display} ({username}) [{status}]")

        # Create invitations
        now = timezone.now()
        for email, cidx, role_name, inv_status, message in DEMO_INVITATIONS:
            role = roles.get(role_name, roles.get("MEMBER"))
            _, created = UserInvitation.objects.get_or_create(
                email=email,
                company=companies[cidx],
                defaults={
                    "requested_role": role,
                    "status": inv_status,
                    "message": message,
                    "expires_at": now + timezone.timedelta(days=7),
                    "reviewed_at": now if inv_status != "PENDING" else None,
                },
            )
            status = "Created" if created else "Exists"
            self.stdout.write(f"  Invitation: {email} → {inv_status} [{status}]")

        self.stdout.write(self.style.SUCCESS("\nDemo data setup complete."))
