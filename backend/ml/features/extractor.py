"""Feature extractor for log entries."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from backend.common.logging import get_logger

logger = get_logger(__name__)


class FeatureExtractor:
    """Extract features from log entries for ML models."""
    
    def __init__(self):
        """Initialize feature extractor."""
        pass
    
    def extract(self, log_entry: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract features from log entry.
        
        Args:
            log_entry: Log entry dictionary
        
        Returns:
            Dictionary of feature names and values
        """
        features = {}
        
        # Statistical features
        features.update(self._extract_statistical_features(log_entry))
        
        # Temporal features
        features.update(self._extract_temporal_features(log_entry))
        
        # Network features
        features.update(self._extract_network_features(log_entry))
        
        # Text features
        features.update(self._extract_text_features(log_entry))
        
        return features
    
    def _extract_statistical_features(self, log_entry: Dict[str, Any]) -> Dict[str, float]:
        """Extract statistical features."""
        features = {}
        
        # Message length
        message = str(log_entry.get("message", ""))
        features["message_length"] = float(len(message))
        features["message_word_count"] = float(len(message.split()))
        
        # Metadata counts
        metadata = log_entry.get("metadata", {})
        features["metadata_count"] = float(len(metadata))
        
        # Number of fields
        features["field_count"] = float(len(log_entry))
        
        return features
    
    def _extract_temporal_features(self, log_entry: Dict[str, Any]) -> Dict[str, float]:
        """Extract temporal features."""
        features = {}
        
        try:
            timestamp = log_entry.get("timestamp", datetime.utcnow().isoformat())
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                dt = timestamp
            
            # Hour of day (0-23)
            features["hour"] = float(dt.hour)
            
            # Day of week (0-6, Monday=0)
            features["day_of_week"] = float(dt.weekday())
            
            # Day of month (1-31)
            features["day_of_month"] = float(dt.day)
            
            # Month (1-12)
            features["month"] = float(dt.month)
            
            # Is weekend
            features["is_weekend"] = 1.0 if dt.weekday() >= 5 else 0.0
            
            # Is business hours (9-17)
            features["is_business_hours"] = 1.0 if 9 <= dt.hour <= 17 else 0.0
        
        except Exception as e:
            logger.warning(f"Error extracting temporal features: {e}")
            # Set default values
            features["hour"] = 12.0
            features["day_of_week"] = 0.0
            features["day_of_month"] = 1.0
            features["month"] = 1.0
            features["is_weekend"] = 0.0
            features["is_business_hours"] = 1.0
        
        return features
    
    def _extract_network_features(self, log_entry: Dict[str, Any]) -> Dict[str, float]:
        """Extract network-related features."""
        features = {}
        
        # IP address features
        ip_fields = ["ip", "ip_address", "src_ip", "dst_ip", "client_ip", "remote_addr"]
        has_ip = False
        ip_value = None
        
        for field in ip_fields:
            if field in log_entry:
                ip_value = log_entry[field]
                has_ip = True
                break
        
        features["has_ip"] = 1.0 if has_ip else 0.0
        
        if has_ip and ip_value:
            # Check if private IP
            try:
                import ipaddress
                ip_obj = ipaddress.ip_address(str(ip_value))
                features["is_private_ip"] = 1.0 if ip_obj.is_private else 0.0
                features["is_multicast_ip"] = 1.0 if ip_obj.is_multicast else 0.0
                features["is_reserved_ip"] = 1.0 if ip_obj.is_reserved else 0.0
            except Exception:
                features["is_private_ip"] = 0.0
                features["is_multicast_ip"] = 0.0
                features["is_reserved_ip"] = 0.0
        
        # Port features
        port_fields = ["port", "src_port", "dst_port"]
        has_port = False
        port_value = None
        
        for field in port_fields:
            if field in log_entry:
                port_value = log_entry[field]
                has_port = True
                break
        
        features["has_port"] = 1.0 if has_port else 0.0
        
        if has_port and port_value:
            try:
                port_num = int(port_value)
                features["port"] = float(port_num)
                # Common port categories
                features["is_well_known_port"] = 1.0 if port_num < 1024 else 0.0
                features["is_http_port"] = 1.0 if port_num in [80, 443, 8080, 8443] else 0.0
                features["is_ssh_port"] = 1.0 if port_num == 22 else 0.0
            except (ValueError, TypeError):
                features["port"] = 0.0
                features["is_well_known_port"] = 0.0
                features["is_http_port"] = 0.0
                features["is_ssh_port"] = 0.0
        
        # Protocol features
        protocol = log_entry.get("protocol", "").upper()
        features["has_protocol"] = 1.0 if protocol else 0.0
        features["is_tcp"] = 1.0 if "TCP" in protocol else 0.0
        features["is_udp"] = 1.0 if "UDP" in protocol else 0.0
        features["is_http"] = 1.0 if "HTTP" in protocol else 0.0
        features["is_https"] = 1.0 if "HTTPS" in protocol else 0.0
        
        # GeoIP features
        geoip = log_entry.get("geoip", {})
        features["has_geoip"] = 1.0 if geoip else 0.0
        features["is_private_geoip"] = 1.0 if geoip.get("type") == "private" else 0.0
        
        # Threat intel features
        threat_intel = log_entry.get("threat_intel", {})
        features["has_threat_intel"] = 1.0 if threat_intel else 0.0
        features["is_malicious"] = 1.0 if threat_intel.get("is_malicious") else 0.0
        features["is_suspicious"] = 1.0 if threat_intel.get("is_suspicious") else 0.0
        features["threat_confidence"] = float(threat_intel.get("confidence", 0))
        
        return features
    
    def _extract_text_features(self, log_entry: Dict[str, Any]) -> Dict[str, float]:
        """Extract text-based features."""
        features = {}
        
        message = str(log_entry.get("message", "")).lower()
        
        # Common attack patterns in text
        attack_patterns = {
            "sql_injection": ["union select", "drop table", "1=1", "or 1=1"],
            "xss": ["<script", "javascript:", "onerror="],
            "path_traversal": ["../", "..\\", "/etc/passwd"],
            "command_injection": [";", "|", "&&", "`"],
            "brute_force": ["failed", "invalid", "unauthorized", "denied"],
        }
        
        for pattern_name, patterns in attack_patterns.items():
            count = sum(1 for pattern in patterns if pattern in message)
            features[f"has_{pattern_name}"] = 1.0 if count > 0 else 0.0
            features[f"{pattern_name}_count"] = float(count)
        
        # Special characters
        features["has_special_chars"] = 1.0 if re.search(r'[!@#$%^&*(),.?":{}|<>]', message) else 0.0
        features["has_numbers"] = 1.0 if re.search(r'\d', message) else 0.0
        features["has_uppercase"] = 1.0 if re.search(r'[A-Z]', message) else 0.0
        
        # URL patterns
        features["has_url"] = 1.0 if re.search(r'https?://', message) else 0.0
        features["has_email"] = 1.0 if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message) else 0.0
        
        # Log level encoding
        level = log_entry.get("level", "INFO").upper()
        level_map = {
            "DEBUG": 0.0,
            "INFO": 1.0,
            "WARNING": 2.0,
            "WARN": 2.0,
            "ERROR": 3.0,
            "CRITICAL": 4.0,
            "FATAL": 4.0,
        }
        features["log_level"] = level_map.get(level, 1.0)
        
        return features
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names."""
        # Create a dummy entry to extract feature names
        dummy_entry = {
            "message": "test",
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "source": "test",
        }
        features = self.extract(dummy_entry)
        return list(features.keys())
