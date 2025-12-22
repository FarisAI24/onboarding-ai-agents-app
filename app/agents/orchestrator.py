"""Main orchestrator using LangGraph for multi-agent coordination."""
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END

from app.agents.base import AgentState, AgentResponse
from app.agents.coordinator import CoordinatorAgent
from app.agents.hr_agent import HRAgent
from app.agents.it_agent import ITAgent
from app.agents.security_agent import SecurityAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.progress_agent import ProgressAgent
from app.services.intent_detector import get_intent_detector
from app.database import get_db
from app.services.semantic_cache import SemanticCacheService
from app.services.i18n import get_translation_service

logger = logging.getLogger(__name__)


class OnboardingOrchestrator:
    """Main orchestrator for the onboarding copilot using LangGraph."""
    
    def __init__(self):
        """Initialize the orchestrator and all agents."""
        # Initialize agents
        self.coordinator = CoordinatorAgent()
        self.hr_agent = HRAgent()
        self.it_agent = ITAgent()
        self.security_agent = SecurityAgent()
        self.finance_agent = FinanceAgent()
        self.progress_agent = ProgressAgent()
        
        # Map department to agent
        self.agent_map = {
            "HR": self.hr_agent,
            "IT": self.it_agent,
            "Security": self.security_agent,
            "Finance": self.finance_agent,
            "Progress": self.progress_agent,
            "General": self.progress_agent  # Default to progress for general queries
        }
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph.
        
        Returns:
            Compiled StateGraph.
        """
        # Create the graph with AgentState
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("coordinator", self._coordinator_node)
        workflow.add_node("hr", self._hr_node)
        workflow.add_node("it", self._it_node)
        workflow.add_node("security", self._security_node)
        workflow.add_node("finance", self._finance_node)
        workflow.add_node("progress", self._progress_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Set entry point
        workflow.set_entry_point("coordinator")
        
        # Add conditional routing from coordinator
        workflow.add_conditional_edges(
            "coordinator",
            self._route_to_agent,
            {
                "HR": "hr",
                "IT": "it",
                "Security": "security",
                "Finance": "finance",
                "Progress": "progress",
                "General": "progress"
            }
        )
        
        # All agents go to finalize
        workflow.add_edge("hr", "finalize")
        workflow.add_edge("it", "finalize")
        workflow.add_edge("security", "finalize")
        workflow.add_edge("finance", "finalize")
        workflow.add_edge("progress", "finalize")
        
        # Finalize goes to END
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _route_to_agent(self, state: AgentState) -> str:
        """Route to the appropriate agent based on coordinator decision.
        
        Args:
            state: Current state.
            
        Returns:
            Agent name to route to.
        """
        return state.get("final_department", "General")
    
    async def _coordinator_node(self, state: AgentState) -> AgentState:
        """Coordinator node that routes queries.
        
        Args:
            state: Current state.
            
        Returns:
            Updated state with routing decision.
        """
        response = await self.coordinator.process(state)
        
        # Update state with routing info
        state["predicted_department"] = response.metadata.get("predicted_department", "General")
        state["prediction_confidence"] = response.metadata.get("prediction_confidence", 0.0)
        state["final_department"] = response.metadata.get("final_department", "General")
        state["was_overridden"] = response.metadata.get("was_overridden", False)
        state["current_agent"] = "coordinator"
        
        return state
    
    async def _hr_node(self, state: AgentState) -> AgentState:
        """HR agent node.
        
        Args:
            state: Current state.
            
        Returns:
            Updated state with HR response.
        """
        response = await self.hr_agent.process(state)
        state["response"] = response.content
        state["sources"] = response.sources
        state["current_agent"] = "hr"
        
        if "agent_responses" not in state:
            state["agent_responses"] = {}
        state["agent_responses"]["hr"] = response.content
        
        return state
    
    async def _it_node(self, state: AgentState) -> AgentState:
        """IT agent node.
        
        Args:
            state: Current state.
            
        Returns:
            Updated state with IT response.
        """
        response = await self.it_agent.process(state)
        state["response"] = response.content
        state["sources"] = response.sources
        state["current_agent"] = "it"
        
        if "agent_responses" not in state:
            state["agent_responses"] = {}
        state["agent_responses"]["it"] = response.content
        
        return state
    
    async def _security_node(self, state: AgentState) -> AgentState:
        """Security agent node.
        
        Args:
            state: Current state.
            
        Returns:
            Updated state with Security response.
        """
        response = await self.security_agent.process(state)
        state["response"] = response.content
        state["sources"] = response.sources
        state["current_agent"] = "security"
        
        if "agent_responses" not in state:
            state["agent_responses"] = {}
        state["agent_responses"]["security"] = response.content
        
        return state
    
    async def _finance_node(self, state: AgentState) -> AgentState:
        """Finance agent node.
        
        Args:
            state: Current state.
            
        Returns:
            Updated state with Finance response.
        """
        response = await self.finance_agent.process(state)
        state["response"] = response.content
        state["sources"] = response.sources
        state["current_agent"] = "finance"
        
        if "agent_responses" not in state:
            state["agent_responses"] = {}
        state["agent_responses"]["finance"] = response.content
        
        return state
    
    async def _progress_node(self, state: AgentState) -> AgentState:
        """Progress agent node.
        
        Args:
            state: Current state.
            
        Returns:
            Updated state with Progress response.
        """
        response = await self.progress_agent.process(state)
        state["response"] = response.content
        state["sources"] = response.sources
        state["task_updates"] = response.task_updates
        state["current_agent"] = "progress"
        
        if "agent_responses" not in state:
            state["agent_responses"] = {}
        state["agent_responses"]["progress"] = response.content
        
        return state
    
    async def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize node that wraps up the response.
        
        Args:
            state: Current state.
            
        Returns:
            Final state.
        """
        state["end_time"] = datetime.utcnow()
        
        if state.get("start_time"):
            start = state["start_time"]
            end = state["end_time"]
            state["total_time_ms"] = (end - start).total_seconds() * 1000
        
        return state
    
    async def _process_single_agent(
        self,
        department: str,
        state: AgentState
    ) -> Dict[str, Any]:
        """Process a query through a single agent.
        
        Args:
            department: Department to query.
            state: Current state.
            
        Returns:
            Agent response with content and sources.
        """
        agent = self.agent_map.get(department, self.progress_agent)
        response = await agent.process(state)
        return {
            "department": department,
            "content": response.content,
            "sources": response.sources,
            "task_updates": getattr(response, 'task_updates', [])
        }
    
    def _detect_multiple_departments(self, message: str) -> List[str]:
        """Detect if query spans multiple departments.
        
        Args:
            message: User message.
            
        Returns:
            List of detected departments.
        """
        intent_detector = get_intent_detector()
        intent_result = intent_detector.detect(message)
        
        departments = []
        
        # Get primary intent's department
        if intent_result.primary_intent.department:
            departments.append(intent_result.primary_intent.department)
        
        # Check secondary intents for additional departments
        for secondary in intent_result.secondary_intents:
            if secondary.department and secondary.department not in departments:
                departments.append(secondary.department)
        
        # Also check for department keywords directly in the message (English and Arabic)
        message_lower = message.lower()
        dept_keywords = {
            "HR": [
                # English
                "benefit", "insurance", "health", "pto", "vacation", "leave", "policy", "handbook",
                # Arabic
                "تأمين", "تامين", "صحي", "إجازة", "اجازة", "مزايا", "موارد بشرية", "سياسة", "عقد"
            ],
            "IT": [
                # English
                "vpn", "laptop", "email", "password", "software", "account", "computer", "network",
                # Arabic
                "كمبيوتر", "حاسوب", "لابتوب", "بريد", "إيميل", "ايميل", "كلمة مرور", "كلمة السر", "برنامج"
            ],
            "Security": [
                # English
                "security", "training", "compliance", "badge", "nda",
                # Arabic
                "أمن", "امن", "تدريب", "بطاقة", "سرية"
            ],
            "Finance": [
                # English
                "expense", "payroll", "reimburse", "tax", "budget", "travel",
                # Arabic
                "راتب", "رواتب", "مصاريف", "نفقات", "ضريبة", "ميزانية", "سفر"
            ]
        }
        
        for dept, keywords in dept_keywords.items():
            if dept not in departments:
                for kw in keywords:
                    if kw in message_lower or kw in message:  # Check both lower and original for Arabic
                        departments.append(dept)
                        break
        
        return departments if departments else ["General"]
    
    async def _combine_multi_agent_responses(
        self,
        responses: List[Dict[str, Any]],
        user_name: str,
        original_message: str
    ) -> str:
        """Combine responses from multiple agents into a coherent reply.
        
        Args:
            responses: List of agent responses.
            user_name: User's name.
            original_message: Original user query.
            
        Returns:
            Combined response text.
        """
        if len(responses) == 1:
            return responses[0]["content"]
        
        # Build combined response with clear sections
        combined_parts = []
        
        for resp in responses:
            dept = resp["department"]
            content = resp["content"]
            
            # Clean up the response (remove greetings if not the first)
            if combined_parts:
                # Remove common greeting patterns from subsequent responses
                import re
                content = re.sub(r'^(Hi|Hello|Hey)[^.!]*[.!]\s*', '', content, flags=re.IGNORECASE)
                content = re.sub(r'^I\'d be happy to help[^.!]*[.!]\s*', '', content, flags=re.IGNORECASE)
            
            if content.strip():
                combined_parts.append(f"**{dept} Information:**\n{content.strip()}")
        
        # Join with separators
        combined = "\n\n---\n\n".join(combined_parts)
        
        return combined
    
    def _cache_response(
        self,
        query: str,
        response: str,
        sources: List[Dict],
        department: str,
        confidence: float
    ):
        """Cache a response for future similar queries (non-blocking)."""
        # OPTIMIZATION: Run caching in background thread to not block response
        from concurrent.futures import ThreadPoolExecutor
        
        def cache_in_background():
            try:
                db = next(get_db())
                cache_service = SemanticCacheService(db)
                cache_service.cache_response(
                    query=query,
                    response=response,
                    sources=sources,
                    department=department,
                    confidence_score=confidence
                )
                db.close()
                logger.debug(f"Cached response for query: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Failed to cache response: {e}")
        
        # Submit to thread pool for async execution
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(cache_in_background)
        executor.shutdown(wait=False)
    
    async def process_message(
        self,
        user_id: int,
        message: str,
        user_name: str = "User",
        user_role: str = "Employee",
        user_department: str = "General",
        user_type: str = "new_hire",
        tasks: List[Dict[str, Any]] = None,
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Process a user message through the agent pipeline.
        
        Args:
            user_id: User ID.
            message: User message.
            user_name: User's name.
            user_role: User's job role.
            user_department: User's department.
            user_type: User type (new_hire, admin).
            tasks: User's onboarding tasks.
            chat_history: Previous chat messages.
            
        Returns:
            Dictionary with response and metadata.
        """
        start_time = datetime.utcnow()
        
        # Detect query language
        translation_service = get_translation_service()
        detected_language = translation_service.detect_language(message)
        is_arabic = detected_language.value == "ar"
        
        logger.info(f"Processing message for user {user_id}: {message[:50]}... (language: {detected_language.value})")
        
        # Check semantic cache first
        db = next(get_db())
        try:
            cache_service = SemanticCacheService(db)
            cached = cache_service.get_cached_response(message)
            
            if cached:
                end_time = datetime.utcnow()
                total_time_ms = (end_time - start_time).total_seconds() * 1000
                logger.info(f"Returning cached response (type: {cached.get('cache_type')})")
                
                return {
                    "response": cached["response"],
                    "sources": cached.get("sources", []),
                    "task_updates": [],
                    "routing": {
                        "predicted_department": cached.get("department"),
                        "prediction_confidence": cached.get("confidence", 1.0),
                        "final_department": cached.get("department"),
                        "was_overridden": False,
                        "is_cached": True,
                        "cache_type": cached.get("cache_type")
                    },
                    "agent": "cache",
                    "total_time_ms": total_time_ms
                }
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
        finally:
            db.close()
        
        # Detect if this is a multi-department query
        detected_departments = self._detect_multiple_departments(message)
        is_multi_intent = len(detected_departments) > 1
        
        # For queries with clear keyword matches, bypass the Coordinator's ML routing
        # This ensures domain-specific terms like "PTO", "VPN", etc. are routed correctly
        # even if the ML model hasn't been trained on them
        has_keyword_match = detected_departments and detected_departments[0] != "General"
        should_bypass_coordinator = has_keyword_match  # Bypass for ANY language with keyword match
        
        logger.info(f"Detected departments: {detected_departments} (multi-intent: {is_multi_intent}, bypass_coordinator: {should_bypass_coordinator})")
        
        try:
            if is_multi_intent or should_bypass_coordinator:
                # Process through multiple agents in parallel
                base_state: AgentState = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_role": user_role,
                    "user_department": user_department,
                    "user_type": user_type,
                    "current_message": message,
                    "messages": chat_history or [],
                    "tasks": tasks or [],
                    "start_time": start_time,
                    "language": detected_language.value,  # Pass detected language
                    "is_arabic": is_arabic
                }
                
                # Run agents in parallel
                agent_tasks = [
                    self._process_single_agent(dept, base_state.copy())
                    for dept in detected_departments
                ]
                
                responses = await asyncio.gather(*agent_tasks)
                
                # Combine responses
                combined_response = await self._combine_multi_agent_responses(
                    responses, user_name, message
                )
                
                # Collect all sources
                all_sources = []
                all_task_updates = []
                for resp in responses:
                    all_sources.extend(resp.get("sources", []))
                    all_task_updates.extend(resp.get("task_updates", []))
                
                end_time = datetime.utcnow()
                total_time_ms = (end_time - start_time).total_seconds() * 1000
                
                # Cache the response
                self._cache_response(
                    message, combined_response, all_sources, 
                    ", ".join(detected_departments), 0.8
                )
                
                return {
                    "response": combined_response,
                    "sources": all_sources,
                    "task_updates": all_task_updates,
                    "routing": {
                        "predicted_department": detected_departments[0],
                        "prediction_confidence": 0.8,
                        "final_department": ", ".join(detected_departments),
                        "was_overridden": False,
                        "is_multi_intent": True,
                        "departments": detected_departments
                    },
                    "agent": ", ".join(detected_departments),
                    "total_time_ms": total_time_ms
                }
            
            else:
                # Single department - use the standard graph flow
                initial_state: AgentState = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_role": user_role,
                    "user_department": user_department,
                    "user_type": user_type,
                    "current_message": message,
                    "messages": chat_history or [],
                    "tasks": tasks or [],
                    "start_time": start_time,
                    "language": detected_language.value,  # Pass detected language
                    "is_arabic": is_arabic
                }
                
                final_state = await self.graph.ainvoke(initial_state)
                
                response = final_state.get("response", "I apologize, but I couldn't process your request.")
                sources = final_state.get("sources", [])
                department = final_state.get("final_department")
                confidence = final_state.get("prediction_confidence", 0.5)
                
                # Cache the response
                self._cache_response(message, response, sources, department, confidence)
                
                return {
                    "response": response,
                    "sources": sources,
                    "task_updates": final_state.get("task_updates", []),
                    "routing": {
                        "predicted_department": final_state.get("predicted_department"),
                        "prediction_confidence": confidence,
                        "final_department": department,
                        "was_overridden": final_state.get("was_overridden"),
                        "is_multi_intent": False
                    },
                    "agent": final_state.get("current_agent"),
                    "total_time_ms": final_state.get("total_time_ms", 0)
                }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again or contact support.",
                "sources": [],
                "task_updates": [],
                "routing": {},
                "agent": None,
                "error": str(e),
                "total_time_ms": 0
            }


# Singleton instance
_orchestrator: Optional[OnboardingOrchestrator] = None


def get_orchestrator() -> OnboardingOrchestrator:
    """Get or create orchestrator singleton.
    
    Returns:
        OnboardingOrchestrator instance.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OnboardingOrchestrator()
    return _orchestrator

