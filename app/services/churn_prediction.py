"""Churn prediction service based on onboarding engagement."""
import logging
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database.models import (
    User, Task, TaskStatus, Message, EngagementMetrics,
    ChurnPrediction, ChurnRisk, TrainingProgress, Feedback
)

logger = logging.getLogger(__name__)


@dataclass
class EngagementScore:
    """User engagement score breakdown."""
    user_id: int
    overall_score: float  # 0-100
    activity_score: float
    task_completion_score: float
    learning_score: float
    interaction_score: float
    trend: str  # improving, declining, stable
    risk_factors: List[str]


class ChurnPredictionService:
    """Service for predicting churn risk based on engagement."""
    
    # Weights for different engagement factors
    WEIGHTS = {
        "task_completion": 0.30,
        "activity_frequency": 0.25,
        "learning_progress": 0.20,
        "chat_engagement": 0.15,
        "feedback_sentiment": 0.10
    }
    
    # Risk thresholds
    RISK_THRESHOLDS = {
        "critical": 25,
        "high": 45,
        "medium": 65,
        "low": 100
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_engagement_score(self, user_id: int) -> EngagementScore:
        """Calculate comprehensive engagement score for a user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Calculate individual scores
        task_score = self._calculate_task_score(user_id)
        activity_score = self._calculate_activity_score(user_id, user.start_date)
        learning_score = self._calculate_learning_score(user_id)
        interaction_score = self._calculate_interaction_score(user_id)
        
        # Calculate weighted overall score
        overall_score = (
            task_score * self.WEIGHTS["task_completion"] +
            activity_score * self.WEIGHTS["activity_frequency"] +
            learning_score * self.WEIGHTS["learning_progress"] +
            interaction_score * (self.WEIGHTS["chat_engagement"] + self.WEIGHTS["feedback_sentiment"])
        )
        
        # Determine trend
        trend = self._calculate_trend(user_id)
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            user_id, user.start_date,
            task_score, activity_score, learning_score, interaction_score
        )
        
        return EngagementScore(
            user_id=user_id,
            overall_score=round(overall_score, 1),
            activity_score=round(activity_score, 1),
            task_completion_score=round(task_score, 1),
            learning_score=round(learning_score, 1),
            interaction_score=round(interaction_score, 1),
            trend=trend,
            risk_factors=risk_factors
        )
    
    def _calculate_task_score(self, user_id: int) -> float:
        """Calculate task completion score."""
        total_tasks = self.db.query(Task).filter(Task.user_id == user_id).count()
        
        if total_tasks == 0:
            return 50.0  # Neutral score if no tasks
        
        completed_tasks = self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.DONE
        ).count()
        
        in_progress_tasks = self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.IN_PROGRESS
        ).count()
        
        overdue_tasks = self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.status != TaskStatus.DONE,
            Task.due_date < date.today()
        ).count()
        
        # Score calculation
        completion_rate = completed_tasks / total_tasks
        progress_bonus = (in_progress_tasks / total_tasks) * 0.3
        overdue_penalty = (overdue_tasks / total_tasks) * 0.5
        
        score = (completion_rate + progress_bonus - overdue_penalty) * 100
        return max(0, min(100, score))
    
    def _calculate_activity_score(self, user_id: int, start_date: date) -> float:
        """Calculate activity frequency score."""
        days_since_start = (date.today() - start_date).days
        if days_since_start <= 0:
            return 100.0  # Just started
        
        # Get days with activity in last 14 days
        two_weeks_ago = date.today() - timedelta(days=14)
        
        # Count days with messages
        active_days = self.db.query(
            func.date(Message.timestamp)
        ).filter(
            Message.user_id == user_id,
            Message.timestamp >= two_weeks_ago
        ).distinct().count()
        
        # Count days with task updates
        task_activity = self.db.query(
            func.date(Task.updated_at)
        ).filter(
            Task.user_id == user_id,
            Task.updated_at >= two_weeks_ago
        ).distinct().count()
        
        total_active_days = min(14, active_days + task_activity)
        
        # Calculate score (expecting activity ~50% of days)
        expected_active_days = min(days_since_start, 7)  # At least half of first week
        score = (total_active_days / expected_active_days) * 100 if expected_active_days > 0 else 100
        
        return max(0, min(100, score))
    
    def _calculate_learning_score(self, user_id: int) -> float:
        """Calculate learning/training progress score."""
        from app.database.models import TrainingModule
        
        total_modules = self.db.query(TrainingModule).filter(
            TrainingModule.is_active == True,
            TrainingModule.is_required == True
        ).count()
        
        if total_modules == 0:
            return 100.0  # No required training
        
        # Get training progress
        completed = self.db.query(TrainingProgress).filter(
            TrainingProgress.user_id == user_id,
            TrainingProgress.status == "completed"
        ).count()
        
        in_progress = self.db.query(TrainingProgress).filter(
            TrainingProgress.user_id == user_id,
            TrainingProgress.status == "in_progress"
        ).count()
        
        # Get average scores
        avg_score = self.db.query(
            func.avg(TrainingProgress.score)
        ).filter(
            TrainingProgress.user_id == user_id,
            TrainingProgress.score.isnot(None)
        ).scalar() or 0
        
        completion_score = (completed / total_modules) * 60
        progress_score = (in_progress / total_modules) * 20
        performance_score = (avg_score / 100) * 20
        
        return min(100, completion_score + progress_score + performance_score)
    
    def _calculate_interaction_score(self, user_id: int) -> float:
        """Calculate chat interaction and feedback score."""
        # Count recent messages
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        message_count = self.db.query(Message).filter(
            Message.user_id == user_id,
            Message.source == "user",
            Message.timestamp >= week_ago
        ).count()
        
        # Get feedback sentiment
        positive_feedback = self.db.query(Feedback).filter(
            Feedback.user_id == user_id,
            Feedback.feedback_type == "helpful"
        ).count()
        
        negative_feedback = self.db.query(Feedback).filter(
            Feedback.user_id == user_id,
            Feedback.feedback_type == "not_helpful"
        ).count()
        
        # Message score (expecting 2-5 messages per week)
        message_score = min(100, (message_count / 3) * 100)
        
        # Sentiment score
        total_feedback = positive_feedback + negative_feedback
        if total_feedback > 0:
            sentiment_score = (positive_feedback / total_feedback) * 100
        else:
            sentiment_score = 50  # Neutral if no feedback
        
        return (message_score * 0.6 + sentiment_score * 0.4)
    
    def _calculate_trend(self, user_id: int) -> str:
        """Calculate engagement trend over time."""
        # Compare last week to previous week
        now = datetime.utcnow()
        last_week_start = now - timedelta(days=7)
        prev_week_start = now - timedelta(days=14)
        
        last_week_activity = self.db.query(Message).filter(
            Message.user_id == user_id,
            Message.timestamp >= last_week_start
        ).count()
        
        prev_week_activity = self.db.query(Message).filter(
            Message.user_id == user_id,
            Message.timestamp >= prev_week_start,
            Message.timestamp < last_week_start
        ).count()
        
        if prev_week_activity == 0:
            return "stable"
        
        change_rate = (last_week_activity - prev_week_activity) / prev_week_activity
        
        if change_rate > 0.2:
            return "improving"
        elif change_rate < -0.2:
            return "declining"
        return "stable"
    
    def _identify_risk_factors(
        self,
        user_id: int,
        start_date: date,
        task_score: float,
        activity_score: float,
        learning_score: float,
        interaction_score: float
    ) -> List[str]:
        """Identify specific risk factors."""
        risk_factors = []
        
        if task_score < 40:
            risk_factors.append("Low task completion rate")
        
        if activity_score < 30:
            risk_factors.append("Infrequent platform activity")
        
        if learning_score < 50:
            risk_factors.append("Training modules incomplete")
        
        if interaction_score < 40:
            risk_factors.append("Low engagement with assistant")
        
        # Check for overdue tasks
        overdue = self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.status != TaskStatus.DONE,
            Task.due_date < date.today()
        ).count()
        
        if overdue > 0:
            risk_factors.append(f"{overdue} overdue task(s)")
        
        # Check days without activity
        last_activity = self.db.query(
            func.max(Message.timestamp)
        ).filter(Message.user_id == user_id).scalar()
        
        if last_activity:
            days_inactive = (datetime.utcnow() - last_activity).days
            if days_inactive >= 3:
                risk_factors.append(f"No activity in {days_inactive} days")
        
        # Check time since start
        days_since_start = (date.today() - start_date).days
        if days_since_start > 30:
            all_tasks = self.db.query(Task).filter(Task.user_id == user_id).count()
            completed = self.db.query(Task).filter(
                Task.user_id == user_id,
                Task.status == TaskStatus.DONE
            ).count()
            
            if all_tasks > 0 and (completed / all_tasks) < 0.5:
                risk_factors.append("Onboarding behind schedule")
        
        return risk_factors
    
    def predict_churn_risk(self, user_id: int) -> ChurnPrediction:
        """Predict churn risk for a user."""
        engagement = self.calculate_engagement_score(user_id)
        
        # Determine risk level
        score = engagement.overall_score
        if score <= self.RISK_THRESHOLDS["critical"]:
            risk_level = ChurnRisk.CRITICAL
        elif score <= self.RISK_THRESHOLDS["high"]:
            risk_level = ChurnRisk.HIGH
        elif score <= self.RISK_THRESHOLDS["medium"]:
            risk_level = ChurnRisk.MEDIUM
        else:
            risk_level = ChurnRisk.LOW
        
        # Adjust for trend
        if engagement.trend == "declining" and risk_level != ChurnRisk.CRITICAL:
            # Elevate risk if declining
            risk_levels = [ChurnRisk.LOW, ChurnRisk.MEDIUM, ChurnRisk.HIGH, ChurnRisk.CRITICAL]
            current_idx = risk_levels.index(risk_level)
            if current_idx < len(risk_levels) - 1:
                risk_level = risk_levels[current_idx + 1]
        
        # Calculate churn probability
        churn_probability = 1 - (score / 100)
        if engagement.trend == "declining":
            churn_probability = min(1.0, churn_probability + 0.1)
        elif engagement.trend == "improving":
            churn_probability = max(0.0, churn_probability - 0.1)
        
        # Generate recommended actions
        recommended_actions = self._get_recommended_actions(
            risk_level, engagement.risk_factors
        )
        
        # Save prediction
        prediction = ChurnPrediction(
            user_id=user_id,
            risk_level=risk_level,
            churn_probability=round(churn_probability, 3),
            risk_factors=engagement.risk_factors,
            recommended_actions=recommended_actions,
            model_version="v1.0"
        )
        
        self.db.add(prediction)
        self.db.commit()
        self.db.refresh(prediction)
        
        logger.info(f"Churn prediction: user={user_id}, risk={risk_level.value}, prob={churn_probability:.2f}")
        return prediction
    
    def _get_recommended_actions(
        self,
        risk_level: ChurnRisk,
        risk_factors: List[str]
    ) -> List[str]:
        """Get recommended actions based on risk."""
        actions = []
        
        if risk_level in [ChurnRisk.CRITICAL, ChurnRisk.HIGH]:
            actions.append("Schedule 1-on-1 check-in with manager")
            actions.append("Assign buddy/mentor for additional support")
        
        for factor in risk_factors:
            if "task completion" in factor.lower():
                actions.append("Review and prioritize pending tasks")
                actions.append("Consider extending deadlines if needed")
            elif "activity" in factor.lower():
                actions.append("Send engagement reminder")
                actions.append("Highlight quick wins and easy tasks")
            elif "training" in factor.lower():
                actions.append("Send training reminder with deadlines")
                actions.append("Offer training assistance")
            elif "overdue" in factor.lower():
                actions.append("Address overdue tasks immediately")
            elif "no activity" in factor.lower():
                actions.append("Reach out via email/phone")
        
        if risk_level == ChurnRisk.CRITICAL:
            actions.append("Escalate to HR for intervention")
        
        return list(set(actions))[:5]  # Return unique top 5 actions
    
    def get_at_risk_users(self, min_risk: ChurnRisk = ChurnRisk.MEDIUM) -> List[Dict]:
        """Get users at or above specified risk level."""
        risk_order = {
            ChurnRisk.LOW: 0,
            ChurnRisk.MEDIUM: 1,
            ChurnRisk.HIGH: 2,
            ChurnRisk.CRITICAL: 3
        }
        
        # Get latest predictions for each user
        subquery = self.db.query(
            ChurnPrediction.user_id,
            func.max(ChurnPrediction.prediction_date).label("latest")
        ).group_by(ChurnPrediction.user_id).subquery()
        
        predictions = self.db.query(ChurnPrediction).join(
            subquery,
            and_(
                ChurnPrediction.user_id == subquery.c.user_id,
                ChurnPrediction.prediction_date == subquery.c.latest
            )
        ).join(User).all()
        
        at_risk = []
        for pred in predictions:
            if risk_order.get(pred.risk_level, 0) >= risk_order.get(min_risk, 1):
                user = self.db.query(User).filter(User.id == pred.user_id).first()
                
                # Calculate engagement factors for display
                factors = self._get_user_factors(pred.user_id, user.start_date if user else date.today())
                
                at_risk.append({
                    "user_id": pred.user_id,
                    "user_name": user.name if user else "Unknown",  # Frontend expects user_name
                    "user_email": user.email if user else "",       # Frontend expects user_email
                    "department": user.department if user else "",
                    "risk_level": pred.risk_level.value.upper(),    # Frontend expects uppercase
                    "risk_score": pred.churn_probability,           # Frontend expects risk_score
                    "factors": factors,                             # Frontend expects factors object
                    "recommendations": pred.recommended_actions or [],  # Frontend expects recommendations
                    "predicted_at": pred.prediction_date.isoformat()
                })
        
        # Sort by risk level (highest first)
        at_risk.sort(key=lambda x: risk_order.get(ChurnRisk(x["risk_level"].lower()), 0), reverse=True)
        return at_risk
    
    def _get_user_factors(self, user_id: int, start_date: date) -> Dict[str, float]:
        """Get detailed engagement factors for display."""
        task_score = self._calculate_task_score(user_id) / 100
        activity_score = self._calculate_activity_score(user_id, start_date) / 100
        learning_score = self._calculate_learning_score(user_id) / 100
        interaction_score = self._calculate_interaction_score(user_id) / 100
        
        # Calculate days since last activity
        last_activity = self.db.query(
            func.max(Message.timestamp)
        ).filter(Message.user_id == user_id).scalar()
        
        days_inactive = 0
        if last_activity:
            days_inactive = (datetime.utcnow() - last_activity).days
        
        return {
            "login_frequency": activity_score,
            "task_completion_rate": task_score,
            "chat_engagement": interaction_score,
            "training_progress": learning_score,
            "days_since_last_activity": days_inactive
        }
    
    def record_daily_engagement(self, user_id: int):
        """Record daily engagement metrics for a user."""
        today = date.today()
        
        # Check if already recorded today
        existing = self.db.query(EngagementMetrics).filter(
            EngagementMetrics.user_id == user_id,
            EngagementMetrics.date == today
        ).first()
        
        if existing:
            return existing
        
        # Calculate today's metrics
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        messages = self.db.query(Message).filter(
            Message.user_id == user_id,
            Message.source == "user",
            Message.timestamp >= today_start,
            Message.timestamp <= today_end
        ).count()
        
        tasks_completed = self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.DONE,
            Task.completed_at >= today_start,
            Task.completed_at <= today_end
        ).count()
        
        metrics = EngagementMetrics(
            user_id=user_id,
            date=today,
            chat_messages_sent=messages,
            tasks_completed=tasks_completed,
            login_count=1
        )
        
        self.db.add(metrics)
        self.db.commit()
        
        return metrics

