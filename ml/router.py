"""Question routing model for department classification."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache
from dataclasses import dataclass

import numpy as np
import joblib
from sklearn.pipeline import Pipeline

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


@dataclass
class RoutingPrediction:
    """Result from routing model prediction."""
    department: str
    confidence: float
    all_probabilities: Dict[str, float]


class QuestionRouter:
    """Router for classifying questions by department."""
    
    # Labels in order
    DEPARTMENTS = ["Finance", "General", "HR", "IT", "Security"]
    
    def __init__(self, model_path: Path = None):
        """Initialize the router.
        
        Args:
            model_path: Path to the trained model file.
        """
        self.model_path = model_path or settings.models_dir / "question_router.joblib"
        self._model: Optional[Pipeline] = None
        self._labels: Optional[Dict[int, str]] = None
    
    @property
    def model(self) -> Pipeline:
        """Lazy load the model."""
        if self._model is None:
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model not found at {self.model_path}. "
                    "Please run the training script first."
                )
            
            logger.info(f"Loading routing model from {self.model_path}")
            self._model = joblib.load(self.model_path)
            
            # Load labels
            label_path = self.model_path.parent / "question_router_labels.json"
            if label_path.exists():
                with open(label_path, "r") as f:
                    self._labels = {int(k): v for k, v in json.load(f).items()}
            else:
                self._labels = {i: d for i, d in enumerate(self.DEPARTMENTS)}
            
            logger.info("Routing model loaded successfully")
        
        return self._model
    
    @property
    def labels(self) -> Dict[int, str]:
        """Get label mapping."""
        if self._labels is None:
            _ = self.model  # Force load
        return self._labels
    
    def predict(self, text: str) -> RoutingPrediction:
        """Predict the department for a question.
        
        Args:
            text: Question text.
            
        Returns:
            RoutingPrediction with department and confidence.
        """
        # Get prediction and probabilities
        prediction = self.model.predict([text])[0]
        probabilities = self.model.predict_proba([text])[0]
        
        # Get confidence (probability of predicted class)
        classes = self.model.classes_
        pred_idx = np.where(classes == prediction)[0][0]
        confidence = float(probabilities[pred_idx])
        
        # Create probability dictionary
        all_probs = {
            cls: float(prob) 
            for cls, prob in zip(classes, probabilities)
        }
        
        return RoutingPrediction(
            department=prediction,
            confidence=confidence,
            all_probabilities=all_probs
        )
    
    def predict_batch(self, texts: list) -> list:
        """Predict departments for multiple questions.
        
        Args:
            texts: List of question texts.
            
        Returns:
            List of RoutingPrediction objects.
        """
        predictions = self.model.predict(texts)
        probabilities = self.model.predict_proba(texts)
        classes = self.model.classes_
        
        results = []
        for pred, probs in zip(predictions, probabilities):
            pred_idx = np.where(classes == pred)[0][0]
            confidence = float(probs[pred_idx])
            all_probs = {cls: float(p) for cls, p in zip(classes, probs)}
            
            results.append(RoutingPrediction(
                department=pred,
                confidence=confidence,
                all_probabilities=all_probs
            ))
        
        return results
    
    def get_top_k_departments(
        self, 
        text: str, 
        k: int = 3
    ) -> list:
        """Get top-k most likely departments.
        
        Args:
            text: Question text.
            k: Number of top predictions to return.
            
        Returns:
            List of (department, probability) tuples.
        """
        probabilities = self.model.predict_proba([text])[0]
        classes = self.model.classes_
        
        # Sort by probability
        sorted_indices = np.argsort(probabilities)[::-1]
        
        return [
            (classes[idx], float(probabilities[idx]))
            for idx in sorted_indices[:k]
        ]


@lru_cache()
def get_router() -> QuestionRouter:
    """Get cached router instance."""
    return QuestionRouter()


def create_fallback_router() -> QuestionRouter:
    """Create a router with a simple fallback if model doesn't exist.
    
    This trains a minimal model on-the-fly for development.
    """
    from ml.training import train_router_model
    
    model_path = settings.models_dir / "question_router.joblib"
    
    if not model_path.exists():
        logger.warning("No trained model found. Training a new model...")
        train_router_model(register_model=False)
    
    return QuestionRouter(model_path)

