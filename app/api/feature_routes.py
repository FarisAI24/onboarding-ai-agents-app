"""API routes for new features."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.database.models import (
    User, FAQ, Department, FeedbackType, AuditLog,
    Achievement, TrainingModule, CalendarEvent, Workflow,
    ChurnPrediction as ChurnPredictionModel, ChurnRisk
)
from app.auth.dependencies import get_current_active_user, require_roles
from app.services import (
    FeedbackService, FAQService, AchievementService,
    ChurnPredictionService, WorkflowService, TrainingService,
    CalendarService, get_translation_service
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============== Schemas ==============

class FeedbackCreate(BaseModel):
    message_id: int
    feedback_type: str = Field(..., pattern="^(helpful|not_helpful)$")
    comment: Optional[str] = None
    routing_was_correct: Optional[bool] = None
    answer_was_accurate: Optional[bool] = None
    suggested_department: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    message_id: int
    feedback_type: str
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str
    department: Optional[str] = None
    question_ar: Optional[str] = None
    answer_ar: Optional[str] = None
    tags: Optional[List[str]] = None


class FAQResponse(BaseModel):
    id: int
    question: str
    answer: str
    category: str
    department: Optional[str]
    question_ar: Optional[str]
    answer_ar: Optional[str]
    tags: Optional[List[str]]
    view_count: int
    helpful_count: int
    is_published: bool

    class Config:
        from_attributes = True


class AchievementResponse(BaseModel):
    id: int
    name: str
    name_ar: Optional[str]
    description: str
    description_ar: Optional[str]
    icon: str
    category: str
    points: int
    unlocked: bool
    progress: float
    unlocked_at: Optional[str]


class TrainingModuleResponse(BaseModel):
    id: int
    title: str
    title_ar: Optional[str]
    description: Optional[str]
    department: str
    duration_minutes: int
    passing_score: int
    is_required: bool
    order_index: int

    class Config:
        from_attributes = True


class TrainingProgressResponse(BaseModel):
    module_id: int
    module_title: str
    status: str
    current_step: int
    score: Optional[int]
    attempts: int
    started_at: Optional[str]
    completed_at: Optional[str]


class QuizSubmission(BaseModel):
    answers: List[int]


class QuizResult(BaseModel):
    score: int
    passing_score: int
    passed: bool
    correct: int
    total: int


class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    all_day: bool = False
    task_id: Optional[int] = None
    reminder_minutes: int = 30


class CalendarEventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    all_day: bool
    task_id: Optional[int]

    class Config:
        from_attributes = True


class ChurnPredictionResponse(BaseModel):
    user_id: int
    risk_level: str
    churn_probability: float
    risk_factors: List[str]
    recommended_actions: List[str]
    prediction_date: datetime


class TranslationsResponse(BaseModel):
    language: str
    direction: str
    translations: dict


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    action: str
    resource_type: str
    resource_id: Optional[int]
    user_id: Optional[int]
    user_email: Optional[str]
    ip_address: Optional[str]
    status: str
    details: Optional[dict]

    class Config:
        from_attributes = True


# ============== Feedback Routes ==============

@router.post("/feedback", response_model=FeedbackResponse, tags=["Feedback"])
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit feedback on an assistant response."""
    service = FeedbackService(db)
    
    result = service.submit_feedback(
        user_id=current_user.id,
        message_id=feedback.message_id,
        feedback_type=FeedbackType(feedback.feedback_type),
        comment=feedback.comment,
        routing_was_correct=feedback.routing_was_correct,
        answer_was_accurate=feedback.answer_was_accurate,
        suggested_department=feedback.suggested_department
    )
    
    return result


@router.get("/feedback/stats", tags=["Feedback"], dependencies=[Depends(require_roles("admin", "manager", "hr_admin"))])
async def get_feedback_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get feedback statistics (manager+ only)."""
    service = FeedbackService(db)
    return service.get_feedback_stats(days=days)


# ============== FAQ Routes ==============

@router.get("/faqs", response_model=List[FAQResponse], tags=["FAQ"])
async def get_faqs(
    category: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    language: str = Query("en", pattern="^(en|ar)$"),
    db: Session = Depends(get_db)
):
    """Get FAQs with optional filtering."""
    service = FAQService(db)
    
    if search:
        faqs = service.search_faqs(search, language=language)
    else:
        dept = Department(department) if department else None
        faqs = service.get_faqs(category=category, department=dept)
    
    return faqs


@router.get("/faqs/categories", tags=["FAQ"])
async def get_faq_categories(db: Session = Depends(get_db)):
    """Get all FAQ categories."""
    service = FAQService(db)
    return {"categories": service.get_categories()}


@router.get("/faqs/popular", response_model=List[FAQResponse], tags=["FAQ"])
async def get_popular_faqs(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get most popular FAQs."""
    service = FAQService(db)
    return service.get_popular_faqs(limit=limit)


@router.get("/faqs/{faq_id}", response_model=FAQResponse, tags=["FAQ"])
async def get_faq(faq_id: int, db: Session = Depends(get_db)):
    """Get a specific FAQ."""
    service = FAQService(db)
    faq = service.get_faq(faq_id)
    
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    service.increment_view_count(faq_id)
    return faq


@router.post("/faqs", response_model=FAQResponse, tags=["FAQ"], dependencies=[Depends(require_roles("admin", "hr_admin"))])
async def create_faq(
    faq: FAQCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new FAQ (admin only)."""
    service = FAQService(db)
    
    dept = Department(faq.department) if faq.department else None
    
    return service.create_faq(
        question=faq.question,
        answer=faq.answer,
        category=faq.category,
        department=dept,
        question_ar=faq.question_ar,
        answer_ar=faq.answer_ar,
        tags=faq.tags,
        created_by=current_user.id
    )


@router.put("/faqs/{faq_id}", response_model=FAQResponse, tags=["FAQ"], dependencies=[Depends(require_roles("admin", "hr_admin"))])
async def update_faq(
    faq_id: int,
    faq: FAQCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an FAQ (admin only)."""
    service = FAQService(db)
    
    result = service.update_faq(
        faq_id,
        question=faq.question,
        answer=faq.answer,
        category=faq.category,
        question_ar=faq.question_ar,
        answer_ar=faq.answer_ar,
        tags=faq.tags
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    return result


@router.delete("/faqs/{faq_id}", tags=["FAQ"], dependencies=[Depends(require_roles("admin", "hr_admin"))])
async def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an FAQ (admin only)."""
    service = FAQService(db)
    
    if not service.delete_faq(faq_id):
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    return {"status": "deleted"}


@router.post("/faqs/{faq_id}/feedback", tags=["FAQ"])
async def faq_feedback(
    faq_id: int,
    helpful: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit feedback on an FAQ."""
    service = FAQService(db)
    service.record_feedback(faq_id, helpful)
    return {"status": "recorded"}


# ============== Achievement Routes ==============

@router.get("/achievements", response_model=List[AchievementResponse], tags=["Achievements"])
async def get_achievements(
    include_locked: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's achievements."""
    service = AchievementService(db)
    return service.get_user_achievements(current_user.id, include_locked=include_locked)


@router.get("/achievements/points", tags=["Achievements"])
async def get_achievement_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's total achievement points."""
    service = AchievementService(db)
    return {"points": service.get_user_points(current_user.id)}


@router.get("/achievements/leaderboard", tags=["Achievements"])
async def get_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get achievement leaderboard."""
    service = AchievementService(db)
    return service.get_leaderboard(limit=limit)


@router.get("/achievements/notifications", tags=["Achievements"])
async def get_achievement_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get unnotified achievement unlocks."""
    service = AchievementService(db)
    return service.get_unnotified_achievements(current_user.id)


@router.post("/achievements/check", tags=["Achievements"])
async def check_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Check and unlock eligible achievements."""
    service = AchievementService(db)
    unlocked = service.check_and_unlock(current_user.id)
    return {
        "checked": True,
        "unlocked": [{"id": a.id, "name": a.name, "points": a.points} for a in unlocked]
    }


# ============== Training Routes ==============

@router.get("/training/modules", response_model=List[TrainingModuleResponse], tags=["Training"])
async def get_training_modules(
    department: Optional[str] = None,
    required_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get available training modules."""
    service = TrainingService(db)
    dept = Department(department) if department else None
    return service.list_modules(department=dept, required_only=required_only)


@router.get("/training/modules/{module_id}", tags=["Training"])
async def get_training_module(
    module_id: int,
    language: str = Query("en", pattern="^(en|ar)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get training module content."""
    service = TrainingService(db)
    content = service.get_module_content(module_id, language=language)
    
    if not content:
        raise HTTPException(status_code=404, detail="Module not found")
    
    return content


@router.get("/training/progress", response_model=List[TrainingProgressResponse], tags=["Training"])
async def get_training_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's training progress."""
    service = TrainingService(db)
    return service.get_user_progress(current_user.id)


@router.get("/training/summary", tags=["Training"])
async def get_training_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's training summary."""
    service = TrainingService(db)
    return service.get_user_training_summary(current_user.id)


@router.post("/training/modules/{module_id}/start", tags=["Training"])
async def start_training_module(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start a training module."""
    service = TrainingService(db)
    progress = service.start_module(current_user.id, module_id)
    return {"status": "started", "module_id": module_id, "attempt": progress.attempts}


@router.post("/training/modules/{module_id}/progress", tags=["Training"])
async def update_training_progress(
    module_id: int,
    current_step: int,
    time_spent: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update training progress."""
    service = TrainingService(db)
    service.update_progress(current_user.id, module_id, current_step, time_spent)
    return {"status": "updated"}


@router.post("/training/modules/{module_id}/quiz", response_model=QuizResult, tags=["Training"])
async def submit_training_quiz(
    module_id: int,
    submission: QuizSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit quiz answers."""
    service = TrainingService(db)
    
    try:
        result = service.submit_quiz(current_user.id, module_id, submission.answers)
        return QuizResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Calendar Routes ==============

@router.get("/calendar/events", response_model=List[CalendarEventResponse], tags=["Calendar"])
async def get_calendar_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's calendar events."""
    service = CalendarService(db)
    return service.get_events(current_user.id, start_date=start_date, end_date=end_date)


@router.post("/calendar/events", response_model=CalendarEventResponse, tags=["Calendar"])
async def create_calendar_event(
    event: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a calendar event."""
    service = CalendarService(db)
    return service.create_event(
        user_id=current_user.id,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        all_day=event.all_day,
        task_id=event.task_id,
        reminder_minutes=event.reminder_minutes
    )


@router.get("/calendar/week", tags=["Calendar"])
async def get_week_view(
    week_start: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get week view of calendar events."""
    service = CalendarService(db)
    return service.get_week_view(current_user.id, week_start=week_start)


@router.post("/calendar/sync-tasks", tags=["Calendar"])
async def sync_tasks_to_calendar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync tasks to calendar."""
    service = CalendarService(db)
    events = service.sync_tasks_to_calendar(current_user.id)
    return {"synced": len(events), "events": [e.id for e in events]}


@router.get("/calendar/export.ics", response_class=PlainTextResponse, tags=["Calendar"])
async def export_calendar_ics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export calendar as iCal file."""
    service = CalendarService(db)
    ical = service.generate_ical(current_user.id)
    return Response(
        content=ical,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=onboarding-calendar.ics"}
    )


@router.delete("/calendar/events/{event_id}", tags=["Calendar"])
async def delete_calendar_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a calendar event."""
    service = CalendarService(db)
    event = service.get_event(event_id)
    
    if not event or event.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Event not found")
    
    service.delete_event(event_id)
    return {"status": "deleted"}


# ============== Churn Prediction Routes ==============

@router.get("/churn/risk", response_model=ChurnPredictionResponse, tags=["Churn Prediction"], dependencies=[Depends(require_roles("admin", "manager", "hr_admin"))])
async def get_churn_risk(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get churn risk for current user (manager only for demo)."""
    service = ChurnPredictionService(db)
    
    # For managers viewing their own risk
    prediction = service.predict_churn_risk(current_user.id)
    
    return ChurnPredictionResponse(
        user_id=prediction.user_id,
        risk_level=prediction.risk_level.value,
        churn_probability=prediction.churn_probability,
        risk_factors=prediction.risk_factors or [],
        recommended_actions=prediction.recommended_actions or [],
        prediction_date=prediction.prediction_date
    )


@router.get("/churn/at-risk", tags=["Churn Prediction"], dependencies=[Depends(require_roles("admin", "hr_admin"))])
async def get_at_risk_users(
    min_risk: str = Query("medium", pattern="^(low|medium|high|critical)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get users at risk of churning (HR admin only)."""
    service = ChurnPredictionService(db)
    return service.get_at_risk_users(min_risk=ChurnRisk(min_risk))


@router.post("/churn/predict/{user_id}", response_model=ChurnPredictionResponse, tags=["Churn Prediction"], dependencies=[Depends(require_roles("admin", "hr_admin"))])
async def predict_user_churn(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Predict churn risk for a specific user (HR admin only)."""
    service = ChurnPredictionService(db)
    
    try:
        prediction = service.predict_churn_risk(user_id)
        return ChurnPredictionResponse(
            user_id=prediction.user_id,
            risk_level=prediction.risk_level.value,
            churn_probability=prediction.churn_probability,
            risk_factors=prediction.risk_factors or [],
            recommended_actions=prediction.recommended_actions or [],
            prediction_date=prediction.prediction_date
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============== i18n Routes ==============

@router.get("/i18n/{language}", response_model=TranslationsResponse, tags=["i18n"])
async def get_translations(language: str):
    """Get all translations for a language (en or ar)."""
    if language not in ["en", "ar"]:
        raise HTTPException(status_code=400, detail="Language must be 'en' or 'ar'")
    
    service = get_translation_service()
    
    return TranslationsResponse(
        language=language,
        direction=service.get_direction(language),
        translations=service.get_all_translations(language)
    )


# ============== Audit Log Routes ==============

@router.get("/audit/logs", response_model=List[AuditLogResponse], tags=["Audit"], dependencies=[Depends(require_roles("admin", "security_admin"))])
async def get_audit_logs(
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit logs with filtering (admin only)."""
    query = db.query(AuditLog)
    
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    return logs


@router.get("/audit/summary", tags=["Audit"], dependencies=[Depends(require_roles("admin", "security_admin"))])
async def get_audit_summary(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get audit log summary (admin only)."""
    from sqlalchemy import func
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Count by action type
    action_counts = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label("count")
    ).filter(
        AuditLog.timestamp >= cutoff
    ).group_by(AuditLog.action).all()
    
    # Count by status
    status_counts = db.query(
        AuditLog.status,
        func.count(AuditLog.id).label("count")
    ).filter(
        AuditLog.timestamp >= cutoff
    ).group_by(AuditLog.status).all()
    
    # Recent failures
    recent_failures = db.query(AuditLog).filter(
        AuditLog.timestamp >= cutoff,
        AuditLog.status == "failure"
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return {
        "period_days": days,
        "action_counts": {a: c for a, c in action_counts},
        "status_counts": {s: c for s, c in status_counts},
        "recent_failures": [
            {
                "id": f.id,
                "action": f.action,
                "user_email": f.user_email,
                "timestamp": f.timestamp.isoformat(),
                "error": f.error_message
            }
            for f in recent_failures
        ]
    }

