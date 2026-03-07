import React from 'react';
import { usePermissions } from './usePermissions';

type ResourceType = 'company' | 'user' | 'invitation' | 'rma' | 'item' | 'po' | 'order' | 'delivery';

interface PermissionGuardProps {
  /**
   * Resource type (e.g., 'company', 'user', 'rma')
   */
  resource: ResourceType;
  
  /**
   * Permission action (e.g., 'can_edit', 'can_create')
   */
  action: string;
  
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
 * <PermissionGuard resource="company" action="can_edit_own">
 *   <EditButton />
 * </PermissionGuard>
 * 
 * // With fallback
 * <PermissionGuard resource="user" action="can_delete" fallback={<ViewOnlyBadge />}>
 *   <DeleteButton />
 * </PermissionGuard>
 * ```
 */
export function PermissionGuard({ resource, action, children, fallback = null }: PermissionGuardProps) {
  const permissions = usePermissions();
  
  // Access nested permission (e.g., permissions.company.can_edit_own)
  const resourcePerms = permissions[resource] as Record<string, boolean>;
  const hasPermission = resourcePerms?.[action] ?? false;
  
  if (!hasPermission) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
}
