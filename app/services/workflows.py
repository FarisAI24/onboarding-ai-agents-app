"""Automated workflow service for trigger-based actions."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database.models import (
    Workflow, WorkflowExecution, WorkflowTrigger,
    User, Task, TaskStatus
)

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for managing automated workflows."""
    
    def __init__(self, db: Session):
        self.db = db
        self._action_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default action handlers."""
        self._action_handlers = {
            "send_notification": self._action_send_notification,
            "send_email": self._action_send_email,
            "create_task": self._action_create_task,
            "assign_badge": self._action_assign_badge,
            "update_progress": self._action_update_progress,
            "escalate_to_manager": self._action_escalate_to_manager,
            "add_calendar_reminder": self._action_add_calendar_reminder,
            "log_event": self._action_log_event,
        }
    
    def register_action_handler(self, action_type: str, handler: Callable):
        """Register a custom action handler."""
        self._action_handlers[action_type] = handler
    
    def create_workflow(
        self,
        name: str,
        trigger: WorkflowTrigger,
        actions: List[Dict],
        conditions: Optional[Dict] = None,
        description: Optional[str] = None,
        priority: int = 0
    ) -> Workflow:
        """Create a new workflow."""
        workflow = Workflow(
            name=name,
            description=description,
            trigger=trigger,
            conditions=conditions,
            actions=actions,
            priority=priority,
            is_active=True
        )
        
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        
        logger.info(f"Created workflow: {name} (trigger: {trigger.value})")
        return workflow
    
    def trigger_workflows(
        self,
        trigger_type: WorkflowTrigger,
        user_id: int,
        trigger_data: Optional[Dict] = None
    ) -> List[WorkflowExecution]:
        """Trigger all workflows matching the trigger type."""
        workflows = self.db.query(Workflow).filter(
            Workflow.trigger == trigger_type,
            Workflow.is_active == True
        ).order_by(Workflow.priority.desc()).all()
        
        executions = []
        for workflow in workflows:
            if self._check_conditions(workflow.conditions, user_id, trigger_data):
                execution = self._execute_workflow(workflow, user_id, trigger_data)
                executions.append(execution)
        
        return executions
    
    def _check_conditions(
        self,
        conditions: Optional[Dict],
        user_id: int,
        trigger_data: Optional[Dict]
    ) -> bool:
        """Check if workflow conditions are met."""
        if not conditions:
            return True
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Check department condition
        if "department" in conditions:
            if user.department not in conditions["department"]:
                return False
        
        # Check role condition
        if "role" in conditions:
            if user.user_type.value not in conditions["role"]:
                return False
        
        # Check days since start
        if "min_days_since_start" in conditions:
            days = (datetime.utcnow().date() - user.start_date).days
            if days < conditions["min_days_since_start"]:
                return False
        
        if "max_days_since_start" in conditions:
            days = (datetime.utcnow().date() - user.start_date).days
            if days > conditions["max_days_since_start"]:
                return False
        
        # Check task-related conditions
        if trigger_data and "task_department" in conditions:
            if trigger_data.get("department") not in conditions["task_department"]:
                return False
        
        return True
    
    def _execute_workflow(
        self,
        workflow: Workflow,
        user_id: int,
        trigger_data: Optional[Dict]
    ) -> WorkflowExecution:
        """Execute a workflow."""
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            user_id=user_id,
            trigger_data=trigger_data,
            status="running"
        )
        
        self.db.add(execution)
        self.db.commit()
        
        results = []
        errors = []
        
        try:
            for action in workflow.actions:
                action_type = action.get("type")
                action_params = action.get("params", {})
                
                handler = self._action_handlers.get(action_type)
                if handler:
                    try:
                        result = handler(user_id, action_params, trigger_data)
                        results.append({
                            "action": action_type,
                            "status": "success",
                            "result": result
                        })
                    except Exception as e:
                        errors.append({
                            "action": action_type,
                            "error": str(e)
                        })
                else:
                    errors.append({
                        "action": action_type,
                        "error": f"Unknown action handler: {action_type}"
                    })
            
            execution.status = "completed" if not errors else "completed_with_errors"
            execution.result = {"actions": results, "errors": errors}
            execution.completed_at = datetime.utcnow()
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            logger.error(f"Workflow execution failed: {e}")
        
        self.db.commit()
        logger.info(f"Workflow executed: {workflow.name}, status: {execution.status}")
        
        return execution
    
    # Action handlers
    def _action_send_notification(
        self,
        user_id: int,
        params: Dict,
        trigger_data: Optional[Dict]
    ) -> Dict:
        """Send an in-app notification."""
        title = params.get("title", "Notification")
        message = params.get("message", "")
        
        # Format message with trigger data
        if trigger_data:
            message = message.format(**trigger_data)
        
        # In production, this would integrate with a notification system
        logger.info(f"Notification sent to user {user_id}: {title}")
        
        return {"notification_sent": True, "title": title}
    
    def _action_send_email(
        self,
        user_id: int,
        params: Dict,
        trigger_data: Optional[Dict]
    ) -> Dict:
        """Send an email notification."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        subject = params.get("subject", "Onboarding Update")
        template = params.get("template", "generic")
        
        # In production, this would integrate with an email service
        logger.info(f"Email sent to {user.email}: {subject}")
        
        return {"email_sent": True, "recipient": user.email}
    
    def _action_create_task(
        self,
        user_id: int,
        params: Dict,
        trigger_data: Optional[Dict]
    ) -> Dict:
        """Create a new task for the user."""
        from app.database.models import Task, Department
        
        task = Task(
            user_id=user_id,
            title=params.get("title", "New Task"),
            description=params.get("description", ""),
            department=Department(params.get("department", "General")),
            due_date=datetime.utcnow().date() + timedelta(days=params.get("due_in_days", 7)),
            status=TaskStatus.NOT_STARTED
        )
        
        self.db.add(task)
        self.db.commit()
        
        logger.info(f"Task created for user {user_id}: {task.title}")
        return {"task_id": task.id, "title": task.title}
    
    def _action_assign_badge(
        self,
        user_id: int,
        params: Dict,
        trigger_data: Optional[Dict]
    ) -> Dict:
        """Assign an achievement badge."""
        from app.services.achievements import AchievementService
        
        service = AchievementService(self.db)
        unlocked = service.check_and_unlock(user_id)
        
        return {"achievements_checked": True, "unlocked_count": len(unlocked)}
    
    def _action_update_progress(
        self,
        user_id: int,
        params: Dict,
        trigger_data: Optional[Dict]
    ) -> Dict:
        """Update user's onboarding progress."""
        # Calculate current progress
        total_tasks = self.db.query(Task).filter(Task.user_id == user_id).count()
        completed = self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.status == TaskStatus.DONE
        ).count()
        
        progress = (completed / total_tasks * 100) if total_tasks > 0 else 0
        
        return {"progress": round(progress, 1), "completed": completed, "total": total_tasks}
    
    def _action_escalate_to_manager(
        self,
        user_id: int,
        params: Dict,
        trigger_data: Optional[Dict]
    ) -> Dict:
        """Escalate to the user's manager."""
        reason = params.get("reason", "Onboarding issue requires attention")
        
        # In production, this would notify the manager
        logger.info(f"Escalation for user {user_id}: {reason}")
        
        return {"escalated": True, "reason": reason}
    
    def _action_add_calendar_reminder(
        self,
        user_id: int,
        params: Dict,
        trigger_data: Optional[Dict]
    ) -> Dict:
        """Add a calendar reminder."""
        from app.database.models import CalendarEvent
        
        event = CalendarEvent(
            user_id=user_id,
            title=params.get("title", "Reminder"),
            description=params.get("description", ""),
            start_time=datetime.utcnow() + timedelta(days=params.get("days_ahead", 1)),
            reminder_minutes=params.get("reminder_minutes", 30)
        )
        
        self.db.add(event)
        self.db.commit()
        
        return {"event_id": event.id}
    
    def _action_log_event(
        self,
        user_id: int,
        params: Dict,
        trigger_data: Optional[Dict]
    ) -> Dict:
        """Log an event for analytics."""
        event_type = params.get("event_type", "workflow_action")
        
        logger.info(f"Event logged: {event_type} for user {user_id}")
        return {"logged": True, "event_type": event_type}
    
    def get_workflow(self, workflow_id: int) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
    
    def list_workflows(self, active_only: bool = True) -> List[Workflow]:
        """List all workflows."""
        query = self.db.query(Workflow)
        if active_only:
            query = query.filter(Workflow.is_active == True)
        return query.order_by(Workflow.priority.desc()).all()
    
    def update_workflow(self, workflow_id: int, **updates) -> Optional[Workflow]:
        """Update a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        self.db.commit()
        self.db.refresh(workflow)
        return workflow
    
    def delete_workflow(self, workflow_id: int) -> bool:
        """Delete (deactivate) a workflow."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False
        
        workflow.is_active = False
        self.db.commit()
        return True
    
    def get_execution_history(
        self,
        workflow_id: Optional[int] = None,
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> List[WorkflowExecution]:
        """Get workflow execution history."""
        query = self.db.query(WorkflowExecution)
        
        if workflow_id:
            query = query.filter(WorkflowExecution.workflow_id == workflow_id)
        if user_id:
            query = query.filter(WorkflowExecution.user_id == user_id)
        
        return query.order_by(WorkflowExecution.started_at.desc()).limit(limit).all()


# Default workflows to create
DEFAULT_WORKFLOWS = [
    {
        "name": "Welcome New Hire",
        "description": "Send welcome notification when user registers",
        "trigger": WorkflowTrigger.USER_REGISTERED,
        "actions": [
            {
                "type": "send_notification",
                "params": {
                    "title": "Welcome! 🎉",
                    "message": "Welcome to the team! Start your onboarding journey today."
                }
            },
            {
                "type": "assign_badge",
                "params": {}
            }
        ],
        "priority": 10
    },
    {
        "name": "Task Completion Celebration",
        "description": "Celebrate when all tasks are completed",
        "trigger": WorkflowTrigger.ALL_TASKS_COMPLETED,
        "actions": [
            {
                "type": "send_notification",
                "params": {
                    "title": "Congratulations! 🏆",
                    "message": "You've completed all your onboarding tasks!"
                }
            },
            {
                "type": "assign_badge",
                "params": {}
            },
            {
                "type": "send_email",
                "params": {
                    "subject": "Onboarding Complete!",
                    "template": "onboarding_complete"
                }
            }
        ],
        "priority": 10
    },
    {
        "name": "Deadline Reminder",
        "description": "Remind about approaching deadlines",
        "trigger": WorkflowTrigger.DEADLINE_APPROACHING,
        "conditions": {
            "min_days_before_due": 2
        },
        "actions": [
            {
                "type": "send_notification",
                "params": {
                    "title": "Deadline Approaching ⏰",
                    "message": "You have tasks due soon. Check your task list!"
                }
            },
            {
                "type": "add_calendar_reminder",
                "params": {
                    "title": "Task Deadline",
                    "days_ahead": 0,
                    "reminder_minutes": 60
                }
            }
        ],
        "priority": 5
    },
    {
        "name": "Overdue Task Alert",
        "description": "Alert when tasks become overdue",
        "trigger": WorkflowTrigger.TASK_OVERDUE,
        "actions": [
            {
                "type": "send_notification",
                "params": {
                    "title": "Overdue Task ⚠️",
                    "message": "You have overdue tasks that need attention."
                }
            },
            {
                "type": "escalate_to_manager",
                "params": {
                    "reason": "User has overdue onboarding tasks"
                }
            }
        ],
        "conditions": {
            "min_days_since_start": 7
        },
        "priority": 8
    }
]


def initialize_default_workflows(db: Session):
    """Initialize default workflows if they don't exist."""
    service = WorkflowService(db)
    
    for workflow_data in DEFAULT_WORKFLOWS:
        existing = db.query(Workflow).filter(
            Workflow.name == workflow_data["name"]
        ).first()
        
        if not existing:
            service.create_workflow(**workflow_data)
    
    logger.info("Default workflows initialized")

