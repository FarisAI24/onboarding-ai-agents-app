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

# Arabic to English query translations for common HR topics
ARABIC_QUERY_MAPPINGS = {
    "إجازة": "leave vacation time off",
    "اجازة": "leave vacation time off",
    "تأمين صحي": "health insurance benefits",
    "تامين صحي": "health insurance benefits",
    "تأمين": "insurance benefits",
    "تامين": "insurance benefits",
    "صحي": "health medical",
    "راتب": "salary pay compensation",
    "رواتب": "salary pay compensation payroll",
    "مزايا": "benefits perks",
    "عقد": "contract employment agreement",
    "استقالة": "resignation termination",
    "تقاعد": "retirement pension",
    "سياسة": "policy policies",
    "موارد بشرية": "human resources HR",
    "إجازة مرضية": "sick leave",
    "إجازة سنوية": "annual leave vacation",
    "أمومة": "maternity parental leave",
    "أبوة": "paternity parental leave",
}


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
5. LANGUAGE: {language_instruction}

User Information:
- Name: {user_name}
- Role: {user_role}
- Department: {user_department}

CONTEXT DOCUMENTS:
{context}
"""

    USER_PROMPT = """Question: {question}

Please provide a helpful answer based on the HR policies above. {response_language}"""
    
    ARABIC_INSTRUCTION = "The user is asking in Arabic. You MUST respond in Arabic (العربية). Translate the relevant policy information to Arabic in your response."
    ENGLISH_INSTRUCTION = "Respond in English."
    
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
    
    def _translate_arabic_query(self, query: str) -> str:
        """Translate Arabic query keywords to English for better RAG retrieval.
        
        Args:
            query: Original Arabic query.
            
        Returns:
            English translation/keywords for retrieval.
        """
        english_terms = []
        query_lower = query.lower()
        
        # Find matching Arabic terms and get English equivalents
        for arabic_term, english_equiv in ARABIC_QUERY_MAPPINGS.items():
            if arabic_term in query or arabic_term in query_lower:
                english_terms.append(english_equiv)
        
        if english_terms:
            # Combine all matched English terms
            translated = " ".join(english_terms)
            logger.info(f"Translated Arabic query for RAG: '{query[:30]}...' -> '{translated}'")
            return translated
        
        # Fallback: return a general HR query if no specific terms matched
        logger.warning(f"No Arabic terms matched for: {query[:50]}... Using generic HR search")
        return "HR policy benefits leave vacation employee handbook"
    
    async def process(self, state: AgentState) -> AgentResponse:
        """Process HR-related query.
        
        Args:
            state: Current agent state.
            
        Returns:
            AgentResponse with HR policy information.
        """
        question = state.get("current_message", "")
        is_arabic = state.get("is_arabic", False)
        language = state.get("language", "en")
        
        logger.info(f"HR Agent processing: {question[:50]}... (language: {language})")
        
        # For Arabic queries, translate to English for better RAG retrieval
        search_query = question
        if is_arabic:
            search_query = self._translate_arabic_query(question)
        
        # Retrieve relevant HR documents using the (possibly translated) query
        rag_response = self.retriever.answer(
            question=search_query,
            user_role=state.get("user_role", "Employee"),
            user_department=state.get("user_department", "General"),
            department_filter="HR"
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

