"""Real-time ML inference predictor."""

from typing import Dict, Any, Optional

from backend.ml.features.extractor import FeatureExtractor
from backend.ml.models.ensemble import EnsembleModel
from backend.common.logging import get_logger

logger = get_logger(__name__)


class MLPredictor:
    """ML predictor for real-time inference."""
    
    def __init__(self, ensemble_model: Optional[EnsembleModel] = None):
        """
        Initialize ML predictor.
        
        Args:
            ensemble_model: Ensemble model instance
        """
        self.feature_extractor = FeatureExtractor()
        self.ensemble_model = ensemble_model
    
    def set_ensemble_model(self, ensemble_model: EnsembleModel) -> None:
        """Set ensemble model."""
        self.ensemble_model = ensemble_model
        logger.info("Ensemble model set for ML predictor")
    
    async def predict(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict threat for log entry.
        
        Args:
            log_entry: Log entry dictionary
        
        Returns:
            Prediction result dictionary
        """
        if not self.ensemble_model or not self.ensemble_model.is_ready():
            # Return default prediction if model not ready
            return {
                "is_threat": False,
                "is_anomaly": False,
                "is_attack": False,
                "attack_type": "normal",
                "confidence": 0.0,
                "model_ready": False,
            }
        
        try:
            # Extract features
            features = self.feature_extractor.extract(log_entry)
            
            # Predict using ensemble model
            prediction = self.ensemble_model.predict(features)
            
            # Add metadata
            prediction["model_ready"] = True
            prediction["features_extracted"] = len(features)
            
            logger.debug(
                f"ML prediction: threat={prediction['is_threat']}, "
                f"type={prediction['attack_type']}, "
                f"confidence={prediction['confidence']:.2f}"
            )
            
            return prediction
        
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}", exc_info=True)
            return {
                "is_threat": False,
                "is_anomaly": False,
                "is_attack": False,
                "attack_type": "unknown",
                "confidence": 0.0,
                "error": str(e),
                "model_ready": True,
            }
