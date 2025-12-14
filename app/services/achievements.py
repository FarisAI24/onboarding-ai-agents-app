"""Achievement and gamification service."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import (
    Achievement, UserAchievement, AchievementCategory,
    User, Task, TaskStatus, Message, TrainingProgress
)

logger = logging.getLogger(__name__)

# Default achievements
DEFAULT_ACHIEVEMENTS = [
    {
        "name": "First Steps",
        "name_ar": "الخطوات الأولى",
        "description": "Complete your first onboarding task",
        "description_ar": "أكمل مهمة الإعداد الأولى",
        "icon": "🎯",
        "category": AchievementCategory.ONBOARDING,
        "points": 10,
        "criteria": {"type": "tasks_completed", "count": 1}
    },
    {
        "name": "Getting Started",
        "name_ar": "البداية",
        "description": "Complete 5 onboarding tasks",
        "description_ar": "أكمل 5 مهام إعداد",
        "icon": "⭐",
        "category": AchievementCategory.ONBOARDING,
        "points": 25,
        "criteria": {"type": "tasks_completed", "count": 5}
    },
    {
        "name": "Onboarding Pro",
        "name_ar": "محترف الإعداد",
        "description": "Complete all onboarding tasks",
        "description_ar": "أكمل جميع مهام الإعداد",
        "icon": "🏆",
        "category": AchievementCategory.ONBOARDING,
        "points": 100,
        "criteria": {"type": "all_tasks_completed"}
    },
    {
        "name": "Quick Learner",
        "name_ar": "سريع التعلم",
        "description": "Complete onboarding within first week",
        "description_ar": "أكمل الإعداد خلال الأسبوع الأول",
        "icon": "⚡",
        "category": AchievementCategory.SPEED,
        "points": 50,
        "criteria": {"type": "onboarding_speed", "days": 7}
    },
    {
        "name": "Curious Mind",
        "name_ar": "عقل فضولي",
        "description": "Ask 10 questions to the assistant",
        "description_ar": "اسأل 10 أسئلة للمساعد",
        "icon": "❓",
        "category": AchievementCategory.ENGAGEMENT,
        "points": 15,
        "criteria": {"type": "questions_asked", "count": 10}
    },
    {
        "name": "Knowledge Seeker",
        "name_ar": "باحث عن المعرفة",
        "description": "Ask 50 questions to the assistant",
        "description_ar": "اسأل 50 سؤالاً للمساعد",
        "icon": "📚",
        "category": AchievementCategory.ENGAGEMENT,
        "points": 40,
        "criteria": {"type": "questions_asked", "count": 50}
    },
    {
        "name": "Training Champion",
        "name_ar": "بطل التدريب",
        "description": "Complete all training modules",
        "description_ar": "أكمل جميع وحدات التدريب",
        "icon": "🎓",
        "category": AchievementCategory.LEARNING,
        "points": 75,
        "criteria": {"type": "all_training_completed"}
    },
    {
        "name": "Perfect Score",
        "name_ar": "النتيجة المثالية",
        "description": "Score 100% on a training quiz",
        "description_ar": "احصل على 100% في اختبار تدريبي",
        "icon": "💯",
        "category": AchievementCategory.LEARNING,
        "points": 30,
        "criteria": {"type": "quiz_perfect_score"}
    },
    {
        "name": "Feedback Helper",
        "name_ar": "مساعد الملاحظات",
        "description": "Provide feedback on 5 responses",
        "description_ar": "قدم ملاحظات على 5 ردود",
        "icon": "👍",
        "category": AchievementCategory.ENGAGEMENT,
        "points": 20,
        "criteria": {"type": "feedback_given", "count": 5}
    },
    {
        "name": "Early Bird",
        "name_ar": "الطائر المبكر",
        "description": "Complete a task before its due date",
        "description_ar": "أكمل مهمة قبل موعدها",
        "icon": "🌅",
        "category": AchievementCategory.SPEED,
        "points": 15,
        "criteria": {"type": "early_completion"}
    },
    {
        "name": "Streak Starter",
        "name_ar": "بداية السلسلة",
        "description": "Log in 3 days in a row",
        "description_ar": "سجل دخولك 3 أيام متتالية",
        "icon": "🔥",
        "category": AchievementCategory.ENGAGEMENT,
        "points": 20,
        "criteria": {"type": "login_streak", "days": 3}
    },
    {
        "name": "Dedicated",
        "name_ar": "مُلتزم",
        "description": "Log in 7 days in a row",
        "description_ar": "سجل دخولك 7 أيام متتالية",
        "icon": "💪",
        "category": AchievementCategory.ENGAGEMENT,
        "points": 50,
        "criteria": {"type": "login_streak", "days": 7}
    },
]


class AchievementService:
    """Service for managing achievements and gamification."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_achievements(self):
        """Initialize default achievements if not exist."""
        for ach_data in DEFAULT_ACHIEVEMENTS:
            existing = self.db.query(Achievement).filter(
                Achievement.name == ach_data["name"]
            ).first()
            
            if not existing:
                achievement = Achievement(**ach_data)
                self.db.add(achievement)
        
        self.db.commit()
        logger.info("Default achievements initialized")
    
    def check_and_unlock(self, user_id: int) -> List[Achievement]:
        """Check and unlock achievements for a user."""
        unlocked = []
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return unlocked
        
        achievements = self.db.query(Achievement).filter(
            Achievement.is_active == True
        ).all()
        
        for achievement in achievements:
            # Skip if already unlocked
            existing = self.db.query(UserAchievement).filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement.id,
                UserAchievement.progress >= 100
            ).first()
            
            if existing:
                continue
            
            # Check criteria
            progress = self._calculate_progress(user_id, achievement.criteria)
            
            if progress >= 100:
                self._unlock_achievement(user_id, achievement.id)
                unlocked.append(achievement)
            else:
                # Update partial progress
                self._update_progress(user_id, achievement.id, progress)
        
        return unlocked
    
    def _calculate_progress(self, user_id: int, criteria: Dict) -> float:
        """Calculate achievement progress based on criteria."""
        criteria_type = criteria.get("type")
        
        if criteria_type == "tasks_completed":
            count = self.db.query(Task).filter(
                Task.user_id == user_id,
                Task.status == TaskStatus.DONE
            ).count()
            target = criteria.get("count", 1)
            return min(100, (count / target) * 100)
        
        elif criteria_type == "all_tasks_completed":
            total = self.db.query(Task).filter(Task.user_id == user_id).count()
            done = self.db.query(Task).filter(
                Task.user_id == user_id,
                Task.status == TaskStatus.DONE
            ).count()
            if total == 0:
                return 0
            return 100 if done == total else (done / total) * 100
        
        elif criteria_type == "questions_asked":
            count = self.db.query(Message).filter(
                Message.user_id == user_id,
                Message.source == "user"
            ).count()
            target = criteria.get("count", 1)
            return min(100, (count / target) * 100)
        
        elif criteria_type == "onboarding_speed":
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return 0
            
            # Check if all tasks completed
            total = self.db.query(Task).filter(Task.user_id == user_id).count()
            done = self.db.query(Task).filter(
                Task.user_id == user_id,
                Task.status == TaskStatus.DONE
            ).count()
            
            if done != total or total == 0:
                return 0
            
            # Check if completed within time limit
            last_task = self.db.query(Task).filter(
                Task.user_id == user_id,
                Task.status == TaskStatus.DONE
            ).order_by(Task.completed_at.desc()).first()
            
            if last_task and last_task.completed_at:
                days = (last_task.completed_at.date() - user.start_date).days
                target_days = criteria.get("days", 7)
                return 100 if days <= target_days else 0
            
            return 0
        
        elif criteria_type == "all_training_completed":
            from app.database.models import TrainingModule
            total_modules = self.db.query(TrainingModule).filter(
                TrainingModule.is_active == True
            ).count()
            
            completed = self.db.query(TrainingProgress).filter(
                TrainingProgress.user_id == user_id,
                TrainingProgress.status == "completed"
            ).count()
            
            if total_modules == 0:
                return 0
            return 100 if completed >= total_modules else (completed / total_modules) * 100
        
        elif criteria_type == "quiz_perfect_score":
            perfect = self.db.query(TrainingProgress).filter(
                TrainingProgress.user_id == user_id,
                TrainingProgress.score == 100
            ).first()
            return 100 if perfect else 0
        
        elif criteria_type == "early_completion":
            early = self.db.query(Task).filter(
                Task.user_id == user_id,
                Task.status == TaskStatus.DONE,
                Task.completed_at < Task.due_date
            ).first()
            return 100 if early else 0
        
        elif criteria_type == "feedback_given":
            from app.database.models import Feedback
            count = self.db.query(Feedback).filter(
                Feedback.user_id == user_id
            ).count()
            target = criteria.get("count", 1)
            return min(100, (count / target) * 100)
        
        elif criteria_type == "login_streak":
            # Would need login history tracking
            # Simplified: return 0 for now
            return 0
        
        return 0
    
    def _unlock_achievement(self, user_id: int, achievement_id: int):
        """Unlock an achievement for a user."""
        user_achievement = self.db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id
        ).first()
        
        if user_achievement:
            user_achievement.progress = 100
            user_achievement.unlocked_at = datetime.utcnow()
        else:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                progress=100,
                unlocked_at=datetime.utcnow()
            )
            self.db.add(user_achievement)
        
        self.db.commit()
        logger.info(f"Achievement unlocked: user={user_id}, achievement={achievement_id}")
    
    def _update_progress(self, user_id: int, achievement_id: int, progress: float):
        """Update partial progress for an achievement."""
        user_achievement = self.db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id
        ).first()
        
        if user_achievement:
            if progress > user_achievement.progress:
                user_achievement.progress = progress
        else:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                progress=progress
            )
            self.db.add(user_achievement)
        
        self.db.commit()
    
    def get_user_achievements(self, user_id: int, include_locked: bool = False) -> List[Dict]:
        """Get achievements for a user."""
        if include_locked:
            achievements = self.db.query(Achievement).filter(
                Achievement.is_active == True
            ).all()
        else:
            achievements = self.db.query(Achievement).join(
                UserAchievement
            ).filter(
                UserAchievement.user_id == user_id,
                UserAchievement.progress >= 100
            ).all()
        
        result = []
        for ach in achievements:
            user_ach = self.db.query(UserAchievement).filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == ach.id
            ).first()
            
            result.append({
                "id": ach.id,
                "name": ach.name,
                "name_ar": ach.name_ar,
                "description": ach.description,
                "description_ar": ach.description_ar,
                "icon": ach.icon,
                "category": ach.category.value,
                "points": ach.points,
                "unlocked": user_ach.progress >= 100 if user_ach else False,
                "progress": user_ach.progress if user_ach else 0,
                "unlocked_at": user_ach.unlocked_at.isoformat() if user_ach and user_ach.unlocked_at else None
            })
        
        return result
    
    def get_user_points(self, user_id: int) -> int:
        """Get total points for a user."""
        result = self.db.query(
            func.sum(Achievement.points)
        ).join(
            UserAchievement
        ).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.progress >= 100
        ).scalar()
        
        return result or 0
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get achievement leaderboard."""
        results = self.db.query(
            User.id,
            User.name,
            func.sum(Achievement.points).label("total_points"),
            func.count(UserAchievement.id).label("achievement_count")
        ).join(
            UserAchievement, User.id == UserAchievement.user_id
        ).join(
            Achievement
        ).filter(
            UserAchievement.progress >= 100
        ).group_by(
            User.id
        ).order_by(
            func.sum(Achievement.points).desc()
        ).limit(limit).all()
        
        return [
            {
                "user_id": r.id,
                "name": r.name,
                "total_points": r.total_points or 0,
                "achievement_count": r.achievement_count
            }
            for r in results
        ]
    
    def get_unnotified_achievements(self, user_id: int) -> List[Dict]:
        """Get achievements that user hasn't been notified about."""
        user_achievements = self.db.query(UserAchievement).join(
            Achievement
        ).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.progress >= 100,
            UserAchievement.is_notified == False
        ).all()
        
        result = []
        for ua in user_achievements:
            result.append({
                "id": ua.achievement.id,
                "name": ua.achievement.name,
                "name_ar": ua.achievement.name_ar,
                "description": ua.achievement.description,
                "icon": ua.achievement.icon,
                "points": ua.achievement.points,
                "unlocked_at": ua.unlocked_at.isoformat()
            })
            ua.is_notified = True
        
        self.db.commit()
        return result

