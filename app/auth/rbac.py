"""Role-Based Access Control (RBAC) system."""
import logging
from enum import Enum
from typing import List, Dict, Set, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """System permissions."""
    # Chat permissions
    CHAT_SEND = "chat:send"
    CHAT_READ_OWN = "chat:read:own"
    CHAT_READ_ALL = "chat:read:all"
    
    # Task permissions
    TASK_READ_OWN = "task:read:own"
    TASK_UPDATE_OWN = "task:update:own"
    TASK_READ_ALL = "task:read:all"
    TASK_UPDATE_ALL = "task:update:all"
    TASK_CREATE = "task:create"
    TASK_DELETE = "task:delete"
    
    # User permissions
    USER_READ_OWN = "user:read:own"
    USER_UPDATE_OWN = "user:update:own"
    USER_READ_ALL = "user:read:all"
    USER_CREATE = "user:create"
    USER_UPDATE_ALL = "user:update:all"
    USER_DELETE = "user:delete"
    
    # Admin permissions
    ADMIN_DASHBOARD = "admin:dashboard"
    ADMIN_METRICS = "admin:metrics"
    ADMIN_LOGS = "admin:logs"
    ADMIN_AUDIT = "admin:audit"
    
    # System permissions
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MAINTENANCE = "system:maintenance"


class Role(str, Enum):
    """User roles with hierarchical permissions."""
    NEW_HIRE = "new_hire"
    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR_ADMIN = "hr_admin"
    IT_ADMIN = "it_admin"
    SECURITY_ADMIN = "security_admin"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.NEW_HIRE: {
        Permission.CHAT_SEND,
        Permission.CHAT_READ_OWN,
        Permission.TASK_READ_OWN,
        Permission.TASK_UPDATE_OWN,
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
    },
    Role.EMPLOYEE: {
        Permission.CHAT_SEND,
        Permission.CHAT_READ_OWN,
        Permission.TASK_READ_OWN,
        Permission.TASK_UPDATE_OWN,
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
    },
    Role.MANAGER: {
        Permission.CHAT_SEND,
        Permission.CHAT_READ_OWN,
        Permission.CHAT_READ_ALL,  # Can view team chats
        Permission.TASK_READ_OWN,
        Permission.TASK_UPDATE_OWN,
        Permission.TASK_READ_ALL,  # Can view team tasks
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
        Permission.USER_READ_ALL,  # Can view team members
        Permission.ADMIN_DASHBOARD,
    },
    Role.HR_ADMIN: {
        Permission.CHAT_SEND,
        Permission.CHAT_READ_OWN,
        Permission.CHAT_READ_ALL,
        Permission.TASK_READ_OWN,
        Permission.TASK_UPDATE_OWN,
        Permission.TASK_READ_ALL,
        Permission.TASK_UPDATE_ALL,
        Permission.TASK_CREATE,
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
        Permission.USER_READ_ALL,
        Permission.USER_CREATE,
        Permission.USER_UPDATE_ALL,
        Permission.ADMIN_DASHBOARD,
        Permission.ADMIN_METRICS,
    },
    Role.IT_ADMIN: {
        Permission.CHAT_SEND,
        Permission.CHAT_READ_OWN,
        Permission.TASK_READ_OWN,
        Permission.TASK_UPDATE_OWN,
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
        Permission.ADMIN_DASHBOARD,
        Permission.ADMIN_LOGS,
        Permission.SYSTEM_CONFIG,
    },
    Role.SECURITY_ADMIN: {
        Permission.CHAT_SEND,
        Permission.CHAT_READ_OWN,
        Permission.CHAT_READ_ALL,
        Permission.TASK_READ_OWN,
        Permission.TASK_UPDATE_OWN,
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
        Permission.USER_READ_ALL,
        Permission.ADMIN_DASHBOARD,
        Permission.ADMIN_LOGS,
        Permission.ADMIN_AUDIT,
    },
    Role.ADMIN: {
        Permission.CHAT_SEND,
        Permission.CHAT_READ_OWN,
        Permission.CHAT_READ_ALL,
        Permission.TASK_READ_OWN,
        Permission.TASK_UPDATE_OWN,
        Permission.TASK_READ_ALL,
        Permission.TASK_UPDATE_ALL,
        Permission.TASK_CREATE,
        Permission.TASK_DELETE,
        Permission.USER_READ_OWN,
        Permission.USER_UPDATE_OWN,
        Permission.USER_READ_ALL,
        Permission.USER_CREATE,
        Permission.USER_UPDATE_ALL,
        Permission.USER_DELETE,
        Permission.ADMIN_DASHBOARD,
        Permission.ADMIN_METRICS,
        Permission.ADMIN_LOGS,
        Permission.ADMIN_AUDIT,
    },
    Role.SUPER_ADMIN: set(Permission),  # All permissions
}


class RBACService:
    """Role-Based Access Control service."""
    
    def __init__(self):
        self.role_permissions = ROLE_PERMISSIONS
    
    def get_role_permissions(self, role: str) -> Set[Permission]:
        """Get all permissions for a role."""
        try:
            role_enum = Role(role)
            return self.role_permissions.get(role_enum, set())
        except ValueError:
            # Unknown role, return minimal permissions
            logger.warning(f"Unknown role: {role}, returning minimal permissions")
            return self.role_permissions.get(Role.NEW_HIRE, set())
    
    def has_permission(self, user_role: str, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        permissions = self.get_role_permissions(user_role)
        return permission in permissions
    
    def has_any_permission(self, user_role: str, permissions: List[Permission]) -> bool:
        """Check if a role has any of the specified permissions."""
        user_permissions = self.get_role_permissions(user_role)
        return bool(user_permissions.intersection(set(permissions)))
    
    def has_all_permissions(self, user_role: str, permissions: List[Permission]) -> bool:
        """Check if a role has all of the specified permissions."""
        user_permissions = self.get_role_permissions(user_role)
        return set(permissions).issubset(user_permissions)
    
    def get_permission_list(self, role: str) -> List[str]:
        """Get list of permission strings for a role."""
        permissions = self.get_role_permissions(role)
        return [p.value for p in permissions]
    
    def can_access_resource(
        self, 
        user_role: str, 
        resource_type: str, 
        action: str,
        resource_owner_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Check if user can access a resource.
        
        Args:
            user_role: User's role
            resource_type: Type of resource (chat, task, user, admin)
            action: Action to perform (read, update, create, delete)
            resource_owner_id: ID of the resource owner
            user_id: Current user's ID
        
        Returns:
            True if access is allowed
        """
        # Build permission string
        is_own = resource_owner_id == user_id if resource_owner_id and user_id else False
        
        if action in ["read", "update"]:
            # Check if user can access own resource
            own_permission = f"{resource_type}:{action}:own"
            all_permission = f"{resource_type}:{action}:all"
            
            try:
                if is_own and self.has_permission(user_role, Permission(own_permission)):
                    return True
                if self.has_permission(user_role, Permission(all_permission)):
                    return True
            except ValueError:
                pass
        else:
            # For create/delete, check direct permission
            permission_str = f"{resource_type}:{action}"
            try:
                return self.has_permission(user_role, Permission(permission_str))
            except ValueError:
                pass
        
        return False


@lru_cache()
def get_rbac_service() -> RBACService:
    """Get cached RBAC service instance."""
    return RBACService()

