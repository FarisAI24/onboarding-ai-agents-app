"""Training module service for interactive onboarding."""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.models import (
    TrainingModule, TrainingProgress, Department, User
)

logger = logging.getLogger(__name__)


# Default training modules
DEFAULT_MODULES = [
    {
        "title": "Company Overview",
        "title_ar": "نظرة عامة على الشركة",
        "description": "Learn about our company history, mission, and values",
        "description_ar": "تعرف على تاريخ شركتنا ورسالتها وقيمها",
        "department": Department.GENERAL,
        "duration_minutes": 15,
        "passing_score": 70,
        "is_required": True,
        "order_index": 1,
        "content": {
            "sections": [
                {
                    "title": "Our History",
                    "type": "text",
                    "content": "Founded in 2010, our company has grown from a small startup to a global leader..."
                },
                {
                    "title": "Mission & Vision",
                    "type": "text",
                    "content": "Our mission is to empower businesses with innovative solutions..."
                },
                {
                    "title": "Core Values",
                    "type": "list",
                    "items": [
                        "Innovation - We embrace new ideas",
                        "Integrity - We do the right thing",
                        "Collaboration - We work together",
                        "Excellence - We strive for the best"
                    ]
                }
            ],
            "quiz": [
                {
                    "question": "When was the company founded?",
                    "options": ["2005", "2010", "2015", "2020"],
                    "correct": 1
                },
                {
                    "question": "Which is NOT one of our core values?",
                    "options": ["Innovation", "Competition", "Integrity", "Excellence"],
                    "correct": 1
                }
            ]
        }
    },
    {
        "title": "IT Security Basics",
        "title_ar": "أساسيات أمن تكنولوجيا المعلومات",
        "description": "Essential security practices for all employees",
        "description_ar": "الممارسات الأمنية الأساسية لجميع الموظفين",
        "department": Department.SECURITY,
        "duration_minutes": 20,
        "passing_score": 80,
        "is_required": True,
        "order_index": 2,
        "content": {
            "sections": [
                {
                    "title": "Password Security",
                    "type": "text",
                    "content": "Strong passwords are your first line of defense. Always use: at least 12 characters, mix of uppercase, lowercase, numbers, and symbols."
                },
                {
                    "title": "Phishing Awareness",
                    "type": "text",
                    "content": "Phishing emails try to trick you into revealing sensitive information. Always verify sender addresses and never click suspicious links."
                },
                {
                    "title": "Data Protection",
                    "type": "list",
                    "items": [
                        "Lock your computer when away",
                        "Never share passwords",
                        "Use VPN on public networks",
                        "Report suspicious activity immediately"
                    ]
                }
            ],
            "quiz": [
                {
                    "question": "What is the minimum recommended password length?",
                    "options": ["6 characters", "8 characters", "12 characters", "4 characters"],
                    "correct": 2
                },
                {
                    "question": "What should you do if you receive a suspicious email?",
                    "options": [
                        "Click the link to verify",
                        "Forward to all colleagues",
                        "Report to IT security",
                        "Reply asking for more info"
                    ],
                    "correct": 2
                },
                {
                    "question": "When should you use VPN?",
                    "options": [
                        "Only at home",
                        "On public/untrusted networks",
                        "Never",
                        "Only on mobile"
                    ],
                    "correct": 1
                }
            ]
        }
    },
    {
        "title": "HR Policies Overview",
        "title_ar": "نظرة عامة على سياسات الموارد البشرية",
        "description": "Understanding company policies and benefits",
        "description_ar": "فهم سياسات الشركة والمزايا",
        "department": Department.HR,
        "duration_minutes": 25,
        "passing_score": 70,
        "is_required": True,
        "order_index": 3,
        "content": {
            "sections": [
                {
                    "title": "Time Off Policies",
                    "type": "text",
                    "content": "You receive 15 days of PTO annually, plus 10 company holidays. PTO requests should be submitted at least 2 weeks in advance."
                },
                {
                    "title": "Benefits Overview",
                    "type": "list",
                    "items": [
                        "Health Insurance (PPO options available)",
                        "Dental and Vision coverage",
                        "401(k) with 4% company match",
                        "Life insurance",
                        "Employee Assistance Program"
                    ]
                },
                {
                    "title": "Code of Conduct",
                    "type": "text",
                    "content": "We maintain a respectful and inclusive workplace. Harassment and discrimination are not tolerated."
                }
            ],
            "quiz": [
                {
                    "question": "How many PTO days do you receive annually?",
                    "options": ["10 days", "15 days", "20 days", "Unlimited"],
                    "correct": 1
                },
                {
                    "question": "What is the company 401(k) match?",
                    "options": ["2%", "4%", "6%", "No match"],
                    "correct": 1
                }
            ]
        }
    },
    {
        "title": "IT Tools & Systems",
        "title_ar": "أدوات وأنظمة تكنولوجيا المعلومات",
        "description": "Getting started with company tools",
        "description_ar": "البدء باستخدام أدوات الشركة",
        "department": Department.IT,
        "duration_minutes": 20,
        "passing_score": 70,
        "is_required": True,
        "order_index": 4,
        "content": {
            "sections": [
                {
                    "title": "Email & Calendar",
                    "type": "text",
                    "content": "We use Microsoft 365 for email and calendar. Access at outlook.office.com with your company credentials."
                },
                {
                    "title": "Communication Tools",
                    "type": "list",
                    "items": [
                        "Slack - daily team communication",
                        "Zoom - video meetings",
                        "Teams - department meetings"
                    ]
                },
                {
                    "title": "VPN Access",
                    "type": "text",
                    "content": "Download the VPN client from the IT portal. Use your network credentials to connect."
                }
            ],
            "quiz": [
                {
                    "question": "Which tool is used for daily team communication?",
                    "options": ["Email", "Slack", "Zoom", "Teams"],
                    "correct": 1
                },
                {
                    "question": "Where do you download the VPN client?",
                    "options": ["App Store", "IT Portal", "Google Play", "Email attachment"],
                    "correct": 1
                }
            ]
        }
    }
]


class TrainingService:
    """Service for managing training modules."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def initialize_modules(self):
        """Initialize default training modules."""
        for module_data in DEFAULT_MODULES:
            existing = self.db.query(TrainingModule).filter(
                TrainingModule.title == module_data["title"]
            ).first()
            
            if not existing:
                module = TrainingModule(**module_data)
                self.db.add(module)
        
        self.db.commit()
        logger.info("Default training modules initialized")
    
    def get_module(self, module_id: int) -> Optional[TrainingModule]:
        """Get a training module by ID."""
        return self.db.query(TrainingModule).filter(
            TrainingModule.id == module_id
        ).first()
    
    def list_modules(
        self,
        department: Optional[Department] = None,
        required_only: bool = False,
        active_only: bool = True
    ) -> List[TrainingModule]:
        """List training modules."""
        query = self.db.query(TrainingModule)
        
        if active_only:
            query = query.filter(TrainingModule.is_active == True)
        if required_only:
            query = query.filter(TrainingModule.is_required == True)
        if department:
            query = query.filter(TrainingModule.department == department)
        
        return query.order_by(TrainingModule.order_index).all()
    
    def get_user_progress(
        self,
        user_id: int,
        module_id: Optional[int] = None
    ) -> List[Dict]:
        """Get training progress for a user."""
        query = self.db.query(TrainingProgress).filter(
            TrainingProgress.user_id == user_id
        )
        
        if module_id:
            query = query.filter(TrainingProgress.module_id == module_id)
        
        progress_list = query.all()
        
        result = []
        for progress in progress_list:
            module = self.get_module(progress.module_id)
            result.append({
                "module_id": progress.module_id,
                "module_title": module.title if module else "Unknown",
                "status": progress.status,
                "current_step": progress.current_step,
                "score": progress.score,
                "attempts": progress.attempts,
                "started_at": progress.started_at.isoformat() if progress.started_at else None,
                "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
                "time_spent_seconds": progress.time_spent_seconds
            })
        
        return result
    
    def start_module(self, user_id: int, module_id: int) -> TrainingProgress:
        """Start a training module for a user."""
        # Check if already started
        existing = self.db.query(TrainingProgress).filter(
            TrainingProgress.user_id == user_id,
            TrainingProgress.module_id == module_id
        ).first()
        
        if existing:
            if existing.status == "completed":
                # Allow retake
                existing.status = "in_progress"
                existing.current_step = 0
                existing.score = None
                existing.started_at = datetime.utcnow()
                existing.completed_at = None
                existing.attempts += 1
            elif existing.status == "not_started":
                existing.status = "in_progress"
                existing.started_at = datetime.utcnow()
            
            self.db.commit()
            return existing
        
        progress = TrainingProgress(
            user_id=user_id,
            module_id=module_id,
            status="in_progress",
            started_at=datetime.utcnow(),
            attempts=1
        )
        
        self.db.add(progress)
        self.db.commit()
        self.db.refresh(progress)
        
        logger.info(f"Training started: user={user_id}, module={module_id}")
        return progress
    
    def update_progress(
        self,
        user_id: int,
        module_id: int,
        current_step: int,
        time_spent_seconds: int = 0
    ) -> TrainingProgress:
        """Update training progress."""
        progress = self.db.query(TrainingProgress).filter(
            TrainingProgress.user_id == user_id,
            TrainingProgress.module_id == module_id
        ).first()
        
        if not progress:
            progress = self.start_module(user_id, module_id)
        
        progress.current_step = current_step
        progress.time_spent_seconds += time_spent_seconds
        
        self.db.commit()
        self.db.refresh(progress)
        
        return progress
    
    def submit_quiz(
        self,
        user_id: int,
        module_id: int,
        answers: List[int]
    ) -> Dict[str, Any]:
        """Submit quiz answers and calculate score."""
        module = self.get_module(module_id)
        if not module:
            raise ValueError(f"Module {module_id} not found")
        
        quiz = module.content.get("quiz", [])
        if not quiz:
            raise ValueError("Module has no quiz")
        
        # Calculate score
        correct = 0
        total = len(quiz)
        results = []
        
        for i, question in enumerate(quiz):
            user_answer = answers[i] if i < len(answers) else -1
            is_correct = user_answer == question.get("correct", -1)
            
            if is_correct:
                correct += 1
            
            results.append({
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": question["correct"],
                "is_correct": is_correct
            })
        
        score = int((correct / total) * 100) if total > 0 else 0
        passed = score >= module.passing_score
        
        # Update progress
        progress = self.db.query(TrainingProgress).filter(
            TrainingProgress.user_id == user_id,
            TrainingProgress.module_id == module_id
        ).first()
        
        if not progress:
            progress = self.start_module(user_id, module_id)
        
        progress.score = score
        progress.answers = answers
        progress.status = "completed" if passed else "failed"
        progress.completed_at = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Quiz submitted: user={user_id}, module={module_id}, score={score}, passed={passed}")
        
        return {
            "score": score,
            "passing_score": module.passing_score,
            "passed": passed,
            "correct": correct,
            "total": total,
            "results": results
        }
    
    def get_module_content(
        self,
        module_id: int,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Get module content for display."""
        module = self.get_module(module_id)
        if not module:
            return {}
        
        content = module.content
        if language == "ar" and module.content_ar:
            content = module.content_ar
        
        return {
            "id": module.id,
            "title": module.title_ar if language == "ar" and module.title_ar else module.title,
            "description": module.description_ar if language == "ar" and module.description_ar else module.description,
            "department": module.department.value,
            "duration_minutes": module.duration_minutes,
            "passing_score": module.passing_score,
            "is_required": module.is_required,
            "content": content
        }
    
    def get_user_training_summary(self, user_id: int) -> Dict[str, Any]:
        """Get training summary for a user."""
        total_modules = self.db.query(TrainingModule).filter(
            TrainingModule.is_active == True,
            TrainingModule.is_required == True
        ).count()
        
        completed = self.db.query(TrainingProgress).filter(
            TrainingProgress.user_id == user_id,
            TrainingProgress.status == "completed"
        ).count()
        
        in_progress = self.db.query(TrainingProgress).filter(
            TrainingProgress.user_id == user_id,
            TrainingProgress.status == "in_progress"
        ).count()
        
        avg_score = self.db.query(
            func.avg(TrainingProgress.score)
        ).filter(
            TrainingProgress.user_id == user_id,
            TrainingProgress.score.isnot(None)
        ).scalar() or 0
        
        total_time = self.db.query(
            func.sum(TrainingProgress.time_spent_seconds)
        ).filter(
            TrainingProgress.user_id == user_id
        ).scalar() or 0
        
        return {
            "total_required_modules": total_modules,
            "completed_modules": completed,
            "in_progress_modules": in_progress,
            "completion_percentage": round((completed / total_modules) * 100, 1) if total_modules > 0 else 0,
            "average_score": round(avg_score, 1),
            "total_time_spent_minutes": round(total_time / 60, 1)
        }
    
    def create_module(
        self,
        title: str,
        description: str,
        department: Department,
        content: Dict,
        **kwargs
    ) -> TrainingModule:
        """Create a new training module."""
        module = TrainingModule(
            title=title,
            description=description,
            department=department,
            content=content,
            **kwargs
        )
        
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        
        logger.info(f"Training module created: {title}")
        return module
    
    def update_module(self, module_id: int, **updates) -> Optional[TrainingModule]:
        """Update a training module."""
        module = self.get_module(module_id)
        if not module:
            return None
        
        for key, value in updates.items():
            if hasattr(module, key):
                setattr(module, key, value)
        
        self.db.commit()
        self.db.refresh(module)
        return module
    
    def delete_module(self, module_id: int) -> bool:
        """Deactivate a training module."""
        module = self.get_module(module_id)
        if not module:
            return False
        
        module.is_active = False
        self.db.commit()
        return True

