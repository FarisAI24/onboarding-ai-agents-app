"""Calendar integration service.

This module handles the internal calendar system. For external calendar
integration (Google Calendar, Microsoft Outlook), see:
    app/services/external_calendar_integration.py (commented-out future implementation)
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database.models import CalendarEvent, Task, TrainingModule, User

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for calendar integration and event management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_event(
        self,
        user_id: int,
        title: str,
        start_time: datetime,
        description: Optional[str] = None,
        end_time: Optional[datetime] = None,
        all_day: bool = False,
        task_id: Optional[int] = None,
        training_module_id: Optional[int] = None,
        reminder_minutes: int = 30
    ) -> CalendarEvent:
        """Create a calendar event."""
        event = CalendarEvent(
            user_id=user_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time or (start_time + timedelta(hours=1)),
            all_day=all_day,
            task_id=task_id,
            training_module_id=training_module_id,
            reminder_minutes=reminder_minutes
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        logger.info(f"Calendar event created: {title} for user {user_id}")
        return event
    
    def get_events(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_past: bool = False
    ) -> List[CalendarEvent]:
        """Get calendar events for a user."""
        query = self.db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id
        )
        
        if not include_past:
            query = query.filter(CalendarEvent.start_time >= datetime.utcnow())
        
        if start_date:
            query = query.filter(CalendarEvent.start_time >= start_date)
        
        if end_date:
            query = query.filter(CalendarEvent.start_time <= end_date)
        
        return query.order_by(CalendarEvent.start_time).all()
    
    def get_event(self, event_id: int) -> Optional[CalendarEvent]:
        """Get a calendar event by ID."""
        return self.db.query(CalendarEvent).filter(
            CalendarEvent.id == event_id
        ).first()
    
    def update_event(self, event_id: int, **updates) -> Optional[CalendarEvent]:
        """Update a calendar event."""
        event = self.get_event(event_id)
        if not event:
            return None
        
        for key, value in updates.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def delete_event(self, event_id: int) -> bool:
        """Delete a calendar event."""
        event = self.get_event(event_id)
        if not event:
            return False
        
        self.db.delete(event)
        self.db.commit()
        return True
    
    def sync_tasks_to_calendar(self, user_id: int) -> List[CalendarEvent]:
        """Create calendar events for all user tasks."""
        tasks = self.db.query(Task).filter(
            Task.user_id == user_id
        ).all()
        
        created_events = []
        
        for task in tasks:
            # Check if event already exists for this task
            existing = self.db.query(CalendarEvent).filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.task_id == task.id
            ).first()
            
            if not existing:
                event = self.create_event(
                    user_id=user_id,
                    title=f"📋 {task.title}",
                    description=task.description,
                    start_time=datetime.combine(task.due_date, datetime.min.time()),
                    all_day=True,
                    task_id=task.id,
                    reminder_minutes=1440  # 1 day before
                )
                created_events.append(event)
        
        logger.info(f"Synced {len(created_events)} tasks to calendar for user {user_id}")
        return created_events
    
    def get_upcoming_reminders(self, minutes_ahead: int = 60) -> List[Dict]:
        """Get events with reminders due in the next X minutes."""
        now = datetime.utcnow()
        
        events = self.db.query(CalendarEvent).filter(
            CalendarEvent.is_reminder_sent == False,
            CalendarEvent.start_time > now
        ).all()
        
        reminders_due = []
        
        for event in events:
            reminder_time = event.start_time - timedelta(minutes=event.reminder_minutes)
            if now >= reminder_time and now < event.start_time:
                user = self.db.query(User).filter(User.id == event.user_id).first()
                reminders_due.append({
                    "event_id": event.id,
                    "user_id": event.user_id,
                    "user_email": user.email if user else None,
                    "user_name": user.name if user else None,
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.start_time.isoformat(),
                    "minutes_until": int((event.start_time - now).total_seconds() / 60)
                })
        
        return reminders_due
    
    def mark_reminder_sent(self, event_id: int):
        """Mark a reminder as sent."""
        event = self.get_event(event_id)
        if event:
            event.is_reminder_sent = True
            self.db.commit()
    
    def generate_ical(self, user_id: int) -> str:
        """Generate iCal format for user's events."""
        events = self.get_events(user_id, include_past=False)
        
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Onboarding Copilot//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH"
        ]
        
        for event in events:
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{event.id}@onboarding-copilot",
                f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                f"DTSTART:{event.start_time.strftime('%Y%m%dT%H%M%SZ')}",
                f"DTEND:{(event.end_time or event.start_time + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')}",
                f"SUMMARY:{event.title}",
            ])
            
            if event.description:
                lines.append(f"DESCRIPTION:{event.description.replace(chr(10), '\\n')}")
            
            if event.reminder_minutes > 0:
                lines.extend([
                    "BEGIN:VALARM",
                    "ACTION:DISPLAY",
                    f"TRIGGER:-PT{event.reminder_minutes}M",
                    f"DESCRIPTION:Reminder: {event.title}",
                    "END:VALARM"
                ])
            
            lines.append("END:VEVENT")
        
        lines.append("END:VCALENDAR")
        
        return "\r\n".join(lines)
    
    def generate_google_calendar_url(self, event: CalendarEvent) -> str:
        """Generate Google Calendar add event URL."""
        base_url = "https://calendar.google.com/calendar/render?action=TEMPLATE"
        
        params = [
            f"text={event.title}",
            f"dates={event.start_time.strftime('%Y%m%dT%H%M%SZ')}/{(event.end_time or event.start_time + timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')}"
        ]
        
        if event.description:
            params.append(f"details={event.description}")
        
        return f"{base_url}&{'&'.join(params)}"
    
    def generate_outlook_calendar_url(self, event: CalendarEvent) -> str:
        """Generate Outlook Calendar add event URL."""
        base_url = "https://outlook.office.com/calendar/0/deeplink/compose"
        
        params = [
            f"subject={event.title}",
            f"startdt={event.start_time.isoformat()}",
            f"enddt={(event.end_time or event.start_time + timedelta(hours=1)).isoformat()}"
        ]
        
        if event.description:
            params.append(f"body={event.description}")
        
        return f"{base_url}?{'&'.join(params)}"
    
    def get_calendar_feed_url(self, user_id: int, token: str) -> Dict[str, str]:
        """Get calendar feed URLs for external calendar apps."""
        base_url = "/api/v1/calendar"
        
        return {
            "ical": f"{base_url}/feed/{user_id}?token={token}&format=ics",
            "google_calendar": f"https://calendar.google.com/calendar/r?cid=webcal://your-domain{base_url}/feed/{user_id}?token={token}&format=ics",
            "outlook": f"https://outlook.office.com/owa/?path=/calendar/action/compose&rru=addsubscription&url=webcal://your-domain{base_url}/feed/{user_id}?token={token}&format=ics"
        }
    
    def get_week_view(self, user_id: int, week_start: Optional[datetime] = None) -> Dict[str, List[Dict]]:
        """Get events organized by day for a week view."""
        if not week_start:
            today = datetime.utcnow().date()
            week_start = datetime.combine(
                today - timedelta(days=today.weekday()),
                datetime.min.time()
            )
        
        week_end = week_start + timedelta(days=7)
        
        events = self.get_events(
            user_id,
            start_date=week_start,
            end_date=week_end,
            include_past=True
        )
        
        # Organize by day
        days = {}
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            days[day_str] = []
        
        for event in events:
            day_str = event.start_time.strftime("%Y-%m-%d")
            if day_str in days:
                days[day_str].append({
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat() if event.end_time else None,
                    "all_day": event.all_day,
                    "task_id": event.task_id,
                    "is_past": event.start_time < datetime.utcnow()
                })
        
        return days

