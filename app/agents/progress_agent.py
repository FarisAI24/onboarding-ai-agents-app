"""Enhanced Progress Agent with task recommendations and timeline views."""
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.agents.base import BaseAgent, AgentState, AgentResponse, ConfidenceLevel

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskPriority(str, Enum):
    """Task priority levels."""
    CRITICAL = "critical"  # Overdue
    HIGH = "high"  # Due today or tomorrow
    MEDIUM = "medium"  # Due this week
    LOW = "low"  # Due next week or later


@dataclass
class TaskRecommendation:
    """A recommended task with reasoning."""
    task_id: int
    title: str
    reason: str
    priority: TaskPriority
    estimated_time: str = "15-30 minutes"


@dataclass
class TimelineView:
    """Timeline view of tasks."""
    overdue: List[Dict[str, Any]] = field(default_factory=list)
    today: List[Dict[str, Any]] = field(default_factory=list)
    this_week: List[Dict[str, Any]] = field(default_factory=list)
    next_week: List[Dict[str, Any]] = field(default_factory=list)
    later: List[Dict[str, Any]] = field(default_factory=list)


# Task dependencies - certain tasks should be done before others
TASK_DEPENDENCIES = {
    "Set up MFA on Okta": ["Set up laptop and accounts"],
    "Configure VPN access": ["Set up MFA on Okta"],
    "Install required software": ["Set up laptop and accounts"],
    "Complete Security Awareness training": ["Sign NDA and confidentiality agreement"],
    "Complete Data Protection training": ["Complete Security Awareness training"],
    "Set up Expensify account": ["Set up direct deposit"],
    "Review expense policy": ["Set up Expensify account"],
    "Enroll in benefits": ["Complete HR orientation session", "Submit W-4 and I-9 forms"],
}

# Estimated time for common tasks
TASK_ESTIMATED_TIMES = {
    "Complete HR orientation session": "1-2 hours",
    "Review and sign employee handbook": "30-45 minutes",
    "Submit W-4 and I-9 forms": "15-20 minutes",
    "Set up direct deposit": "10-15 minutes",
    "Enroll in benefits": "30-60 minutes",
    "Set up laptop and accounts": "30-45 minutes",
    "Configure email and calendar": "15-20 minutes",
    "Set up MFA on Okta": "10-15 minutes",
    "Install required software": "20-30 minutes",
    "Configure VPN access": "15-20 minutes",
    "Sign NDA and confidentiality agreement": "15-20 minutes",
    "Complete Security Awareness training": "45-60 minutes",
    "Complete Data Protection training": "30-45 minutes",
    "Complete Phishing Prevention training": "20-30 minutes",
    "Set up Expensify account": "10-15 minutes",
    "Review expense policy": "15-20 minutes",
    "Set up Concur travel profile": "15-20 minutes",
}


class ProgressAgent(BaseAgent):
    """Enhanced agent for task management with recommendations and timeline views."""
    
    name = "progress_agent"
    description = "Handles task queries, progress tracking, recommendations, and timeline views"
    department = "General"
    
    SYSTEM_PROMPT = """You are a Progress Tracking assistant helping new employees manage their onboarding tasks.
You can:
- Show the user their onboarding tasks and progress
- Provide personalized task recommendations
- Show timeline views (today, this week, next week)
- Help them understand task dependencies
- Mark tasks as complete when they report finishing something
- Highlight overdue tasks with urgency

IMPORTANT RULES:
1. Be encouraging about progress made.
2. Clearly highlight overdue tasks and their importance.
3. When recommending tasks, consider dependencies (some tasks must be done before others).
4. Provide estimated times for tasks when available.
5. Use Markdown formatting for clarity.

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

CURRENT ONBOARDING STATUS:
{tasks_summary}

TIMELINE VIEW:
{timeline_view}

RECOMMENDED NEXT TASKS:
{recommendations}

TASK COMPLETION INSTRUCTIONS:
If the user mentions completing a task, respond with a JSON block like this at the END of your response:
```json
{{"task_update": {{"task_id": <id>, "new_status": "DONE"}}}}
```
Only include this if you're confident about which task they completed.
"""

    USER_PROMPT = """User message: {question}

Please help the user with their onboarding progress. Use Markdown formatting."""
    
    def __init__(self):
        """Initialize the Progress agent."""
        super().__init__()
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=settings.openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("human", self.USER_PROMPT)
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def _parse_due_date(self, due_date: Any) -> Optional[date]:
        """Parse due date from various formats."""
        if due_date is None:
            return None
        if isinstance(due_date, date):
            return due_date
        if isinstance(due_date, datetime):
            return due_date.date()
        if isinstance(due_date, str):
            try:
                return datetime.strptime(due_date, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None
    
    def _get_task_priority(self, task: Dict[str, Any], today: date) -> TaskPriority:
        """Determine task priority based on due date and status."""
        due_date = self._parse_due_date(task.get("due_date"))
        status = task.get("status", "NOT_STARTED")
        
        if status == "DONE":
            return TaskPriority.LOW
        
        if due_date is None:
            return TaskPriority.MEDIUM
        
        days_until_due = (due_date - today).days
        
        if days_until_due < 0:
            return TaskPriority.CRITICAL
        elif days_until_due <= 1:
            return TaskPriority.HIGH
        elif days_until_due <= 7:
            return TaskPriority.MEDIUM
        else:
            return TaskPriority.LOW
    
    def build_timeline_view(self, tasks: List[Dict[str, Any]]) -> TimelineView:
        """Build a timeline view of tasks.
        
        Args:
            tasks: List of task dictionaries.
            
        Returns:
            TimelineView with tasks grouped by time period.
        """
        today = date.today()
        end_of_week = today + timedelta(days=(6 - today.weekday()))
        end_of_next_week = end_of_week + timedelta(days=7)
        
        timeline = TimelineView()
        
        for task in tasks:
            if task.get("status") == "DONE":
                continue
            
            due_date = self._parse_due_date(task.get("due_date"))
            if due_date is None:
                timeline.later.append(task)
                continue
            
            if due_date < today:
                timeline.overdue.append(task)
            elif due_date == today:
                timeline.today.append(task)
            elif due_date <= end_of_week:
                timeline.this_week.append(task)
            elif due_date <= end_of_next_week:
                timeline.next_week.append(task)
            else:
                timeline.later.append(task)
        
        return timeline
    
    def format_timeline_view(self, timeline: TimelineView) -> str:
        """Format timeline view as a string."""
        lines = []
        
        if timeline.overdue:
            lines.append("⚠️ **OVERDUE** (Needs immediate attention):")
            for t in timeline.overdue:
                lines.append(f"  • {t.get('title')} (Was due: {t.get('due_date')})")
        
        if timeline.today:
            lines.append("\n📅 **DUE TODAY**:")
            for t in timeline.today:
                lines.append(f"  • {t.get('title')}")
        
        if timeline.this_week:
            lines.append("\n📆 **THIS WEEK**:")
            for t in timeline.this_week:
                due = self._parse_due_date(t.get("due_date"))
                day_name = due.strftime("%A") if due else ""
                lines.append(f"  • {t.get('title')} ({day_name})")
        
        if timeline.next_week:
            lines.append("\n📅 **NEXT WEEK**:")
            for t in timeline.next_week:
                lines.append(f"  • {t.get('title')}")
        
        if not any([timeline.overdue, timeline.today, timeline.this_week, timeline.next_week]):
            lines.append("No urgent tasks! Great progress! 🎉")
        
        return "\n".join(lines)
    
    def get_task_recommendations(
        self, 
        tasks: List[Dict[str, Any]],
        max_recommendations: int = 3
    ) -> List[TaskRecommendation]:
        """Get recommended tasks to work on next.
        
        Args:
            tasks: List of all tasks.
            max_recommendations: Maximum recommendations to return.
            
        Returns:
            List of TaskRecommendation objects.
        """
        today = date.today()
        recommendations = []
        
        # Get completed task titles for dependency checking
        completed_titles = {
            t.get("title") for t in tasks if t.get("status") == "DONE"
        }
        
        # Get pending tasks
        pending_tasks = [
            t for t in tasks 
            if t.get("status") in ("NOT_STARTED", "IN_PROGRESS")
        ]
        
        for task in pending_tasks:
            title = task.get("title", "")
            priority = self._get_task_priority(task, today)
            
            # Check if dependencies are met
            dependencies = TASK_DEPENDENCIES.get(title, [])
            deps_met = all(dep in completed_titles for dep in dependencies)
            
            if not deps_met:
                continue  # Skip if dependencies not met
            
            # Determine reason for recommendation
            if priority == TaskPriority.CRITICAL:
                reason = "⚠️ This task is overdue!"
            elif priority == TaskPriority.HIGH:
                due = self._parse_due_date(task.get("due_date"))
                if due == today:
                    reason = "📅 Due today"
                else:
                    reason = "⏰ Due tomorrow"
            elif task.get("status") == "IN_PROGRESS":
                reason = "🔄 Already in progress - finish what you started"
            else:
                # Check if this task unlocks others
                unlocks = [
                    k for k, v in TASK_DEPENDENCIES.items() 
                    if title in v and k not in completed_titles
                ]
                if unlocks:
                    reason = f"🔓 Completing this unlocks: {', '.join(unlocks[:2])}"
                else:
                    reason = "📋 Quick win to build momentum"
            
            recommendations.append(TaskRecommendation(
                task_id=task.get("id"),
                title=title,
                reason=reason,
                priority=priority,
                estimated_time=TASK_ESTIMATED_TIMES.get(title, "15-30 minutes")
            ))
        
        # Sort by priority
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        recommendations.sort(key=lambda r: priority_order[r.priority])
        
        return recommendations[:max_recommendations]
    
    def format_recommendations(self, recommendations: List[TaskRecommendation]) -> str:
        """Format recommendations as a string."""
        if not recommendations:
            return "All tasks completed! 🎉"
        
        lines = []
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. **{rec.title}** (ID: {rec.task_id})")
            lines.append(f"   {rec.reason}")
            lines.append(f"   ⏱️ Estimated time: {rec.estimated_time}")
        
        return "\n".join(lines)
    
    def format_tasks_summary(self, tasks: List[Dict[str, Any]]) -> str:
        """Format tasks into a readable summary."""
        if not tasks:
            return "No tasks assigned yet."
        
        today = date.today()
        
        # Count by status
        not_started = sum(1 for t in tasks if t.get("status") == "NOT_STARTED")
        in_progress = sum(1 for t in tasks if t.get("status") == "IN_PROGRESS")
        completed = sum(1 for t in tasks if t.get("status") == "DONE")
        
        # Count overdue
        overdue = sum(
            1 for t in tasks
            if t.get("status") != "DONE"
            and self._parse_due_date(t.get("due_date"))
            and self._parse_due_date(t.get("due_date")) < today
        )
        
        total = len(tasks)
        progress_pct = (completed / total * 100) if total > 0 else 0
        
        lines = [
            f"**Overall Progress: {completed}/{total} tasks ({progress_pct:.0f}%)**",
            "",
            f"✅ Completed: {completed}",
            f"🔄 In Progress: {in_progress}",
            f"📋 Not Started: {not_started}",
        ]
        
        if overdue > 0:
            lines.append(f"⚠️ **Overdue: {overdue}**")
        
        return "\n".join(lines)
    
    def extract_task_update(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract task update from response if present."""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                data = json.loads(json_str)
                return data.get("task_update")
        except (json.JSONDecodeError, ValueError):
            pass
        return None
    
    def clean_response(self, response: str) -> str:
        """Remove JSON block from response for display."""
        if "```json" in response:
            json_start = response.find("```json")
            json_end = response.find("```", json_start + 7) + 3
            return response[:json_start].strip() + response[json_end:].strip()
        return response
    
    async def process(self, state: AgentState) -> AgentResponse:
        """Process task-related query with enhanced recommendations."""
        question = state.get("current_message", "")
        tasks = state.get("tasks", [])
        
        logger.info(f"Progress Agent processing: {question[:50]}...")
        
        # Build timeline view
        timeline = self.build_timeline_view(tasks)
        timeline_str = self.format_timeline_view(timeline)
        
        # Get recommendations
        recommendations = self.get_task_recommendations(tasks)
        recommendations_str = self.format_recommendations(recommendations)
        
        # Format tasks summary
        tasks_summary = self.format_tasks_summary(tasks)
        
        # Generate response
        response = self.chain.invoke({
            "tasks_summary": tasks_summary,
            "timeline_view": timeline_str,
            "recommendations": recommendations_str,
            "question": question,
            "user_name": state.get("user_name", ""),
            "user_role": state.get("user_role", "Employee"),
            "user_department": state.get("user_department", "General")
        })
        
        # Extract any task updates
        task_update = self.extract_task_update(response)
        task_updates = [task_update] if task_update else []
        
        # Clean response for display
        clean_content = self.clean_response(response)
        
        # Calculate confidence
        confidence_level, confidence_score = self.calculate_confidence(
            retrieval_confidence=0.8,  # Progress agent has direct access to data
            num_sources=len(tasks),
            answer_length=len(clean_content)
        )
        
        # Generate follow-up suggestions
        followups = []
        if timeline.overdue:
            followups.append("What overdue tasks do I have?")
        if recommendations:
            followups.append("What should I work on next?")
        followups.append("Show me my weekly timeline")
        
        return AgentResponse(
            content=clean_content,
            task_updates=task_updates,
            confidence=confidence_level,
            confidence_score=confidence_score,
            suggested_followups=followups[:3],
            metadata={
                "tasks_count": len(tasks),
                "overdue_count": len(timeline.overdue),
                "recommendations_count": len(recommendations),
                "has_update": bool(task_updates)
            }
        )
