"""Attack classification models."""

import pickle
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report

from backend.common.logging import get_logger

logger = get_logger(__name__)


class AttackClassifier:
    """Attack classifier using Random Forest."""
    
    # Attack types
    ATTACK_TYPES = [
        "normal",
        "ddos",
        "malware",
        "scada_attack",
        "insider_threat",
        "network_intrusion",
        "apt",
        "ransomware",
        "phishing",
        "other",
    ]
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        random_state: int = 42
    ):
        """
        Initialize attack classifier.
        
        Args:
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of trees
            random_state: Random state for reproducibility
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.feature_names: Optional[List[str]] = None
        self.is_trained = False
    
    def train(
        self,
        features: List[Dict[str, float]],
        labels: List[str],
        feature_names: List[str]
    ) -> Dict[str, Any]:
        """
        Train attack classifier.
        
        Args:
            features: List of feature dictionaries
            labels: List of attack type labels
            feature_names: List of feature names
        
        Returns:
            Training metrics
        """
        try:
            # Convert to numpy array
            X = np.array([[f.get(name, 0.0) for name in feature_names] for f in features])
            y = np.array(labels)
            
            # Encode labels
            self.label_encoder = LabelEncoder()
            y_encoded = self.label_encoder.fit_transform(y)
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Random Forest
            self.model = RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                random_state=self.random_state,
                n_jobs=-1,
                class_weight="balanced"  # Handle imbalanced classes
            )
            self.model.fit(X_scaled, y_encoded)
            
            self.feature_names = feature_names
            self.is_trained = True
            
            # Calculate training metrics
            y_pred = self.model.predict(X_scaled)
            report = classification_report(
                y_encoded,
                y_pred,
                target_names=self.label_encoder.classes_,
                output_dict=True
            )
            
            logger.info(f"Attack classifier trained on {len(features)} samples")
            logger.info(f"Training accuracy: {report['accuracy']:.4f}")
            
            return {
                "accuracy": report["accuracy"],
                "report": report,
            }
        
        except Exception as e:
            logger.error(f"Error training attack classifier: {e}", exc_info=True)
            raise
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict attack type.
        
        Args:
            features: Feature dictionary
        
        Returns:
            Prediction dictionary with attack type and probabilities
        """
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        try:
            # Convert to numpy array
            X = np.array([[features.get(name, 0.0) for name in self.feature_names]])
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict
            prediction_encoded = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            # Decode prediction
            attack_type = self.label_encoder.inverse_transform([prediction_encoded])[0]
            
            # Get probabilities for all classes
            class_probs = {
                self.label_encoder.classes_[i]: float(prob)
                for i, prob in enumerate(probabilities)
            }
            
            return {
                "attack_type": attack_type,
                "confidence": float(max(probabilities)),
                "probabilities": class_probs,
            }
        
        except Exception as e:
            logger.error(f"Error predicting attack type: {e}", exc_info=True)
            return {
                "attack_type": "unknown",
                "confidence": 0.0,
                "probabilities": {},
            }
    
    def save(self, filepath: str) -> None:
        """Save model to file."""
        try:
            model_data = {
                "model": self.model,
                "scaler": self.scaler,
                "label_encoder": self.label_encoder,
                "feature_names": self.feature_names,
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
            }
            with open(filepath, "wb") as f:
                pickle.dump(model_data, f)
            logger.info(f"Attack classifier saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving attack classifier: {e}", exc_info=True)
            raise
    
    def load(self, filepath: str) -> None:
        """Load model from file."""
        try:
            with open(filepath, "rb") as f:
                model_data = pickle.load(f)
            
            self.model = model_data["model"]
            self.scaler = model_data["scaler"]
            self.label_encoder = model_data["label_encoder"]
            self.feature_names = model_data["feature_names"]
            self.n_estimators = model_data.get("n_estimators", 100)
            self.max_depth = model_data.get("max_depth", None)
            self.is_trained = True
            
            logger.info(f"Attack classifier loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading attack classifier: {e}", exc_info=True)
            raise
