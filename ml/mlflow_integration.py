"""MLflow integration for experiment tracking and model registry."""
import os
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient
from mlflow.models import infer_signature
import joblib
import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ModelMetrics:
    """Metrics for a trained model."""
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    per_class_metrics: Dict[str, Dict[str, float]]


@dataclass
class ModelInfo:
    """Information about a registered model."""
    name: str
    version: str
    stage: str
    run_id: str
    metrics: Dict[str, float]
    created_at: str
    description: str


class MLflowManager:
    """Manager for MLflow experiment tracking and model registry."""
    
    EXPERIMENT_NAME = "onboarding_routing_model"
    MODEL_NAME = "question_router"
    
    def __init__(
        self,
        tracking_uri: str = None,
        artifact_location: str = None
    ):
        """Initialize MLflow manager.
        
        Args:
            tracking_uri: MLflow tracking server URI.
            artifact_location: Path for storing artifacts.
        """
        self.tracking_uri = tracking_uri or f"file://{settings.mlflow_tracking_uri}"
        self.artifact_location = artifact_location or str(
            Path(settings.mlflow_tracking_uri) / "artifacts"
        )
        
        # Set up MLflow
        mlflow.set_tracking_uri(self.tracking_uri)
        
        # Create experiment if it doesn't exist
        self.experiment = self._get_or_create_experiment()
        
        self.client = MlflowClient()
        
        logger.info(f"MLflow initialized with tracking URI: {self.tracking_uri}")
    
    def _get_or_create_experiment(self) -> mlflow.entities.Experiment:
        """Get or create the experiment."""
        experiment = mlflow.get_experiment_by_name(self.EXPERIMENT_NAME)
        
        if experiment is None:
            experiment_id = mlflow.create_experiment(
                self.EXPERIMENT_NAME,
                artifact_location=self.artifact_location
            )
            experiment = mlflow.get_experiment(experiment_id)
            logger.info(f"Created experiment: {self.EXPERIMENT_NAME}")
        
        mlflow.set_experiment(self.EXPERIMENT_NAME)
        return experiment
    
    def start_run(
        self,
        run_name: str = None,
        tags: Dict[str, str] = None
    ) -> mlflow.ActiveRun:
        """Start a new MLflow run.
        
        Args:
            run_name: Name for the run.
            tags: Optional tags for the run.
            
        Returns:
            Active MLflow run.
        """
        if run_name is None:
            run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return mlflow.start_run(
            run_name=run_name,
            tags=tags or {}
        )
    
    def log_training_run(
        self,
        params: Dict[str, Any],
        metrics: ModelMetrics,
        model,
        vectorizer,
        training_data_info: Dict[str, Any] = None,
        run_name: str = None
    ) -> str:
        """Log a complete training run.
        
        Args:
            params: Training parameters.
            metrics: Model metrics.
            model: Trained model object.
            vectorizer: TF-IDF vectorizer.
            training_data_info: Information about training data.
            run_name: Optional run name.
            
        Returns:
            Run ID.
        """
        with self.start_run(run_name=run_name) as run:
            run_id = run.info.run_id
            
            # Log parameters
            for key, value in params.items():
                mlflow.log_param(key, value)
            
            # Log metrics
            mlflow.log_metric("accuracy", metrics.accuracy)
            mlflow.log_metric("precision_macro", metrics.precision_macro)
            mlflow.log_metric("recall_macro", metrics.recall_macro)
            mlflow.log_metric("f1_macro", metrics.f1_macro)
            
            # Log per-class metrics
            for class_name, class_metrics in metrics.per_class_metrics.items():
                for metric_name, value in class_metrics.items():
                    mlflow.log_metric(
                        f"{class_name}_{metric_name}",
                        value
                    )
            
            # Log training data info
            if training_data_info:
                mlflow.log_dict(
                    training_data_info,
                    "training_data_info.json"
                )
            
            # Save and log model artifacts
            model_artifact = {
                "model": model,
                "vectorizer": vectorizer,
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "params": params,
                    "metrics": {
                        "accuracy": metrics.accuracy,
                        "f1_macro": metrics.f1_macro
                    }
                }
            }
            
            # Log the model
            artifact_path = "routing_model"
            
            # Create a temporary file for the model
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                model_path = Path(tmpdir) / "model.joblib"
                joblib.dump(model_artifact, model_path)
                mlflow.log_artifact(str(model_path), artifact_path)
            
            # Log the model using sklearn flavor
            try:
                mlflow.sklearn.log_model(
                    model,
                    "sklearn_model",
                    registered_model_name=None  # Don't register yet
                )
            except Exception as e:
                logger.warning(f"Could not log sklearn model: {e}")
            
            logger.info(f"Logged training run: {run_id}")
            
            return run_id
    
    def register_model(
        self,
        run_id: str,
        stage: str = "Production",
        description: str = None
    ) -> ModelInfo:
        """Register a model from a run to the model registry.
        
        Args:
            run_id: Run ID to register model from.
            stage: Stage to transition to (Staging, Production, Archived).
            description: Model description.
            
        Returns:
            ModelInfo with registration details.
        """
        try:
            # Get the run
            run = self.client.get_run(run_id)
            artifact_uri = f"runs:/{run_id}/routing_model/model.joblib"
            
            # Check if model exists
            try:
                self.client.get_registered_model(self.MODEL_NAME)
            except mlflow.exceptions.RestException:
                # Create the model
                self.client.create_registered_model(
                    self.MODEL_NAME,
                    description="Question routing model for onboarding copilot"
                )
            
            # Create a new version
            model_version = self.client.create_model_version(
                name=self.MODEL_NAME,
                source=artifact_uri,
                run_id=run_id,
                description=description or f"Model from run {run_id}"
            )
            
            # Transition to the specified stage
            self.client.transition_model_version_stage(
                name=self.MODEL_NAME,
                version=model_version.version,
                stage=stage
            )
            
            # Get metrics from run
            metrics = run.data.metrics
            
            logger.info(
                f"Registered model {self.MODEL_NAME} version {model_version.version} "
                f"to stage {stage}"
            )
            
            return ModelInfo(
                name=self.MODEL_NAME,
                version=model_version.version,
                stage=stage,
                run_id=run_id,
                metrics=metrics,
                created_at=datetime.now().isoformat(),
                description=description or ""
            )
        
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            raise
    
    def get_production_model(self) -> Optional[Dict[str, Any]]:
        """Get the current production model.
        
        Returns:
            Model artifact dictionary or None.
        """
        try:
            # Get the latest production version
            versions = self.client.get_latest_versions(
                self.MODEL_NAME,
                stages=["Production"]
            )
            
            if not versions:
                logger.warning("No production model found")
                return None
            
            latest = versions[0]
            
            # Load the model artifact
            model_path = f"runs:/{latest.run_id}/routing_model/model.joblib"
            
            # Download and load
            local_path = mlflow.artifacts.download_artifacts(model_path)
            model_artifact = joblib.load(local_path)
            
            logger.info(
                f"Loaded production model version {latest.version} "
                f"from run {latest.run_id}"
            )
            
            return model_artifact
        
        except Exception as e:
            logger.error(f"Failed to load production model: {e}")
            return None
    
    def get_model_versions(self) -> List[ModelInfo]:
        """Get all versions of the model.
        
        Returns:
            List of ModelInfo objects.
        """
        try:
            versions = self.client.search_model_versions(
                f"name='{self.MODEL_NAME}'"
            )
            
            result = []
            for v in versions:
                run = self.client.get_run(v.run_id)
                result.append(ModelInfo(
                    name=v.name,
                    version=v.version,
                    stage=v.current_stage,
                    run_id=v.run_id,
                    metrics=run.data.metrics,
                    created_at=str(v.creation_timestamp),
                    description=v.description or ""
                ))
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to get model versions: {e}")
            return []
    
    def compare_runs(
        self,
        run_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Compare metrics across multiple runs.
        
        Args:
            run_ids: List of run IDs to compare.
            
        Returns:
            Dictionary with run comparisons.
        """
        comparison = {}
        
        for run_id in run_ids:
            try:
                run = self.client.get_run(run_id)
                comparison[run_id] = {
                    "params": run.data.params,
                    "metrics": run.data.metrics,
                    "status": run.info.status,
                    "start_time": run.info.start_time
                }
            except Exception as e:
                logger.warning(f"Could not get run {run_id}: {e}")
        
        return comparison
    
    def get_experiment_history(
        self,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent experiment runs.
        
        Args:
            max_results: Maximum number of runs to return.
            
        Returns:
            List of run information dictionaries.
        """
        runs = self.client.search_runs(
            experiment_ids=[self.experiment.experiment_id],
            max_results=max_results,
            order_by=["start_time DESC"]
        )
        
        return [
            {
                "run_id": run.info.run_id,
                "run_name": run.info.run_name,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "metrics": run.data.metrics,
                "params": run.data.params
            }
            for run in runs
        ]


# Global MLflow manager instance
_mlflow_manager: Optional[MLflowManager] = None


def get_mlflow_manager() -> MLflowManager:
    """Get the global MLflow manager instance."""
    global _mlflow_manager
    if _mlflow_manager is None:
        _mlflow_manager = MLflowManager()
    return _mlflow_manager

