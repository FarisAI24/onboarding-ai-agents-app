"""Pydantic schemas for authentication."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Data embedded in JWT token."""
    user_id: int
    email: str
    user_type: str
    permissions: List[str] = []
    session_id: Optional[str] = None


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserRegister(BaseModel):
    """User registration request."""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., description="Job role, e.g., 'Junior Backend Engineer'")
    department: str = Field(..., description="Work department, e.g., 'Engineering'")


class PasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordReset(BaseModel):
    """Password reset request."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class SessionInfo(BaseModel):
    """User session information."""
    session_id: str
    user_id: int
    user_name: str
    user_email: str
    user_type: str
    permissions: List[str]
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UserAuthResponse(BaseModel):
    """User response after authentication."""
    id: int
    name: str
    email: str
    role: str
    department: str
    user_type: str
    permissions: List[str]
    
    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request."""
    all_sessions: bool = False  # Whether to logout from all sessions

