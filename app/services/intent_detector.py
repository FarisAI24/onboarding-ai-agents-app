"""Intent detection service for multi-intent queries and clarification."""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Types of user intents."""
    QUESTION = "question"
    TASK_UPDATE = "task_update"
    TASK_QUERY = "task_query"
    GREETING = "greeting"
    THANKS = "thanks"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    HELP = "help"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    NAVIGATION = "navigation"


@dataclass
class Intent:
    """Detected intent with confidence."""
    intent_type: IntentType
    confidence: float
    department: Optional[str] = None
    entities: Optional[Dict] = None
    requires_clarification: bool = False
    clarification_question: Optional[str] = None


@dataclass
class IntentResult:
    """Result of intent detection."""
    primary_intent: Intent
    secondary_intents: List[Intent]
    is_multi_intent: bool
    needs_clarification: bool
    clarification_prompt: Optional[str]
    raw_query: str


# Intent patterns
INTENT_PATTERNS = {
    IntentType.GREETING: [
        r"\b(hi|hello|hey|good\s+(morning|afternoon|evening)|greetings)\b",
    ],
    IntentType.THANKS: [
        r"\b(thank(s| you)?|appreciate|grateful)\b",
    ],
    IntentType.HELP: [
        r"\b(help|assist|support|guide|how\s+do\s+i)\b",
    ],
    IntentType.TASK_UPDATE: [
        r"\b(complete|done|finish|mark|update)\b.*\b(task|item|checklist)\b",
        r"\b(i('ve| have)?\s+(done|completed|finished))\b",
    ],
    IntentType.TASK_QUERY: [
        r"\b(what|which|show|list|remaining)\b.*\b(task|todo|item|checklist)\b",
        r"\b(my|pending|incomplete|overdue)\s+task",
    ],
    IntentType.COMPLAINT: [
        r"\b(problem|issue|broken|not working|error|bug|frustrated)\b",
    ],
    IntentType.FEEDBACK: [
        r"\b(suggest|feedback|improve|better|feature|request)\b",
    ],
    IntentType.CLARIFICATION: [
        r"\b(what\s+do\s+you\s+mean|clarify|explain|more\s+detail|elaborate)\b",
    ],
    IntentType.CONFIRMATION: [
        r"^(yes|no|okay|ok|sure|correct|right|exactly|confirmed?)[\.\!\?]?$",
    ],
    IntentType.NAVIGATION: [
        r"\b(where|find|locate|access|get\s+to|navigate)\b",
    ],
}

# Department indicators
DEPARTMENT_INDICATORS = {
    "HR": [
        r"\b(benefit|insurance|health|dental|vision|401k|pto|leave|vacation|sick|policy|handbook|hiring|termination|harassment|diversity|compensation|salary|bonus|review)\b",
    ],
    "IT": [
        r"\b(laptop|computer|email|password|vpn|network|wifi|software|hardware|install|access|account|login|credentials|printer|scanner|monitor|keyboard|mouse|developer|code|git|ide)\b",
    ],
    "Security": [
        r"\b(security|compliance|nda|confidential|data\s+protection|gdpr|training|badge|access\s+control|clearance|incident|breach|policy)\b",
    ],
    "Finance": [
        r"\b(expense|reimburse|travel|budget|invoice|payment|payroll|tax|w2|direct\s+deposit|bank|corporate\s+card)\b",
    ],
}

# Clarification triggers
AMBIGUOUS_PATTERNS = [
    (r"\b(it|this|that|these|those)\b", "Could you please specify what you're referring to?"),
    (r"\b(something|anything|everything)\b", "Could you be more specific about what you need?"),
    (r"^.{1,15}$", "Could you provide more details about your question?"),  # Very short queries
]


class IntentDetector:
    """Detect intents from user queries."""
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,
        multi_intent_threshold: float = 0.3
    ):
        self.confidence_threshold = confidence_threshold
        self.multi_intent_threshold = multi_intent_threshold
    
    def detect(self, query: str) -> IntentResult:
        """
        Detect intents from a query.
        
        Returns:
            IntentResult with primary and secondary intents
        """
        query_lower = query.lower().strip()
        detected_intents: List[Intent] = []
        
        # Detect intent types
        for intent_type, patterns in INTENT_PATTERNS.items():
            confidence = self._calculate_pattern_confidence(query_lower, patterns)
            if confidence >= self.multi_intent_threshold:
                intent = Intent(
                    intent_type=intent_type,
                    confidence=confidence
                )
                detected_intents.append(intent)
        
        # If no specific intent detected, default to QUESTION
        if not detected_intents:
            detected_intents.append(Intent(
                intent_type=IntentType.QUESTION,
                confidence=0.7
            ))
        
        # Detect departments for question intents
        departments = self._detect_departments(query_lower)
        for intent in detected_intents:
            if intent.intent_type in [IntentType.QUESTION, IntentType.HELP, IntentType.NAVIGATION]:
                if departments:
                    intent.department = departments[0][0]  # Primary department
                    intent.confidence = min(1.0, intent.confidence + departments[0][1] * 0.2)
        
        # Sort by confidence
        detected_intents.sort(key=lambda x: x.confidence, reverse=True)
        
        # Check for clarification needs
        clarification_prompt = None
        needs_clarification = False
        
        if len(departments) > 1 and abs(departments[0][1] - departments[1][1]) < 0.2:
            # Ambiguous department
            needs_clarification = True
            dept_names = [d[0] for d in departments[:2]]
            clarification_prompt = f"I noticed your question might relate to multiple areas ({', '.join(dept_names)}). Which department would you like me to focus on?"
        
        # Check for ambiguous patterns
        if not needs_clarification:
            for pattern, question in AMBIGUOUS_PATTERNS:
                if re.search(pattern, query_lower) and len(query_lower) < 50:
                    # Only trigger for short ambiguous queries
                    if detected_intents[0].intent_type == IntentType.QUESTION:
                        needs_clarification = True
                        clarification_prompt = question
                        break
        
        primary = detected_intents[0]
        secondary = [i for i in detected_intents[1:] if i.confidence >= self.multi_intent_threshold]
        
        return IntentResult(
            primary_intent=primary,
            secondary_intents=secondary,
            is_multi_intent=len(secondary) > 0,
            needs_clarification=needs_clarification,
            clarification_prompt=clarification_prompt,
            raw_query=query
        )
    
    def _calculate_pattern_confidence(self, query: str, patterns: List[str]) -> float:
        """Calculate confidence based on pattern matches."""
        matches = 0
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                matches += 1
        
        if matches == 0:
            return 0.0
        
        # Base confidence plus bonus for multiple matches
        return min(1.0, 0.5 + (matches * 0.2))
    
    def _detect_departments(self, query: str) -> List[Tuple[str, float]]:
        """Detect relevant departments with confidence scores."""
        departments = []
        
        for dept, patterns in DEPARTMENT_INDICATORS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    matches += 1
            
            if matches > 0:
                confidence = min(1.0, 0.4 + (matches * 0.2))
                departments.append((dept, confidence))
        
        departments.sort(key=lambda x: x[1], reverse=True)
        return departments
    
    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities from the query."""
        entities = {
            "tasks": [],
            "dates": [],
            "departments": [],
            "actions": []
        }
        
        # Extract task-related keywords
        task_pattern = r"\b(task|item|checklist|todo)\b"
        entities["tasks"] = re.findall(task_pattern, query, re.IGNORECASE)
        
        # Extract date references
        date_pattern = r"\b(today|tomorrow|yesterday|this week|next week|monday|tuesday|wednesday|thursday|friday)\b"
        entities["dates"] = re.findall(date_pattern, query, re.IGNORECASE)
        
        # Extract departments
        for dept, _ in self._detect_departments(query):
            entities["departments"].append(dept)
        
        # Extract action words
        action_pattern = r"\b(submit|request|update|complete|start|check|review|approve|reject)\b"
        entities["actions"] = re.findall(action_pattern, query, re.IGNORECASE)
        
        return entities
    
    def is_follow_up(self, query: str, previous_context: Optional[str] = None) -> bool:
        """Determine if query is a follow-up to previous conversation."""
        follow_up_indicators = [
            r"^(and|also|what about|how about|another thing)",
            r"^(yes|no|okay|sure|right)\s",
            r"\b(you mentioned|earlier|before|regarding that|about that)\b",
            r"^(so|then|but)\s",
        ]
        
        query_lower = query.lower().strip()
        for pattern in follow_up_indicators:
            if re.search(pattern, query_lower):
                return True
        
        # Short queries after context are often follow-ups
        if previous_context and len(query_lower) < 30:
            return True
        
        return False


# Singleton instance
_intent_detector: Optional[IntentDetector] = None


def get_intent_detector() -> IntentDetector:
    """Get or create the intent detector singleton."""
    global _intent_detector
    if _intent_detector is None:
        _intent_detector = IntentDetector()
    return _intent_detector

