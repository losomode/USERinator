/**
 * Permissions module for RBAC system.
 * 
 * Provides hooks and components for permission-based UI rendering.
 */

export { usePermissions } from './usePermissions';
export { PermissionGuard } from './PermissionGuard';
export { RoleGuard } from './RoleGuard';
export type { Permissions, RoleName } from './types';
export { RoleLevel } from './types';
