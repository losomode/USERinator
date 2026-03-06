"""Tests for companies app."""

from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APITestCase

from companies.models import Company
from users.models import User


class CompanyModelTest(TestCase):
    def test_str(self):
        company = Company.objects.create(name="Acme Corp")
        self.assertEqual(str(company), "Acme Corp")

    def test_default_status(self):
        company = Company.objects.create(name="NewCo")
        self.assertEqual(company.account_status, "active")

    def test_tags_default(self):
        company = Company.objects.create(name="TagCo")
        self.assertEqual(company.tags, [])

    def test_custom_fields_default(self):
        company = Company.objects.create(name="FieldCo")
        self.assertEqual(company.custom_fields, {})


class CompanyAPITest(APITestCase):

    def setUp(self):
        self.company = Company.objects.create(name="TestCo")
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

    def test_list_companies_admin(self):
        self._auth(role_level=100)
        response = self.client.get("/api/companies/")
        self.assertEqual(response.status_code, 200)

    def test_list_companies_denied_member(self):
        self._auth(role_level=10)
        response = self.client.get("/api/companies/")
        self.assertEqual(response.status_code, 403)

    def test_create_company_admin(self):
        self._auth(role_level=100)
        response = self.client.post("/api/companies/", {"name": "NewCo"})
        self.assertEqual(response.status_code, 201)

    def test_create_company_denied_manager(self):
        self._auth(role_level=30)
        response = self.client.post("/api/companies/", {"name": "NewCo2"})
        self.assertEqual(response.status_code, 403)

    def test_get_company_detail(self):
        self._auth(role_level=10)
        response = self.client.get(f"/api/companies/{self.company.id}/")
        self.assertEqual(response.status_code, 200)

    def test_get_my_company(self):
        self._auth(role_level=10)
        response = self.client.get("/api/companies/my/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "TestCo")

    # --- Coverage: CompanyDetailView PATCH branches (lines 43, 48, 55, 58-60) ---

    def test_update_company_admin_own(self):
        """Company admin can update own company (lines 43, 48)."""
        self._auth(role_level=30)
        response = self.client.patch(
            f"/api/companies/{self.company.id}/",
            {"name": "RenamedCo"},
        )
        self.assertEqual(response.status_code, 200)

    def test_update_company_platform_admin(self):
        """Platform admin can update any company (line 55)."""
        self._auth(role_level=100)
        response = self.client.patch(
            f"/api/companies/{self.company.id}/",
            {"name": "AdminRenamed"},
        )
        self.assertEqual(response.status_code, 200)

    def test_update_company_cross_company_denied(self):
        """Company admin cannot update other company (lines 58-60)."""
        other = Company.objects.create(name="OtherCo")
        self._auth(role_level=30)  # company_id = self.company.id
        response = self.client.patch(
            f"/api/companies/{other.id}/",
            {"name": "Hacked"},
        )
        self.assertEqual(response.status_code, 403)

    # --- Coverage: CompanyUsersView queryset branches (lines 70-83) ---

    def test_company_users_platform_admin(self):
        """Platform admin can list any company's users (lines 75-76)."""
        from users.models import UserProfile

        UserProfile.objects.create(
            user_id=10,
            username="cu1",
            email="cu1@t.com",
            company=self.company,
            display_name="CU1",
            role_name="MEMBER",
            role_level=10,
        )
        self._auth(role_level=100)
        response = self.client.get(f"/api/companies/{self.company.id}/users/")
        self.assertEqual(response.status_code, 200)

    def test_company_users_same_company(self):
        """Member can see own company's users (line 83)."""
        from users.models import UserProfile

        UserProfile.objects.create(
            user_id=10,
            username="cu2",
            email="cu2@t.com",
            company=self.company,
            display_name="CU2",
            role_name="MEMBER",
            role_level=10,
        )
        self._auth(role_level=10)
        response = self.client.get(f"/api/companies/{self.company.id}/users/")
        self.assertEqual(response.status_code, 200)

    def test_company_users_cross_company_empty(self):
        """Member cannot see other company's users (lines 80-81)."""
        other = Company.objects.create(name="OtherCo2")
        self._auth(role_level=10)  # company_id = self.company.id
        response = self.client.get(f"/api/companies/{other.id}/users/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

    # --- Coverage: CompanyMyView edge cases (lines 94, 100-101) ---

    def test_my_company_no_association(self):
        """User without company_id_remote (line 94)."""
        patcher = patch("core.authentication.authinator_client")
        mock_client = patcher.start()
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": None,
            "company_name": None,
            "is_verified": True,
            "is_active": True,
        }
        self.addCleanup(patcher.stop)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get("/api/companies/my/")
        self.assertEqual(response.status_code, 404)

    def test_my_company_not_found(self):
        """company_id_remote points to nonexistent company (lines 100-101)."""
        self._auth(role_level=10, company_id=99999)
        response = self.client.get("/api/companies/my/")
        self.assertEqual(response.status_code, 404)
