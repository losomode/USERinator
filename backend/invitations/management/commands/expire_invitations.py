"""Management command to mark expired invitations."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from invitations.models import UserInvitation


class Command(BaseCommand):
    help = "Mark pending invitations past their expiration date as EXPIRED"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be expired without making changes",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        expired_qs = UserInvitation.objects.filter(
            status=UserInvitation.Status.PENDING,
            expires_at__lt=now,
        )

        count = expired_qs.count()

        if options["dry_run"]:
            self.stdout.write(f"Would expire {count} invitation(s).")
            for inv in expired_qs:
                self.stdout.write(f"  {inv.email} → {inv.company.name}")
        else:
            expired_qs.update(status=UserInvitation.Status.EXPIRED)
            self.stdout.write(self.style.SUCCESS(f"Expired {count} invitation(s)."))
