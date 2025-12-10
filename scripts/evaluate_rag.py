"""RAG evaluation script with test questions and expected sources."""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from app.config import get_settings
from rag.retriever import RAGRetriever, get_rag_retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class EvalQuestion:
    """Evaluation question with expected source."""
    question: str
    expected_doc: str
    expected_section: str = ""
    department: str = ""


# Hand-written evaluation set
EVAL_SET: List[EvalQuestion] = [
    # HR Questions
    EvalQuestion(
        question="What health insurance options are available?",
        expected_doc="hr_policies.md",
        expected_section="Health Insurance",
        department="HR"
    ),
    EvalQuestion(
        question="How much PTO do new employees get?",
        expected_doc="hr_policies.md",
        expected_section="Annual Leave",
        department="HR"
    ),
    EvalQuestion(
        question="How long is the probation period?",
        expected_doc="hr_policies.md",
        expected_section="Probation Period",
        department="HR"
    ),
    EvalQuestion(
        question="What is the parental leave policy?",
        expected_doc="hr_policies.md",
        expected_section="Parental Leave",
        department="HR"
    ),
    
    # IT Questions
    EvalQuestion(
        question="How do I connect to the VPN?",
        expected_doc="it_policies.md",
        expected_section="VPN Access",
        department="IT"
    ),
    EvalQuestion(
        question="What are the password requirements?",
        expected_doc="it_policies.md",
        expected_section="Password Requirements",
        department="IT"
    ),
    EvalQuestion(
        question="What equipment do new employees receive?",
        expected_doc="it_policies.md",
        expected_section="Company-Issued Equipment",
        department="IT"
    ),
    EvalQuestion(
        question="How do I get help from IT support?",
        expected_doc="it_policies.md",
        expected_section="IT Support",
        department="IT"
    ),
    
    # Security Questions
    EvalQuestion(
        question="What security training is required?",
        expected_doc="security_policies.md",
        expected_section="Mandatory Training",
        department="Security"
    ),
    EvalQuestion(
        question="How do I report a security incident?",
        expected_doc="security_policies.md",
        expected_section="Incident Reporting",
        department="Security"
    ),
    EvalQuestion(
        question="What are the data classification levels?",
        expected_doc="security_policies.md",
        expected_section="Data Classification",
        department="Security"
    ),
    EvalQuestion(
        question="What is the NDA policy?",
        expected_doc="security_policies.md",
        expected_section="Non-Disclosure Agreement",
        department="Security"
    ),
    
    # Finance Questions
    EvalQuestion(
        question="When do employees get paid?",
        expected_doc="finance_policies.md",
        expected_section="Pay Schedule",
        department="Finance"
    ),
    EvalQuestion(
        question="How do I submit expense reimbursements?",
        expected_doc="finance_policies.md",
        expected_section="Expense Reimbursement",
        department="Finance"
    ),
    EvalQuestion(
        question="What is the travel policy?",
        expected_doc="finance_policies.md",
        expected_section="Travel Policy",
        department="Finance"
    ),
    EvalQuestion(
        question="How do I get a corporate card?",
        expected_doc="finance_policies.md",
        expected_section="Corporate Card",
        department="Finance"
    ),
]


def evaluate_retrieval(
    retriever: RAGRetriever,
    eval_set: List[EvalQuestion],
    top_k: int = 5
) -> Dict[str, Any]:
    """Evaluate RAG retrieval quality.
    
    Args:
        retriever: RAG retriever to evaluate.
        eval_set: List of evaluation questions.
        top_k: Number of documents to retrieve.
        
    Returns:
        Dictionary with evaluation metrics.
    """
    results = {
        "total_questions": len(eval_set),
        "correct_doc_top1": 0,
        "correct_doc_topk": 0,
        "correct_section_top1": 0,
        "correct_section_topk": 0,
        "avg_retrieval_time_ms": 0.0,
        "details": []
    }
    
    total_time = 0.0
    
    for q in eval_set:
        logger.info(f"Evaluating: {q.question[:50]}...")
        
        # Retrieve
        result = retriever.retrieve(q.question, top_k=top_k)
        total_time += result.retrieval_time_ms
        
        # Check if expected doc is in results
        doc_in_top1 = False
        doc_in_topk = False
        section_in_top1 = False
        section_in_topk = False
        
        for i, meta in enumerate(result.metadatas):
            doc_match = q.expected_doc in meta.get("filename", "")
            section_match = q.expected_section.lower() in meta.get("section", "").lower()
            
            if doc_match:
                doc_in_topk = True
                if i == 0:
                    doc_in_top1 = True
            
            if section_match:
                section_in_topk = True
                if i == 0:
                    section_in_top1 = True
        
        if doc_in_top1:
            results["correct_doc_top1"] += 1
        if doc_in_topk:
            results["correct_doc_topk"] += 1
        if section_in_top1:
            results["correct_section_top1"] += 1
        if section_in_topk:
            results["correct_section_topk"] += 1
        
        # Store details
        results["details"].append({
            "question": q.question,
            "expected_doc": q.expected_doc,
            "expected_section": q.expected_section,
            "doc_in_top1": doc_in_top1,
            "doc_in_topk": doc_in_topk,
            "section_in_top1": section_in_top1,
            "section_in_topk": section_in_topk,
            "retrieved_docs": [m.get("filename") for m in result.metadatas],
            "retrieval_time_ms": result.retrieval_time_ms
        })
    
    # Calculate averages
    n = len(eval_set)
    results["avg_retrieval_time_ms"] = total_time / n if n > 0 else 0
    results["doc_recall_at_1"] = results["correct_doc_top1"] / n if n > 0 else 0
    results["doc_recall_at_k"] = results["correct_doc_topk"] / n if n > 0 else 0
    results["section_recall_at_1"] = results["correct_section_top1"] / n if n > 0 else 0
    results["section_recall_at_k"] = results["correct_section_topk"] / n if n > 0 else 0
    
    return results


def main():
    """Run RAG evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval quality")
    parser.add_argument("--top-k", type=int, default=5, help="Number of documents to retrieve")
    parser.add_argument("--output", type=str, default="rag_eval_results.json", help="Output file")
    args = parser.parse_args()
    
    logger.info("Loading RAG retriever...")
    retriever = get_rag_retriever()
    
    logger.info(f"Running evaluation with {len(EVAL_SET)} questions...")
    results = evaluate_retrieval(retriever, EVAL_SET, top_k=args.top_k)
    
    # Print summary
    print("\n" + "="*60)
    print("RAG Evaluation Results")
    print("="*60)
    print(f"Total Questions: {results['total_questions']}")
    print(f"\nDocument Retrieval:")
    print(f"  Recall@1: {results['doc_recall_at_1']:.2%}")
    print(f"  Recall@{args.top_k}: {results['doc_recall_at_k']:.2%}")
    print(f"\nSection Retrieval:")
    print(f"  Recall@1: {results['section_recall_at_1']:.2%}")
    print(f"  Recall@{args.top_k}: {results['section_recall_at_k']:.2%}")
    print(f"\nPerformance:")
    print(f"  Avg Retrieval Time: {results['avg_retrieval_time_ms']:.2f}ms")
    print("="*60)
    
    # Save results
    output_path = settings.data_dir / args.output
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    # Return exit code based on quality threshold
    if results["doc_recall_at_k"] < 0.7:
        logger.warning("Document recall below 70% threshold!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

