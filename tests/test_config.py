"""
Unit tests for the configuration module.
"""

import os
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock

from src.config import Config
from src.error_handler import ConfigError, ValidationError

class TestConfig(unittest.TestCase):
    """Tests for the configuration module."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a valid test config
        self.valid_config = {
            "user_agent": "TestAgent/1.0",
            "request_delay": 1.0,
            "max_pages": 10,
            "max_depth": 2,
            "document_types": ["html", "pdf"],
            "headers": {"Accept": "text/html"},
            "sources": [
                {
                    "name": "test_source",
                    "url": "https://example.com",
                    "selectors": {
                        "content": "div.content",
                        "links": "a.link"
                    }
                }
            ]
        }
    
    def test_init_valid_config(self):
        """Test initialization with valid config."""
        config = Config(self.valid_config)
        self.assertEqual(config.config_data, self.valid_config)
    
    def test_init_invalid_config(self):
        """Test initialization with invalid config."""
        # Test missing required keys
        invalid_config = {
            "user_agent": "TestAgent/1.0",
            # Missing request_delay
            "max_pages": 10,
            "max_depth": 2,
            "sources": []
        }
        
        with self.assertRaises(ConfigError) as context:
            Config(invalid_config)
        
        self.assertIn("Required configuration key missing", str(context.exception))
        
        # Test invalid request delay
        invalid_config = dict(self.valid_config)
        invalid_config["request_delay"] = 0.1  # Too low
        
        with self.assertRaises(ConfigError) as context:
            Config(invalid_config)
        
        self.assertIn("Request delay must be a number", str(context.exception))
        
        # Test invalid sources
        invalid_config = dict(self.valid_config)
        invalid_config["sources"] = []  # Empty sources
        
        with self.assertRaises(ConfigError) as context:
            Config(invalid_config)
        
        self.assertIn("sources must be a non-empty list", str(context.exception))
        
        # Test invalid source URL
        invalid_config = dict(self.valid_config)
        invalid_config["sources"] = [
            {
                "name": "test_source",
                "url": "invalid-url"  # Invalid URL
            }
        ]
        
        with self.assertRaises(ConfigError) as context:
            Config(invalid_config)
        
        self.assertIn("Invalid URL in source", str(context.exception))
    
    def test_from_file_valid(self):
        """Test loading config from a valid file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(self.valid_config, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Load config from file
            config = Config.from_file(temp_file_path)
            self.assertEqual(config.config_data, self.valid_config)
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_from_file_not_found(self):
        """Test loading config from a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            Config.from_file("/nonexistent/path/config.json")
    
    def test_from_file_invalid_json(self):
        """Test loading config from an invalid JSON file."""
        # Create a temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write("This is not valid JSON")
            temp_file_path = temp_file.name
        
        try:
            # Try to load config from file
            with self.assertRaises(ConfigError) as context:
                Config.from_file(temp_file_path)
            
            self.assertIn("Invalid JSON in configuration file", str(context.exception))
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_getter_methods(self):
        """Test getter methods."""
        config = Config(self.valid_config)
        
        # Test get method
        self.assertEqual(config.get("user_agent"), "TestAgent/1.0")
        self.assertEqual(config.get("nonexistent_key", "default"), "default")
        
        # Test specific getters
        self.assertEqual(config.get_user_agent(), "TestAgent/1.0")
        self.assertEqual(config.get_request_delay(), 1.0)
        self.assertEqual(config.get_max_pages(), 10)
        self.assertEqual(config.get_max_depth(), 2)
        self.assertEqual(config.get_document_types(), ["html", "pdf"])
        
        # Test get_headers
        expected_headers = {
            "User-Agent": "TestAgent/1.0",
            "Accept": "text/html"
        }
        self.assertEqual(config.get_headers(), expected_headers)
        
        # Test get_sources
        self.assertEqual(config.get_sources(), self.valid_config["sources"])
    
    def test_is_valid_url(self):
        """Test URL validation."""
        config = Config(self.valid_config)
        
        # Test valid URLs
        self.assertTrue(config._is_valid_url("https://example.com"))
        self.assertTrue(config._is_valid_url("http://example.co.uk/path?query=1"))
        
        # Test invalid URLs
        self.assertFalse(config._is_valid_url("ftp://example.com"))
        self.assertFalse(config._is_valid_url("example.com"))
        self.assertFalse(config._is_valid_url(""))
        self.assertFalse(config._is_valid_url(None))


if __name__ == "__main__":
    unittest.main()
