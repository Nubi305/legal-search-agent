"""
Configuration module for the legal search agent.
"""

import json
import os
from typing import Dict, List, Any, Optional

class Config:
    """Configuration class for the legal search agent."""
    
    def __init__(self, config_data: Dict[str, Any]):
        """
        Initialize configuration.
        
        Args:
            config_data: Dictionary with configuration data
        """
        self.config_data = config_data
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Config':
        """
        Load configuration from a file.
        
        Args:
            file_path: Path to the configuration file
            
        Returns:
            Config object
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        return cls(config_data)
    
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