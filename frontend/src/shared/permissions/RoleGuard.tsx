import React from 'react';
import { usePermissions } from './usePermissions';
import type { RoleName } from './types';

interface RoleGuardProps {
  /**
   * Minimum role required (e.g., 'MANAGER' allows MANAGER and ADMIN)
   */
  minRole?: RoleName;
  
  /**
   * Exact role required (e.g., 'ADMIN' only allows ADMIN)
   */
  exactRole?: RoleName;
  
  /**
   * Content to render if user has required role
   */
  children: React.ReactNode;
  
  /**
   * Optional fallback content to render if user lacks role
   */
  fallback?: React.ReactNode;
}

const ROLE_LEVELS = {
  MEMBER: 10,
  MANAGER: 30,
  ADMIN: 100,
};

/**
 * Guard component that conditionally renders children based on user role.
 * 
 * Usage:
 * ```tsx
 * // Only show to MANAGER and ADMIN
 * <RoleGuard minRole="MANAGER">
 *   <AdminPanel />
 * </RoleGuard>
 * 
 * // Only show to ADMIN
 * <RoleGuard exactRole="ADMIN">
 *   <SuperAdminPanel />
 * </RoleGuard>
 * 
 * // With fallback
 * <RoleGuard minRole="ADMIN" fallback={<UpgradePrompt />}>
 *   <PremiumFeature />
 * </RoleGuard>
 * ```
 */
export function RoleGuard({ minRole, exactRole, children, fallback = null }: RoleGuardProps) {
  const { roleLevel } = usePermissions();
  
  let hasAccess = false;
  
  if (exactRole) {
    hasAccess = roleLevel === ROLE_LEVELS[exactRole];
  } else if (minRole) {
    hasAccess = roleLevel >= ROLE_LEVELS[minRole];
  } else {
    // If neither specified, default to authenticated (any role)
    hasAccess = roleLevel >= 10;
  }
  
  if (!hasAccess) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
}
