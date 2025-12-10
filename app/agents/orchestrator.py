"""Main orchestrator using LangGraph for multi-agent coordination."""
import logging
import time
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
        # Initialize state
        initial_state: AgentState = {
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "user_department": user_department,
            "user_type": user_type,
            "current_message": message,
            "messages": chat_history or [],
            "tasks": tasks or [],
            "start_time": datetime.utcnow()
        }
        
        logger.info(f"Processing message for user {user_id}: {message[:50]}...")
        
        # Run the graph
        try:
            final_state = await self.graph.ainvoke(initial_state)
            
            return {
                "response": final_state.get("response", "I apologize, but I couldn't process your request."),
                "sources": final_state.get("sources", []),
                "task_updates": final_state.get("task_updates", []),
                "routing": {
                    "predicted_department": final_state.get("predicted_department"),
                    "prediction_confidence": final_state.get("prediction_confidence"),
                    "final_department": final_state.get("final_department"),
                    "was_overridden": final_state.get("was_overridden")
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

