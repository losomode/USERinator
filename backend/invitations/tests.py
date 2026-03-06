"""Tests for invitations app."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from companies.models import Company
from invitations.models import UserInvitation
from roles.models import Role
from users.models import User


class InvitationModelTest(TestCase):

    def setUp(self):
        self.company = Company.objects.create(name="TestCo")
        self.role = Role.objects.create(role_name="MEMBER", role_level=10)

    def test_str(self):
        inv = UserInvitation.objects.create(
            email="test@test.com",
            company=self.company,
            requested_role=self.role,
        )
        self.assertIn("test@test.com", str(inv))

    def test_default_status(self):
        inv = UserInvitation.objects.create(
            email="test@test.com",
            company=self.company,
            requested_role=self.role,
        )
        self.assertEqual(inv.status, "PENDING")

    def test_is_expired(self):
        inv = UserInvitation.objects.create(
            email="exp@test.com",
            company=self.company,
            requested_role=self.role,
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(inv.is_expired)

    def test_is_pending(self):
        inv = UserInvitation.objects.create(
            email="pend@test.com",
            company=self.company,
            requested_role=self.role,
        )
        self.assertTrue(inv.is_pending)

    def test_approved_not_pending(self):
        inv = UserInvitation.objects.create(
            email="appr@test.com",
            company=self.company,
            requested_role=self.role,
            status=UserInvitation.Status.APPROVED,
        )
        self.assertFalse(inv.is_pending)
        self.assertFalse(inv.is_expired)


class InvitationAPITest(APITestCase):

    def setUp(self):
        self.company = Company.objects.create(name="TestCo")
        self.role = Role.objects.create(role_name="MEMBER", role_level=10)
        User.objects.create(id=1, username="admin", email="admin@t.com")

    def _auth(self, role_level=100, company_id=None):
        if company_id is None:
            company_id = self.company.id
        patcher = patch("core.authentication.authinator_client")
        mock_client = patcher.start()
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": role_level,
            "company_id": company_id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.addCleanup(patcher.stop)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")

    def test_create_invitation(self):
        self._auth(role_level=10)
        response = self.client.post(
            "/api/invitations/",
            {
                "email": "new@test.com",
                "company": self.company.id,
                "requested_role": self.role.id,
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_duplicate_invitation_rejected(self):
        self._auth(role_level=10)
        self.client.post(
            "/api/invitations/",
            {
                "email": "dup@test.com",
                "company": self.company.id,
                "requested_role": self.role.id,
            },
        )
        response = self.client.post(
            "/api/invitations/",
            {
                "email": "dup@test.com",
                "company": self.company.id,
                "requested_role": self.role.id,
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_approve_invitation(self):
        self._auth(role_level=100)
        inv = UserInvitation.objects.create(
            email="approve@test.com",
            company=self.company,
            requested_role=self.role,
        )
        response = self.client.post(f"/api/invitations/{inv.id}/approve/")
        self.assertEqual(response.status_code, 200)
        inv.refresh_from_db()
        self.assertEqual(inv.status, "APPROVED")

    def test_reject_invitation(self):
        self._auth(role_level=100)
        inv = UserInvitation.objects.create(
            email="reject@test.com",
            company=self.company,
            requested_role=self.role,
        )
        response = self.client.post(
            f"/api/invitations/{inv.id}/reject/", {"review_notes": "Not approved"}
        )
        self.assertEqual(response.status_code, 200)
        inv.refresh_from_db()
        self.assertEqual(inv.status, "REJECTED")

    def test_approve_already_approved(self):
        self._auth(role_level=100)
        inv = UserInvitation.objects.create(
            email="done@test.com",
            company=self.company,
            requested_role=self.role,
            status=UserInvitation.Status.APPROVED,
        )
        response = self.client.post(f"/api/invitations/{inv.id}/approve/")
        self.assertEqual(response.status_code, 400)

    def test_approve_expired(self):
        self._auth(role_level=100)
        inv = UserInvitation.objects.create(
            email="exp@test.com",
            company=self.company,
            requested_role=self.role,
            expires_at=timezone.now() - timedelta(days=1),
        )
        response = self.client.post(f"/api/invitations/{inv.id}/approve/")
        self.assertEqual(response.status_code, 400)

    def test_list_invitations_admin(self):
        self._auth(role_level=100)
        response = self.client.get("/api/invitations/")
        self.assertEqual(response.status_code, 200)

    def test_list_invitations_denied_member(self):
        self._auth(role_level=10)
        response = self.client.get("/api/invitations/")
        self.assertEqual(response.status_code, 403)
