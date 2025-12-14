"""Feedback service for collecting and processing user feedback."""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import Feedback, FeedbackType, Message, RoutingLog

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for managing user feedback on assistant responses."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def submit_feedback(
        self,
        user_id: int,
        message_id: int,
        feedback_type: FeedbackType,
        comment: Optional[str] = None,
        routing_was_correct: Optional[bool] = None,
        answer_was_accurate: Optional[bool] = None,
        suggested_department: Optional[str] = None
    ) -> Feedback:
        """Submit feedback for a message."""
        # Check if feedback already exists
        existing = self.db.query(Feedback).filter(
            Feedback.message_id == message_id
        ).first()
        
        if existing:
            # Update existing feedback
            existing.feedback_type = feedback_type
            existing.comment = comment
            existing.routing_was_correct = routing_was_correct
            existing.answer_was_accurate = answer_was_accurate
            existing.suggested_department = suggested_department
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Get message details for routing feedback
        message = self.db.query(Message).filter(Message.id == message_id).first()
        query_text = None
        predicted_department = None
        
        if message and message.extra_data:
            routing_info = message.extra_data.get("routing", {})
            query_text = message.extra_data.get("original_query")
            predicted_department = routing_info.get("predicted_department")
        
        feedback = Feedback(
            user_id=user_id,
            message_id=message_id,
            feedback_type=feedback_type,
            comment=comment,
            routing_was_correct=routing_was_correct,
            answer_was_accurate=answer_was_accurate,
            query_text=query_text,
            predicted_department=predicted_department,
            suggested_department=suggested_department
        )
        
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        
        logger.info(f"Feedback submitted: user={user_id}, message={message_id}, type={feedback_type}")
        return feedback
    
    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get feedback statistics for the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        total = self.db.query(Feedback).filter(
            Feedback.created_at >= cutoff
        ).count()
        
        helpful = self.db.query(Feedback).filter(
            Feedback.created_at >= cutoff,
            Feedback.feedback_type == FeedbackType.HELPFUL
        ).count()
        
        not_helpful = self.db.query(Feedback).filter(
            Feedback.created_at >= cutoff,
            Feedback.feedback_type == FeedbackType.NOT_HELPFUL
        ).count()
        
        routing_correct = self.db.query(Feedback).filter(
            Feedback.created_at >= cutoff,
            Feedback.routing_was_correct == True
        ).count()
        
        routing_incorrect = self.db.query(Feedback).filter(
            Feedback.created_at >= cutoff,
            Feedback.routing_was_correct == False
        ).count()
        
        return {
            "period_days": days,
            "total_feedback": total,
            "helpful_count": helpful,
            "not_helpful_count": not_helpful,
            "helpful_rate": helpful / total if total > 0 else 0,
            "routing_correct_count": routing_correct,
            "routing_incorrect_count": routing_incorrect,
            "routing_accuracy": routing_correct / (routing_correct + routing_incorrect) if (routing_correct + routing_incorrect) > 0 else 0
        }
    
    def get_feedback_for_retraining(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get feedback data suitable for model retraining."""
        feedback_data = self.db.query(Feedback).filter(
            Feedback.routing_was_correct.isnot(None),
            Feedback.query_text.isnot(None)
        ).order_by(Feedback.created_at.desc()).limit(limit).all()
        
        training_data = []
        for fb in feedback_data:
            if fb.routing_was_correct:
                # Use predicted department as label
                label = fb.predicted_department
            else:
                # Use suggested department as corrected label
                label = fb.suggested_department or fb.predicted_department
            
            if label and fb.query_text:
                training_data.append({
                    "query": fb.query_text,
                    "department": label,
                    "is_correction": not fb.routing_was_correct
                })
        
        return training_data
    
    def get_recent_negative_feedback(self, limit: int = 50) -> List[Feedback]:
        """Get recent negative feedback for review."""
        return self.db.query(Feedback).filter(
            Feedback.feedback_type == FeedbackType.NOT_HELPFUL
        ).order_by(Feedback.created_at.desc()).limit(limit).all()

