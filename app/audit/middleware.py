"""Audit logging middleware for automatic request/response logging."""
import time
import logging
from typing import Callable
from datetime import datetime

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import structlog

from app.audit.service import AuditLogger, AuditAction, AuditResource

logger = structlog.get_logger()


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically logs all API requests for audit purposes.
    """
    
    # Paths to exclude from audit logging
    EXCLUDED_PATHS = {
        "/health",
        "/api/v1/health",
        "/metrics",
        "/api/v1/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
    }
    
    # Paths that contain sensitive data (log with redaction)
    SENSITIVE_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/password",
    }
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)
        
        # Capture request details
        start_time = time.time()
        request_id = f"{datetime.utcnow().timestamp()}-{id(request)}"
        
        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Store request_id for correlation
        request.state.request_id = request_id
        
        # Log request start
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
        )
        
        # Process request
        response = None
        error_message = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_message = str(e)
            status_code = 500
            raise
        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Get user info if available
            user_id = None
            user_email = None
            session_id = None
            
            if hasattr(request.state, "user"):
                user = request.state.user
                user_id = user.id
                user_email = user.email
            
            if hasattr(request.state, "session_id"):
                session_id = request.state.session_id
            
            # Determine action based on path and method
            action = self._determine_action(request.method, request.url.path)
            resource_type = self._determine_resource_type(request.url.path)
            
            # Build audit details
            details = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
            }
            
            # Add query params (excluding sensitive ones)
            if request.query_params and request.url.path not in self.SENSITIVE_PATHS:
                details["query_params"] = dict(request.query_params)
            
            # Determine audit status
            if status_code < 400:
                audit_status = "success"
            elif status_code < 500:
                audit_status = "failure"
            else:
                audit_status = "error"
            
            # Log audit entry
            audit_logger = AuditLogger()
            audit_logger.log(
                action=action,
                resource_type=resource_type,
                user_id=user_id,
                user_email=user_email,
                session_id=session_id,
                ip_address=client_ip,
                user_agent=user_agent,
                details=details,
                status=audit_status,
                error_message=error_message,
            )
            
            # Log request completion
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
                user_id=user_id,
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, handling proxies."""
        # Check for forwarded headers (in order of preference)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _determine_action(self, method: str, path: str) -> AuditAction:
        """Determine audit action based on HTTP method and path."""
        # Auth endpoints
        if "/auth/" in path:
            if "login" in path:
                return AuditAction.LOGIN
            elif "logout" in path:
                return AuditAction.LOGOUT
            elif "register" in path:
                return AuditAction.REGISTER
            elif "refresh" in path:
                return AuditAction.TOKEN_REFRESH
            elif "password" in path:
                return AuditAction.PASSWORD_CHANGE
        
        # Admin endpoints
        if "/admin/" in path:
            if "dashboard" in path or "metrics" in path:
                return AuditAction.ADMIN_DASHBOARD_VIEW
            elif "audit" in path:
                return AuditAction.ADMIN_AUDIT_VIEW
            elif "logs" in path:
                return AuditAction.ADMIN_LOGS_VIEW
            return AuditAction.ADMIN_METRICS_VIEW
        
        # User endpoints
        if "/users" in path:
            if method == "POST":
                return AuditAction.USER_CREATE
            elif method == "GET":
                return AuditAction.USER_READ
            elif method in ("PUT", "PATCH"):
                return AuditAction.USER_UPDATE
            elif method == "DELETE":
                return AuditAction.USER_DELETE
        
        # Task endpoints
        if "/tasks" in path:
            if method == "POST":
                if "status" in path:
                    return AuditAction.TASK_STATUS_CHANGE
                return AuditAction.TASK_CREATE
            elif method == "GET":
                return AuditAction.TASK_READ
            elif method in ("PUT", "PATCH"):
                return AuditAction.TASK_UPDATE
            elif method == "DELETE":
                return AuditAction.TASK_DELETE
        
        # Chat endpoints
        if "/chat" in path:
            return AuditAction.CHAT_SEND
        
        # Default
        return AuditAction.USER_READ
    
    def _determine_resource_type(self, path: str) -> AuditResource:
        """Determine resource type based on path."""
        if "/auth/" in path or "/session" in path:
            return AuditResource.SESSION
        elif "/admin/" in path:
            return AuditResource.ADMIN
        elif "/users" in path:
            return AuditResource.USER
        elif "/tasks" in path:
            return AuditResource.TASK
        elif "/chat" in path or "/messages" in path:
            return AuditResource.MESSAGE
        else:
            return AuditResource.SYSTEM

