"""RAG Evaluation module for testing retrieval quality."""
import logging
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from rag.retriever import RAGRetriever, get_rag_retriever

logger = logging.getLogger(__name__)


@dataclass
class EvalQuestion:
    """A single evaluation question."""
    id: str
    question: str
    expected_doc: str  # Expected source document filename
    expected_section: Optional[str] = None  # Expected section
    department: Optional[str] = None  # Expected department
    keywords: List[str] = field(default_factory=list)  # Keywords that should appear


@dataclass
class EvalResult:
    """Result of evaluating a single question."""
    question_id: str
    question: str
    expected_doc: str
    expected_section: Optional[str]
    retrieved_docs: List[str]
    retrieved_sections: List[str]
    doc_found: bool
    section_found: bool
    doc_rank: int  # Rank at which expected doc was found (0 if not found)
    retrieval_time_ms: float
    confidence_score: float
    answer_preview: str


@dataclass
class EvalMetrics:
    """Aggregate evaluation metrics."""
    total_questions: int
    doc_hit_rate: float  # Percentage of questions where expected doc was in top-k
    section_hit_rate: float  # Percentage where expected section was found
    mrr: float  # Mean Reciprocal Rank
    avg_retrieval_time_ms: float
    avg_confidence_score: float
    results_by_department: Dict[str, Dict[str, float]]
    timestamp: str


# Evaluation dataset
EVAL_DATASET: List[EvalQuestion] = [
    # HR Questions
    EvalQuestion(
        id="hr_1",
        question="What are the health insurance options available to employees?",
        expected_doc="hr_policies.md",
        expected_section="1.1 Health Insurance",
        department="HR",
        keywords=["PPO", "HMO", "HDHP", "premium"]
    ),
    EvalQuestion(
        id="hr_2",
        question="How much PTO do I get as a new employee?",
        expected_doc="hr_policies.md",
        expected_section="2. Paid Time Off",
        department="HR",
        keywords=["PTO", "vacation", "days"]
    ),
    EvalQuestion(
        id="hr_3",
        question="What is the probation period policy?",
        expected_doc="hr_policies.md",
        expected_section="5. Probation Period",
        department="HR",
        keywords=["probation", "90 days", "review"]
    ),
    EvalQuestion(
        id="hr_4",
        question="What are the working hours and remote work options?",
        expected_doc="hr_policies.md",
        expected_section="3. Working Hours",
        department="HR",
        keywords=["hours", "remote", "flexible"]
    ),
    # IT Questions
    EvalQuestion(
        id="it_1",
        question="How do I set up VPN for remote work?",
        expected_doc="it_policies.md",
        expected_section="3.2 VPN Setup",
        department="IT",
        keywords=["VPN", "GlobalProtect", "remote"]
    ),
    EvalQuestion(
        id="it_2",
        question="What is the password policy?",
        expected_doc="it_policies.md",
        expected_section="2.1 Password Requirements",
        department="IT",
        keywords=["password", "characters", "MFA"]
    ),
    EvalQuestion(
        id="it_3",
        question="What devices can I use for work?",
        expected_doc="it_policies.md",
        expected_section="1. Device Policy",
        department="IT",
        keywords=["device", "laptop", "BYOD"]
    ),
    EvalQuestion(
        id="it_4",
        question="What software do I need to install?",
        expected_doc="it_policies.md",
        expected_section="4. Required Software",
        department="IT",
        keywords=["software", "Slack", "install"]
    ),
    # Security Questions
    EvalQuestion(
        id="sec_1",
        question="What security training do I need to complete?",
        expected_doc="security_policies.md",
        expected_section="2. Required Security Training",
        department="Security",
        keywords=["training", "security", "awareness"]
    ),
    EvalQuestion(
        id="sec_2",
        question="How should I handle confidential data?",
        expected_doc="security_policies.md",
        expected_section="3. Data Classification",
        department="Security",
        keywords=["confidential", "data", "handling"]
    ),
    EvalQuestion(
        id="sec_3",
        question="What should I do if I receive a phishing email?",
        expected_doc="security_policies.md",
        expected_section="4. Phishing Prevention",
        department="Security",
        keywords=["phishing", "report", "suspicious"]
    ),
    # Finance Questions
    EvalQuestion(
        id="fin_1",
        question="How do I submit expense reports?",
        expected_doc="finance_policies.md",
        expected_section="2. Expense Reports",
        department="Finance",
        keywords=["expense", "Expensify", "receipt"]
    ),
    EvalQuestion(
        id="fin_2",
        question="When is payday and how does direct deposit work?",
        expected_doc="finance_policies.md",
        expected_section="1. Payroll",
        department="Finance",
        keywords=["payroll", "15th", "direct deposit"]
    ),
    EvalQuestion(
        id="fin_3",
        question="What is the travel and booking policy?",
        expected_doc="finance_policies.md",
        expected_section="3. Travel Policy",
        department="Finance",
        keywords=["travel", "booking", "Concur"]
    ),
]


class RAGEvaluator:
    """Evaluator for RAG retrieval quality."""
    
    def __init__(self, retriever: RAGRetriever = None, top_k: int = 5):
        """Initialize the evaluator.
        
        Args:
            retriever: RAG retriever to evaluate.
            top_k: Number of documents to retrieve for evaluation.
        """
        self.retriever = retriever or get_rag_retriever()
        self.top_k = top_k
    
    def evaluate_question(self, question: EvalQuestion) -> EvalResult:
        """Evaluate retrieval for a single question.
        
        Args:
            question: Evaluation question.
            
        Returns:
            EvalResult with evaluation metrics.
        """
        # Retrieve documents
        start_time = time.time()
        rag_response = self.retriever.answer(
            question=question.question,
            department_filter=question.department
        )
        retrieval_time = (time.time() - start_time) * 1000
        
        # Extract retrieved documents and sections
        retrieved_docs = [s["document"] for s in rag_response.sources]
        retrieved_sections = [s.get("section", "") for s in rag_response.sources]
        
        # Check if expected doc was found
        doc_found = question.expected_doc in retrieved_docs
        doc_rank = 0
        if doc_found:
            doc_rank = retrieved_docs.index(question.expected_doc) + 1
        
        # Check if expected section was found
        section_found = False
        if question.expected_section:
            section_found = any(
                question.expected_section.lower() in s.lower() 
                for s in retrieved_sections
            )
        
        return EvalResult(
            question_id=question.id,
            question=question.question,
            expected_doc=question.expected_doc,
            expected_section=question.expected_section,
            retrieved_docs=retrieved_docs,
            retrieved_sections=retrieved_sections,
            doc_found=doc_found,
            section_found=section_found,
            doc_rank=doc_rank,
            retrieval_time_ms=retrieval_time,
            confidence_score=rag_response.confidence_score,
            answer_preview=rag_response.answer[:200] + "..." if len(rag_response.answer) > 200 else rag_response.answer
        )
    
    def run_evaluation(
        self,
        questions: List[EvalQuestion] = None
    ) -> tuple[List[EvalResult], EvalMetrics]:
        """Run evaluation on all questions.
        
        Args:
            questions: List of evaluation questions. Uses default if None.
            
        Returns:
            Tuple of (list of results, aggregate metrics).
        """
        if questions is None:
            questions = EVAL_DATASET
        
        logger.info(f"Running evaluation on {len(questions)} questions")
        
        results = []
        for q in questions:
            try:
                result = self.evaluate_question(q)
                results.append(result)
                logger.info(
                    f"[{q.id}] doc_found={result.doc_found}, "
                    f"section_found={result.section_found}, "
                    f"rank={result.doc_rank}"
                )
            except Exception as e:
                logger.error(f"Error evaluating question {q.id}: {e}")
        
        # Calculate metrics
        metrics = self._calculate_metrics(results, questions)
        
        return results, metrics
    
    def _calculate_metrics(
        self,
        results: List[EvalResult],
        questions: List[EvalQuestion]
    ) -> EvalMetrics:
        """Calculate aggregate metrics from results."""
        if not results:
            return EvalMetrics(
                total_questions=0,
                doc_hit_rate=0.0,
                section_hit_rate=0.0,
                mrr=0.0,
                avg_retrieval_time_ms=0.0,
                avg_confidence_score=0.0,
                results_by_department={},
                timestamp=datetime.now().isoformat()
            )
        
        # Overall metrics
        doc_hits = sum(1 for r in results if r.doc_found)
        section_hits = sum(1 for r in results if r.section_found)
        
        # MRR (Mean Reciprocal Rank)
        reciprocal_ranks = [1/r.doc_rank if r.doc_rank > 0 else 0 for r in results]
        mrr = sum(reciprocal_ranks) / len(results)
        
        avg_time = sum(r.retrieval_time_ms for r in results) / len(results)
        avg_confidence = sum(r.confidence_score for r in results) / len(results)
        
        # Per-department metrics
        dept_results: Dict[str, List[EvalResult]] = {}
        for q, r in zip(questions, results):
            dept = q.department or "General"
            if dept not in dept_results:
                dept_results[dept] = []
            dept_results[dept].append(r)
        
        results_by_department = {}
        for dept, dept_res in dept_results.items():
            dept_doc_hits = sum(1 for r in dept_res if r.doc_found)
            dept_section_hits = sum(1 for r in dept_res if r.section_found)
            results_by_department[dept] = {
                "doc_hit_rate": dept_doc_hits / len(dept_res),
                "section_hit_rate": dept_section_hits / len(dept_res),
                "count": len(dept_res)
            }
        
        return EvalMetrics(
            total_questions=len(results),
            doc_hit_rate=doc_hits / len(results),
            section_hit_rate=section_hits / len(results),
            mrr=mrr,
            avg_retrieval_time_ms=avg_time,
            avg_confidence_score=avg_confidence,
            results_by_department=results_by_department,
            timestamp=datetime.now().isoformat()
        )
    
    def save_results(
        self,
        results: List[EvalResult],
        metrics: EvalMetrics,
        output_path: str = "data/eval_results.json"
    ):
        """Save evaluation results to file.
        
        Args:
            results: List of evaluation results.
            metrics: Aggregate metrics.
            output_path: Path to save results.
        """
        output = {
            "metrics": {
                "total_questions": metrics.total_questions,
                "doc_hit_rate": metrics.doc_hit_rate,
                "section_hit_rate": metrics.section_hit_rate,
                "mrr": metrics.mrr,
                "avg_retrieval_time_ms": metrics.avg_retrieval_time_ms,
                "avg_confidence_score": metrics.avg_confidence_score,
                "results_by_department": metrics.results_by_department,
                "timestamp": metrics.timestamp
            },
            "results": [
                {
                    "question_id": r.question_id,
                    "question": r.question,
                    "expected_doc": r.expected_doc,
                    "expected_section": r.expected_section,
                    "retrieved_docs": r.retrieved_docs,
                    "doc_found": r.doc_found,
                    "section_found": r.section_found,
                    "doc_rank": r.doc_rank,
                    "retrieval_time_ms": r.retrieval_time_ms,
                    "confidence_score": r.confidence_score
                }
                for r in results
            ]
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Saved evaluation results to {output_path}")
    
    def print_report(self, results: List[EvalResult], metrics: EvalMetrics):
        """Print a human-readable evaluation report."""
        print("\n" + "=" * 60)
        print("RAG EVALUATION REPORT")
        print("=" * 60)
        print(f"\nTimestamp: {metrics.timestamp}")
        print(f"Total Questions: {metrics.total_questions}")
        print(f"\n{'Metric':<30} {'Value':>15}")
        print("-" * 45)
        print(f"{'Document Hit Rate':<30} {metrics.doc_hit_rate*100:>14.1f}%")
        print(f"{'Section Hit Rate':<30} {metrics.section_hit_rate*100:>14.1f}%")
        print(f"{'Mean Reciprocal Rank (MRR)':<30} {metrics.mrr:>15.3f}")
        print(f"{'Avg Retrieval Time':<30} {metrics.avg_retrieval_time_ms:>12.1f}ms")
        print(f"{'Avg Confidence Score':<30} {metrics.avg_confidence_score:>15.2f}")
        
        print(f"\n{'Department':<15} {'Doc Hit%':>10} {'Sec Hit%':>10} {'Count':>8}")
        print("-" * 45)
        for dept, dept_metrics in metrics.results_by_department.items():
            print(
                f"{dept:<15} "
                f"{dept_metrics['doc_hit_rate']*100:>9.1f}% "
                f"{dept_metrics['section_hit_rate']*100:>9.1f}% "
                f"{int(dept_metrics['count']):>8}"
            )
        
        # Show failures
        failures = [r for r in results if not r.doc_found]
        if failures:
            print(f"\n{'FAILED RETRIEVALS':^60}")
            print("-" * 60)
            for r in failures:
                print(f"  [{r.question_id}] {r.question[:50]}...")
                print(f"    Expected: {r.expected_doc}")
                print(f"    Got: {r.retrieved_docs[:3]}")
        
        print("\n" + "=" * 60)


def run_evaluation_cli():
    """CLI function to run RAG evaluation."""
    evaluator = RAGEvaluator()
    results, metrics = evaluator.run_evaluation()
    evaluator.print_report(results, metrics)
    evaluator.save_results(results, metrics)
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_evaluation_cli()

