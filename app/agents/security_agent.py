"""Security/Compliance Agent for handling security-related queries."""
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


class SecurityAgent(BaseAgent):
    """Agent for handling security and compliance questions."""
    
    name = "security_agent"
    description = "Handles questions about security training, passwords, NDAs, access rules, and compliance"
    department = "Security"
    
    SYSTEM_PROMPT = """You are a Security and Compliance assistant helping new employees understand security policies.
You specialize in:
- Security training requirements
- Password and authentication policies
- Non-Disclosure Agreements (NDA)
- Data classification and handling
- Access control and permissions
- Incident reporting
- Physical security
- Compliance requirements (SOC 2, GDPR, etc.)

IMPORTANT RULES:
1. Only answer based on the Security policy documents provided below.
2. If the question is not covered in the documents, say "I don't have specific information about that. Please contact the Security Team at security@company.com."
3. Security is critical - never suggest workarounds to security policies.
4. For security incidents or concerns, always emphasize reporting immediately.
5. Be clear about mandatory vs. optional requirements.

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

CONTEXT DOCUMENTS:
{context}
"""

    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the Security policies above."""
    
    def __init__(self, retriever: RAGRetriever = None):
        """Initialize the Security agent.
        
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
        """Process security-related query.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with security policy information.
        """
        question = state.get("current_message", "")
        
        logger.info(f"Security Agent processing: {question[:50]}...")
        
        # Retrieve relevant Security documents
        rag_response = self.retriever.answer(
            question=question,
            user_role=state.get("user_role", "Employee"),
            user_department=state.get("user_department", "General"),
            department_filter="Security"
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

