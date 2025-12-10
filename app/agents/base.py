"""Base agent class and shared state definitions with conversation memory."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib


class ConfidenceLevel(str, Enum):
    """Confidence levels for agent responses."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AgentState(TypedDict, total=False):
    """Shared state for the agent graph."""
    # User context
    user_id: int
    user_name: str
    user_role: str  # Job role (e.g., "Junior Backend Engineer")
    user_department: str  # Work department
    user_type: str  # Access level (new_hire, admin)
    
    # Conversation
    messages: List[Dict[str, str]]  # Chat history
    current_message: str  # Current user message
    conversation_context: str  # Summarized context from recent messages
    
    # Routing
    predicted_department: str
    prediction_confidence: float
    final_department: str
    was_overridden: bool
    
    # Agent execution
    current_agent: str
    agent_responses: Dict[str, str]
    
    # RAG context
    retrieved_docs: List[Dict[str, Any]]
    retrieval_time_ms: float
    retrieval_confidence: float
    
    # Task context
    tasks: List[Dict[str, Any]]
    task_updates: List[Dict[str, Any]]
    pending_tasks: List[Dict[str, Any]]
    overdue_tasks: List[Dict[str, Any]]
    
    # Final response
    response: str
    sources: List[Dict[str, str]]
    response_confidence: ConfidenceLevel
    
    # Metadata
    start_time: datetime
    end_time: datetime
    total_time_ms: float
    error: Optional[str]


@dataclass
class AgentResponse:
    """Response from an agent."""
    content: str
    sources: List[Dict[str, str]] = field(default_factory=list)
    task_updates: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    confidence_score: float = 0.5
    needs_handoff: bool = False
    handoff_to: Optional[str] = None
    suggested_followups: List[str] = field(default_factory=list)


class ConversationMemory:
    """Manages conversation memory and context for agents."""
    
    MAX_HISTORY_LENGTH = 10
    SUMMARY_THRESHOLD = 5
    
    def __init__(self):
        """Initialize conversation memory."""
        self._conversations: Dict[int, List[Dict[str, str]]] = {}
        self._summaries: Dict[int, str] = {}
    
    def add_message(
        self, 
        user_id: int, 
        role: str, 
        content: str,
        metadata: Dict[str, Any] = None
    ):
        """Add a message to conversation history.
        
        Args:
            user_id: User ID.
            role: Message role (user/assistant).
            content: Message content.
            metadata: Optional metadata.
        """
        if user_id not in self._conversations:
            self._conversations[user_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self._conversations[user_id].append(message)
        
        # Trim history if too long
        if len(self._conversations[user_id]) > self.MAX_HISTORY_LENGTH:
            self._conversations[user_id] = self._conversations[user_id][-self.MAX_HISTORY_LENGTH:]
    
    def get_history(
        self, 
        user_id: int, 
        limit: int = None
    ) -> List[Dict[str, str]]:
        """Get conversation history for a user.
        
        Args:
            user_id: User ID.
            limit: Optional limit on number of messages.
            
        Returns:
            List of messages.
        """
        history = self._conversations.get(user_id, [])
        if limit:
            return history[-limit:]
        return history
    
    def get_context_string(
        self, 
        user_id: int, 
        max_messages: int = 5
    ) -> str:
        """Get formatted context string from recent conversation.
        
        Args:
            user_id: User ID.
            max_messages: Maximum messages to include.
            
        Returns:
            Formatted context string.
        """
        history = self.get_history(user_id, max_messages)
        
        if not history:
            return "No previous conversation."
        
        context_parts = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            # Truncate long messages
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def clear_history(self, user_id: int):
        """Clear conversation history for a user.
        
        Args:
            user_id: User ID.
        """
        if user_id in self._conversations:
            del self._conversations[user_id]
        if user_id in self._summaries:
            del self._summaries[user_id]
    
    def get_topic_context(self, user_id: int) -> Dict[str, Any]:
        """Extract topic context from recent conversation.
        
        Args:
            user_id: User ID.
            
        Returns:
            Dictionary with topic information.
        """
        history = self.get_history(user_id, 5)
        
        # Simple topic extraction from recent messages
        topics = set()
        departments = set()
        
        topic_keywords = {
            "benefits": ["benefits", "insurance", "health", "dental", "vision", "401k"],
            "pto": ["pto", "vacation", "time off", "leave", "sick"],
            "equipment": ["laptop", "computer", "equipment", "monitor", "device"],
            "security": ["security", "password", "mfa", "training", "nda"],
            "payroll": ["payroll", "salary", "pay", "direct deposit", "expense"]
        }
        
        for msg in history:
            content = msg["content"].lower()
            for topic, keywords in topic_keywords.items():
                if any(kw in content for kw in keywords):
                    topics.add(topic)
        
        return {
            "recent_topics": list(topics),
            "message_count": len(history)
        }


# Global conversation memory instance
_conversation_memory: Optional[ConversationMemory] = None


def get_conversation_memory() -> ConversationMemory:
    """Get the global conversation memory instance."""
    global _conversation_memory
    if _conversation_memory is None:
        _conversation_memory = ConversationMemory()
    return _conversation_memory


class BaseAgent(ABC):
    """Abstract base class for all agents with enhanced capabilities."""
    
    name: str = "base_agent"
    description: str = "Base agent"
    department: str = "General"
    
    SYSTEM_PROMPT = """You are a helpful AI assistant for employee onboarding.
You help new employees understand company policies and complete their onboarding tasks.

IMPORTANT RULES:
1. Only answer based on the provided context documents.
2. If you don't have information to answer, say "I don't have information about that. Please contact {department} for assistance."
3. Be concise but helpful.
4. Always cite your sources when providing policy information.
5. Never make up policies or information not in the documents.
6. Format your responses using Markdown for clarity (bullet points, bold, headers).

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

Recent Conversation Context:
{conversation_context}
"""
    
    def __init__(self):
        """Initialize the base agent."""
        self.memory = get_conversation_memory()
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentResponse:
        """Process the current state and return a response.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with content and metadata.
        """
        pass
    
    def format_system_prompt(self, state: AgentState) -> str:
        """Format the system prompt with user context and conversation memory.
        
        Args:
            state: Current agent state.
            
        Returns:
            Formatted system prompt.
        """
        user_id = state.get("user_id", 0)
        conversation_context = self.memory.get_context_string(user_id, max_messages=3)
        
        return self.SYSTEM_PROMPT.format(
            department=self.department,
            user_name=state.get("user_name", "User"),
            user_role=state.get("user_role", "Employee"),
            user_department=state.get("user_department", "General"),
            conversation_context=conversation_context
        )
    
    def format_context(self, docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents as context.
        
        Args:
            docs: List of retrieved documents.
            
        Returns:
            Formatted context string.
        """
        if not docs:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.get("filename", "Unknown")
            section = doc.get("section", "")
            content = doc.get("content", doc.get("text", ""))
            
            header = f"[Document {i}] {source}"
            if section:
                header += f" - {section}"
            
            context_parts.append(f"{header}\n{content}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def calculate_confidence(
        self, 
        retrieval_confidence: float,
        num_sources: int,
        answer_length: int
    ) -> tuple[ConfidenceLevel, float]:
        """Calculate confidence level for a response.
        
        Args:
            retrieval_confidence: Confidence from RAG retrieval.
            num_sources: Number of source documents used.
            answer_length: Length of the generated answer.
            
        Returns:
            Tuple of (ConfidenceLevel, confidence_score).
        """
        # Factors affecting confidence
        source_factor = min(1.0, num_sources / 3)  # More sources = higher confidence
        length_factor = min(1.0, answer_length / 500)  # Longer, detailed answers
        
        # Weighted combination
        score = (
            0.6 * retrieval_confidence +
            0.25 * source_factor +
            0.15 * length_factor
        )
        
        if score >= 0.7:
            level = ConfidenceLevel.HIGH
        elif score >= 0.4:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW
        
        return level, score
    
    def generate_followups(
        self, 
        state: AgentState,
        current_topic: str = None
    ) -> List[str]:
        """Generate suggested follow-up questions.
        
        Args:
            state: Current agent state.
            current_topic: Current topic being discussed.
            
        Returns:
            List of suggested follow-up questions.
        """
        # Department-specific follow-ups
        followups = {
            "HR": [
                "What are my PTO policies?",
                "How do I enroll in benefits?",
                "What is the performance review process?"
            ],
            "IT": [
                "How do I set up VPN?",
                "What software do I need to install?",
                "How do I reset my password?"
            ],
            "Security": [
                "What security training do I need?",
                "How do I report a security incident?",
                "What are the data handling policies?"
            ],
            "Finance": [
                "How do I submit expenses?",
                "When is payday?",
                "How do I get a corporate card?"
            ]
        }
        
        dept = state.get("final_department", self.department)
        return followups.get(dept, [])[:3]
    
    def update_memory(self, state: AgentState, response: AgentResponse):
        """Update conversation memory with the interaction.
        
        Args:
            state: Current agent state.
            response: Agent response.
        """
        user_id = state.get("user_id", 0)
        
        # Add user message
        self.memory.add_message(
            user_id=user_id,
            role="user",
            content=state.get("current_message", ""),
            metadata={"agent": self.name}
        )
        
        # Add assistant response
        self.memory.add_message(
            user_id=user_id,
            role="assistant",
            content=response.content,
            metadata={
                "agent": self.name,
                "confidence": response.confidence.value,
                "sources": len(response.sources)
            }
        )
