"""Ensemble model for combining multiple ML models."""

from typing import Dict, Any, List, Optional

from backend.ml.models.anomaly_detector import AnomalyDetector
from backend.ml.models.attack_classifier import AttackClassifier
from backend.common.logging import get_logger

logger = get_logger(__name__)


class EnsembleModel:
    """Ensemble model combining anomaly detection and attack classification."""
    
    def __init__(
        self,
        anomaly_detector: Optional[AnomalyDetector] = None,
        attack_classifier: Optional[AttackClassifier] = None,
        anomaly_weight: float = 0.5,
        classification_weight: float = 0.5
    ):
        """
        Initialize ensemble model.
        
        Args:
            anomaly_detector: Anomaly detection model
            attack_classifier: Attack classification model
            anomaly_weight: Weight for anomaly detection (0-1)
            classification_weight: Weight for attack classification (0-1)
        """
        self.anomaly_detector = anomaly_detector
        self.attack_classifier = attack_classifier
        self.anomaly_weight = anomaly_weight
        self.classification_weight = classification_weight
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict using ensemble model.
        
        Args:
            features: Feature dictionary
        
        Returns:
            Combined prediction dictionary
        """
        results = {
            "is_anomaly": False,
            "is_attack": False,
            "attack_type": "normal",
            "confidence": 0.0,
            "anomaly_score": 0.0,
            "anomaly_prediction": None,
            "classification_prediction": None,
        }
        
        # Anomaly detection
        if self.anomaly_detector and self.anomaly_detector.is_trained:
            try:
                anomaly_result = self.anomaly_detector.predict(features)
                results["is_anomaly"] = anomaly_result["is_anomaly"]
                results["anomaly_score"] = anomaly_result["anomaly_score"]
                results["anomaly_prediction"] = anomaly_result
            except Exception as e:
                logger.warning(f"Error in anomaly detection: {e}")
        
        # Attack classification
        if self.attack_classifier and self.attack_classifier.is_trained:
            try:
                classification_result = self.attack_classifier.predict(features)
                attack_type = classification_result["attack_type"]
                confidence = classification_result["confidence"]
                
                results["attack_type"] = attack_type
                results["confidence"] = confidence
                results["classification_prediction"] = classification_result
                
                # Consider it an attack if not "normal" and confidence is high
                if attack_type != "normal" and confidence > 0.5:
                    results["is_attack"] = True
            except Exception as e:
                logger.warning(f"Error in attack classification: {e}")
        
        # Combined decision
        # If anomaly detected OR attack classified, mark as threat
        if results["is_anomaly"] or results["is_attack"]:
            results["is_threat"] = True
        else:
            results["is_threat"] = False
        
        # Calculate combined confidence score
        anomaly_confidence = abs(results["anomaly_score"]) / 10.0 if results["anomaly_score"] != 0 else 0.0
        classification_confidence = results["confidence"]
        
        results["combined_confidence"] = (
            anomaly_confidence * self.anomaly_weight +
            classification_confidence * self.classification_weight
        )
        
        return results
    
    def is_ready(self) -> bool:
        """Check if ensemble model is ready for prediction."""
        anomaly_ready = self.anomaly_detector is None or self.anomaly_detector.is_trained
        classification_ready = self.attack_classifier is None or self.attack_classifier.is_trained
        return anomaly_ready and classification_ready
