"""SQLAlchemy database models."""
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, 
    ForeignKey, Enum, Float, Boolean, JSON, Index
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class TaskStatus(str, PyEnum):
    """Task status enumeration."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Department(str, PyEnum):
    """Department enumeration."""
    HR = "HR"
    IT = "IT"
    SECURITY = "Security"
    FINANCE = "Finance"
    GENERAL = "General"


class UserRole(str, PyEnum):
    """User role enumeration for access control."""
    NEW_HIRE = "new_hire"
    EMPLOYEE = "employee"
    MANAGER = "manager"
    HR_ADMIN = "hr_admin"
    IT_ADMIN = "it_admin"
    SECURITY_ADMIN = "security_admin"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class User(Base):
    """User model for employees."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for backward compatibility
    role = Column(String(100), nullable=False)  # Job role (e.g., "Junior Backend Engineer")
    department = Column(String(100), nullable=False)  # Work department
    user_type = Column(Enum(UserRole), default=UserRole.NEW_HIRE)  # Access level
    is_active = Column(Boolean, default=True, nullable=False)
    start_date = Column(Date, default=date.today)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"


class Task(Base):
    """Onboarding task model."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(Enum(Department), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"


class Message(Base):
    """Chat message model."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    text_redacted = Column(Text)  # PII-redacted version for logging
    source = Column(String(50), nullable=False)  # "user" or "assistant"
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)  # Additional metadata (agent used, etc.)
    
    # Relationships
    user = relationship("User", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(id={self.id}, source={self.source})>"


class RoutingLog(Base):
    """Log for routing model predictions."""
    __tablename__ = "routing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    query_text_redacted = Column(Text)  # PII-redacted
    predicted_department = Column(String(50), nullable=False)
    prediction_confidence = Column(Float)
    final_department = Column(String(50))  # After rule override
    was_overridden = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RoutingLog(id={self.id}, predicted={self.predicted_department})>"


class AgentCallLog(Base):
    """Log for agent invocations."""
    __tablename__ = "agent_call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    agent_name = Column(String(100), nullable=False)
    input_summary = Column(Text)  # Summarized/redacted input
    output_summary = Column(Text)  # Summarized/redacted output
    retrieval_k = Column(Integer)  # Number of docs retrieved
    retrieval_docs = Column(JSON)  # Doc names/sections retrieved
    retrieval_time_ms = Column(Float)
    total_time_ms = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    error = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<AgentCallLog(id={self.id}, agent={self.agent_name})>"


class SystemMetrics(Base):
    """System metrics for monitoring."""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    labels = Column(JSON)  # Additional labels/dimensions
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemMetrics(name={self.metric_name}, value={self.metric_value})>"


class AuditLog(Base):
    """Comprehensive audit log for all system actions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
    status = Column(String(20), default="success", nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_logs_action_timestamp', 'action', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"


class UserSession(Base):
    """User session tracking for persistent session management."""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    refresh_token_hash = Column(String(64), nullable=False)  # SHA-256 hash
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationship
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
