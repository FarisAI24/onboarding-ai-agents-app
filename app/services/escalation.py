"""Escalation service for confidence-based escalation to human support."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EscalationReason(str, Enum):
    """Reasons for escalation."""
    LOW_CONFIDENCE = "low_confidence"
    NO_DOCUMENTS_FOUND = "no_documents_found"
    SENSITIVE_TOPIC = "sensitive_topic"
    USER_REQUEST = "user_request"
    REPEATED_QUERY = "repeated_query"
    NEGATIVE_FEEDBACK = "negative_feedback"
    COMPLEX_QUERY = "complex_query"
    PII_DETECTED = "pii_detected"


class EscalationPriority(str, Enum):
    """Escalation priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class EscalationDecision:
    """Decision on whether to escalate."""
    should_escalate: bool
    reason: Optional[EscalationReason]
    priority: EscalationPriority
    confidence_score: float
    escalation_message: Optional[str]
    contact_info: Optional[Dict[str, str]]
    alternative_actions: List[str]


# Sensitive topic indicators that require human review
SENSITIVE_TOPICS = [
    r"\b(harass|discriminat|bully|hostile|threat|legal|lawsuit|terminat|fire|resign)\b",
    r"\b(mental health|depress|anxiet|stress|burnout|suicide)\b",
    r"\b(complaint|grievance|whistle|report\s+misconduct)\b",
    r"\b(confidential|proprietary|trade\s+secret|classified)\b",
]

# Contact information by department
DEPARTMENT_CONTACTS = {
    "HR": {
        "email": "hr@company.com",
        "phone": "ext. 2000",
        "name": "HR Support Team",
        "hours": "Monday-Friday, 9 AM - 5 PM"
    },
    "IT": {
        "email": "it-helpdesk@company.com",
        "phone": "ext. 3000",
        "name": "IT Help Desk",
        "hours": "24/7 for emergencies"
    },
    "Security": {
        "email": "security@company.com",
        "phone": "ext. 4000",
        "name": "Security Team",
        "hours": "24/7"
    },
    "Finance": {
        "email": "finance@company.com",
        "phone": "ext. 5000",
        "name": "Finance Department",
        "hours": "Monday-Friday, 9 AM - 5 PM"
    },
    "General": {
        "email": "support@company.com",
        "phone": "ext. 1000",
        "name": "General Support",
        "hours": "Monday-Friday, 8 AM - 6 PM"
    }
}


class EscalationService:
    """Service for handling escalation decisions."""
    
    def __init__(
        self,
        db: Optional[Session] = None,
        confidence_threshold: float = 0.5,
        no_docs_threshold: int = 0,
        repeated_query_threshold: int = 2
    ):
        self.db = db
        self.confidence_threshold = confidence_threshold
        self.no_docs_threshold = no_docs_threshold
        self.repeated_query_threshold = repeated_query_threshold
        self._user_query_history: Dict[int, List[str]] = {}
    
    def evaluate(
        self,
        query: str,
        user_id: int,
        routing_confidence: float,
        documents_found: int,
        department: str,
        answer_confidence: Optional[float] = None,
        pii_detected: bool = False,
        user_requested: bool = False
    ) -> EscalationDecision:
        """
        Evaluate whether a query should be escalated.
        
        Returns:
            EscalationDecision with escalation details
        """
        reasons = []
        priority = EscalationPriority.LOW
        
        # Check user request
        if user_requested:
            reasons.append(EscalationReason.USER_REQUEST)
            priority = EscalationPriority.MEDIUM
        
        # Check confidence
        effective_confidence = answer_confidence if answer_confidence is not None else routing_confidence
        if effective_confidence < self.confidence_threshold:
            reasons.append(EscalationReason.LOW_CONFIDENCE)
            if effective_confidence < 0.3:
                priority = max(priority, EscalationPriority.MEDIUM)
        
        # Check document retrieval
        if documents_found <= self.no_docs_threshold:
            reasons.append(EscalationReason.NO_DOCUMENTS_FOUND)
            priority = max(priority, EscalationPriority.MEDIUM)
        
        # Check for sensitive topics
        import re
        for pattern in SENSITIVE_TOPICS:
            if re.search(pattern, query, re.IGNORECASE):
                reasons.append(EscalationReason.SENSITIVE_TOPIC)
                priority = EscalationPriority.HIGH
                break
        
        # Check PII
        if pii_detected:
            reasons.append(EscalationReason.PII_DETECTED)
            priority = max(priority, EscalationPriority.MEDIUM)
        
        # Check for repeated queries
        if self._is_repeated_query(user_id, query):
            reasons.append(EscalationReason.REPEATED_QUERY)
            priority = max(priority, EscalationPriority.MEDIUM)
        
        # Track query
        self._track_query(user_id, query)
        
        # Decide on escalation
        should_escalate = len(reasons) > 0
        primary_reason = reasons[0] if reasons else None
        
        # Generate escalation message
        escalation_message = None
        alternative_actions = []
        
        if should_escalate:
            escalation_message = self._generate_escalation_message(
                primary_reason, department, effective_confidence
            )
            alternative_actions = self._get_alternative_actions(primary_reason, department)
        
        contact_info = DEPARTMENT_CONTACTS.get(department, DEPARTMENT_CONTACTS["General"])
        
        return EscalationDecision(
            should_escalate=should_escalate,
            reason=primary_reason,
            priority=priority,
            confidence_score=effective_confidence,
            escalation_message=escalation_message,
            contact_info=contact_info if should_escalate else None,
            alternative_actions=alternative_actions
        )
    
    def _is_repeated_query(self, user_id: int, query: str) -> bool:
        """Check if this is a repeated query from the user."""
        if user_id not in self._user_query_history:
            return False
        
        query_lower = query.lower().strip()
        similar_count = sum(
            1 for q in self._user_query_history[user_id]
            if self._similarity(q, query_lower) > 0.8
        )
        
        return similar_count >= self.repeated_query_threshold
    
    def _track_query(self, user_id: int, query: str):
        """Track a query for repeated query detection."""
        if user_id not in self._user_query_history:
            self._user_query_history[user_id] = []
        
        self._user_query_history[user_id].append(query.lower().strip())
        
        # Keep only last 10 queries per user
        if len(self._user_query_history[user_id]) > 10:
            self._user_query_history[user_id] = self._user_query_history[user_id][-10:]
    
    def _similarity(self, s1: str, s2: str) -> float:
        """Simple word-based similarity."""
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _generate_escalation_message(
        self,
        reason: EscalationReason,
        department: str,
        confidence: float
    ) -> str:
        """Generate an escalation message for the user."""
        contact = DEPARTMENT_CONTACTS.get(department, DEPARTMENT_CONTACTS["General"])
        
        messages = {
            EscalationReason.LOW_CONFIDENCE: (
                f"I'm not fully confident in my answer (confidence: {confidence:.0%}). "
                f"For accurate information, please contact {contact['name']} at {contact['email']} "
                f"or {contact['phone']}."
            ),
            EscalationReason.NO_DOCUMENTS_FOUND: (
                f"I couldn't find relevant documentation for your question. "
                f"Please reach out to {contact['name']} at {contact['email']} for assistance."
            ),
            EscalationReason.SENSITIVE_TOPIC: (
                f"This appears to be a sensitive matter that requires human attention. "
                f"Please contact {contact['name']} directly at {contact['email']} or {contact['phone']}. "
                f"They are available {contact['hours']}."
            ),
            EscalationReason.USER_REQUEST: (
                f"I'll connect you with a human representative. "
                f"Please contact {contact['name']} at {contact['email']} or {contact['phone']}."
            ),
            EscalationReason.REPEATED_QUERY: (
                f"I notice you've asked similar questions before. "
                f"For personalized help, please contact {contact['name']} at {contact['email']}."
            ),
            EscalationReason.PII_DETECTED: (
                f"Your message may contain sensitive personal information. "
                f"For security, please contact {contact['name']} directly at {contact['phone']}."
            ),
        }
        
        return messages.get(
            reason,
            f"For further assistance, please contact {contact['name']} at {contact['email']}."
        )
    
    def _get_alternative_actions(
        self,
        reason: EscalationReason,
        department: str
    ) -> List[str]:
        """Get alternative actions the user can take."""
        actions = []
        
        if reason == EscalationReason.LOW_CONFIDENCE:
            actions.extend([
                "Try rephrasing your question with more specific details",
                "Check the company intranet for related documentation",
                "Ask a colleague who might know the answer"
            ])
        elif reason == EscalationReason.NO_DOCUMENTS_FOUND:
            actions.extend([
                "This might be a new topic not yet in our knowledge base",
                "Try searching with different keywords",
                "Check if there's a relevant FAQ section"
            ])
        elif reason == EscalationReason.REPEATED_QUERY:
            actions.extend([
                "Review previous answers you received",
                "Provide additional context about what's not clear"
            ])
        
        return actions
    
    def request_human_escalation(
        self,
        user_id: int,
        query: str,
        department: str,
        reason: str = "user_request"
    ) -> Dict[str, Any]:
        """Explicitly request human escalation."""
        contact = DEPARTMENT_CONTACTS.get(department, DEPARTMENT_CONTACTS["General"])
        
        return {
            "status": "escalated",
            "ticket_reference": f"ESC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{user_id}",
            "contact": contact,
            "message": (
                f"Your request has been noted. Please contact {contact['name']} "
                f"at {contact['email']} or {contact['phone']} for immediate assistance. "
                f"Reference your ticket number for faster service."
            ),
            "estimated_response": "Within 24 hours for email, immediate for phone"
        }


# Singleton instance
_escalation_service: Optional[EscalationService] = None


def get_escalation_service(db: Optional[Session] = None) -> EscalationService:
    """Get or create the escalation service."""
    global _escalation_service
    if _escalation_service is None:
        _escalation_service = EscalationService(db=db)
    return _escalation_service

