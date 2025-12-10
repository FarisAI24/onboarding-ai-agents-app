"""HR Agent for handling HR-related queries."""
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


class HRAgent(BaseAgent):
    """Agent for handling HR-related questions."""
    
    name = "hr_agent"
    description = "Handles questions about benefits, PTO, leave policies, contracts, and HR policies"
    department = "HR"
    
    SYSTEM_PROMPT = """You are an HR assistant helping new employees with HR-related questions.
You specialize in:
- Employee benefits (health insurance, 401k, life insurance)
- Paid time off (vacation, sick leave, parental leave)
- Employment policies (probation, performance reviews)
- Workplace guidelines (working hours, remote work, dress code)
- Onboarding documentation (W-4, I-9, direct deposit)

IMPORTANT RULES:
1. Only answer based on the HR policy documents provided below.
2. If the question is not covered in the documents, say "I don't have specific information about that in our HR policies. Please contact HR at hr@company.com or extension 2000."
3. Always mention the relevant policy section when citing information.
4. Be empathetic and supportive - starting a new job can be stressful.

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

CONTEXT DOCUMENTS:
{context}
"""

    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the HR policies above."""
    
    def __init__(self, retriever: RAGRetriever = None):
        """Initialize the HR agent.
        
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
        """Process HR-related query.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with HR policy information.
        """
        question = state.get("current_message", "")
        
        logger.info(f"HR Agent processing: {question[:50]}...")
        
        # Retrieve relevant HR documents
        rag_response = self.retriever.answer(
            question=question,
            user_role=state.get("user_role", "Employee"),
            user_department=state.get("user_department", "General"),
            department_filter="HR"
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

