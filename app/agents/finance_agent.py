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

# Arabic to English query translations for common Finance topics
ARABIC_QUERY_MAPPINGS = {
    "راتب": "salary pay compensation payroll",
    "رواتب": "salary pay compensation payroll",
    "مصاريف": "expense reimbursement",
    "نفقات": "expense reimbursement",
    "استرداد": "reimbursement expense",
    "ضريبة": "tax W-4 W-2",
    "ضرائب": "tax W-4 W-2",
    "ميزانية": "budget finance",
    "سفر": "travel expense booking",
    "بطاقة ائتمان": "corporate credit card",
    "بطاقة الشركة": "corporate credit card",
    "موعد الراتب": "pay schedule payday",
    "حساب بنكي": "direct deposit bank account",
    "إيداع": "direct deposit",
}


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
6. LANGUAGE: {language_instruction}

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

CONTEXT DOCUMENTS:
{context}
"""

    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the Finance policies above. {response_language}"""
    
    ARABIC_INSTRUCTION = "The user is asking in Arabic. You MUST respond in Arabic (العربية). Translate the relevant policy information to Arabic in your response."
    ENGLISH_INSTRUCTION = "Respond in English."
    
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
        
        logger.warning(f"No Arabic terms matched for: {query[:50]}... Using generic Finance search")
        return "finance payroll expense reimbursement salary pay schedule"
    
    async def process(self, state: AgentState) -> AgentResponse:
        """Process finance-related query.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with finance policy information.
        """
        question = state.get("current_message", "")
        is_arabic = state.get("is_arabic", False)
        language = state.get("language", "en")
        
        logger.info(f"Finance Agent processing: {question[:50]}... (language: {language})")
        
        # For Arabic queries, translate to English for better RAG retrieval
        search_query = question
        if is_arabic:
            search_query = self._translate_arabic_query(question)
        
        # Retrieve relevant Finance documents
        rag_response = self.retriever.answer(
            question=search_query,
            user_role=state.get("user_role", "Employee"),
            user_department=state.get("user_department", "General"),
            department_filter="Finance"
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

