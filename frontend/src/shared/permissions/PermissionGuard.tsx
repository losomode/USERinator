import React from 'react';
import { usePermissions } from './usePermissions';
import type { Permissions } from './types';

interface PermissionGuardProps {
  /**
   * Permission key to check (e.g., 'can_edit_company')
   */
  permission: keyof Permissions;
  
  /**
   * Content to render if user has permission
   */
  children: React.ReactNode;
  
  /**
   * Optional fallback content to render if user lacks permission
   */
  fallback?: React.ReactNode;
}

/**
 * Guard component that conditionally renders children based on user permissions.
 * 
 * Usage:
 * ```tsx
 * <PermissionGuard permission="can_edit_company">
 *   <EditButton />
 * </PermissionGuard>
 * 
 * // With fallback
 * <PermissionGuard permission="can_delete_user" fallback={<ViewOnlyBadge />}>
 *   <DeleteButton />
 * </PermissionGuard>
 * ```
 */
export function PermissionGuard({ permission, children, fallback = null }: PermissionGuardProps) {
  const permissions = usePermissions();
  
  if (!permissions[permission]) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
}
