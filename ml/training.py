"""Training script for the question routing model."""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
from sklearn.pipeline import Pipeline
import joblib
import mlflow
import mlflow.sklearn

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def load_dataset(dataset_path: Path = None) -> pd.DataFrame:
    """Load the routing dataset.
    
    Args:
        dataset_path: Path to the dataset JSON file.
        
    Returns:
        DataFrame with text and label columns.
    """
    if dataset_path is None:
        dataset_path = settings.data_dir / "routing_dataset.json"
    
    with open(dataset_path, "r") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data["data"])
    logger.info(f"Loaded {len(df)} samples from {dataset_path}")
    logger.info(f"Label distribution:\n{df['label'].value_counts()}")
    
    return df


def create_pipeline(
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (1, 2),
    C: float = 1.0,
    max_iter: int = 1000
) -> Pipeline:
    """Create the training pipeline.
    
    Args:
        max_features: Maximum number of TF-IDF features.
        ngram_range: N-gram range for TF-IDF.
        C: Regularization parameter for LogisticRegression.
        max_iter: Maximum iterations for LogisticRegression.
        
    Returns:
        Sklearn Pipeline.
    """
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            stop_words='english',
            lowercase=True,
            strip_accents='unicode'
        )),
        ('classifier', LogisticRegression(
            C=C,
            max_iter=max_iter,
            class_weight='balanced',
            multi_class='multinomial',
            solver='lbfgs',
            random_state=42
        ))
    ])
    
    return pipeline


def evaluate_model(
    model: Pipeline,
    X_test: np.ndarray,
    y_test: np.ndarray,
    labels: list
) -> Dict[str, Any]:
    """Evaluate the model and return metrics.
    
    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test labels.
        labels: List of class labels.
        
    Returns:
        Dictionary of metrics.
    """
    y_pred = model.predict(X_test)
    
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision_macro": precision_score(y_test, y_pred, average='macro', zero_division=0),
        "recall_macro": recall_score(y_test, y_pred, average='macro', zero_division=0),
        "f1_macro": f1_score(y_test, y_pred, average='macro', zero_division=0),
        "precision_weighted": precision_score(y_test, y_pred, average='weighted', zero_division=0),
        "recall_weighted": recall_score(y_test, y_pred, average='weighted', zero_division=0),
        "f1_weighted": f1_score(y_test, y_pred, average='weighted', zero_division=0)
    }
    
    # Per-class metrics
    for label in labels:
        mask = y_test == label
        if mask.any():
            label_pred = y_pred[mask]
            label_true = y_test[mask]
            metrics[f"accuracy_{label}"] = accuracy_score(label_true, label_pred)
    
    # Log classification report
    report = classification_report(y_test, y_pred, target_names=labels)
    logger.info(f"\nClassification Report:\n{report}")
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    logger.info(f"\nConfusion Matrix:\n{cm}")
    
    return metrics


def train_router_model(
    max_features: int = 5000,
    ngram_range: Tuple[int, int] = (1, 2),
    C: float = 1.0,
    max_iter: int = 1000,
    test_size: float = 0.2,
    register_model: bool = True,
    model_name: str = "question_router"
) -> Dict[str, Any]:
    """Train the question routing model.
    
    Args:
        max_features: Maximum TF-IDF features.
        ngram_range: N-gram range.
        C: LogisticRegression regularization.
        max_iter: Maximum iterations.
        test_size: Test split ratio.
        register_model: Whether to register model in MLflow.
        model_name: Name for the registered model.
        
    Returns:
        Dictionary with training results.
    """
    # Set up MLflow
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)
    
    # Load data
    df = load_dataset()
    X = df['text'].values
    y = df['label'].values
    labels = sorted(df['label'].unique().tolist())
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    logger.info(f"Training set size: {len(X_train)}")
    logger.info(f"Test set size: {len(X_test)}")
    
    with mlflow.start_run() as run:
        # Log parameters
        params = {
            "max_features": max_features,
            "ngram_range": str(ngram_range),
            "C": C,
            "max_iter": max_iter,
            "test_size": test_size,
            "train_size": len(X_train),
            "test_samples": len(X_test),
            "num_classes": len(labels)
        }
        mlflow.log_params(params)
        
        # Create and train pipeline
        logger.info("Training model...")
        pipeline = create_pipeline(
            max_features=max_features,
            ngram_range=ngram_range,
            C=C,
            max_iter=max_iter
        )
        pipeline.fit(X_train, y_train)
        
        # Evaluate
        logger.info("Evaluating model...")
        metrics = evaluate_model(pipeline, X_test, y_test, labels)
        
        # Log metrics
        mlflow.log_metrics(metrics)
        
        # Log model
        mlflow.sklearn.log_model(
            pipeline,
            "model",
            registered_model_name=model_name if register_model else None
        )
        
        # Save model locally as well
        model_path = settings.models_dir / f"{model_name}.joblib"
        joblib.dump(pipeline, model_path)
        logger.info(f"Model saved to {model_path}")
        
        # Save label mapping
        label_mapping = {i: label for i, label in enumerate(labels)}
        label_path = settings.models_dir / f"{model_name}_labels.json"
        with open(label_path, "w") as f:
            json.dump(label_mapping, f)
        
        mlflow.log_artifact(str(label_path))
        
        results = {
            "run_id": run.info.run_id,
            "model_path": str(model_path),
            "metrics": metrics,
            "labels": labels
        }
        
        logger.info(f"\nTraining complete!")
        logger.info(f"Run ID: {run.info.run_id}")
        logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"F1 Macro: {metrics['f1_macro']:.4f}")
        
        return results


def main():
    """Main training function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train question routing model")
    parser.add_argument("--max-features", type=int, default=5000)
    parser.add_argument("--ngram-min", type=int, default=1)
    parser.add_argument("--ngram-max", type=int, default=2)
    parser.add_argument("--C", type=float, default=1.0)
    parser.add_argument("--max-iter", type=int, default=1000)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--no-register", action="store_true")
    
    args = parser.parse_args()
    
    results = train_router_model(
        max_features=args.max_features,
        ngram_range=(args.ngram_min, args.ngram_max),
        C=args.C,
        max_iter=args.max_iter,
        test_size=args.test_size,
        register_model=not args.no_register
    )
    
    print("\n" + "="*50)
    print("Training Results")
    print("="*50)
    print(f"Accuracy: {results['metrics']['accuracy']:.4f}")
    print(f"F1 Macro: {results['metrics']['f1_macro']:.4f}")
    print(f"Model saved to: {results['model_path']}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()

