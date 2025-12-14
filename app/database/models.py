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


class FeedbackType(str, PyEnum):
    """Feedback type enumeration."""
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"


class AchievementCategory(str, PyEnum):
    """Achievement category enumeration."""
    ONBOARDING = "onboarding"
    LEARNING = "learning"
    ENGAGEMENT = "engagement"
    SPEED = "speed"
    SOCIAL = "social"


class WorkflowTrigger(str, PyEnum):
    """Workflow trigger types."""
    TASK_COMPLETED = "task_completed"
    ALL_TASKS_COMPLETED = "all_tasks_completed"
    MODULE_COMPLETED = "module_completed"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    USER_REGISTERED = "user_registered"
    DEADLINE_APPROACHING = "deadline_approaching"
    TASK_OVERDUE = "task_overdue"


class ChurnRisk(str, PyEnum):
    """Churn risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class User(Base):
    """User model for employees."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(100), nullable=False)  # Job role
    department = Column(String(100), nullable=False)
    user_type = Column(Enum(UserRole), default=UserRole.NEW_HIRE)
    is_active = Column(Boolean, default=True, nullable=False)
    start_date = Column(Date, default=date.today)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    preferred_language = Column(String(10), default="en")  # For i18n: "en", "ar"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    training_progress = relationship("TrainingProgress", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"


class Task(Base):
    """Onboarding task model."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(Enum(Department), nullable=False)
    title = Column(String(255), nullable=False)
    title_ar = Column(String(255), nullable=True)  # Arabic translation
    description = Column(Text)
    description_ar = Column(Text, nullable=True)  # Arabic translation
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
    text_redacted = Column(Text)
    source = Column(String(50), nullable=False)
    language = Column(String(10), default="en")  # Message language
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="messages")
    feedback = relationship("Feedback", back_populates="message", uselist=False)
    
    def __repr__(self):
        return f"<Message(id={self.id}, source={self.source})>"


class Feedback(Base):
    """User feedback on assistant responses."""
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, unique=True)
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    comment = Column(Text, nullable=True)
    routing_was_correct = Column(Boolean, nullable=True)
    answer_was_accurate = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # For routing model retraining
    query_text = Column(Text, nullable=True)
    predicted_department = Column(String(50), nullable=True)
    suggested_department = Column(String(50), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    message = relationship("Message", back_populates="feedback")
    
    __table_args__ = (
        Index('ix_feedback_type_date', 'feedback_type', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, type={self.feedback_type})>"


class SemanticCache(Base):
    """Cache for semantically similar queries."""
    __tablename__ = "semantic_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    query_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256 of normalized query
    query_text = Column(Text, nullable=False)
    query_embedding = Column(JSON, nullable=True)  # Store embedding vector
    response = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)
    department = Column(String(50), nullable=True)
    hit_count = Column(Integer, default=0)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_valid = Column(Boolean, default=True)
    
    __table_args__ = (
        Index('ix_semantic_cache_valid_expires', 'is_valid', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<SemanticCache(id={self.id}, hits={self.hit_count})>"


class FAQ(Base):
    """Managed FAQ entries."""
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    question_ar = Column(Text, nullable=True)  # Arabic translation
    answer = Column(Text, nullable=False)
    answer_ar = Column(Text, nullable=True)  # Arabic translation
    category = Column(String(50), nullable=False, index=True)
    department = Column(Enum(Department), nullable=True)
    tags = Column(JSON, nullable=True)  # List of tags for searchability
    is_published = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_faqs_category_published', 'category', 'is_published'),
    )
    
    def __repr__(self):
        return f"<FAQ(id={self.id}, category={self.category})>"


class Achievement(Base):
    """Achievement definitions for gamification."""
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    name_ar = Column(String(100), nullable=True)  # Arabic translation
    description = Column(Text, nullable=False)
    description_ar = Column(Text, nullable=True)  # Arabic translation
    icon = Column(String(50), nullable=False)  # Icon name/emoji
    category = Column(Enum(AchievementCategory), nullable=False)
    points = Column(Integer, default=0)
    criteria = Column(JSON, nullable=False)  # Criteria to unlock
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement")
    
    def __repr__(self):
        return f"<Achievement(id={self.id}, name={self.name})>"


class UserAchievement(Base):
    """User-earned achievements."""
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Float, default=0.0)  # 0-100 for partial progress
    is_notified = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")
    
    __table_args__ = (
        Index('ix_user_achievements_user_achievement', 'user_id', 'achievement_id', unique=True),
    )
    
    def __repr__(self):
        return f"<UserAchievement(user_id={self.user_id}, achievement_id={self.achievement_id})>"


class TrainingModule(Base):
    """Interactive training module definitions."""
    __tablename__ = "training_modules"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    title_ar = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    description_ar = Column(Text, nullable=True)
    department = Column(Enum(Department), nullable=False)
    content = Column(JSON, nullable=False)  # Module content (steps, questions, etc.)
    content_ar = Column(JSON, nullable=True)  # Arabic content
    duration_minutes = Column(Integer, default=30)
    passing_score = Column(Integer, default=70)  # Percentage to pass
    is_required = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    prerequisites = Column(JSON, nullable=True)  # List of module IDs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    progress = relationship("TrainingProgress", back_populates="module")
    
    def __repr__(self):
        return f"<TrainingModule(id={self.id}, title={self.title})>"


class TrainingProgress(Base):
    """User progress in training modules."""
    __tablename__ = "training_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("training_modules.id"), nullable=False)
    status = Column(String(20), default="not_started")  # not_started, in_progress, completed, failed
    current_step = Column(Integer, default=0)
    score = Column(Integer, nullable=True)
    answers = Column(JSON, nullable=True)  # User's quiz answers
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0)
    time_spent_seconds = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="training_progress")
    module = relationship("TrainingModule", back_populates="progress")
    
    __table_args__ = (
        Index('ix_training_progress_user_module', 'user_id', 'module_id', unique=True),
    )
    
    def __repr__(self):
        return f"<TrainingProgress(user_id={self.user_id}, module_id={self.module_id}, status={self.status})>"


class Workflow(Base):
    """Automated workflow definitions."""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    trigger = Column(Enum(WorkflowTrigger), nullable=False)
    conditions = Column(JSON, nullable=True)  # Conditions to execute
    actions = Column(JSON, nullable=False)  # Actions to perform
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher = runs first
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name={self.name}, trigger={self.trigger})>"


class WorkflowExecution(Base):
    """Log of workflow executions."""
    __tablename__ = "workflow_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    trigger_data = Column(JSON, nullable=True)  # Data that triggered workflow
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    result = Column(JSON, nullable=True)  # Execution result
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"


class EngagementMetrics(Base):
    """User engagement tracking for churn prediction."""
    __tablename__ = "engagement_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    
    # Daily engagement metrics
    chat_messages_sent = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_started = Column(Integer, default=0)
    login_count = Column(Integer, default=0)
    session_duration_seconds = Column(Integer, default=0)
    faq_views = Column(Integer, default=0)
    training_time_seconds = Column(Integer, default=0)
    positive_feedback_given = Column(Integer, default=0)
    negative_feedback_given = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_engagement_user_date', 'user_id', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<EngagementMetrics(user_id={self.user_id}, date={self.date})>"


class ChurnPrediction(Base):
    """Churn prediction results."""
    __tablename__ = "churn_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prediction_date = Column(DateTime, default=datetime.utcnow)
    risk_level = Column(Enum(ChurnRisk), nullable=False)
    churn_probability = Column(Float, nullable=False)  # 0-1 probability
    risk_factors = Column(JSON, nullable=True)  # Factors contributing to risk
    recommended_actions = Column(JSON, nullable=True)
    model_version = Column(String(50), nullable=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('ix_churn_user_date', 'user_id', 'prediction_date'),
    )
    
    def __repr__(self):
        return f"<ChurnPrediction(user_id={self.user_id}, risk={self.risk_level})>"


class CalendarEvent(Base):
    """Calendar events for task deadlines."""
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    training_module_id = Column(Integer, ForeignKey("training_modules.id"), nullable=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    all_day = Column(Boolean, default=False)
    
    # External calendar sync
    external_calendar_type = Column(String(50), nullable=True)  # google, outlook
    external_event_id = Column(String(255), nullable=True)
    sync_status = Column(String(20), default="pending")  # pending, synced, failed
    last_synced_at = Column(DateTime, nullable=True)
    
    reminder_minutes = Column(Integer, default=30)
    is_reminder_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, title={self.title})>"


class RoutingLog(Base):
    """Log for routing model predictions."""
    __tablename__ = "routing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query_text = Column(Text, nullable=False)
    query_text_redacted = Column(Text)
    predicted_department = Column(String(50), nullable=False)
    prediction_confidence = Column(Float)
    final_department = Column(String(50))
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
    input_summary = Column(Text)
    output_summary = Column(Text)
    retrieval_k = Column(Integer)
    retrieval_docs = Column(JSON)
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
    labels = Column(JSON)
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
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
    status = Column(String(20), default="success", nullable=False)
    error_message = Column(Text, nullable=True)
    
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
    refresh_token_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
