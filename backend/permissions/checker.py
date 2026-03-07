"""Permission checker for centralized RBAC.

Supports:
- Role-level checks (ADMIN=100, MANAGER=30, MEMBER=10)
- Action-based checks (view, create, edit, delete)
- Company scoping
- Extensible to fine-grained permission strings in the future
"""
from typing import Optional


class PermissionChecker:
    """Centralized permission validation.
    
    Current implementation uses role levels, but designed to support
    fine-grained permission strings in the future.
    """
    
    # Role level constants
    ADMIN_LEVEL = 100
    MANAGER_LEVEL = 30
    MEMBER_LEVEL = 10
    
    def __init__(self, user_id: int, role_level: int, company_id: Optional[int]):
        """Initialize permission checker with user context.
        
        Args:
            user_id: User's ID
            role_level: User's numeric role level (10/30/100)
            company_id: User's company ID (None for platform admins)
        """
        self.user_id = user_id
        self.role_level = role_level
        self.company_id = company_id
    
    @property
    def is_admin(self) -> bool:
        """Check if user is platform admin."""
        return self.role_level >= self.ADMIN_LEVEL
    
    @property
    def is_manager(self) -> bool:
        """Check if user is manager or higher."""
        return self.role_level >= self.MANAGER_LEVEL
    
    @property
    def is_member(self) -> bool:
        """Check if user is at least a member."""
        return self.role_level >= self.MEMBER_LEVEL
    
    def can_view_company(self, target_company_id: int) -> bool:
        """Check if user can view company information.
        
        Rules:
        - ADMIN: all companies
        - MANAGER/MEMBER: own company only
        """
        if self.is_admin:
            return True
        return self.company_id == target_company_id
    
    def can_edit_company(self, target_company_id: int) -> bool:
        """Check if user can edit company information.
        
        Rules:
        - ADMIN: all companies
        - MANAGER: own company only
        - MEMBER: no
        """
        if self.is_admin:
            return True
        if self.is_manager:
            return self.company_id == target_company_id
        return False
    
    def can_create_company(self) -> bool:
        """Check if user can create companies.
        
        Rules:
        - ADMIN: yes
        - MANAGER/MEMBER: no
        """
        return self.is_admin
    
    def can_delete_company(self) -> bool:
        """Check if user can delete companies.
        
        Rules:
        - ADMIN: yes
        - MANAGER/MEMBER: no
        """
        return self.is_admin
    
    def can_view_user(self, target_company_id: int) -> bool:
        """Check if user can view user profiles.
        
        Rules:
        - ADMIN: all users
        - MANAGER/MEMBER: own company only
        """
        if self.is_admin:
            return True
        return self.company_id == target_company_id
    
    def can_edit_user(self, target_company_id: int) -> bool:
        """Check if user can edit user profiles.
        
        Rules:
        - ADMIN: all users
        - MANAGER: own company only
        - MEMBER: no
        """
        if self.is_admin:
            return True
        if self.is_manager:
            return self.company_id == target_company_id
        return False
    
    def can_create_user(self, role_level: int) -> bool:
        """Check if user can create users with specified role.
        
        Rules:
        - ADMIN: can create any role (including other ADMINs)
        - MANAGER: can create MEMBER-level users only
        - MEMBER: no
        """
        if self.is_admin:
            return True
        if self.is_manager:
            return role_level <= self.MEMBER_LEVEL
        return False
    
    def can_delete_user(self) -> bool:
        """Check if user can permanently delete users.
        
        Rules:
        - ADMIN: yes
        - MANAGER/MEMBER: no
        """
        return self.is_admin
    
    def can_deactivate_user(self, target_company_id: int, target_role_level: int) -> bool:
        """Check if user can deactivate users.
        
        Rules:
        - ADMIN: can deactivate anyone
        - MANAGER: can deactivate MEMBER/MANAGER in own company (not ADMIN)
        - MEMBER: no
        """
        if self.is_admin:
            return True
        if self.is_manager:
            # Must be same company and not an ADMIN
            return (self.company_id == target_company_id and 
                   target_role_level < self.ADMIN_LEVEL)
        return False
    
    def can_change_role(self) -> bool:
        """Check if user can change user roles.
        
        Rules:
        - ADMIN: yes
        - MANAGER/MEMBER: no
        """
        return self.is_admin
    
    def can_approve_invitation(self, target_company_id: int) -> bool:
        """Check if user can approve invitations.
        
        Rules:
        - ADMIN: all companies
        - MANAGER: own company only
        - MEMBER: no
        """
        if self.is_admin:
            return True
        if self.is_manager:
            return self.company_id == target_company_id
        return False
    
    def can_view_resource(self, resource_company_id: int) -> bool:
        """Check if user can view company-scoped resource.
        
        Generic check for RMAs, POs, Orders, Deliveries.
        
        Rules:
        - ADMIN: all companies
        - MANAGER/MEMBER: own company only
        """
        if self.is_admin:
            return True
        return self.company_id == resource_company_id
    
    def can_create_for_company(self, target_company_id: int) -> bool:
        """Check if user can create resources for company.
        
        Rules:
        - ADMIN: any company
        - MANAGER/MEMBER: own company only
        """
        if self.is_admin:
            return True
        return self.company_id == target_company_id
    
    def get_permissions_dict(self) -> dict:
        """Get dictionary of all permissions for frontend.
        
        Returns dict with permission flags for UI to hide/show actions.
        """
        return {
            'role_level': self.role_level,
            'is_admin': self.is_admin,
            'is_manager': self.is_manager,
            'is_member': self.is_member,
            'company': {
                'can_create': self.can_create_company(),
                'can_edit_own': self.is_manager or self.is_admin,
                'can_delete': self.can_delete_company(),
            },
            'user': {
                'can_create_member': self.is_manager or self.is_admin,
                'can_create_admin': self.is_admin,
                'can_edit': self.is_manager or self.is_admin,
                'can_delete': self.is_admin,
                'can_deactivate': self.is_manager or self.is_admin,
                'can_change_role': self.is_admin,
            },
            'invitation': {
                'can_approve': self.is_manager or self.is_admin,
            },
            'rma': {
                'can_view': True,
                'can_create': True,
                'can_edit': self.is_admin,
                'can_delete': self.is_admin,
                'can_approve': self.is_admin,
            },
            'item': {
                'can_view': self.is_admin,
                'can_create': self.is_admin,
                'can_edit': self.is_admin,
                'can_delete': self.is_admin,
            },
            'po': {
                'can_view': True,
                'can_create': True,
                'can_edit': self.is_admin,
                'can_delete': self.is_admin,
            },
            'order': {
                'can_view': True,
                'can_create': self.is_admin,
                'can_edit': self.is_admin,
                'can_delete': False,  # No one can delete orders (audit trail)
            },
            'delivery': {
                'can_view': True,
                'can_create': self.is_admin,
                'can_edit': self.is_admin,
                'can_delete': False,  # No one can delete deliveries (audit trail)
            },
        }
