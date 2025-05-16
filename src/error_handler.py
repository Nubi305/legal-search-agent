"""
Error handling module for the legal search agent.

This module provides consistent error handling and logging across the application.
"""

import logging
import traceback
from typing import Any, Dict, Optional, Callable, TypeVar, cast

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

class LegalSearchError(Exception):
    """Base exception class for the legal search agent."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the exception.
        
        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)


class ConfigError(LegalSearchError):
    """Exception raised for configuration errors."""
    pass


class CrawlerError(LegalSearchError):
    """Exception raised for crawler errors."""
    pass


class ProcessorError(LegalSearchError):
    """Exception raised for document processor errors."""
    pass


class IndexerError(LegalSearchError):
    """Exception raised for indexer errors."""
    pass


class SearchError(LegalSearchError):
    """Exception raised for search errors."""
    pass


class APIError(LegalSearchError):
    """Exception raised for API errors."""
    pass


class ValidationError(LegalSearchError):
    """Exception raised for validation errors."""
    pass


def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Set up file handler if log file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def safe_execute(func: Callable[..., R], 
                 error_message: str, 
                 logger: logging.Logger,
                 default_return: Optional[R] = None, 
                 error_class: type = LegalSearchError,
                 log_level: int = logging.ERROR,
                 raise_error: bool = False,
                 **kwargs: Any) -> R:
    """
    Execute a function safely with proper error handling.
    
    Args:
        func: Function to execute
        error_message: Message to log on error
        logger: Logger to use
        default_return: Default value to return on error
        error_class: Exception class to raise
        log_level: Logging level for errors
        raise_error: Whether to raise the error or just log it
        **kwargs: Arguments to pass to the function
        
    Returns:
        Function result or default return value on error
        
    Raises:
        Exception of error_class type if raise_error is True
    """
    try:
        return func(**kwargs)
    except Exception as e:
        error_details = {
            'exception_type': type(e).__name__,
            'exception_message': str(e),
            'traceback': traceback.format_exc()
        }
        
        # Log the error
        logger.log(log_level, f"{error_message}: {e}", extra={'error_details': error_details})
        
        if raise_error:
            raise error_class(error_message, error_details) from e
        
        return cast(R, default_return)


def validate_input(value: Any, 
                  validators: Dict[str, Callable[[Any], bool]], 
                  error_message: str = "Input validation failed") -> None:
    """
    Validate an input value against a set of validators.
    
    Args:
        value: Value to validate
        validators: Dictionary of validator name to validator function
        error_message: Base error message
        
    Raises:
        ValidationError: If validation fails
    """
    errors = []
    
    for name, validator in validators.items():
        if not validator(value):
            errors.append(name)
    
    if errors:
        raise ValidationError(
            f"{error_message}: {', '.join(errors)}",
            {'value': str(value), 'failed_validations': errors}
        )
