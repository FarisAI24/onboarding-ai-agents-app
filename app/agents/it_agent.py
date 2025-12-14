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

# Arabic to English query translations for common IT topics
ARABIC_QUERY_MAPPINGS = {
    "كمبيوتر": "computer laptop device",
    "حاسوب": "computer laptop device",
    "لابتوب": "laptop device setup",
    "بريد": "email setup outlook",
    "إيميل": "email setup outlook",
    "ايميل": "email setup outlook",
    "كلمة مرور": "password reset authentication",
    "كلمة السر": "password reset authentication",
    "برنامج": "software application install",
    "VPN": "VPN remote access",
    "في بي ان": "VPN remote access",
    "شبكة": "network wifi connection",
    "واي فاي": "wifi network connection",
    "حساب": "account setup login",
    "تسجيل دخول": "login account access",
    "طابعة": "printer setup",
    "سلاك": "slack messaging",
    "جيرا": "jira project tracking",
}


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
5. LANGUAGE: {language_instruction}

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

CONTEXT DOCUMENTS:
{context}
"""

    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the IT policies above. {response_language}"""
    
    ARABIC_INSTRUCTION = "The user is asking in Arabic. You MUST respond in Arabic (العربية). Translate the relevant policy information to Arabic in your response."
    ENGLISH_INSTRUCTION = "Respond in English."
    
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
        
        logger.warning(f"No Arabic terms matched for: {query[:50]}... Using generic IT search")
        return "IT setup computer laptop email account VPN"
    
    async def process(self, state: AgentState) -> AgentResponse:
        """Process IT-related query.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with IT information.
        """
        question = state.get("current_message", "")
        is_arabic = state.get("is_arabic", False)
        language = state.get("language", "en")
        
        logger.info(f"IT Agent processing: {question[:50]}... (language: {language})")
        
        # For Arabic queries, translate to English for better RAG retrieval
        search_query = question
        if is_arabic:
            search_query = self._translate_arabic_query(question)
        
        # Retrieve relevant IT documents
        rag_response = self.retriever.answer(
            question=search_query,
            user_role=state.get("user_role", "Employee"),
            user_department=state.get("user_department", "General"),
            department_filter="IT"
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

