"""Tests for roles app."""

from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APITestCase

from roles.models import Role
from users.models import User


class RoleModelTest(TestCase):
    def test_str(self):
        role = Role.objects.create(role_name="TESTER", role_level=50)
        self.assertEqual(str(role), "TESTER (level 50)")

    def test_ordering(self):
        Role.objects.create(role_name="LOW", role_level=5)
        Role.objects.create(role_name="HIGH", role_level=90)
        roles = list(Role.objects.values_list("role_name", flat=True))
        self.assertEqual(roles[0], "HIGH")

    def test_unique_level(self):
        Role.objects.create(role_name="A", role_level=50)
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            Role.objects.create(role_name="B", role_level=50)


class RoleAPITest(APITestCase):

    def setUp(self):
        self.system_role = Role.objects.create(
            role_name="ADMIN", role_level=100, is_system_role=True
        )
        User.objects.create(id=1, username="admin", email="admin@t.com")

    def _auth(self, role_level=100):
        patcher = patch("core.authentication.authinator_client")
        mock_client = patcher.start()
        mock_client.get_user_from_token.return_value = {
            "id": 1,
            "username": "admin",
            "email": "admin@t.com",
            "role": "ADMIN",
            "role_level": role_level,
            "company_id": 1,
            "company_name": "TestCo",
            "is_verified": True,
            "is_active": True,
        }
        self.addCleanup(patcher.stop)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer tok")

    def test_list_roles(self):
        self._auth(role_level=10)
        response = self.client.get("/api/roles/")
        self.assertEqual(response.status_code, 200)

    def test_create_custom_role_admin(self):
        self._auth(role_level=100)
        response = self.client.post(
            "/api/roles/",
            {"role_name": "SUPERVISOR", "role_level": 50, "description": "Mid-level"},
        )
        self.assertEqual(response.status_code, 201)

    def test_create_role_denied_member(self):
        self._auth(role_level=10)
        response = self.client.post(
            "/api/roles/", {"role_name": "HACKER", "role_level": 99}
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_system_role_denied(self):
        self._auth(role_level=100)
        response = self.client.delete(f"/api/roles/{self.system_role.id}/")
        self.assertEqual(response.status_code, 400)

    def test_delete_custom_role(self):
        self._auth(role_level=100)
        custom = Role.objects.create(role_name="CUSTOM", role_level=40)
        response = self.client.delete(f"/api/roles/{custom.id}/")
        self.assertEqual(response.status_code, 204)

    def test_update_system_role_denied(self):
        self._auth(role_level=100)
        response = self.client.patch(
            f"/api/roles/{self.system_role.id}/", {"description": "Changed"}
        )
        self.assertEqual(response.status_code, 400)

    def test_update_custom_role(self):
        """Custom role can be updated (covers RoleUpdateSerializer lines 42-44)."""
        self._auth(role_level=100)
        custom = Role.objects.create(role_name="CUSTOM2", role_level=45)
        response = self.client.patch(
            f"/api/roles/{custom.id}/",
            {"description": "Updated"},
        )
        self.assertEqual(response.status_code, 200)

    def test_get_role_detail(self):
        """GET a single role (covers RoleDetailView GET serializer line 36)."""
        self._auth(role_level=10)
        response = self.client.get(f"/api/roles/{self.system_role.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role_name"], "ADMIN")


class RoleSerializerTest(TestCase):
    """Coverage for role serializer validation branches."""

    def test_create_invalid_level_below(self):
        """Role level below 1 rejected (line 26)."""
        from roles.serializers import RoleCreateSerializer
        from unittest.mock import MagicMock

        mock_request = MagicMock()
        serializer = RoleCreateSerializer(
            data={"role_name": "INVALID", "role_level": 0},
            context={"request": mock_request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("role_level", serializer.errors)

    def test_create_invalid_level_above(self):
        """Role level above 100 rejected (line 26)."""
        from roles.serializers import RoleCreateSerializer
        from unittest.mock import MagicMock

        mock_request = MagicMock()
        serializer = RoleCreateSerializer(
            data={"role_name": "INVALID", "role_level": 101},
            context={"request": mock_request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("role_level", serializer.errors)

    def test_update_invalid_level(self):
        """Update serializer level validation (lines 42-44)."""
        from roles.serializers import RoleUpdateSerializer

        role = Role.objects.create(role_name="TEST", role_level=50)
        serializer = RoleUpdateSerializer(
            role,
            data={"role_level": 200},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("role_level", serializer.errors)

    def test_update_system_role_validate(self):
        """System role blocked by validate() (line 48-49)."""
        from roles.serializers import RoleUpdateSerializer

        role = Role.objects.create(role_name="SYS", role_level=55, is_system_role=True)
        serializer = RoleUpdateSerializer(
            role,
            data={"description": "New"},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
