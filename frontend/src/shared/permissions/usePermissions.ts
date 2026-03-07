import { useMemo } from 'react';
import { useAuth } from '../auth/AuthProvider';
import type { Permissions, RoleLevel } from './types';

/**
 * Hook to access user permissions from the auth context.
 * 
 * Returns the full permissions object from the backend, plus convenience
 * role-level checks (isAdmin, isManager, isMember).
 * 
 * Usage:
 * ```tsx
 * const { can_edit_company, isAdmin } = usePermissions();
 * 
 * if (can_edit_company) {
 *   return <EditButton />;
 * }
 * ```
 */
export function usePermissions() {
  const { user } = useAuth();

  const permissions: Permissions = useMemo(() => {
    // Default to no permissions if user not loaded or no permissions object
    if (!user || !user.permissions) {
      return {
        role_level: 0,
        is_admin: false,
        is_manager: false,
        is_member: false,
        company: {
          can_create: false,
          can_edit_own: false,
          can_delete: false,
        },
        user: {
          can_create_member: false,
          can_create_admin: false,
          can_edit: false,
          can_delete: false,
          can_deactivate: false,
          can_change_role: false,
        },
        invitation: {
          can_approve: false,
        },
        rma: {
          can_view: false,
          can_create: false,
          can_edit: false,
          can_delete: false,
          can_approve: false,
        },
        item: {
          can_view: false,
          can_create: false,
          can_edit: false,
          can_delete: false,
        },
        po: {
          can_view: false,
          can_create: false,
          can_edit: false,
          can_delete: false,
        },
        order: {
          can_view: false,
          can_create: false,
          can_edit: false,
          can_delete: false,
        },
        delivery: {
          can_view: false,
          can_create: false,
          can_edit: false,
          can_delete: false,
        },
      };
    }

    return user.permissions;
  }, [user]);

  // Convenience role checks
  const roleLevel = (user?.role_level ?? 0) as RoleLevel;
  const isAdmin = roleLevel >= 100;
  const isManager = roleLevel >= 30;
  const isMember = roleLevel >= 10;

  return {
    ...permissions,
    roleLevel,
    isAdmin,
    isManager,
    isMember,
  };
}
