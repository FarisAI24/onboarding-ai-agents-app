"""API routes for the onboarding copilot."""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import get_settings
from app.database import get_db, User, Task, Message, RoutingLog, AgentCallLog
from app.database.models import TaskStatus as DBTaskStatus, Department as DBDepartment, UserRole
from app.api.schemas import (
    UserCreate, UserResponse, UserWithProgress, UserProgressStats,
    TaskCreate, TaskResponse, TaskStatusUpdate, TaskWithOverdue,
    ChatRequest, ChatResponse, SourceReference, RoutingInfo,
    MessageResponse, AggregateMetrics, FAQTopic, FAQListResponse,
    HealthResponse
)
from app.agents.orchestrator import get_orchestrator
from app.services.security import redact_pii
from app.monitoring import get_metrics_collector
from app.services.achievements import AchievementService
from app.auth.service import get_password_hash
from app.audit.service import AuditLogger, AuditAction, AuditResource

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


# FAQ Topics
FAQ_TOPICS = [
    FAQTopic(id="benefits", title="Employee Benefits", category="HR", 
             question="What health insurance and benefits options are available?"),
    FAQTopic(id="pto", title="Paid Time Off", category="HR",
             question="How much PTO do I get and how do I request time off?"),
    FAQTopic(id="leave", title="Leave Policies", category="HR",
             question="What are the different leave policies (sick, parental, bereavement)?"),
    FAQTopic(id="equipment", title="Equipment & Devices", category="IT",
             question="How do I set up my laptop and request additional equipment?"),
    FAQTopic(id="vpn", title="VPN & Remote Access", category="IT",
             question="How do I connect to the VPN for remote work?"),
    FAQTopic(id="accounts", title="Account Setup", category="IT",
             question="How do I set up my email, Slack, and other accounts?"),
    FAQTopic(id="security_training", title="Security Training", category="Security",
             question="What security training do I need to complete?"),
    FAQTopic(id="passwords", title="Password Policy", category="Security",
             question="What are the password requirements and how do I reset my password?"),
    FAQTopic(id="expenses", title="Expense Reimbursement", category="Finance",
             question="How do I submit expenses for reimbursement?"),
    FAQTopic(id="payroll", title="Payroll & Pay Schedule", category="Finance",
             question="When do I get paid and how do I access my pay stubs?"),
]


# Health check
@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database="connected",
        vectorstore="connected"
    )


# Prometheus metrics endpoint
@router.get("/metrics", tags=["Monitoring"])
async def get_prometheus_metrics():
    """Get Prometheus-formatted metrics."""
    metrics = get_metrics_collector()
    return PlainTextResponse(
        content=metrics.get_prometheus_metrics().decode("utf-8"),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


# Dashboard metrics endpoint
@router.get("/dashboard/metrics", tags=["Monitoring"])
async def get_dashboard_metrics():
    """Get aggregated metrics for dashboard display."""
    metrics = get_metrics_collector()
    return metrics.get_dashboard_metrics()


# User endpoints
@router.post("/users", response_model=UserResponse, tags=["Users"])
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=get_password_hash(user.password),
        role=user.role,
        department=user.department,
        user_type=UserRole(user.user_type.value),
        start_date=user.start_date or date.today()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default onboarding tasks for new hire
    if user.user_type == "new_hire":
        await _create_default_tasks(db, db_user.id)
    
    return db_user


@router.get("/users/{user_id}", response_model=UserWithProgress, tags=["Users"])
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID with progress stats."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate progress
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    total = len(tasks)
    completed = len([t for t in tasks if t.status == DBTaskStatus.DONE])
    overdue = len([t for t in tasks if t.due_date < date.today() and t.status != DBTaskStatus.DONE])
    
    return UserWithProgress(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        department=user.department,
        user_type=user.user_type.value,
        start_date=user.start_date,
        created_at=user.created_at,
        total_tasks=total,
        completed_tasks=completed,
        progress_percentage=(completed / total * 100) if total > 0 else 0,
        overdue_tasks=overdue
    )


# Task endpoints
@router.get("/tasks", response_model=List[TaskWithOverdue], tags=["Tasks"])
async def get_tasks(
    user_id: int,
    status: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get tasks for a user."""
    query = db.query(Task).filter(Task.user_id == user_id)
    
    if status:
        query = query.filter(Task.status == DBTaskStatus(status))
    if department:
        query = query.filter(Task.department == DBDepartment(department))
    
    tasks = query.order_by(Task.due_date).all()
    today = date.today()
    
    return [
        TaskWithOverdue(
            id=t.id,
            user_id=t.user_id,
            title=t.title,
            description=t.description,
            department=t.department.value,
            due_date=t.due_date,
            status=t.status.value,
            created_at=t.created_at,
            updated_at=t.updated_at,
            completed_at=t.completed_at,
            is_overdue=t.due_date < today and t.status != DBTaskStatus.DONE
        )
        for t in tasks
    ]


@router.post("/tasks/{task_id}/status", response_model=TaskResponse, tags=["Tasks"])
async def update_task_status(
    task_id: int,
    update: TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update task status."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = DBTaskStatus(update.status.value)
    if update.status == "DONE":
        task.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    # Check and unlock achievements when task is completed
    if update.status == "DONE":
        try:
            achievement_service = AchievementService(db)
            achievement_service.check_and_unlock(task.user_id)
        except Exception as e:
            logger.error(f"Failed to check achievements: {e}")
    
    return task


# Background task queue for non-blocking operations
import asyncio
from concurrent.futures import ThreadPoolExecutor

_background_executor = ThreadPoolExecutor(max_workers=4)


def _save_user_message_background(db_session_factory, user_id: int, request_message: str, result: dict):
    """Save user message and routing log to DB in background thread.
    
    Note: Assistant message is saved synchronously to get message_id for feedback.
    """
    try:
        from app.database import get_db
        db = next(db_session_factory())
        
        redacted_message = redact_pii(request_message)
        
        # Save user message
        user_message = Message(
            user_id=user_id,
            text=request_message,
            text_redacted=redacted_message,
            source="user"
        )
        db.add(user_message)
        
        # Save routing log
        routing = result.get("routing", {})
        routing_log = RoutingLog(
            user_id=user_id,
            query_text=request_message,
            query_text_redacted=redacted_message,
            predicted_department=routing.get("predicted_department", "General"),
            prediction_confidence=routing.get("prediction_confidence", 0.0),
            final_department=routing.get("final_department", "General"),
            was_overridden=routing.get("was_overridden", False)
        )
        db.add(routing_log)
        
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Background user message save failed: {e}")


def _check_achievements_background(db_session_factory, user_id: int):
    """Check achievements in background thread."""
    try:
        from app.database import get_db
        db = next(db_session_factory())
        achievement_service = AchievementService(db)
        achievement_service.check_and_unlock(user_id)
        db.close()
    except Exception as e:
        logger.error(f"Background achievement check failed: {e}")


# Chat endpoint
@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Main chat endpoint for the onboarding assistant (optimized)."""
    # OPTIMIZATION: Single query with eager loading instead of multiple queries
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # OPTIMIZATION: Run task and message queries in parallel using ThreadPoolExecutor
    loop = asyncio.get_event_loop()
    
    def get_tasks():
        return db.query(Task).filter(Task.user_id == request.user_id).all()
    
    def get_messages():
        return db.query(Message).filter(
            Message.user_id == request.user_id
        ).order_by(Message.timestamp.desc()).limit(10).all()
    
    # Execute both queries concurrently
    tasks_future = loop.run_in_executor(None, get_tasks)
    messages_future = loop.run_in_executor(None, get_messages)
    
    tasks, recent_messages = await asyncio.gather(tasks_future, messages_future)
    
    tasks_data = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "department": t.department.value,
            "due_date": t.due_date.isoformat(),
            "status": t.status.value
        }
        for t in tasks
    ]
    
    chat_history = [
        {"role": "user" if m.source == "user" else "assistant", "content": m.text}
        for m in reversed(recent_messages)
    ]
    
    # Process message through orchestrator
    orchestrator = get_orchestrator()
    result = await orchestrator.process_message(
        user_id=user.id,
        message=request.message,
        user_name=user.name,
        user_role=user.role,
        user_department=user.department,
        user_type=user.user_type.value,
        tasks=tasks_data,
        chat_history=chat_history
    )
    
    # Apply task updates synchronously (important for consistency)
    for task_update in result.get("task_updates", []):
        task_id = task_update.get("task_id")
        new_status = task_update.get("new_status")
        if task_id and new_status:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task and task.user_id == user.id:
                task.status = DBTaskStatus(new_status)
                if new_status == "DONE":
                    task.completed_at = datetime.utcnow()
    
    # Save assistant message SYNCHRONOUSLY to get the message_id for feedback
    # This is required for the feedback system to work
    assistant_message = Message(
        user_id=user.id,
        text=result["response"],
        text_redacted=result["response"],
        source="assistant",
        extra_data={
            "agent": result.get("agent"),
            "routing": result.get("routing")
        }
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    # Get the message_id for frontend feedback
    saved_message_id = assistant_message.id
    
    # Save user message and routing log in background (non-blocking)
    _background_executor.submit(
        _save_user_message_background, 
        get_db, user.id, request.message, result
    )
    # Check achievements in background
    _background_executor.submit(
        _check_achievements_background, 
        get_db, user.id
    )
    
    routing = result.get("routing", {})
    
    # Log chat to audit with full details (query, response, department, user)
    audit_logger = AuditLogger(db)
    audit_logger.log(
        action=AuditAction.CHAT_SEND,
        resource_type=AuditResource.MESSAGE,
        resource_id=saved_message_id,
        user_id=user.id,
        user_email=user.email,
        details={
            "query": request.message[:500],  # Truncate long queries
            "response": result["response"][:500],  # Truncate long responses
            "department": routing.get("final_department", "General"),
            "predicted_department": routing.get("predicted_department"),
            "confidence": routing.get("prediction_confidence"),
            "agent": result.get("agent"),
            "duration_ms": result.get("total_time_ms", 0),
        },
        status="success"
    )
    
    # Build response
    sources = [
        SourceReference(
            document=s.get("document", ""),
            section=s.get("section", ""),
            department=s.get("department", "")
        )
        for s in result.get("sources", [])
    ]
    
    routing = result.get("routing", {})
    
    return ChatResponse(
        response=result["response"],
        sources=sources,
        task_updates=result.get("task_updates", []),
        routing=RoutingInfo(
            predicted_department=routing.get("predicted_department"),
            prediction_confidence=routing.get("prediction_confidence"),
            final_department=routing.get("final_department"),
            was_overridden=routing.get("was_overridden", False)
        ),
        agent=result.get("agent"),
        total_time_ms=result.get("total_time_ms", 0),
        message_id=saved_message_id  # Include message ID for feedback
    )


# FAQ endpoints
@router.get("/faq", response_model=FAQListResponse, tags=["FAQ"])
async def get_faq_topics():
    """Get list of FAQ topics."""
    return FAQListResponse(topics=FAQ_TOPICS)


@router.post("/faq/{topic_id}", response_model=ChatResponse, tags=["FAQ"])
async def ask_faq(topic_id: str, user_id: int, db: Session = Depends(get_db)):
    """Ask a predefined FAQ question."""
    topic = next((t for t in FAQ_TOPICS if t.id == topic_id), None)
    if not topic:
        raise HTTPException(status_code=404, detail="FAQ topic not found")
    
    # Use the chat endpoint with the FAQ question
    request = ChatRequest(user_id=user_id, message=topic.question)
    return await chat(request, db)


# Admin endpoints
@router.get("/admin/users", response_model=List[UserProgressStats], tags=["Admin"])
async def get_all_users_progress(db: Session = Depends(get_db)):
    """Get all users with progress stats (admin only)."""
    users = db.query(User).filter(User.user_type == UserRole.NEW_HIRE).all()
    today = date.today()
    
    results = []
    for user in users:
        tasks = db.query(Task).filter(Task.user_id == user.id).all()
        total = len(tasks)
        completed = len([t for t in tasks if t.status == DBTaskStatus.DONE])
        overdue = len([t for t in tasks if t.due_date < today and t.status != DBTaskStatus.DONE])
        
        results.append(UserProgressStats(
            user_id=user.id,
            user_name=user.name,
            role=user.role,
            department=user.department,
            start_date=user.start_date,
            total_tasks=total,
            completed_tasks=completed,
            progress_percentage=(completed / total * 100) if total > 0 else 0,
            overdue_tasks=overdue,
            days_since_start=(today - user.start_date).days
        ))
    
    return results


@router.get("/admin/metrics", response_model=AggregateMetrics, tags=["Admin"])
async def get_aggregate_metrics(db: Session = Depends(get_db)):
    """Get aggregate metrics for admin dashboard."""
    today = date.today()
    
    # Total users
    total_users = db.query(User).count()
    total_new_hires = db.query(User).filter(User.user_type == UserRole.NEW_HIRE).count()
    
    # Completion stats
    new_hires = db.query(User).filter(User.user_type == UserRole.NEW_HIRE).all()
    completion_percentages = []
    days_to_complete = []
    
    for user in new_hires:
        tasks = db.query(Task).filter(Task.user_id == user.id).all()
        if tasks:
            total = len(tasks)
            completed = len([t for t in tasks if t.status == DBTaskStatus.DONE])
            completion_percentages.append(completed / total * 100)
            
            # If fully completed, calculate days
            if completed == total and tasks:
                last_completion = max(
                    (t.completed_at for t in tasks if t.completed_at),
                    default=None
                )
                if last_completion:
                    days = (last_completion.date() - user.start_date).days
                    days_to_complete.append(days)
    
    avg_completion = sum(completion_percentages) / len(completion_percentages) if completion_percentages else 0
    avg_days = sum(days_to_complete) / len(days_to_complete) if days_to_complete else None
    
    # Completion by department
    completion_by_dept = {}
    for dept in ["Engineering", "Sales", "Marketing", "Operations"]:
        dept_users = [u for u in new_hires if u.department == dept]
        if dept_users:
            dept_completions = []
            for user in dept_users:
                tasks = db.query(Task).filter(Task.user_id == user.id).all()
                if tasks:
                    completed = len([t for t in tasks if t.status == DBTaskStatus.DONE])
                    dept_completions.append(completed / len(tasks) * 100)
            if dept_completions:
                completion_by_dept[dept] = sum(dept_completions) / len(dept_completions)
    
    # Queries by department (from routing logs)
    queries_by_dept = {}
    for dept in ["HR", "IT", "Security", "Finance", "General"]:
        count = db.query(RoutingLog).filter(
            RoutingLog.final_department == dept
        ).count()
        queries_by_dept[dept] = count
    
    # Today's queries
    today_start = datetime.combine(today, datetime.min.time())
    queries_today = db.query(RoutingLog).filter(
        RoutingLog.timestamp >= today_start
    ).count()
    
    # Resolution rate (simplified - % of conversations that don't have escalation keywords)
    total_conversations = db.query(Message).filter(Message.source == "assistant").count()
    resolution_rate = 0.85  # Placeholder - would need actual escalation tracking
    
    return AggregateMetrics(
        total_users=total_users,
        total_new_hires=total_new_hires,
        avg_completion_percentage=avg_completion,
        avg_days_to_complete=avg_days,
        completion_by_department=completion_by_dept,
        queries_by_department=queries_by_dept,
        total_queries_today=queries_today,
        resolution_rate=resolution_rate
    )


# Helper function to create default tasks
async def _create_default_tasks(db: Session, user_id: int):
    """Create default onboarding tasks for a new user."""
    today = date.today()
    
    default_tasks = [
        # HR Tasks
        {"title": "Complete HR orientation session", "department": "HR", "days": 1},
        {"title": "Review and sign employee handbook", "department": "HR", "days": 2},
        {"title": "Submit W-4 and I-9 forms", "department": "HR", "days": 3},
        {"title": "Set up direct deposit", "department": "HR", "days": 3},
        {"title": "Enroll in benefits", "department": "HR", "days": 30},
        
        # IT Tasks
        {"title": "Set up laptop and accounts", "department": "IT", "days": 1},
        {"title": "Configure email and calendar", "department": "IT", "days": 1},
        {"title": "Set up MFA on Okta", "department": "IT", "days": 1},
        {"title": "Install required software", "department": "IT", "days": 2},
        {"title": "Configure VPN access", "department": "IT", "days": 3},
        
        # Security Tasks
        {"title": "Sign NDA and confidentiality agreement", "department": "Security", "days": 1},
        {"title": "Complete Security Awareness training", "department": "Security", "days": 7},
        {"title": "Complete Data Protection training", "department": "Security", "days": 7},
        {"title": "Complete Phishing Prevention training", "department": "Security", "days": 14},
        
        # Finance Tasks
        {"title": "Set up Expensify account", "department": "Finance", "days": 7},
        {"title": "Review expense policy", "department": "Finance", "days": 7},
        {"title": "Set up Concur travel profile", "department": "Finance", "days": 14},
    ]
    
    for task_data in default_tasks:
        task = Task(
            user_id=user_id,
            title=task_data["title"],
            description=f"Complete {task_data['title'].lower()}",
            department=DBDepartment(task_data["department"]),
            due_date=today + timedelta(days=task_data["days"]),
            status=DBTaskStatus.NOT_STARTED
        )
        db.add(task)
    
    db.commit()

