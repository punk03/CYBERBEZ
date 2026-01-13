"""Anomaly detection models."""

import pickle
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from backend.common.logging import get_logger

logger = get_logger(__name__)


class AnomalyDetector:
    """Anomaly detection using Isolation Forest."""
    
    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        random_state: int = 42
    ):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies
            n_estimators: Number of trees in the forest
            random_state: Random state for reproducibility
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: Optional[List[str]] = None
        self.is_trained = False
    
    def train(self, features: List[Dict[str, float]], feature_names: List[str]) -> None:
        """
        Train anomaly detection model.
        
        Args:
            features: List of feature dictionaries
            feature_names: List of feature names
        """
        try:
            # Convert to numpy array
            X = np.array([[f.get(name, 0.0) for name in feature_names] for f in features])
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.model = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                n_jobs=-1
            )
            self.model.fit(X_scaled)
            
            self.feature_names = feature_names
            self.is_trained = True
            
            logger.info(f"Anomaly detector trained on {len(features)} samples")
        
        except Exception as e:
            logger.error(f"Error training anomaly detector: {e}", exc_info=True)
            raise
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict if log entry is an anomaly.
        
        Args:
            features: Feature dictionary
        
        Returns:
            Prediction dictionary with anomaly score and label
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        try:
            # Convert to numpy array
            X = np.array([[features.get(name, 0.0) for name in self.feature_names]])
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction = self.model.predict(X_scaled)[0]
            score = self.model.score_samples(X_scaled)[0]
            
            # Convert prediction: -1 = anomaly, 1 = normal
            is_anomaly = prediction == -1
            anomaly_score = -score  # Negative because lower scores indicate anomalies
            
            return {
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": float(anomaly_score),
                "prediction": int(prediction),
            }
        
        except Exception as e:
            logger.error(f"Error predicting anomaly: {e}", exc_info=True)
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "prediction": 1,
            }
    
    def save(self, filepath: str) -> None:
        """Save model to file."""
        try:
            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "feature_names": self.feature_names,
                "contamination": self.contamination,
                "n_estimators": self.n_estimators,
            }
            with open(filepath, "wb") as f:
                pickle.dump(model_data, f)
            logger.info(f"Anomaly detector saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving anomaly detector: {e}", exc_info=True)
            raise
    
    def load(self, filepath: str) -> None:
        """Load model from file."""
        try:
            with open(filepath, "rb") as f:
                model_data = pickle.load(f)
            
            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.feature_names = model_data["feature_names"]
            self.contamination = model_data.get("contamination", 0.1)
            self.n_estimators = model_data.get("n_estimators", 100)
            self.is_trained = True
            
            logger.info(f"Anomaly detector loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading anomaly detector: {e}", exc_info=True)
            raise
