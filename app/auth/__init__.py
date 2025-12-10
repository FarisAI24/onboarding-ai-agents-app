"""Authentication and authorization module."""
from app.auth.service import (
    AuthService,
    get_auth_service,
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    require_roles,
    get_optional_user,
)
from app.auth.rbac import (
    Permission,
    Role,
    RBACService,
    get_rbac_service,
)
from app.auth.schemas import (
    Token,
    TokenData,
    UserLogin,
    UserRegister,
    PasswordChange,
    SessionInfo,
)

__all__ = [
    # Service
    "AuthService",
    "get_auth_service",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "require_roles",
    "get_optional_user",
    # RBAC
    "Permission",
    "Role",
    "RBACService",
    "get_rbac_service",
    # Schemas
    "Token",
    "TokenData",
    "UserLogin",
    "UserRegister",
    "PasswordChange",
    "SessionInfo",
]

