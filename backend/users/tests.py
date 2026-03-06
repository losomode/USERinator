"""Tests for users app — models, serializers, views."""

from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APITestCase

from companies.models import Company
from users.models import User, UserProfile


class UserProfileModelTest(TestCase):
    """Tests for UserProfile model."""

    def setUp(self):
        self.company = Company.objects.create(name="TestCo")
        self.profile = UserProfile.objects.create(
            user_id=1,
            username="testuser",
            email="test@test.com",
            company=self.company,
            display_name="Test User",
            role_name="ADMIN",
            role_level=100,
        )

    def test_str(self):
        self.assertEqual(str(self.profile), "Test User (testuser)")

    def test_is_admin_property(self):
        self.assertTrue(self.profile.is_admin)

    def test_is_company_admin_property(self):
        self.assertTrue(self.profile.is_company_admin)

    def test_member_not_admin(self):
        member = UserProfile.objects.create(
            user_id=2,
            username="member",
            email="m@t.com",
            company=self.company,
            display_name="Member",
            role_name="MEMBER",
            role_level=10,
        )
        self.assertFalse(member.is_admin)
        self.assertFalse(member.is_company_admin)

    def test_company_protect(self):
        """Cannot delete company with profiles."""
        from django.db.models import ProtectedError

        with self.assertRaises(ProtectedError):
            self.company.delete()


def _mock_auth(user_data):
    """Helper to mock authentication for API tests."""

    def decorator(func):
        @patch("core.authentication.authinator_client")
        def wrapper(self, mock_client, *args, **kwargs):
            mock_client.get_user_from_token.return_value = user_data
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class HealthCheckTest(APITestCase):
    """Test health check endpoint."""

    def test_health_check(self):
        response = self.client.get("/api/users/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "healthy")


class UserProfileAPITest(APITestCase):
    """Tests for user profile API endpoints."""

    def setUp(self):
        self.company = Company.objects.create(name="TestCo")
        self.admin_user = User.objects.create(
            id=1, username="admin", email="admin@t.com"
        )
        self.member_user = User.objects.create(
            id=2, username="member", email="member@t.com"
        )
        self.admin_profile = UserProfile.objects.create(
            user_id=1,
            username="admin",
            email="admin@t.com",
            company=self.company,
            display_name="Admin User",
            role_name="ADMIN",
            role_level=100,
        )
        self.member_profile = UserProfile.objects.create(
            user_id=2,
            username="member",
            email="member@t.com",
            company=self.company,
            display_name="Member User",
            role_name="MEMBER",
            role_level=10,
        )

    def _auth_as(self, user_id, role_level, company_id):
        """Set up mock auth for a specific user."""
        user_data = {
            "id": user_id,
            "username": f"user{user_id}",
            "email": f"u{user_id}@t.com",
            "role": "ADMIN" if role_level >= 100 else "MEMBER",
            "role_level": role_level,
            "company_id": company_id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        patcher = patch("core.authentication.authinator_client")
        mock_client = patcher.start()
        mock_client.get_user_from_token.return_value = user_data
        self.addCleanup(patcher.stop)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer test-token")

    @patch("core.authentication.authinator_client")
    def test_list_profiles_admin(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get("/api/users/")
        self.assertEqual(response.status_code, 200)

    @patch("core.authentication.authinator_client")
    def test_get_me(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "admin")

    @patch("core.authentication.authinator_client")
    def test_get_user_role(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get(f"/api/users/{self.admin_profile.user_id}/role/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role_name"], "ADMIN")
        self.assertEqual(response.data["role_level"], 100)

    @patch("core.authentication.authinator_client")
    def test_update_own_profile(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 2,
            "username": "member",
            "email": "member@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.patch("/api/users/me/", {"display_name": "New Name"})
        self.assertEqual(response.status_code, 200)

    @patch("core.authentication.authinator_client")
    def test_search_profiles(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get("/api/users/?search=admin")
        self.assertEqual(response.status_code, 200)

    @patch("core.authentication.authinator_client")
    def test_preferences_me(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get("/api/users/preferences/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["timezone"], "UTC")

    @patch("core.authentication.authinator_client")
    def test_preferences_update(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.patch(
            "/api/users/preferences/me/",
            {"timezone": "US/Eastern", "language": "es"},
        )
        self.assertEqual(response.status_code, 200)

    # --- Coverage: UserProfileListCreateView POST branch (lines 27, 32) ---

    @patch("core.authentication.authinator_client")
    def test_create_profile_admin(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.post(
            "/api/users/",
            {
                "user_id": 99,
                "username": "newbie",
                "email": "newbie@t.com",
                "company": self.company.id,
                "display_name": "Newbie",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(response.status_code, 201)

    @patch("core.authentication.authinator_client")
    def test_create_profile_denied_member(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 2,
            "username": "member",
            "email": "member@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.post(
            "/api/users/",
            {
                "user_id": 99,
                "username": "newbie",
                "email": "newbie@t.com",
                "company": self.company.id,
                "display_name": "Newbie",
                "role_name": "MEMBER",
                "role_level": 10,
            },
        )
        self.assertEqual(response.status_code, 403)

    # --- Coverage: role_level filter (line 52) ---

    @patch("core.authentication.authinator_client")
    def test_filter_by_role_level(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get("/api/users/?role_level=100")
        self.assertEqual(response.status_code, 200)

    # --- Coverage: Detail view GET/PATCH/DELETE branches (lines 63-67, 70-72, 75, 79-80, 84-104) ---

    @patch("core.authentication.authinator_client")
    def test_detail_get_profile(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get(f"/api/users/{self.admin_profile.user_id}/")
        self.assertEqual(response.status_code, 200)

    @patch("core.authentication.authinator_client")
    def test_detail_patch_admin(self, mock_client):
        """Admin PATCH uses AdminUpdateSerializer (lines 64-65)."""
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.patch(
            f"/api/users/{self.member_profile.user_id}/",
            {"display_name": "Updated by Admin"},
        )
        self.assertEqual(response.status_code, 200)

    @patch("core.authentication.authinator_client")
    def test_detail_patch_member_own_profile(self, mock_client):
        """Member PATCH own profile uses UpdateSerializer (line 66)."""
        mock_client.get_user_from_token.return_value = {
            "id": 2,
            "username": "member",
            "email": "member@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.patch(
            f"/api/users/{self.member_profile.user_id}/",
            {"display_name": "Updated Self"},
        )
        self.assertEqual(response.status_code, 200)

    @patch("core.authentication.authinator_client")
    def test_detail_patch_member_other_denied(self, mock_client):
        """Member cannot PATCH another member's profile (line 103-104)."""
        mock_client.get_user_from_token.return_value = {
            "id": 2,
            "username": "member",
            "email": "member@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.patch(
            f"/api/users/{self.admin_profile.user_id}/",
            {"display_name": "Hacked"},
        )
        self.assertEqual(response.status_code, 403)

    @patch("core.authentication.authinator_client")
    def test_detail_get_cross_company_denied(self, mock_client):
        """Member cannot view profiles from other company (lines 99-102)."""
        other_co = Company.objects.create(name="OtherCo")
        other_profile = UserProfile.objects.create(
            user_id=99,
            username="other",
            email="other@t.com",
            company=other_co,
            display_name="Other",
            role_name="MEMBER",
            role_level=10,
        )
        mock_client.get_user_from_token.return_value = {
            "id": 2,
            "username": "member",
            "email": "member@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get(f"/api/users/{other_profile.user_id}/")
        self.assertEqual(response.status_code, 403)

    @patch("core.authentication.authinator_client")
    def test_detail_manager_cross_company_denied(self, mock_client):
        """Manager cannot access profiles from other company (lines 91-94)."""
        other_co = Company.objects.create(name="OtherCo2")
        other_profile = UserProfile.objects.create(
            user_id=98,
            username="other2",
            email="other2@t.com",
            company=other_co,
            display_name="Other2",
            role_name="MEMBER",
            role_level=10,
        )
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "MANAGER",
            "role_level": 30,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get(f"/api/users/{other_profile.user_id}/")
        self.assertEqual(response.status_code, 403)

    @patch("core.authentication.authinator_client")
    def test_delete_profile_admin(self, mock_client):
        """Admin soft-deletes a profile (lines 70-72, 79-80)."""
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.delete(f"/api/users/{self.member_profile.user_id}/")
        self.assertEqual(response.status_code, 204)
        self.member_profile.refresh_from_db()
        self.assertFalse(self.member_profile.is_active)

    # --- Coverage: Me view 404 branches (lines 117-118, 128-129) ---

    @patch("core.authentication.authinator_client")
    def test_me_get_no_profile(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 999,
            "username": "ghost",
            "email": "ghost@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, 404)

    @patch("core.authentication.authinator_client")
    def test_me_patch_no_profile(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 999,
            "username": "ghost",
            "email": "ghost@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.patch("/api/users/me/", {"display_name": "X"})
        self.assertEqual(response.status_code, 404)

    # --- Coverage: Batch view (lines 147-158) ---

    @patch("core.authentication.authinator_client")
    def test_batch_fetch(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.post(
            "/api/users/batch/",
            {"user_ids": [1, 2]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    @patch("core.authentication.authinator_client")
    def test_batch_invalid_input(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.post(
            "/api/users/batch/",
            {"user_ids": "not-a-list"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    # --- Coverage: Role view 404 (lines 169-170) ---

    @patch("core.authentication.authinator_client")
    def test_role_view_not_found(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": 100,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get("/api/users/99999/role/")
        self.assertEqual(response.status_code, 404)

    # --- Coverage: Preferences 404 branches (lines 186-187, 197-198) ---

    @patch("core.authentication.authinator_client")
    def test_preferences_get_no_profile(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 999,
            "username": "ghost",
            "email": "ghost@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.get("/api/users/preferences/me/")
        self.assertEqual(response.status_code, 404)

    @patch("core.authentication.authinator_client")
    def test_preferences_patch_no_profile(self, mock_client):
        mock_client.get_user_from_token.return_value = {
            "id": 999,
            "username": "ghost",
            "email": "ghost@t.com",
            "role": "MEMBER",
            "role_level": 10,
            "company_id": self.company.id,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")
        response = self.client.patch("/api/users/preferences/me/", {"timezone": "UTC"})
        self.assertEqual(response.status_code, 404)


class UserSerializerTest(TestCase):
    """Coverage for serializer validation branches."""

    def setUp(self):
        self.company = Company.objects.create(name="TestCo")
        self.profile = UserProfile.objects.create(
            user_id=1,
            username="admin",
            email="admin@t.com",
            company=self.company,
            display_name="Admin",
            role_name="ADMIN",
            role_level=100,
        )

    def test_detail_serializer_hides_fields_for_member(self):
        """Non-admin users don't see notification fields (lines 37-38)."""
        from users.serializers import UserProfileDetailSerializer

        mock_request = MagicMock()
        mock_request.user.role_level = 10
        serializer = UserProfileDetailSerializer(
            self.profile, context={"request": mock_request}
        )
        data = serializer.data
        self.assertNotIn("notification_email", data)
        self.assertNotIn("notification_in_app", data)

    def test_admin_update_escalation_denied(self):
        """Cannot assign role_level higher than own (lines 69-76)."""
        from users.serializers import UserProfileAdminUpdateSerializer

        mock_request = MagicMock()
        mock_request.user.role_level = 30
        serializer = UserProfileAdminUpdateSerializer(
            self.profile,
            data={"role_level": 100},
            partial=True,
            context={"request": mock_request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("role_level", serializer.errors)

    def test_create_serializer_escalation_denied(self):
        """Create serializer prevents escalation (lines 90-97)."""
        from users.serializers import UserProfileCreateSerializer

        mock_request = MagicMock()
        mock_request.user.role_level = 30
        serializer = UserProfileCreateSerializer(
            data={
                "user_id": 50,
                "username": "esc",
                "email": "esc@t.com",
                "company": self.company.id,
                "display_name": "Esc",
                "role_name": "ADMIN",
                "role_level": 100,
            },
            context={"request": mock_request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("role_level", serializer.errors)

    def test_invalid_timezone_rejected(self):
        """Invalid timezone rejected (lines 123-124)."""
        from users.serializers import PreferencesSerializer

        serializer = PreferencesSerializer(
            self.profile,
            data={"timezone": "Invalid/Zone"},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("timezone", serializer.errors)

    def test_invalid_language_rejected(self):
        """Invalid language rejected (line 131)."""
        from users.serializers import PreferencesSerializer

        serializer = PreferencesSerializer(
            self.profile,
            data={"language": "xx"},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("language", serializer.errors)


class ServiceKeyAuthTest(APITestCase):
    """Tests for service-key authentication on the role endpoint."""

    def setUp(self):
        self.company = Company.objects.create(name="TestCo")
        self.profile = UserProfile.objects.create(
            user_id=1,
            username="testuser",
            email="test@t.com",
            company=self.company,
            display_name="Test User",
            role_name="ADMIN",
            role_level=100,
        )

    def test_role_endpoint_with_valid_service_key(self):
        """Service key grants access to role endpoint without JWT."""
        from django.conf import settings

        response = self.client.get(
            f"/api/users/{self.profile.user_id}/role/",
            HTTP_X_SERVICE_KEY=settings.INTERNAL_SERVICE_KEY,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role_name"], "ADMIN")
        self.assertEqual(response.data["role_level"], 100)

    def test_role_endpoint_with_invalid_service_key(self):
        """Invalid service key is rejected."""
        response = self.client.get(
            f"/api/users/{self.profile.user_id}/role/",
            HTTP_X_SERVICE_KEY="wrong-key",
        )
        self.assertEqual(response.status_code, 403)

    def test_role_endpoint_without_any_auth(self):
        """No auth at all is rejected."""
        response = self.client.get(
            f"/api/users/{self.profile.user_id}/role/",
        )
        self.assertEqual(response.status_code, 403)

    def test_role_endpoint_service_key_not_found(self):
        """Service key auth works but user not found returns 404."""
        from django.conf import settings

        response = self.client.get(
            "/api/users/99999/role/",
            HTTP_X_SERVICE_KEY=settings.INTERNAL_SERVICE_KEY,
        )
        self.assertEqual(response.status_code, 404)
