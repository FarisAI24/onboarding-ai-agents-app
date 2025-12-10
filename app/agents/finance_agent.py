"""Finance/Admin Agent for handling finance-related queries."""
import logging
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import get_settings
from app.agents.base import BaseAgent, AgentState, AgentResponse
from rag.retriever import RAGRetriever, get_rag_retriever

logger = logging.getLogger(__name__)
settings = get_settings()


class FinanceAgent(BaseAgent):
    """Agent for handling finance and admin questions."""
    
    name = "finance_agent"
    description = "Handles questions about payroll, expenses, reimbursements, corporate cards, and travel"
    department = "Finance"
    
    SYSTEM_PROMPT = """You are a Finance and Administration assistant helping new employees with finance-related questions.
You specialize in:
- Payroll and pay schedules
- Expense reimbursement
- Corporate credit cards
- Travel booking and policies
- Purchasing and procurement
- Tax information (W-4, W-2)
- Employee assistance programs (commuter benefits, tuition reimbursement)

IMPORTANT RULES:
1. Only answer based on the Finance policy documents provided below.
2. If the question is not covered in the documents, say "I don't have specific information about that. Please contact Finance at finance@company.com or Payroll at payroll@company.com."
3. For sensitive financial information (like specific salary amounts), direct them to the appropriate HR or Finance contact.
4. Be precise about deadlines and limits (expense submission deadlines, approval thresholds, etc.).
5. Always mention relevant tools (Expensify, Concur, ADP) when applicable.

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

CONTEXT DOCUMENTS:
{context}
"""

    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the Finance policies above."""
    
    def __init__(self, retriever: RAGRetriever = None):
        """Initialize the Finance agent.
        
        Args:
            retriever: RAG retriever to use.
        """
        self.retriever = retriever or get_rag_retriever()
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
    
    async def process(self, state: AgentState) -> AgentResponse:
        """Process finance-related query.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with finance policy information.
        """
        question = state.get("current_message", "")
        
        logger.info(f"Finance Agent processing: {question[:50]}...")
        
        # Retrieve relevant Finance documents
        rag_response = self.retriever.answer(
            question=question,
            user_role=state.get("user_role", "Employee"),
            user_department=state.get("user_department", "General"),
            department_filter="Finance"
        )
        
        # Format context from retrieval
        context = self.retriever.format_context(rag_response.retrieval_result)
        
        # Generate response
        response = self.chain.invoke({
            "context": context,
            "question": question,
            "user_name": state.get("user_name", ""),
            "user_role": state.get("user_role", "Employee"),
            "user_department": state.get("user_department", "General")
        })
        
        return AgentResponse(
            content=response,
            sources=rag_response.sources,
            metadata={
                "retrieval_time_ms": rag_response.retrieval_result.retrieval_time_ms,
                "docs_retrieved": len(rag_response.retrieval_result.documents)
            }
        )

