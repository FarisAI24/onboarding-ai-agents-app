"""FastAPI dependencies for authentication."""
import logging
from typing import Optional, List, Callable

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db, User
from app.auth.service import decode_token, AuthService, _session_cache
from app.auth.rbac import Permission, get_rbac_service

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_token_data(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """Extract and validate token from request."""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        return None
    
    # Check token type
    if payload.get("type") != "access":
        return None
    
    return payload


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token_data: Optional[dict] = Depends(get_token_data)
) -> User:
    """Get the current authenticated user."""
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = int(token_data.get("sub"))
    session_id = token_data.get("session_id")
    
    # Verify session is still valid
    if session_id:
        session = _session_cache.get(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalidated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Update session activity
        _session_cache.update_activity(session_id)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Store user and token data in request state for audit logging
    request.state.user = user
    request.state.token_data = token_data
    request.state.session_id = session_id
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    token_data: Optional[dict] = Depends(get_token_data)
) -> Optional[User]:
    """Get the current user if authenticated, None otherwise."""
    if not token_data:
        return None
    
    try:
        user_id = int(token_data.get("sub"))
        session_id = token_data.get("session_id")
        
        # Verify session is still valid
        if session_id:
            session = _session_cache.get(session_id)
            if not session:
                return None
            _session_cache.update_activity(session_id)
        
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            request.state.user = user
            request.state.token_data = token_data
            request.state.session_id = session_id
        return user
    except Exception:
        return None


def require_roles(*allowed_roles: str) -> Callable:
    """
    Dependency factory that requires the user to have one of the allowed roles.
    
    Usage:
        @router.get("/admin/users", dependencies=[Depends(require_roles("admin", "hr_admin"))])
        async def get_users():
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.user_type.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


def require_permissions(*required_permissions: Permission) -> Callable:
    """
    Dependency factory that requires the user to have all specified permissions.
    
    Usage:
        @router.get("/admin/audit", dependencies=[Depends(require_permissions(Permission.ADMIN_AUDIT))])
        async def get_audit_logs():
            ...
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        rbac = get_rbac_service()
        
        if not rbac.has_all_permissions(current_user.user_type.value, list(required_permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permissions: {', '.join(p.value for p in required_permissions)}"
            )
        return current_user
    
    return permission_checker


def require_any_permission(*required_permissions: Permission) -> Callable:
    """
    Dependency factory that requires the user to have at least one of the specified permissions.
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        rbac = get_rbac_service()
        
        if not rbac.has_any_permission(current_user.user_type.value, list(required_permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Need at least one of: {', '.join(p.value for p in required_permissions)}"
            )
        return current_user
    
    return permission_checker


class ResourceAccessChecker:
    """Helper class for checking resource-level access."""
    
    def __init__(self, resource_type: str):
        self.resource_type = resource_type
        self.rbac = get_rbac_service()
    
    def can_read(self, user: User, resource_owner_id: int) -> bool:
        """Check if user can read the resource."""
        return self.rbac.can_access_resource(
            user.user_type.value,
            self.resource_type,
            "read",
            resource_owner_id,
            user.id
        )
    
    def can_update(self, user: User, resource_owner_id: int) -> bool:
        """Check if user can update the resource."""
        return self.rbac.can_access_resource(
            user.user_type.value,
            self.resource_type,
            "update",
            resource_owner_id,
            user.id
        )
    
    def can_delete(self, user: User, resource_owner_id: int) -> bool:
        """Check if user can delete the resource."""
        return self.rbac.can_access_resource(
            user.user_type.value,
            self.resource_type,
            "delete",
            resource_owner_id,
            user.id
        )
    
    def can_create(self, user: User) -> bool:
        """Check if user can create the resource."""
        return self.rbac.can_access_resource(
            user.user_type.value,
            self.resource_type,
            "create"
        )


# Pre-configured access checkers
task_access = ResourceAccessChecker("task")
user_access = ResourceAccessChecker("user")
chat_access = ResourceAccessChecker("chat")

