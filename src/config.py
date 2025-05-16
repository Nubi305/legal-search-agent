"""
Configuration module for the legal search agent.
"""

import json
import os
import re
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from urllib.parse import urlparse

from src.error_handler import ConfigError, ValidationError, setup_logger, validate_input

# Set up logger
logger = setup_logger('LegalConfig', 'config.log')

class Config:
    """Configuration class for the legal search agent."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize configuration.
        
        Args:
            config_data: Dictionary with configuration data
            
        Raises:
            ConfigError: If configuration is invalid
        """
        try:
            self._validate_config(config_data)
            self.config_data = config_data
            logger.info("Configuration initialized successfully")
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise ConfigError(f"Invalid configuration: {str(e)}", e.details)
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Config':
        """
        Load configuration from a file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Config object
            
        Raises:
            FileNotFoundError: If configuration file not found
            ConfigError: If configuration file is invalid
        """
        if not os.path.exists(file_path):
            logger.error(f"Configuration file not found: {file_path}")
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            logger.info(f"Configuration loaded from {file_path}")
            return cls(config_data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {file_path}: {str(e)}")
            raise ConfigError(f"Invalid JSON in configuration file: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {str(e)}")
            raise ConfigError(f"Error loading configuration: {str(e)}")
    
    def _validate_config(self, config_data: Dict[str, Any]) -> None:
        """
        Validate configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Raises:
            ValidationError: If configuration is invalid
        """
        # Check required keys
        required_keys = ['user_agent', 'request_delay', 'max_pages', 'max_depth', 'sources']
        for key in required_keys:
            if key not in config_data:
                raise ValidationError(f"Required configuration key missing: {key}")
        
        # Validate request delay (prevent too aggressive crawling)
        request_delay = config_data.get('request_delay', 0)
        if not isinstance(request_delay, (int, float)) or request_delay < 0.5:
            raise ValidationError(
                "Request delay must be a number >= 0.5 seconds",
                {'request_delay': request_delay}
            )
        
        # Validate max_pages (prevent excessive crawling)
        max_pages = config_data.get('max_pages', 0)
        if not isinstance(max_pages, int) or max_pages <= 0 or max_pages > 1000:
            raise ValidationError(
                "max_pages must be an integer between 1 and 1000",
                {'max_pages': max_pages}
            )
        
        # Validate sources
        sources = config_data.get('sources', [])
        if not isinstance(sources, list) or not sources:
            raise ValidationError(
                "sources must be a non-empty list",
                {'sources': sources}
            )
        
        # Validate each source
        for i, source in enumerate(sources):
            if not isinstance(source, dict):
                raise ValidationError(
                    f"Source {i} is not a dictionary",
                    {'source_index': i}
                )
            
            # Check required source keys
            source_required_keys = ['name', 'url']
            for key in source_required_keys:
                if key not in source:
                    raise ValidationError(
                        f"Required key missing in source {i}: {key}",
                        {'source_index': i, 'source_name': source.get('name', 'unknown')}
                    )
            
            # Validate URL
            url = source.get('url', '')
            if not self._is_valid_url(url):
                raise ValidationError(
                    f"Invalid URL in source {i}: {url}",
                    {'source_index': i, 'source_name': source.get('name', 'unknown'), 'url': url}
                )
        
        logger.debug("Configuration validated successfully")
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme in ('http', 'https'), result.netloc])
        except Exception:
            return False
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value
        """
        return self.config_data.get(key, default)
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """
        Get the list of sources to crawl.
        
        Returns:
            List of source dictionaries
        """
        return self.config_data.get('sources', [])
    
    def get_user_agent(self) -> str:
        """
        Get the user agent to use for HTTP requests.
        
        Returns:
            User agent string
        """
        return self.config_data.get('user_agent', 'LegalSearchAgent/1.0')
    
    def get_request_delay(self) -> float:
        """
        Get the delay between requests in seconds.
        
        Returns:
            Delay in seconds
        """
        return float(self.config_data.get('request_delay', 1.0))
    
    def get_max_pages(self) -> int:
        """
        Get the maximum number of pages to crawl per source.
        
        Returns:
            Maximum number of pages
        """
        return int(self.config_data.get('max_pages', 100))
    
    def get_max_depth(self) -> int:
        """
        Get the maximum crawl depth.
        
        Returns:
            Maximum crawl depth
        """
        return int(self.config_data.get('max_depth', 3))
    
    def get_document_types(self) -> List[str]:
        """
        Get the document types to download.
        
        Returns:
            List of document types (file extensions)
        """
        return self.config_data.get('document_types', ['html', 'pdf', 'doc', 'docx', 'txt'])
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get the HTTP headers to use for requests.
        
        Returns:
            Dictionary of HTTP headers
        """
        headers = {
            'User-Agent': self.get_user_agent()
        }
        
        custom_headers = self.config_data.get('headers', {})
        headers.update(custom_headers)
        
        return headers
