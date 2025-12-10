"""Coordinator Agent for routing queries to specialist agents."""
import logging
import re
from typing import Dict, Any, Optional, List

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.agents.base import BaseAgent, AgentState, AgentResponse
from ml.router import QuestionRouter, RoutingPrediction

logger = logging.getLogger(__name__)
settings = get_settings()


class CoordinatorAgent(BaseAgent):
    """Coordinator agent that routes queries to specialist agents."""
    
    name = "coordinator_agent"
    description = "Routes user queries to the appropriate specialist agent"
    department = "General"
    
    # Keywords for rule-based override
    DEPARTMENT_KEYWORDS = {
        "HR": [
            "benefits", "insurance", "401k", "pto", "vacation", "sick leave",
            "parental leave", "maternity", "paternity", "probation", "performance review",
            "working hours", "remote work", "dress code", "handbook", "hr policy"
        ],
        "IT": [
            "laptop", "computer", "email", "slack", "vpn", "password", "mfa",
            "two-factor", "software", "install", "github", "jira", "account",
            "wifi", "help desk", "it support", "okta", "equipment", "monitor",
            "device", "keyboard", "mouse", "headset", "printer"
        ],
        "Security": [
            "security training", "nda", "confidential", "data classification",
            "phishing", "incident", "badge", "access control", "compliance",
            "soc 2", "gdpr", "clean desk", "privileged access"
        ],
        "Finance": [
            "payroll", "pay schedule", "expense", "reimbursement", "corporate card",
            "travel", "booking", "per diem", "w-4", "w-2", "direct deposit",
            "expensify", "concur", "purchase order"
        ],
        "Progress": [
            "task", "tasks", "progress", "completed", "finished", "done",
            "checklist", "onboarding progress", "what's next", "overdue",
            "mark as done", "update status"
        ]
    }
    
    # Confidence threshold for ML prediction
    CONFIDENCE_THRESHOLD = 0.6
    
    def __init__(self, router: QuestionRouter = None):
        """Initialize the Coordinator agent.
        
        Args:
            router: Question router model.
        """
        self.router = router
        self._router_loaded = False
        
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0,
            api_key=settings.openai_api_key
        )
    
    def _load_router(self):
        """Lazy load the router model."""
        if not self._router_loaded:
            try:
                from ml.router import get_router
                self.router = get_router()
                self._router_loaded = True
            except FileNotFoundError:
                logger.warning("Router model not found. Using rule-based routing only.")
                self._router_loaded = True
    
    def check_keywords(self, text: str, ml_prediction: str = None) -> Optional[str]:
        """Check for department keywords in text using word boundaries.
        
        Args:
            text: User message text.
            ml_prediction: The ML model's predicted department (to prefer if it has matches).
            
        Returns:
            Department name if keywords match, else None.
        """
        text_lower = text.lower()
        
        # Check each department's keywords with word boundary matching
        matches = {}
        for dept, keywords in self.DEPARTMENT_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundary regex to avoid partial matches (e.g., "pto" in "laptop")
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, text_lower):
                    if dept not in matches:
                        matches[dept] = []
                    matches[dept].append(keyword)
        
        if not matches:
            return None
            
        logger.debug(f"Keyword matches: {matches}")
        
        # If ML prediction has keyword matches, prefer it (confirms the prediction)
        if ml_prediction and ml_prediction in matches:
            logger.info(f"ML prediction '{ml_prediction}' confirmed by keywords: {matches[ml_prediction]}")
            return ml_prediction
        
        # Otherwise, return the department with the most keyword matches
        best_dept = max(matches.keys(), key=lambda d: len(matches[d]))
        logger.debug(f"Selected '{best_dept}' based on keyword count")
        return best_dept
    
    def get_routing_decision(
        self, 
        text: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get routing decision using ML model and rules.
        
        Args:
            text: User message.
            context: Additional context (user role, history, etc.)
            
        Returns:
            Dictionary with routing decision and metadata.
        """
        self._load_router()
        
        result = {
            "predicted_department": "General",
            "prediction_confidence": 0.0,
            "final_department": "General",
            "was_overridden": False,
            "override_reason": None
        }
        
        # Step 1: Get ML prediction if router is available
        if self.router:
            try:
                prediction = self.router.predict(text)
                result["predicted_department"] = prediction.department
                result["prediction_confidence"] = prediction.confidence
                result["all_probabilities"] = prediction.all_probabilities
                result["final_department"] = prediction.department
            except Exception as e:
                logger.error(f"Router prediction failed: {e}")
        
        # Step 2: Check rule-based keywords (pass ML prediction to prefer it if it has matches)
        keyword_dept = self.check_keywords(text, ml_prediction=result["predicted_department"])
        
        # Step 3: Apply override rules
        
        # Rule 1: If keyword matches ML prediction, boost confidence in that choice
        if keyword_dept and keyword_dept == result["predicted_department"]:
            # Keywords confirm ML prediction, keep it
            logger.info(f"Keywords confirm ML prediction: {keyword_dept}")
        # Rule 2: If keyword differs from ML and ML confidence is low, prefer keyword
        elif keyword_dept and result["prediction_confidence"] < self.CONFIDENCE_THRESHOLD:
            result["final_department"] = keyword_dept
            result["was_overridden"] = True
            result["override_reason"] = f"Low ML confidence ({result['prediction_confidence']:.2f}), keyword match for {keyword_dept}"
        
        # Rule 2: Strong keyword match overrides weak ML prediction
        if keyword_dept == "Progress" and any(
            kw in text.lower() for kw in ["my task", "my progress", "completed", "finished", "mark"]
        ):
            result["final_department"] = "Progress"
            if result["final_department"] != result["predicted_department"]:
                result["was_overridden"] = True
                result["override_reason"] = "Strong progress/task keywords detected"
        
        # Rule 3: Greetings and general questions go to General/Progress
        greeting_patterns = [
            r"^(hi|hello|hey|good morning|good afternoon)\b",
            r"^(thanks|thank you)",
            r"^(what should i do|where do i start|help me)"
        ]
        for pattern in greeting_patterns:
            if re.match(pattern, text.lower().strip()):
                result["final_department"] = "Progress"
                if result["final_department"] != result["predicted_department"]:
                    result["was_overridden"] = True
                    result["override_reason"] = "Greeting or general query detected"
                break
        
        return result
    
    async def process(self, state: AgentState) -> AgentResponse:
        """Route query to appropriate agent.
        
        This method determines which specialist agent should handle the query.
        It doesn't generate a response itself, but updates the state with routing info.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with routing decision.
        """
        message = state.get("current_message", "")
        
        logger.info(f"Coordinator processing: {message[:50]}...")
        
        # Get routing decision
        routing = self.get_routing_decision(message, {
            "user_role": state.get("user_role"),
            "user_department": state.get("user_department")
        })
        
        logger.info(
            f"Routing decision: ML={routing['predicted_department']} "
            f"({routing['prediction_confidence']:.2f}), "
            f"Final={routing['final_department']}"
        )
        
        if routing["was_overridden"]:
            logger.info(f"Override reason: {routing['override_reason']}")
        
        return AgentResponse(
            content="",  # Coordinator doesn't generate response
            metadata=routing,
            needs_handoff=True,
            handoff_to=routing["final_department"]
        )

