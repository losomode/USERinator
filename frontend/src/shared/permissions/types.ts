/**
 * Permission types for RBAC system.
 * These match the permissions returned by USERinator's /api/users/{user_id}/context/ endpoint.
 */

export interface Permissions {
  // Company permissions
  can_view_company: boolean;
  can_edit_company: boolean;
  can_create_company: boolean;
  can_delete_company: boolean;

  // User permissions
  can_view_user: boolean;
  can_edit_user: boolean;
  can_create_member: boolean;
  can_create_manager: boolean;
  can_create_admin: boolean;
  can_change_role: boolean;
  can_delete_user: boolean;
  can_deactivate_user: boolean;

  // Invitation permissions
  can_approve_invitation: boolean;

  // RMA permissions
  can_view_rmas: boolean;
  can_create_rma: boolean;
  can_edit_rma: boolean;
  can_delete_rma: boolean;
  can_approve_rma: boolean;

  // Item permissions (catalog/SKU management)
  can_view_items: boolean;
  can_create_item: boolean;
  can_edit_item: boolean;
  can_delete_item: boolean;

  // Purchase Order permissions
  can_view_pos: boolean;
  can_create_po: boolean;
  can_edit_po: boolean;
  can_delete_po: boolean;

  // Order permissions
  can_view_orders: boolean;
  can_create_order: boolean;
  can_edit_order: boolean;

  // Delivery permissions
  can_view_deliveries: boolean;
  can_create_delivery: boolean;
  can_edit_delivery: boolean;

  // Service registry permissions
  can_view_services: boolean;
  can_register_service: boolean;

  // Audit log permissions
  can_view_audit_logs: boolean;
}

export enum RoleLevel {
  MEMBER = 10,
  MANAGER = 30,
  ADMIN = 100,
}

export type RoleName = 'MEMBER' | 'MANAGER' | 'ADMIN';
