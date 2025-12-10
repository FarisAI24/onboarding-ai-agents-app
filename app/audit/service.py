"""Audit logging service for comprehensive system auditing."""
import logging
import json
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from functools import lru_cache

from sqlalchemy.orm import Session
import structlog

from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class AuditAction(str, Enum):
    """Audit action types."""
    # Authentication
    LOGIN = "auth.login"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    LOGOUT_ALL = "auth.logout_all"
    TOKEN_REFRESH = "auth.token_refresh"
    PASSWORD_CHANGE = "auth.password_change"
    PASSWORD_RESET = "auth.password_reset"
    REGISTER = "auth.register"
    
    # User actions
    USER_CREATE = "user.create"
    USER_READ = "user.read"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ACTIVATE = "user.activate"
    USER_DEACTIVATE = "user.deactivate"
    
    # Task actions
    TASK_CREATE = "task.create"
    TASK_READ = "task.read"
    TASK_UPDATE = "task.update"
    TASK_STATUS_CHANGE = "task.status_change"
    TASK_DELETE = "task.delete"
    
    # Chat actions
    CHAT_SEND = "chat.send"
    CHAT_RECEIVE = "chat.receive"
    
    # Admin actions
    ADMIN_DASHBOARD_VIEW = "admin.dashboard_view"
    ADMIN_METRICS_VIEW = "admin.metrics_view"
    ADMIN_AUDIT_VIEW = "admin.audit_view"
    ADMIN_LOGS_VIEW = "admin.logs_view"
    
    # System actions
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    SYSTEM_ERROR = "system.error"
    
    # Security actions
    SECURITY_PII_DETECTED = "security.pii_detected"
    SECURITY_RATE_LIMIT = "security.rate_limit"
    SECURITY_ACCESS_DENIED = "security.access_denied"


class AuditResource(str, Enum):
    """Resource types for audit logging."""
    USER = "user"
    TASK = "task"
    MESSAGE = "message"
    SESSION = "session"
    SYSTEM = "system"
    ADMIN = "admin"


class AuditLogger:
    """
    Comprehensive audit logger that logs to both database and structured logs.
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self._log_queue: List[Dict[str, Any]] = []
    
    def log(
        self,
        action: AuditAction,
        resource_type: AuditResource,
        resource_id: Optional[int] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> None:
        """
        Log an audit event.
        
        Args:
            action: The action being performed
            resource_type: Type of resource being acted upon
            resource_id: ID of the specific resource (if applicable)
            user_id: ID of the user performing the action
            user_email: Email of the user (for logging when user_id not available)
            session_id: Session ID of the user
            ip_address: Client IP address
            user_agent: Client user agent
            details: Additional details about the action
            status: Status of the action (success, failure, error)
            error_message: Error message if status is not success
        """
        timestamp = datetime.utcnow()
        
        audit_entry = {
            "timestamp": timestamp.isoformat(),
            "action": action.value,
            "resource_type": resource_type.value,
            "resource_id": resource_id,
            "user_id": user_id,
            "user_email": user_email,
            "session_id": session_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {},
            "status": status,
            "error_message": error_message,
        }
        
        # Log to structured logger
        log_method = logger.info if status == "success" else logger.warning
        log_method(
            "audit_event",
            **{k: v for k, v in audit_entry.items() if v is not None}
        )
        
        # Log to database if available
        if self.db:
            self._log_to_database(audit_entry)
    
    def _log_to_database(self, audit_entry: Dict[str, Any]) -> None:
        """Log audit entry to database."""
        try:
            from app.database.models import AuditLog
            
            db_entry = AuditLog(
                action=audit_entry["action"],
                resource_type=audit_entry["resource_type"],
                resource_id=audit_entry.get("resource_id"),
                user_id=audit_entry.get("user_id"),
                user_email=audit_entry.get("user_email"),
                session_id=audit_entry.get("session_id"),
                ip_address=audit_entry.get("ip_address"),
                user_agent=audit_entry.get("user_agent"),
                details=audit_entry.get("details"),
                status=audit_entry["status"],
                error_message=audit_entry.get("error_message"),
                timestamp=datetime.fromisoformat(audit_entry["timestamp"])
            )
            self.db.add(db_entry)
            self.db.commit()
        except Exception as e:
            logger.error("failed_to_log_audit_to_db", error=str(e))
    
    def log_auth_event(
        self,
        action: AuditAction,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Convenience method for logging authentication events."""
        self.log(
            action=action,
            resource_type=AuditResource.SESSION,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            status="success" if success else "failure",
            error_message=error_message,
        )
    
    def log_resource_access(
        self,
        action: AuditAction,
        resource_type: AuditResource,
        resource_id: int,
        user_id: int,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Convenience method for logging resource access."""
        self.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            session_id=session_id,
            details=details,
        )
    
    def log_security_event(
        self,
        action: AuditAction,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Convenience method for logging security events."""
        self.log(
            action=action,
            resource_type=AuditResource.SYSTEM,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            status="warning",
        )


def get_audit_logger(db: Optional[Session] = None) -> AuditLogger:
    """Get an audit logger instance."""
    return AuditLogger(db)


# Standalone logging functions for use without database
def log_audit_event(
    action: AuditAction,
    resource_type: AuditResource,
    **kwargs
) -> None:
    """Log an audit event without database."""
    audit_logger = AuditLogger()
    audit_logger.log(action, resource_type, **kwargs)

