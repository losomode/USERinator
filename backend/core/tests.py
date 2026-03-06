"""Tests for core authentication, permissions, and management commands."""

from io import StringIO
from unittest.mock import patch, MagicMock

from django.core.management import call_command
from django.test import TestCase, RequestFactory, override_settings
from rest_framework.exceptions import AuthenticationFailed

from companies.models import Company
from core.authentication import (
    AuthinatorJWTAuthentication,
    _get_or_create_local_user,
    _attach_userinator_attrs,
)
from core.permissions import (
    IsCompanyAdmin,
    IsPlatformAdmin,
    IsOwnerOrCompanyAdmin,
)
from invitations.models import UserInvitation
from roles.models import Role
from users.models import User, UserProfile


class AuthinatorClientTest(TestCase):
    """Tests for AuthinatorClient."""

    @patch("core.authinator_client.requests.get")
    @patch("core.authinator_client.cache")
    def test_get_user_from_token_success(self, mock_cache, mock_get):
        from core.authinator_client import AuthinatorClient

        mock_cache.get.return_value = None
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "role": "MEMBER",
            "role_level": 10,
            "company": {"id": 1, "name": "TestCo"},
            "is_verified": True,
            "is_active": True,
        }
        mock_get.return_value = mock_response

        client = AuthinatorClient()
        result = client.get_user_from_token("valid-token-12345")

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["username"], "testuser")
        self.assertEqual(result["company_id"], 1)
        mock_cache.set.assert_called_once()

    @patch("core.authinator_client.requests.get")
    @patch("core.authinator_client.cache")
    def test_get_user_from_token_cached(self, mock_cache, mock_get):
        from core.authinator_client import AuthinatorClient

        cached = {"id": 1, "username": "cached"}
        mock_cache.get.return_value = cached

        client = AuthinatorClient()
        result = client.get_user_from_token("cached-token-12345")

        self.assertEqual(result, cached)
        mock_get.assert_not_called()

    @patch("core.authinator_client.requests.get")
    @patch("core.authinator_client.cache")
    def test_get_user_from_token_invalid(self, mock_cache, mock_get):
        from core.authinator_client import AuthinatorClient

        mock_cache.get.return_value = None
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        client = AuthinatorClient()
        result = client.get_user_from_token("bad-token-123456789")
        self.assertIsNone(result)

    @patch("core.authinator_client.requests.get")
    @patch("core.authinator_client.cache")
    def test_get_user_from_token_network_error(self, mock_cache, mock_get):
        from core.authinator_client import AuthinatorClient
        import requests as req

        mock_cache.get.return_value = None
        mock_get.side_effect = req.RequestException("Connection refused")

        client = AuthinatorClient()
        result = client.get_user_from_token("token-network-err1234")
        self.assertIsNone(result)

    @patch("core.authinator_client.requests.get")
    @patch("core.authinator_client.cache")
    def test_verify_token(self, mock_cache, mock_get):
        from core.authinator_client import AuthinatorClient

        mock_cache.get.return_value = {"id": 1}

        client = AuthinatorClient()
        self.assertTrue(client.verify_token("valid-token-12345"))


class GetOrCreateLocalUserTest(TestCase):
    """Tests for _get_or_create_local_user."""

    def test_creates_new_user(self):
        user_data = {"id": 42, "username": "newuser", "email": "new@example.com"}
        user = _get_or_create_local_user(user_data)
        self.assertEqual(user.id, 42)
        self.assertEqual(user.username, "newuser")

    def test_syncs_existing_user(self):
        User.objects.create(id=42, username="oldname", email="old@example.com")
        user_data = {"id": 42, "username": "newname", "email": "new@example.com"}
        user = _get_or_create_local_user(user_data)
        self.assertEqual(user.username, "newname")
        self.assertEqual(user.email, "new@example.com")

    def test_no_update_if_unchanged(self):
        User.objects.create(id=42, username="same", email="same@example.com")
        user_data = {"id": 42, "username": "same", "email": "same@example.com"}
        user = _get_or_create_local_user(user_data)
        self.assertEqual(user.username, "same")


class AttachAttrsTest(TestCase):
    """Tests for _attach_userinator_attrs."""

    def test_attach_admin_attrs(self):
        user = User(id=1, username="admin")
        user_data = {"role": "ADMIN", "role_level": 100, "company_id": 1}
        _attach_userinator_attrs(user, user_data)
        self.assertEqual(user.role_level, 100)
        self.assertTrue(user.is_admin)
        self.assertTrue(user.is_company_admin)

    def test_attach_member_attrs(self):
        user = User(id=2, username="member")
        user_data = {"role": "MEMBER", "role_level": 10, "company_id": 2}
        _attach_userinator_attrs(user, user_data)
        self.assertEqual(user.role_level, 10)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_company_admin)


class AuthenticationTest(TestCase):
    """Tests for AuthinatorJWTAuthentication."""

    def setUp(self):
        self.auth = AuthinatorJWTAuthentication()
        self.factory = RequestFactory()

    def test_no_header_returns_none(self):
        request = self.factory.get("/")
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_invalid_header_format(self):
        request = self.factory.get("/", HTTP_AUTHORIZATION="Token abc123")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @patch("core.authentication.authinator_client")
    def test_invalid_token(self, mock_client):
        mock_client.get_user_from_token.return_value = None
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer invalid")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @patch("core.authentication.authinator_client")
    def test_inactive_user(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "test",
            "email": "t@t.com",
            "is_active": False,
            "role_level": 10,
        }
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer valid-tok")
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    @patch("core.authentication.authinator_client")
    def test_valid_token(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@test.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": 1,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        request = self.factory.get("/", HTTP_AUTHORIZATION="Bearer valid-tok")
        user, token = self.auth.authenticate(request)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role_level, 100)
        self.assertTrue(user.is_admin)


class PermissionTests(TestCase):
    """Tests for permission classes."""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_user(self, role_level=10, company_id=1):
        user = MagicMock()
        user.is_authenticated = True
        user.role_level = role_level
        user.company_id_remote = company_id
        user.id = 1
        return user

    def test_is_company_admin_allows_manager(self):
        request = self.factory.get("/")
        request.user = self._make_user(role_level=30)
        self.assertTrue(IsCompanyAdmin().has_permission(request, None))

    def test_is_company_admin_denies_member(self):
        request = self.factory.get("/")
        request.user = self._make_user(role_level=10)
        self.assertFalse(IsCompanyAdmin().has_permission(request, None))

    def test_is_platform_admin_allows_admin(self):
        request = self.factory.get("/")
        request.user = self._make_user(role_level=100)
        self.assertTrue(IsPlatformAdmin().has_permission(request, None))

    def test_is_platform_admin_denies_manager(self):
        request = self.factory.get("/")
        request.user = self._make_user(role_level=30)
        self.assertFalse(IsPlatformAdmin().has_permission(request, None))

    def test_owner_or_admin_allows_owner(self):
        request = self.factory.get("/")
        request.user = self._make_user(role_level=10)
        obj = MagicMock()
        obj.user_id = 1
        obj.company_id = 1
        self.assertTrue(
            IsOwnerOrCompanyAdmin().has_object_permission(request, None, obj)
        )

    def test_owner_or_admin_allows_company_admin(self):
        request = self.factory.get("/")
        request.user = self._make_user(role_level=30, company_id=1)
        obj = MagicMock()
        obj.company_id = 1
        self.assertTrue(
            IsOwnerOrCompanyAdmin().has_object_permission(request, None, obj)
        )

    def test_owner_or_admin_denies_other_company_admin(self):
        request = self.factory.get("/")
        request.user = self._make_user(role_level=30, company_id=2)
        obj = MagicMock()
        obj.company_id = 1
        self.assertFalse(
            IsOwnerOrCompanyAdmin().has_object_permission(request, None, obj)
        )

    def test_owner_or_admin_allows_platform_admin(self):
        request = self.factory.get("/")
        request.user = self._make_user(role_level=100)
        obj = MagicMock()
        obj.company_id = 999
        self.assertTrue(
            IsOwnerOrCompanyAdmin().has_object_permission(request, None, obj)
        )


# ═══════════════════════════════════════════════════════
# Management Command Tests
# ═══════════════════════════════════════════════════════


class SetupDemoDataCommandTest(TestCase):
    """Tests for the setup_demo_data management command."""

    def test_creates_demo_data(self):
        out = StringIO()
        call_command("setup_demo_data", stdout=out)
        output = out.getvalue()

        self.assertEqual(Company.objects.count(), 3)
        self.assertEqual(UserProfile.objects.count(), 10)
        self.assertEqual(UserInvitation.objects.count(), 3)
        self.assertIn("Demo data setup complete", output)

    def test_idempotent(self):
        call_command("setup_demo_data", stdout=StringIO())
        call_command("setup_demo_data", stdout=StringIO())

        self.assertEqual(Company.objects.count(), 3)
        self.assertEqual(UserProfile.objects.count(), 10)

    def test_output_shows_status(self):
        out1 = StringIO()
        call_command("setup_demo_data", stdout=out1)
        self.assertIn("[Created]", out1.getvalue())

        out2 = StringIO()
        call_command("setup_demo_data", stdout=out2)
        self.assertIn("[Exists]", out2.getvalue())


class VerifyMigrationCommandTest(TestCase):
    """Tests for the verify_migration management command."""

    def setUp(self):
        call_command("create_default_roles", stdout=StringIO())
        self.company = Company.objects.create(name="TestCo")

    def test_empty_database(self):
        out = StringIO()
        call_command("verify_migration", stdout=out)
        output = out.getvalue()
        self.assertIn("User Profiles: 0 total", output)
        self.assertIn("Verification Complete", output)

    def test_with_data(self):
        role = Role.objects.get(role_name="MEMBER")
        UserProfile.objects.create(
            user_id=1,
            username="testuser",
            email="test@test.com",
            company=self.company,
            display_name="Test User",
            role_name=role.role_name,
            role_level=role.role_level,
        )
        out = StringIO()
        call_command("verify_migration", stdout=out)
        output = out.getvalue()
        self.assertIn("User Profiles: 1 total (1 active, 0 inactive)", output)
        self.assertIn("No orphan roles found", output)
        self.assertIn("No duplicate emails found", output)

    def test_detects_orphan_roles(self):
        UserProfile.objects.create(
            user_id=2,
            username="orphan",
            email="orphan@test.com",
            company=self.company,
            display_name="Orphan",
            role_name="CUSTOM_UNKNOWN",
            role_level=50,
        )
        out = StringIO()
        err = StringIO()
        call_command("verify_migration", stdout=out, stderr=err)
        self.assertIn("CUSTOM_UNKNOWN", err.getvalue())

    def test_detects_duplicate_emails(self):
        for uid in (3, 4):
            UserProfile.objects.create(
                user_id=uid,
                username=f"user{uid}",
                email="dupe@test.com",
                company=self.company,
                display_name=f"User {uid}",
                role_name="MEMBER",
                role_level=10,
            )
        out = StringIO()
        err = StringIO()
        call_command("verify_migration", stdout=out, stderr=err)
        self.assertIn("dupe@test.com", err.getvalue())


class MigrateFromAuthinatorCommandTest(TestCase):
    """Tests for the migrate_from_authinator management command."""

    def setUp(self):
        call_command("create_default_roles", stdout=StringIO())

    @patch("core.management.commands.migrate_from_authinator.requests.get")
    def test_dry_run(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": 1,
                    "username": "user1",
                    "email": "u1@test.com",
                    "role": "MEMBER",
                },
            ],
        )
        out = StringIO()
        call_command("migrate_from_authinator", "--dry-run", stdout=out)
        output = out.getvalue()
        self.assertIn("DRY RUN", output)
        self.assertIn("Would create", output)
        self.assertEqual(UserProfile.objects.count(), 0)

    @patch("core.management.commands.migrate_from_authinator.requests.get")
    def test_creates_profiles(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": 10,
                    "username": "migrated",
                    "email": "m@test.com",
                    "role": "ADMIN",
                    "company": {"name": "MigCo"},
                },
            ],
        )
        out = StringIO()
        call_command("migrate_from_authinator", stdout=out)

        self.assertEqual(UserProfile.objects.count(), 1)
        profile = UserProfile.objects.get(user_id=10)
        self.assertEqual(profile.role_name, "ADMIN")
        self.assertEqual(profile.role_level, 100)
        self.assertEqual(profile.company.name, "MigCo")

    @patch("core.management.commands.migrate_from_authinator.requests.get")
    def test_skips_existing(self, mock_get):
        company = Company.objects.create(name="Existing")
        UserProfile.objects.create(
            user_id=20,
            username="existing",
            email="ex@test.com",
            company=company,
            display_name="Existing",
        )
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": 20,
                    "username": "existing",
                    "email": "ex@test.com",
                    "role": "MEMBER",
                },
            ],
        )
        out = StringIO()
        call_command("migrate_from_authinator", stdout=out)
        self.assertIn("Skipped (exists)", out.getvalue())
        self.assertEqual(UserProfile.objects.count(), 1)

    @patch("core.management.commands.migrate_from_authinator.requests.get")
    def test_handles_no_id(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"username": "noid"}],
        )
        out = StringIO()
        err = StringIO()
        call_command("migrate_from_authinator", stdout=out, stderr=err)
        self.assertIn("Skipping user with no id", err.getvalue())

    @patch("core.management.commands.migrate_from_authinator.requests.get")
    def test_handles_api_failure(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=500,
            text="Internal Server Error",
        )
        out = StringIO()
        err = StringIO()
        call_command("migrate_from_authinator", stdout=out, stderr=err)
        self.assertIn("Failed to fetch users", err.getvalue())

    @patch("core.management.commands.migrate_from_authinator.requests.get")
    def test_handles_connection_error(self, mock_get):
        import requests

        mock_get.side_effect = requests.ConnectionError("Connection refused")
        out = StringIO()
        err = StringIO()
        call_command("migrate_from_authinator", stdout=out, stderr=err)
        self.assertIn("Failed to fetch users", err.getvalue())

    @patch("core.management.commands.migrate_from_authinator.requests.get")
    def test_no_roles_error(self, mock_get):
        Role.objects.all().delete()
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [{"id": 1, "username": "u", "email": "u@t.com"}],
        )
        out = StringIO()
        err = StringIO()
        call_command("migrate_from_authinator", stdout=out, stderr=err)
        self.assertIn("No roles found", err.getvalue())

    @patch("core.management.commands.migrate_from_authinator.requests.get")
    def test_default_company(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {
                    "id": 30,
                    "username": "nocompany",
                    "email": "nc@test.com",
                    "role": "MEMBER",
                },
            ],
        )
        out = StringIO()
        call_command(
            "migrate_from_authinator", "--default-company=Fallback Corp", stdout=out
        )
        profile = UserProfile.objects.get(user_id=30)
        self.assertEqual(profile.company.name, "Fallback Corp")

    @patch("core.management.commands.migrate_from_authinator.requests.get")
    def test_paginated_response(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "count": 1,
                "results": [
                    {
                        "id": 40,
                        "username": "paged",
                        "email": "p@t.com",
                        "role": "MEMBER",
                    }
                ],
            },
        )
        out = StringIO()
        call_command("migrate_from_authinator", stdout=out)
        self.assertTrue(UserProfile.objects.filter(user_id=40).exists())


class RegisterServiceCommandTest(TestCase):
    """Tests for register_service management command."""

    @patch("core.management.commands.register_service.requests.post")
    def test_successful_registration(self, mock_post):
        mock_post.return_value = MagicMock(status_code=201)
        out = StringIO()
        call_command("register_service", stdout=out)
        self.assertIn("Successfully registered", out.getvalue())

    @patch("core.management.commands.register_service.requests.post")
    def test_failed_registration(self, mock_post):
        mock_post.return_value = MagicMock(status_code=403, text="Forbidden")
        out = StringIO()
        err = StringIO()
        call_command("register_service", stdout=out, stderr=err)
        self.assertIn("Registration failed", err.getvalue())

    @patch("core.management.commands.register_service.requests.post")
    def test_connection_error(self, mock_post):
        import requests

        mock_post.side_effect = requests.ConnectionError("Connection refused")
        out = StringIO()
        err = StringIO()
        call_command("register_service", stdout=out, stderr=err)
        self.assertIn("Could not reach service registry", err.getvalue())

    @patch("core.management.commands.register_service.requests.post")
    @override_settings(DEPLOY_DOMAIN="app.example.com", DEPLOY_SCHEME="https")
    def test_deploy_domain_updates_urls(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        out = StringIO()
        call_command("register_service", stdout=out)
        call_args = mock_post.call_args
        metadata = call_args.kwargs.get("json") or call_args[1].get("json")
        self.assertIn("app.example.com", metadata["ui_url"])
        self.assertIn("app.example.com", metadata["health_url"])


class HealthCheckEnhancedTest(TestCase):
    """Tests for the enhanced health check endpoint."""

    def test_health_check_returns_enhanced_data(self):
        from users.views import health_check

        request = RequestFactory().get("/api/users/health/")
        response = health_check(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "healthy")
        self.assertEqual(response.data["service"], "USERinator")
        self.assertEqual(response.data["version"], "1.0.0")
        self.assertEqual(response.data["database"], "connected")
        self.assertIn("timestamp", response.data)
