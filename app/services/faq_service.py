"""FAQ management service."""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database.models import FAQ, Department

logger = logging.getLogger(__name__)


class FAQService:
    """Service for managing FAQs."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_faq(
        self,
        question: str,
        answer: str,
        category: str,
        department: Optional[Department] = None,
        question_ar: Optional[str] = None,
        answer_ar: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[int] = None
    ) -> FAQ:
        """Create a new FAQ entry."""
        faq = FAQ(
            question=question,
            question_ar=question_ar,
            answer=answer,
            answer_ar=answer_ar,
            category=category,
            department=department,
            tags=tags or [],
            created_by=created_by,
            is_published=True
        )
        
        self.db.add(faq)
        self.db.commit()
        self.db.refresh(faq)
        
        logger.info(f"Created FAQ: {faq.id} - {question[:50]}")
        return faq
    
    def update_faq(
        self,
        faq_id: int,
        **updates
    ) -> Optional[FAQ]:
        """Update an existing FAQ."""
        faq = self.db.query(FAQ).filter(FAQ.id == faq_id).first()
        
        if not faq:
            return None
        
        for key, value in updates.items():
            if hasattr(faq, key):
                setattr(faq, key, value)
        
        self.db.commit()
        self.db.refresh(faq)
        
        logger.info(f"Updated FAQ: {faq_id}")
        return faq
    
    def delete_faq(self, faq_id: int) -> bool:
        """Delete an FAQ (soft delete by unpublishing)."""
        faq = self.db.query(FAQ).filter(FAQ.id == faq_id).first()
        
        if not faq:
            return False
        
        faq.is_published = False
        self.db.commit()
        
        logger.info(f"Deleted FAQ: {faq_id}")
        return True
    
    def get_faq(self, faq_id: int) -> Optional[FAQ]:
        """Get an FAQ by ID."""
        return self.db.query(FAQ).filter(FAQ.id == faq_id).first()
    
    def get_faqs(
        self,
        category: Optional[str] = None,
        department: Optional[Department] = None,
        published_only: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[FAQ]:
        """Get FAQs with optional filtering."""
        query = self.db.query(FAQ)
        
        if published_only:
            query = query.filter(FAQ.is_published == True)
        
        if category:
            query = query.filter(FAQ.category == category)
        
        if department:
            query = query.filter(FAQ.department == department)
        
        query = query.order_by(FAQ.view_count.desc())
        
        return query.offset(offset).limit(limit).all()
    
    def search_faqs(
        self,
        query: str,
        language: str = "en",
        limit: int = 10
    ) -> List[FAQ]:
        """Search FAQs by question text."""
        search_query = self.db.query(FAQ).filter(FAQ.is_published == True)
        
        if language == "ar":
            search_query = search_query.filter(
                or_(
                    FAQ.question_ar.ilike(f"%{query}%"),
                    FAQ.answer_ar.ilike(f"%{query}%")
                )
            )
        else:
            search_query = search_query.filter(
                or_(
                    FAQ.question.ilike(f"%{query}%"),
                    FAQ.answer.ilike(f"%{query}%")
                )
            )
        
        # Also search tags
        search_query = search_query.union(
            self.db.query(FAQ).filter(
                FAQ.is_published == True,
                FAQ.tags.contains([query.lower()])
            )
        )
        
        return search_query.limit(limit).all()
    
    def increment_view_count(self, faq_id: int):
        """Increment the view count for an FAQ."""
        self.db.query(FAQ).filter(FAQ.id == faq_id).update(
            {"view_count": FAQ.view_count + 1}
        )
        self.db.commit()
    
    def record_feedback(self, faq_id: int, is_helpful: bool):
        """Record user feedback on an FAQ."""
        faq = self.db.query(FAQ).filter(FAQ.id == faq_id).first()
        
        if faq:
            if is_helpful:
                faq.helpful_count += 1
            else:
                faq.not_helpful_count += 1
            self.db.commit()
    
    def get_categories(self) -> List[str]:
        """Get all FAQ categories."""
        result = self.db.query(FAQ.category).distinct().all()
        return [r[0] for r in result]
    
    def get_popular_faqs(self, limit: int = 10) -> List[FAQ]:
        """Get most viewed FAQs."""
        return self.db.query(FAQ).filter(
            FAQ.is_published == True
        ).order_by(FAQ.view_count.desc()).limit(limit).all()
    
    def get_faq_stats(self) -> Dict[str, Any]:
        """Get FAQ statistics."""
        total = self.db.query(FAQ).count()
        published = self.db.query(FAQ).filter(FAQ.is_published == True).count()
        
        total_views = self.db.query(func.sum(FAQ.view_count)).scalar() or 0
        total_helpful = self.db.query(func.sum(FAQ.helpful_count)).scalar() or 0
        total_not_helpful = self.db.query(func.sum(FAQ.not_helpful_count)).scalar() or 0
        
        categories = self.db.query(
            FAQ.category, func.count(FAQ.id)
        ).group_by(FAQ.category).all()
        
        return {
            "total_faqs": total,
            "published_faqs": published,
            "unpublished_faqs": total - published,
            "total_views": total_views,
            "helpful_count": total_helpful,
            "not_helpful_count": total_not_helpful,
            "helpfulness_rate": total_helpful / (total_helpful + total_not_helpful) if (total_helpful + total_not_helpful) > 0 else 0,
            "categories": {cat: count for cat, count in categories}
        }
    
    def bulk_import(self, faqs: List[Dict]) -> int:
        """Bulk import FAQs."""
        count = 0
        for faq_data in faqs:
            try:
                faq = FAQ(
                    question=faq_data["question"],
                    answer=faq_data["answer"],
                    category=faq_data.get("category", "General"),
                    question_ar=faq_data.get("question_ar"),
                    answer_ar=faq_data.get("answer_ar"),
                    department=Department(faq_data["department"]) if faq_data.get("department") else None,
                    tags=faq_data.get("tags", []),
                    is_published=True
                )
                self.db.add(faq)
                count += 1
            except Exception as e:
                logger.error(f"Error importing FAQ: {e}")
        
        self.db.commit()
        logger.info(f"Bulk imported {count} FAQs")
        return count

