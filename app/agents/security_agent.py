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

# Arabic to English query translations for common Security topics
ARABIC_QUERY_MAPPINGS = {
    "أمن": "security policy",
    "امن": "security policy",
    "تدريب": "training security awareness",
    "بطاقة": "badge access card",
    "سرية": "confidential NDA",
    "كلمة مرور": "password policy authentication",
    "صلاحية": "access permissions authorization",
    "صلاحيات": "access permissions authorization",
    "حماية": "protection security",
    "بيانات": "data classification handling",
    "تشفير": "encryption security",
    "حادث": "incident reporting",
    "إبلاغ": "reporting incident",
    "امتثال": "compliance SOC GDPR",
}


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
6. LANGUAGE: {language_instruction}

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

CONTEXT DOCUMENTS:
{context}
"""

    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the Security policies above. {response_language}"""
    
    ARABIC_INSTRUCTION = "The user is asking in Arabic. You MUST respond in Arabic (العربية). Translate the relevant policy information to Arabic in your response."
    ENGLISH_INSTRUCTION = "Respond in English."
    
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
    
    def _translate_arabic_query(self, query: str) -> str:
        """Translate Arabic query keywords to English for better RAG retrieval."""
        english_terms = []
        query_lower = query.lower()
        
        for arabic_term, english_equiv in ARABIC_QUERY_MAPPINGS.items():
            if arabic_term in query or arabic_term in query_lower:
                english_terms.append(english_equiv)
        
        if english_terms:
            translated = " ".join(english_terms)
            logger.info(f"Translated Arabic query for RAG: '{query[:30]}...' -> '{translated}'")
            return translated
        
        logger.warning(f"No Arabic terms matched for: {query[:50]}... Using generic Security search")
        return "security policy password access badge NDA compliance"
    
    async def process(self, state: AgentState) -> AgentResponse:
        """Process security-related query.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with security policy information.
        """
        question = state.get("current_message", "")
        is_arabic = state.get("is_arabic", False)
        language = state.get("language", "en")
        
        logger.info(f"Security Agent processing: {question[:50]}... (language: {language})")
        
        # For Arabic queries, translate to English for better RAG retrieval
        search_query = question
        if is_arabic:
            search_query = self._translate_arabic_query(question)
        
        # Retrieve relevant Security documents
        rag_response = self.retriever.answer(
            question=search_query,
            user_role=state.get("user_role", "Employee"),
            user_department=state.get("user_department", "General"),
            department_filter="Security"
        )
        
        # Format context from retrieval
        context = self.retriever.format_context(rag_response.retrieval_result)
        
        # Set language instruction
        language_instruction = self.ARABIC_INSTRUCTION if is_arabic else self.ENGLISH_INSTRUCTION
        response_language = "Respond in Arabic (العربية)." if is_arabic else ""
        
        # Generate response
        response = self.chain.invoke({
            "context": context,
            "question": question,
            "user_name": state.get("user_name", ""),
            "user_role": state.get("user_role", "Employee"),
            "user_department": state.get("user_department", "General"),
            "language_instruction": language_instruction,
            "response_language": response_language
        })
        
        return AgentResponse(
            content=response,
            sources=rag_response.sources,
            metadata={
                "retrieval_time_ms": rag_response.retrieval_result.retrieval_time_ms,
                "docs_retrieved": len(rag_response.retrieval_result.documents),
                "language": language
            }
        )

