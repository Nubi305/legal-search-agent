"""
Unit tests for the error handler module.
"""

import unittest
import logging
from unittest.mock import patch, MagicMock

from src.error_handler import (
    LegalSearchError, ConfigError, CrawlerError, ProcessorError,
    IndexerError, SearchError, APIError, ValidationError,
    setup_logger, safe_execute, validate_input
)

class TestErrorHandler(unittest.TestCase):
    """Tests for the error handler module."""
    
    def test_error_classes(self):
        """Test error class inheritance."""
        # Test base error
        err = LegalSearchError("Test error")
        self.assertEqual(str(err), "Test error")
        self.assertEqual(err.message, "Test error")
        self.assertEqual(err.details, {})
        
        # Test error with details
        details = {"key": "value"}
        err = LegalSearchError("Test error with details", details)
        self.assertEqual(err.message, "Test error with details")
        self.assertEqual(err.details, details)
        
        # Test subclass errors
        self.assertTrue(issubclass(ConfigError, LegalSearchError))
        self.assertTrue(issubclass(CrawlerError, LegalSearchError))
        self.assertTrue(issubclass(ProcessorError, LegalSearchError))
        self.assertTrue(issubclass(IndexerError, LegalSearchError))
        self.assertTrue(issubclass(SearchError, LegalSearchError))
        self.assertTrue(issubclass(APIError, LegalSearchError))
        self.assertTrue(issubclass(ValidationError, LegalSearchError))
    
    def test_setup_logger(self):
        """Test logger setup."""
        # Test with console handler only
        logger = setup_logger("test_logger")
        self.assertEqual(logger.name, "test_logger")
        self.assertEqual(logger.level, logging.INFO)
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)
        
        # Test with file handler
        with patch("logging.FileHandler") as mock_file_handler:
            mock_file_handler.return_value = MagicMock()
            logger = setup_logger("test_file_logger", "test.log", logging.DEBUG)
            self.assertEqual(logger.name, "test_file_logger")
            self.assertEqual(logger.level, logging.DEBUG)
            self.assertEqual(len(logger.handlers), 2)
            mock_file_handler.assert_called_once_with("test.log")
    
    def test_safe_execute(self):
        """Test safe execution wrapper."""
        # Test successful execution
        def success_func(a, b):
            return a + b
        
        logger = MagicMock()
        result = safe_execute(
            func=success_func,
            error_message="Error adding numbers",
            logger=logger,
            a=1,
            b=2
        )
        self.assertEqual(result, 3)
        logger.log.assert_not_called()
        
        # Test failed execution with default return
        def fail_func():
            raise ValueError("Test error")
        
        result = safe_execute(
            func=fail_func,
            error_message="Error in function",
            logger=logger,
            default_return="default"
        )
        self.assertEqual(result, "default")
        logger.log.assert_called_once()
        
        # Test failed execution with raised error
        logger.reset_mock()
        with self.assertRaises(ConfigError):
            safe_execute(
                func=fail_func,
                error_message="Error in function",
                logger=logger,
                error_class=ConfigError,
                raise_error=True
            )
        logger.log.assert_called_once()
    
    def test_validate_input(self):
        """Test input validation."""
        # Test successful validation
        validators = {
            "positive": lambda x: x > 0,
            "even": lambda x: x % 2 == 0
        }
        
        # Should pass without error
        validate_input(2, validators)
        
        # Test failed validation
        with self.assertRaises(ValidationError) as context:
            validate_input(-2, validators)
        
        self.assertIn("positive", str(context.exception))
        self.assertNotIn("even", str(context.exception))
        
        # Test multiple validation failures
        with self.assertRaises(ValidationError) as context:
            validate_input(-1, validators)
        
        error_message = str(context.exception)
        self.assertIn("positive", error_message)
        self.assertIn("even", error_message)
        
        # Test custom error message
        with self.assertRaises(ValidationError) as context:
            validate_input(-1, validators, "Custom error")
        
        self.assertIn("Custom error", str(context.exception))


if __name__ == "__main__":
    unittest.main()
