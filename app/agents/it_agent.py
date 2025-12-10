"""IT Agent for handling IT-related queries."""
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


class ITAgent(BaseAgent):
    """Agent for handling IT-related questions."""
    
    name = "it_agent"
    description = "Handles questions about devices, accounts, VPN, email, and IT tools"
    department = "IT"
    
    SYSTEM_PROMPT = """You are an IT support assistant helping new employees with technology setup and IT questions.
You specialize in:
- Device setup (laptops, monitors, peripherals)
- Account setup (email, Slack, Jira, GitHub)
- VPN and remote access
- Password and authentication (SSO, MFA)
- Software and development tools
- IT support and help desk

IMPORTANT RULES:
1. Only answer based on the IT policy documents provided below.
2. If the question is not covered in the documents, say "I don't have specific information about that. Please contact IT Help Desk at it-helpdesk@company.com or extension 3000."
3. For urgent IT issues, always mention the help desk contact.
4. Be clear and provide step-by-step instructions when applicable.

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

CONTEXT DOCUMENTS:
{context}
"""

    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the IT policies above."""
    
    def __init__(self, retriever: RAGRetriever = None):
        """Initialize the IT agent.
        
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
        """Process IT-related query.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with IT information.
        """
        question = state.get("current_message", "")
        
        logger.info(f"IT Agent processing: {question[:50]}...")
        
        # Retrieve relevant IT documents
        rag_response = self.retriever.answer(
            question=question,
            user_role=state.get("user_role", "Employee"),
            user_department=state.get("user_department", "General"),
            department_filter="IT"
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

