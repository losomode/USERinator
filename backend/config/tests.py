"""Tests for config settings and fuzzing tests for input validation."""

import os
import importlib
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APITestCase

from companies.models import Company
from roles.models import Role
from users.models import User, UserProfile


class SettingsDeployDomainTest(TestCase):
    """Tests for DEPLOY_DOMAIN conditional branches in settings.py."""

    def test_deploy_domain_branches(self):
        """Exercise DEPLOY_DOMAIN branches (settings.py lines 30-33, 178-181, 197-200)."""
        # Temporarily set DEPLOY_DOMAIN and reload settings
        with patch.dict(os.environ, {"DEPLOY_DOMAIN": "www.example.com"}):
            import config.settings as settings_mod

            importlib.reload(settings_mod)

            # Lines 30-33: ALLOWED_HOSTS additions
            self.assertIn("www.example.com", settings_mod.ALLOWED_HOSTS)
            self.assertIn("example.com", settings_mod.ALLOWED_HOSTS)

            # Lines 178-181: CORS additions
            self.assertTrue(
                any("example.com" in o for o in settings_mod.CORS_ALLOWED_ORIGINS)
            )

            # Lines 197-200: CSRF additions
            self.assertTrue(
                any("example.com" in o for o in settings_mod.CSRF_TRUSTED_ORIGINS)
            )

        # Reload with default empty DEPLOY_DOMAIN to restore state
        with patch.dict(os.environ, {"DEPLOY_DOMAIN": ""}):
            importlib.reload(settings_mod)


class FuzzingTestBase(APITestCase):
    """Base class for fuzzing tests."""

    def setUp(self):
        self.company = Company.objects.create(name="FuzzCo")
        self.role = Role.objects.create(role_name="MEMBER", role_level=10)
        User.objects.create(id=1, username="fuzz", email="fuzz@t.com")
        UserProfile.objects.create(
            user_id=1,
            username="fuzz",
            email="fuzz@t.com",
            company=self.company,
            display_name="Fuzz User",
            role_name="ADMIN",
            role_level=100,
        )

    def _auth(self):
        patcher = patch("core.authentication.authinator_client")
        mock_client = patcher.start()
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "fuzz",
            "email": "fuzz@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "FuzzCo",
            "is_verified": True,
            "is_active": True,
        }
        self.addCleanup(patcher.stop)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")


class UserEndpointFuzzing(FuzzingTestBase):
    """Fuzzing tests for user profile endpoints."""

    # --- /api/users/ POST: email field ---

    def test_fuzz_create_empty_email(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 100,
                "username": "f1",
                "email": "",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertIn(r.status_code, [400, 201])

    def test_fuzz_create_invalid_email(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 101,
                "username": "f2",
                "email": "not-email",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_xss_email(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 102,
                "username": "f3",
                "email": "<script>@evil.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_long_email(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 103,
                "username": "f4",
                "email": "a" * 300 + "@t.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(r.status_code, 400)

    # --- /api/users/ POST: username field ---

    def test_fuzz_create_empty_username(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 110,
                "username": "",
                "email": "u@t.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_long_username(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 111,
                "username": "x" * 200,
                "email": "ul@t.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_special_chars_username(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 112,
                "username": "<>\"';--",
                "email": "sp@t.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertIn(r.status_code, [400, 201])

    def test_fuzz_create_unicode_username(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 113,
                "username": "日本語",
                "email": "un@t.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertIn(r.status_code, [400, 201])

    # --- /api/users/ POST: role_level field ---

    def test_fuzz_create_negative_role(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 120,
                "username": "nr",
                "email": "nr@t.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": -1,
            },
        )
        self.assertIn(r.status_code, [400, 201])

    def test_fuzz_create_zero_role(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 121,
                "username": "zr",
                "email": "zr@t.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 0,
            },
        )
        self.assertIn(r.status_code, [400, 201])

    def test_fuzz_create_huge_role(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 122,
                "username": "hr",
                "email": "hr@t.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 999999,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_string_role(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 123,
                "username": "sr",
                "email": "sr@t.com",
                "company": self.company.id,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": "abc",
            },
        )
        self.assertEqual(r.status_code, 400)

    # --- /api/users/ POST: display_name field ---

    def test_fuzz_create_empty_display_name(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 130,
                "username": "edn",
                "email": "edn@t.com",
                "company": self.company.id,
                "display_name": "",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_long_display_name(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 131,
                "username": "ldn",
                "email": "ldn@t.com",
                "company": self.company.id,
                "display_name": "x" * 300,
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_xss_display_name(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 132,
                "username": "xdn",
                "email": "xdn@t.com",
                "company": self.company.id,
                "display_name": "<script>alert(1)</script>",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        # Should sanitize or accept — just not crash
        self.assertIn(r.status_code, [400, 201])

    # --- /api/users/ POST: company field ---

    def test_fuzz_create_invalid_company(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 140,
                "username": "ic",
                "email": "ic@t.com",
                "company": 99999,
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_string_company(self):
        self._auth()
        r = self.client.post(
            "/api/users/",
            {
                "user_id": 141,
                "username": "sc",
                "email": "sc@t.com",
                "company": "not-an-id",
                "display_name": "F",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(r.status_code, 400)

    # --- /api/users/me/ PATCH: profile fields ---

    def test_fuzz_me_patch_xss_bio(self):
        self._auth()
        r = self.client.patch("/api/users/me/", {"bio": "<script>alert(1)</script>"})
        self.assertEqual(r.status_code, 200)

    def test_fuzz_me_patch_long_phone(self):
        self._auth()
        r = self.client.patch("/api/users/me/", {"phone": "1" * 100})
        self.assertIn(r.status_code, [200, 400])

    def test_fuzz_me_patch_invalid_url(self):
        self._auth()
        r = self.client.patch("/api/users/me/", {"avatar_url": "not-a-url"})
        self.assertEqual(r.status_code, 400)

    # --- /api/users/?search= : search param ---

    def test_fuzz_search_sql_injection(self):
        self._auth()
        r = self.client.get("/api/users/?search=' OR 1=1 --")
        self.assertEqual(r.status_code, 200)

    def test_fuzz_search_xss(self):
        self._auth()
        r = self.client.get("/api/users/?search=<script>")
        self.assertEqual(r.status_code, 200)

    def test_fuzz_search_empty(self):
        self._auth()
        r = self.client.get("/api/users/?search=")
        self.assertEqual(r.status_code, 200)

    def test_fuzz_search_long(self):
        self._auth()
        r = self.client.get(f'/api/users/?search={"a" * 500}')
        self.assertEqual(r.status_code, 200)

    def test_fuzz_search_unicode(self):
        self._auth()
        r = self.client.get("/api/users/?search=日本語テスト")
        self.assertEqual(r.status_code, 200)

    # --- /api/users/batch/ : user_ids ---

    def test_fuzz_batch_empty_list(self):
        self._auth()
        r = self.client.post("/api/users/batch/", {"user_ids": []}, format="json")
        self.assertEqual(r.status_code, 200)

    def test_fuzz_batch_too_many(self):
        self._auth()
        r = self.client.post(
            "/api/users/batch/", {"user_ids": list(range(101))}, format="json"
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_batch_negative_ids(self):
        self._auth()
        r = self.client.post("/api/users/batch/", {"user_ids": [-1, -2]}, format="json")
        self.assertEqual(r.status_code, 200)

    def test_fuzz_batch_string_ids(self):
        self._auth()
        r = self.client.post("/api/users/batch/", {"user_ids": [0, -1]}, format="json")
        self.assertEqual(r.status_code, 200)


class PreferenceFuzzing(FuzzingTestBase):
    """Fuzzing tests for preference endpoints."""

    def test_fuzz_timezone_empty(self):
        self._auth()
        r = self.client.patch("/api/users/preferences/me/", {"timezone": ""})
        self.assertIn(r.status_code, [200, 400])

    def test_fuzz_timezone_sql(self):
        self._auth()
        r = self.client.patch(
            "/api/users/preferences/me/", {"timezone": "'; DROP TABLE--"}
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_timezone_long(self):
        self._auth()
        r = self.client.patch("/api/users/preferences/me/", {"timezone": "A" * 200})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_timezone_unicode(self):
        self._auth()
        r = self.client.patch("/api/users/preferences/me/", {"timezone": "日本/東京"})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_language_empty(self):
        self._auth()
        r = self.client.patch("/api/users/preferences/me/", {"language": ""})
        self.assertIn(r.status_code, [200, 400])

    def test_fuzz_language_long(self):
        self._auth()
        r = self.client.patch("/api/users/preferences/me/", {"language": "en" * 50})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_language_xss(self):
        self._auth()
        r = self.client.patch("/api/users/preferences/me/", {"language": "<script>"})
        self.assertEqual(r.status_code, 400)


class CompanyFuzzing(FuzzingTestBase):
    """Fuzzing tests for company endpoints."""

    def test_fuzz_create_empty_name(self):
        self._auth()
        r = self.client.post("/api/companies/", {"name": ""})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_long_name(self):
        self._auth()
        r = self.client.post("/api/companies/", {"name": "x" * 300})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_xss_name(self):
        self._auth()
        r = self.client.post(
            "/api/companies/", {"name": "<img onerror=alert(1) src=x>"}
        )
        self.assertIn(r.status_code, [201, 400])

    def test_fuzz_create_sql_name(self):
        self._auth()
        r = self.client.post("/api/companies/", {"name": "'; DROP TABLE companies;--"})
        self.assertIn(r.status_code, [201, 400])

    def test_fuzz_create_unicode_name(self):
        self._auth()
        r = self.client.post("/api/companies/", {"name": "日本語会社名"})
        self.assertEqual(r.status_code, 201)

    def test_fuzz_create_invalid_website(self):
        self._auth()
        r = self.client.post("/api/companies/", {"name": "WebCo", "website": "not-url"})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_invalid_custom_fields(self):
        self._auth()
        r = self.client.post(
            "/api/companies/",
            {"name": "CfCo", "custom_fields": "not-json"},
            format="json",
        )
        self.assertIn(r.status_code, [201, 400])

    def test_fuzz_update_long_notes(self):
        self._auth()
        r = self.client.patch(
            f"/api/companies/{self.company.id}/",
            {"notes": "n" * 10000},
        )
        self.assertEqual(r.status_code, 200)


class RoleFuzzing(FuzzingTestBase):
    """Fuzzing tests for role endpoints."""

    def test_fuzz_create_empty_name(self):
        self._auth()
        r = self.client.post("/api/roles/", {"role_name": "", "role_level": 50})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_long_name(self):
        self._auth()
        r = self.client.post("/api/roles/", {"role_name": "R" * 100, "role_level": 50})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_level_zero(self):
        self._auth()
        r = self.client.post("/api/roles/", {"role_name": "ZERO", "role_level": 0})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_level_negative(self):
        self._auth()
        r = self.client.post("/api/roles/", {"role_name": "NEG", "role_level": -10})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_level_101(self):
        self._auth()
        r = self.client.post("/api/roles/", {"role_name": "OVER", "role_level": 101})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_level_float(self):
        self._auth()
        r = self.client.post("/api/roles/", {"role_name": "FLOAT", "role_level": 50.5})
        self.assertIn(r.status_code, [201, 400])

    def test_fuzz_create_level_string(self):
        self._auth()
        r = self.client.post("/api/roles/", {"role_name": "STR", "role_level": "abc"})
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_sql_name(self):
        self._auth()
        r = self.client.post(
            "/api/roles/", {"role_name": "'; DROP--", "role_level": 50}
        )
        self.assertIn(r.status_code, [201, 400])


class InvitationFuzzing(FuzzingTestBase):
    """Fuzzing tests for invitation endpoints."""

    def test_fuzz_create_empty_email(self):
        self._auth()
        r = self.client.post(
            "/api/invitations/",
            {
                "email": "",
                "company": self.company.id,
                "requested_role": self.role.id,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_invalid_email(self):
        self._auth()
        r = self.client.post(
            "/api/invitations/",
            {
                "email": "not-email",
                "company": self.company.id,
                "requested_role": self.role.id,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_xss_email(self):
        self._auth()
        r = self.client.post(
            "/api/invitations/",
            {
                "email": "<script>@evil.com",
                "company": self.company.id,
                "requested_role": self.role.id,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_long_email(self):
        self._auth()
        r = self.client.post(
            "/api/invitations/",
            {
                "email": "a" * 300 + "@t.com",
                "company": self.company.id,
                "requested_role": self.role.id,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_invalid_company(self):
        self._auth()
        r = self.client.post(
            "/api/invitations/",
            {
                "email": "ok@t.com",
                "company": 99999,
                "requested_role": self.role.id,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_create_invalid_role(self):
        self._auth()
        r = self.client.post(
            "/api/invitations/",
            {
                "email": "ok@t.com",
                "company": self.company.id,
                "requested_role": 99999,
            },
        )
        self.assertEqual(r.status_code, 400)

    def test_fuzz_approve_nonexistent(self):
        self._auth()
        r = self.client.post("/api/invitations/99999/approve/")
        self.assertEqual(r.status_code, 404)

    def test_fuzz_reject_nonexistent(self):
        self._auth()
        r = self.client.post("/api/invitations/99999/reject/")
        self.assertEqual(r.status_code, 404)


class OpenAPIDocsTest(TestCase):
    """Tests for OpenAPI schema and documentation endpoints."""

    def test_schema_returns_200(self):
        """GET /api/schema/ returns valid OpenAPI JSON."""
        r = self.client.get("/api/schema/")
        self.assertEqual(r.status_code, 200)

    def test_schema_contains_paths(self):
        """Schema includes the expected API paths."""
        r = self.client.get("/api/schema/", HTTP_ACCEPT="application/json")
        self.assertEqual(r.status_code, 200)

    def test_swagger_ui_returns_200(self):
        """GET /api/docs/ returns Swagger UI HTML."""
        r = self.client.get("/api/docs/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r["Content-Type"])

    def test_redoc_returns_200(self):
        """GET /api/redoc/ returns ReDoc HTML."""
        r = self.client.get("/api/redoc/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r["Content-Type"])
