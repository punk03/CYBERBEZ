"""Unit tests for log parsers."""

import pytest
from backend.ingestion.parsers.json_parser import JSONParser
from backend.ingestion.parsers.csv_parser import CSVParser
from backend.ingestion.parsers.xml_parser import XMLParser
from backend.ingestion.parsers.syslog_parser import SyslogParser


class TestJSONParser:
    """Tests for JSON parser."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        parser = JSONParser()
        log = '{"message": "test", "level": "INFO"}'
        result = parser.parse(log)
        assert result is not None
        assert result["message"] == "test"
        assert result["level"] == "INFO"
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        parser = JSONParser()
        log = "not json"
        result = parser.parse(log)
        assert result is None


class TestCSVParser:
    """Tests for CSV parser."""
    
    def test_parse_csv(self):
        """Test parsing CSV."""
        parser = CSVParser()
        log = "timestamp,level,message\n2024-01-01,INFO,test"
        result = parser.parse(log)
        assert result is not None


class TestXMLParser:
    """Tests for XML parser."""
    
    def test_parse_xml(self):
        """Test parsing XML."""
        parser = XMLParser()
        log = "<log><message>test</message><level>INFO</level></log>"
        result = parser.parse(log)
        assert result is not None


class TestSyslogParser:
    """Tests for syslog parser."""
    
    def test_parse_rfc3164(self):
        """Test parsing RFC 3164 syslog."""
        parser = SyslogParser()
        log = "<34>Oct 11 22:14:15 test-host test-app: test message"
        result = parser.parse(log)
        assert result is not None
        assert result.get("format") == "RFC3164"
