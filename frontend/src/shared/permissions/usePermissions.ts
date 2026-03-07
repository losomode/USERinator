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
        can_view_company: false,
        can_edit_company: false,
        can_create_company: false,
        can_delete_company: false,
        can_view_user: false,
        can_edit_user: false,
        can_create_member: false,
        can_create_manager: false,
        can_create_admin: false,
        can_change_role: false,
        can_delete_user: false,
        can_deactivate_user: false,
        can_approve_invitation: false,
        can_view_rmas: false,
        can_create_rma: false,
        can_edit_rma: false,
        can_delete_rma: false,
        can_approve_rma: false,
        can_view_items: false,
        can_create_item: false,
        can_edit_item: false,
        can_delete_item: false,
        can_view_pos: false,
        can_create_po: false,
        can_edit_po: false,
        can_delete_po: false,
        can_view_orders: false,
        can_create_order: false,
        can_edit_order: false,
        can_view_deliveries: false,
        can_create_delivery: false,
        can_edit_delivery: false,
        can_view_services: false,
        can_register_service: false,
        can_view_audit_logs: false,
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
