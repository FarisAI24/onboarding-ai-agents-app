"""Pydantic schemas for API requests and responses."""
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from pydantic import BaseModel, Field


# Enums
class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Department(str, Enum):
    HR = "HR"
    IT = "IT"
    SECURITY = "Security"
    FINANCE = "Finance"
    GENERAL = "General"


class UserType(str, Enum):
    NEW_HIRE = "new_hire"
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"


# User schemas
class UserBase(BaseModel):
    name: str
    email: str
    role: str  # Job role
    department: str  # Work department


class UserCreate(UserBase):
    user_type: UserType = UserType.NEW_HIRE
    start_date: Optional[date] = None


class UserResponse(UserBase):
    id: int
    user_type: UserType
    start_date: date
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWithProgress(UserResponse):
    total_tasks: int
    completed_tasks: int
    progress_percentage: float
    overdue_tasks: int


# Task schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    department: Department
    due_date: date


class TaskCreate(TaskBase):
    user_id: int


class TaskResponse(TaskBase):
    id: int
    user_id: int
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskWithOverdue(TaskResponse):
    is_overdue: bool


# Chat schemas
class ChatRequest(BaseModel):
    user_id: int
    message: str = Field(..., min_length=1, max_length=2000)


class SourceReference(BaseModel):
    document: str
    section: str
    department: str


class RoutingInfo(BaseModel):
    predicted_department: Optional[str] = None
    prediction_confidence: Optional[float] = None
    final_department: Optional[str] = None
    was_overridden: bool = False


class ChatResponse(BaseModel):
    response: str
    sources: List[SourceReference] = []
    task_updates: List[Dict[str, Any]] = []
    routing: RoutingInfo
    agent: Optional[str] = None
    total_time_ms: float = 0


# Message schemas
class MessageResponse(BaseModel):
    id: int
    user_id: int
    text: str
    source: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Admin schemas
class UserProgressStats(BaseModel):
    user_id: int
    user_name: str
    role: str
    department: str
    start_date: date
    total_tasks: int
    completed_tasks: int
    progress_percentage: float
    overdue_tasks: int
    days_since_start: int


class DepartmentMetrics(BaseModel):
    department: str
    total_users: int
    avg_completion_percentage: float
    avg_days_to_complete: float
    users_completed: int
    top_blocking_tasks: List[str]


class AggregateMetrics(BaseModel):
    total_users: int
    total_new_hires: int
    avg_completion_percentage: float
    avg_days_to_complete: Optional[float]
    completion_by_department: Dict[str, float]
    queries_by_department: Dict[str, int]
    total_queries_today: int
    resolution_rate: float


# FAQ schemas
class FAQTopic(BaseModel):
    id: str
    title: str
    category: str
    question: str


class FAQListResponse(BaseModel):
    topics: List[FAQTopic]


# Health check
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    vectorstore: str

