"""Authentication service for JWT tokens and password management."""
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from functools import lru_cache

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import get_settings
from app.auth.rbac import get_rbac_service

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(32)  # Unique token ID for revocation
    })
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def generate_session_id() -> str:
    """Generate a unique session ID."""
    return secrets.token_urlsafe(32)


class SessionCache:
    """In-memory session cache with TTL."""
    
    def __init__(self, default_ttl: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
    
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set a session in cache."""
        expiry = datetime.utcnow() + timedelta(seconds=ttl or self._default_ttl)
        self._cache[key] = {
            "data": value,
            "expires_at": expiry
        }
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a session from cache."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if datetime.utcnow() > entry["expires_at"]:
            del self._cache[key]
            return None
        
        return entry["data"]
    
    def delete(self, key: str) -> bool:
        """Delete a session from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def delete_user_sessions(self, user_id: int) -> int:
        """Delete all sessions for a user."""
        to_delete = [
            key for key, entry in self._cache.items()
            if entry["data"].get("user_id") == user_id
        ]
        for key in to_delete:
            del self._cache[key]
        return len(to_delete)
    
    def update_activity(self, key: str) -> bool:
        """Update last activity timestamp for a session."""
        if key in self._cache:
            self._cache[key]["data"]["last_activity"] = datetime.utcnow()
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired = [key for key, entry in self._cache.items() if now > entry["expires_at"]]
        for key in expired:
            del self._cache[key]
        return len(expired)
    
    def get_user_sessions(self, user_id: int) -> list:
        """Get all active sessions for a user."""
        sessions = []
        now = datetime.utcnow()
        for key, entry in self._cache.items():
            if entry["data"].get("user_id") == user_id and now <= entry["expires_at"]:
                session_data = entry["data"].copy()
                session_data["session_id"] = key
                sessions.append(session_data)
        return sessions


# Global session cache
_session_cache = SessionCache(default_ttl=ACCESS_TOKEN_EXPIRE_MINUTES * 60)


class AuthService:
    """Authentication service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.rbac = get_rbac_service()
        self.session_cache = _session_cache
    
    def authenticate_user(self, email: str, password: str) -> Optional[Any]:
        """Authenticate user by email and password."""
        from app.database import User
        
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            logger.info(f"Authentication failed: user not found for email {email}")
            return None
        
        if not user.password_hash:
            logger.warning(f"User {user.id} has no password set")
            return None
        
        if not verify_password(password, user.password_hash):
            logger.info(f"Authentication failed: invalid password for user {user.id}")
            return None
        
        if not user.is_active:
            logger.info(f"Authentication failed: user {user.id} is inactive")
            return None
        
        return user
    
    def create_tokens(
        self, 
        user: Any,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, str, str]:
        """Create access and refresh tokens for a user."""
        session_id = generate_session_id()
        permissions = self.rbac.get_permission_list(user.user_type.value)
        
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "user_type": user.user_type.value,
            "session_id": session_id,
            "permissions": permissions
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store session in cache
        session_data = {
            "user_id": user.id,
            "user_name": user.name,
            "user_email": user.email,
            "user_type": user.user_type.value,
            "permissions": permissions,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "refresh_token_hash": hashlib.sha256(refresh_token.encode()).hexdigest()
        }
        self.session_cache.set(
            session_id, 
            session_data, 
            ttl=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        )
        
        return access_token, refresh_token, session_id
    
    def refresh_tokens(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)
        if not payload:
            return None
        
        if payload.get("type") != "refresh":
            logger.warning("Token is not a refresh token")
            return None
        
        session_id = payload.get("session_id")
        if not session_id:
            return None
        
        session_data = self.session_cache.get(session_id)
        if not session_data:
            logger.warning(f"Session {session_id} not found in cache")
            return None
        
        # Verify refresh token hash matches
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if session_data.get("refresh_token_hash") != token_hash:
            logger.warning("Refresh token hash mismatch")
            return None
        
        # Get user
        from app.database import User
        user_id = int(payload.get("sub"))
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None
        
        # Create new tokens
        permissions = self.rbac.get_permission_list(user.user_type.value)
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "user_type": user.user_type.value,
            "session_id": session_id,
            "permissions": permissions
        }
        
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        # Update session
        session_data["last_activity"] = datetime.utcnow()
        session_data["refresh_token_hash"] = hashlib.sha256(new_refresh_token.encode()).hexdigest()
        self.session_cache.set(session_id, session_data, ttl=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600)
        
        return new_access_token, new_refresh_token
    
    def logout(self, session_id: str) -> bool:
        """Logout a single session."""
        return self.session_cache.delete(session_id)
    
    def logout_all_sessions(self, user_id: int) -> int:
        """Logout all sessions for a user."""
        return self.session_cache.delete_user_sessions(user_id)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        return self.session_cache.get(session_id)
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity."""
        return self.session_cache.update_activity(session_id)
    
    def get_user_sessions(self, user_id: int) -> list:
        """Get all active sessions for a user."""
        return self.session_cache.get_user_sessions(user_id)
    
    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        role: str,
        department: str
    ) -> Any:
        """Register a new user."""
        from app.database import User
        from app.database.models import UserRole
        
        # Check if email exists
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            return None
        
        # Create user
        user = User(
            name=name,
            email=email,
            password_hash=get_password_hash(password),
            role=role,
            department=department,
            user_type=UserRole.NEW_HIRE,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password."""
        from app.database import User
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if not verify_password(current_password, user.password_hash):
            return False
        
        user.password_hash = get_password_hash(new_password)
        self.db.commit()
        
        # Invalidate all sessions except current
        self.logout_all_sessions(user_id)
        
        return True


def get_auth_service(db: Session) -> AuthService:
    """Get auth service instance."""
    return AuthService(db)

