"""Unit tests for feature extraction."""

import pytest
from backend.ml.features.extractor import FeatureExtractor
from datetime import datetime


class TestFeatureExtractor:
    """Tests for feature extractor."""
    
    def test_extract_features(self, sample_log_entry):
        """Test feature extraction."""
        extractor = FeatureExtractor()
        features = extractor.extract(sample_log_entry)
        
        assert isinstance(features, dict)
        assert "message_length" in features
        assert "hour" in features
        assert "has_ip" in features
    
    def test_get_feature_names(self):
        """Test getting feature names."""
        extractor = FeatureExtractor()
        names = extractor.get_feature_names()
        assert isinstance(names, list)
        assert len(names) > 0
