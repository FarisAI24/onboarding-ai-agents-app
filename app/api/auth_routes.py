"""Authentication API routes."""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db, User
from app.auth.schemas import (
    Token, UserLogin, UserRegister, PasswordChange, 
    UserAuthResponse, RefreshTokenRequest, LogoutRequest, SessionInfo
)
from app.auth.service import get_auth_service, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.dependencies import get_current_user, get_current_active_user
from app.auth.rbac import get_rbac_service
from app.audit import get_audit_logger, AuditAction, AuditResource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request."""
    # Get IP address
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else "unknown"
    
    user_agent = request.headers.get("user-agent", "unknown")
    return ip_address, user_agent


@router.post("/register", response_model=UserAuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    New users are created with 'new_hire' role by default.
    """
    ip_address, user_agent = get_client_info(request)
    audit = get_audit_logger(db)
    
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        audit.log_auth_event(
            action=AuditAction.REGISTER,
            user_email=user_data.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Email already registered"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    auth_service = get_auth_service(db)
    user = auth_service.register_user(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role,
        department=user_data.department
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    rbac = get_rbac_service()
    permissions = rbac.get_permission_list(user.user_type.value)
    
    # Log successful registration
    audit.log_auth_event(
        action=AuditAction.REGISTER,
        user_id=user.id,
        user_email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        details={"role": user.role, "department": user.department}
    )
    
    return UserAuthResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        department=user.department,
        user_type=user.user_type.value,
        permissions=permissions
    )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    Returns access and refresh tokens on successful authentication.
    """
    ip_address, user_agent = get_client_info(request)
    audit = get_audit_logger(db)
    auth_service = get_auth_service(db)
    
    user = auth_service.authenticate_user(credentials.email, credentials.password)
    
    if not user:
        # Log failed login attempt
        audit.log_auth_event(
            action=AuditAction.LOGIN_FAILED,
            user_email=credentials.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        audit.log_auth_event(
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id,
            user_email=credentials.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Account locked"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked. Try again later."
        )
    
    # Create tokens
    access_token, refresh_token, session_id = auth_service.create_tokens(
        user, ip_address, user_agent
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    user.failed_login_attempts = 0
    db.commit()
    
    # Log successful login
    audit.log_auth_event(
        action=AuditAction.LOGIN,
        user_id=user.id,
        user_email=user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        details={"session_id": session_id}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    """
    ip_address, user_agent = get_client_info(request)
    audit = get_audit_logger(db)
    auth_service = get_auth_service(db)
    
    result = auth_service.refresh_tokens(token_request.refresh_token)
    
    if not result:
        audit.log_auth_event(
            action=AuditAction.TOKEN_REFRESH,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Invalid or expired refresh token"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    new_access_token, new_refresh_token = result
    
    # Log successful token refresh
    audit.log_auth_event(
        action=AuditAction.TOKEN_REFRESH,
        ip_address=ip_address,
        user_agent=user_agent,
        success=True
    )
    
    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    request: Request,
    logout_request: LogoutRequest = LogoutRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout user by invalidating session(s).
    
    If all_sessions is True, invalidates all user sessions.
    """
    ip_address, user_agent = get_client_info(request)
    audit = get_audit_logger(db)
    auth_service = get_auth_service(db)
    
    session_id = getattr(request.state, "session_id", None)
    
    if logout_request.all_sessions:
        count = auth_service.logout_all_sessions(current_user.id)
        action = AuditAction.LOGOUT_ALL
        details = {"sessions_invalidated": count}
    else:
        if session_id:
            auth_service.logout(session_id)
        action = AuditAction.LOGOUT
        details = {"session_id": session_id}
    
    # Log logout
    audit.log_auth_event(
        action=action,
        user_id=current_user.id,
        user_email=current_user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        details=details
    )
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserAuthResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    """
    rbac = get_rbac_service()
    permissions = rbac.get_permission_list(current_user.user_type.value)
    
    return UserAuthResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        department=current_user.department,
        user_type=current_user.user_type.value,
        permissions=permissions
    )


@router.post("/password/change")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Change the current user's password.
    
    This will invalidate all existing sessions.
    """
    ip_address, user_agent = get_client_info(request)
    audit = get_audit_logger(db)
    auth_service = get_auth_service(db)
    
    success = auth_service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        audit.log_auth_event(
            action=AuditAction.PASSWORD_CHANGE,
            user_id=current_user.id,
            user_email=current_user.email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Invalid current password"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    # Log successful password change
    audit.log_auth_event(
        action=AuditAction.PASSWORD_CHANGE,
        user_id=current_user.id,
        user_email=current_user.email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=True
    )
    
    return {"message": "Password changed successfully. Please login again."}


@router.get("/sessions", response_model=List[SessionInfo])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all active sessions for the current user.
    """
    auth_service = get_auth_service(db)
    sessions = auth_service.get_user_sessions(current_user.id)
    
    rbac = get_rbac_service()
    permissions = rbac.get_permission_list(current_user.user_type.value)
    
    return [
        SessionInfo(
            session_id=s.get("session_id", ""),
            user_id=current_user.id,
            user_name=current_user.name,
            user_email=current_user.email,
            user_type=current_user.user_type.value,
            permissions=permissions,
            created_at=s.get("created_at", datetime.utcnow()),
            expires_at=s.get("expires_at", datetime.utcnow()),
            last_activity=s.get("last_activity", datetime.utcnow()),
            ip_address=s.get("ip_address"),
            user_agent=s.get("user_agent")
        )
        for s in sessions
    ]

