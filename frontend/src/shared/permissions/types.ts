/**
 * Permission types for RBAC system.
 * These match the permissions returned by USERinator's /api/users/{user_id}/context/ endpoint.
 * 
 * Permissions are organized by resource type (company, user, rma, etc.)
 */

export interface CompanyPermissions {
  can_create: boolean;
  can_edit_own: boolean;
  can_delete: boolean;
}

export interface UserPermissions {
  can_create_member: boolean;
  can_create_admin: boolean;
  can_edit: boolean;
  can_delete: boolean;
  can_deactivate: boolean;
  can_change_role: boolean;
}

export interface InvitationPermissions {
  can_approve: boolean;
}

export interface RMAPermissions {
  can_view: boolean;
  can_create: boolean;
  can_edit: boolean;
  can_delete: boolean;
  can_approve: boolean;
}

export interface ItemPermissions {
  can_view: boolean;
  can_create: boolean;
  can_edit: boolean;
  can_delete: boolean;
}

export interface POPermissions {
  can_view: boolean;
  can_create: boolean;
  can_edit: boolean;
  can_delete: boolean;
}

export interface OrderPermissions {
  can_view: boolean;
  can_create: boolean;
  can_edit: boolean;
  can_delete: boolean;
}

export interface DeliveryPermissions {
  can_view: boolean;
  can_create: boolean;
  can_edit: boolean;
  can_delete: boolean;
}

/**
 * Complete permissions object returned by backend.
 * Organized by resource type for better clarity.
 */
export interface Permissions {
  role_level: number;
  is_admin: boolean;
  is_manager: boolean;
  is_member: boolean;
  company: CompanyPermissions;
  user: UserPermissions;
  invitation: InvitationPermissions;
  rma: RMAPermissions;
  item: ItemPermissions;
  po: POPermissions;
  order: OrderPermissions;
  delivery: DeliveryPermissions;
}

export enum RoleLevel {
  MEMBER = 10,
  MANAGER = 30,
  ADMIN = 100,
}

export type RoleName = 'MEMBER' | 'MANAGER' | 'ADMIN';
