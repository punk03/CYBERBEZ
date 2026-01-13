"""XML log parser."""

import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional

from backend.ingestion.parsers.base import BaseParser
from backend.common.logging import get_logger

logger = get_logger(__name__)


class XMLParser(BaseParser):
    """Parser for XML formatted logs."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize XML parser."""
        super().__init__("xml", config)
    
    def can_parse(self, raw_log: str) -> bool:
        """Check if log is valid XML."""
        try:
            ET.fromstring(raw_log)
            return True
        except ET.ParseError:
            return False
    
    def _xml_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if result:
                result["_text"] = element.text.strip()
            else:
                result["text"] = element.text.strip()
        
        # Add children
        children = {}
        for child in element:
            child_dict = self._xml_to_dict(child)
            child_tag = child.tag
            
            # Handle multiple children with same tag
            if child_tag in children:
                if not isinstance(children[child_tag], list):
                    children[child_tag] = [children[child_tag]]
                children[child_tag].append(child_dict)
            else:
                children[child_tag] = child_dict
        
        if children:
            result.update(children)
        
        return result
    
    def parse(self, raw_log: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Parse XML log entry."""
        try:
            root = ET.fromstring(raw_log)
            parsed = self._xml_to_dict(root)
            
            # Merge with metadata
            if metadata:
                parsed.update(metadata)
            
            return parsed
        except ET.ParseError as e:
            logger.warning(f"Failed to parse XML log: {e}")
            return None
