"""
Firecrawl integration module for the legal search agent.

This module provides functionality to integrate Firecrawl's advanced web scraping,
crawling, and data extraction capabilities into our legal search agent.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union

# Import Firecrawl SDK
try:
    from firecrawl.firecrawl import FirecrawlApp
    from firecrawl.types import ScrapeParams, CrawlParams, JsonConfig
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    print("Firecrawl SDK not found. To install, run: pip install firecrawl-py")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('firecrawl_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('FirecrawlIntegration')

class FirecrawlClient:
    """Client for interacting with the Firecrawl API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Firecrawl client.
        
        Args:
            api_key: Firecrawl API key (optional, can also be set via FIRECRAWL_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("FIRECRAWL_API_KEY")
        
        if not self.api_key:
            logger.warning("No Firecrawl API key provided. Set FIRECRAWL_API_KEY environment variable or pass api_key parameter.")
        
        if not FIRECRAWL_AVAILABLE:
            logger.error("Firecrawl SDK not installed. Install it with: pip install firecrawl-py")
            raise ImportError("Firecrawl SDK not installed")
        
        # Initialize the FirecrawlApp
        self.client = FirecrawlApp(api_key=self.api_key)
        logger.info("Firecrawl client initialized")
    
    def scrape_url(self, url: str, formats: List[str] = ["markdown", "html"], json_schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Scrape a URL using Firecrawl.
        
        Args:
            url: URL to scrape
            formats: List of output formats to request (markdown, html, json, links, screenshot)
            json_schema: Optional schema for structured data extraction
            
        Returns:
            Scraped data
        """
        try:
            params = {}
            
            if json_schema and "json" in formats:
                json_config = JsonConfig(schema=json_schema)
                response = self.client.scrape_url(url, formats=formats, json_options=json_config)
            else:
                response = self.client.scrape_url(url, formats=formats)
            
            logger.info(f"Successfully scraped URL: {url}")
            return response
        
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            raise
    
    def crawl_url(
        self, 
        url: str, 
        limit: int = 100, 
        max_depth: int = 3,
        formats: List[str] = ["markdown"],
        excludes: List[str] = [], 
        includes: List[str] = [],
        wait_for_completion: bool = True,
        timeout: int = 600,
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crawl a URL and its subpages using Firecrawl.
        
        Args:
            url: URL to crawl
            limit: Maximum number of pages to crawl
            max_depth: Maximum crawl depth
            formats: List of output formats to request
            excludes: List of URL patterns to exclude
            includes: List of URL patterns to include
            wait_for_completion: Whether to wait for the crawl to complete
            timeout: Maximum time to wait for completion (seconds)
            json_schema: Optional schema for structured data extraction
            
        Returns:
            Crawled data
        """
        try:
            crawl_params = {
                "limit": limit,
                "maxDepth": max_depth,
                "crawlerOptions": {
                    "excludes": excludes,
                    "includes": includes
                },
                "scrapeOptions": {
                    "formats": formats
                }
            }
            
            # Add JSON schema if provided
            if json_schema and "json" in formats:
                crawl_params["scrapeOptions"]["jsonOptions"] = {"schema": json_schema}
            
            # Submit the crawl job
            response = self.client.crawl_url(
                url, 
                params=crawl_params, 
                wait_until_done=wait_for_completion,
                timeout=timeout
            )
            
            if wait_for_completion:
                logger.info(f"Completed crawl of {url}, found {len(response.get('data', []))} pages")
            else:
                logger.info(f"Started crawl of {url}, job ID: {response.get('id')}")
            
            return response
        
        except Exception as e:
            logger.error(f"Error crawling URL {url}: {str(e)}")
            raise
    
    def check_crawl_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a crawl job.
        
        Args:
            job_id: Crawl job ID
            
        Returns:
            Crawl job status
        """
        try:
            status = self.client.check_crawl_status(job_id)
            logger.info(f"Crawl job {job_id} status: {status.get('status')}")
            return status
        
        except Exception as e:
            logger.error(f"Error checking crawl status for job {job_id}: {str(e)}")
            raise
    
    def map_website(self, url: str, search: Optional[str] = None) -> List[str]:
        """
        Map a website to get all URLs.
        
        Args:
            url: URL to map
            search: Optional search term to filter URLs
            
        Returns:
            List of URLs
        """
        try:
            params = {"url": url}
            if search:
                params["search"] = search
                
            response = self.client.map_url(url, search)
            links = response.get("links", [])
            
            logger.info(f"Mapped website {url}, found {len(links)} URLs")
            return links
        
        except Exception as e:
            logger.error(f"Error mapping website {url}: {str(e)}")
            raise
            
    def search_web(self, query: str, limit: int = 10, scrape_results: bool = False, formats: List[str] = ["markdown"]) -> Dict[str, Any]:
        """
        Search the web using Firecrawl.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            scrape_results: Whether to scrape the search results
            formats: List of output formats for scraped results
            
        Returns:
            Search results
        """
        try:
            params = {
                "query": query,
                "limit": limit
            }
            
            if scrape_results:
                params["scrapeOptions"] = {
                    "formats": formats
                }
            
            response = self.client.search(query, limit=limit, scrape_results=scrape_results, formats=formats)
            
            logger.info(f"Searched for '{query}', found {len(response.get('data', []))} results")
            return response
        
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            raise
    
    def extract_structured_data(
        self, 
        urls: Union[str, List[str]], 
        schema: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from one or more URLs.
        
        Args:
            urls: URL or list of URLs to extract data from
            schema: JSON schema for the structured data
            prompt: Natural language prompt for extraction
            
        Returns:
            Extracted structured data
        """
        try:
            if isinstance(urls, str):
                urls = [urls]
            
            # Ensure we have either a schema or a prompt
            if not schema and not prompt:
                raise ValueError("Either schema or prompt must be provided")
            
            params = {"urls": urls}
            
            if schema:
                params["schema"] = schema
            
            if prompt:
                params["prompt"] = prompt
            
            response = self.client.extract(urls, schema=schema, prompt=prompt)
            
            logger.info(f"Extracted data from {len(urls)} URLs")
            return response
        
        except Exception as e:
            logger.error(f"Error extracting data from URLs: {str(e)}")
            raise


# Legal document schemas
class LegalSchemas:
    """Collection of JSON schemas for legal document types."""
    
    @staticmethod
    def business_registration_schema() -> Dict[str, Any]:
        """
        Get the schema for business registration data.
        
        Returns:
            JSON schema
        """
        return {
            "type": "object",
            "properties": {
                "entity_name": {
                    "type": "string",
                    "description": "Legal name of the business entity"
                },
                "entity_type": {
                    "type": "string",
                    "description": "Type of entity (LLC, Corporation, etc.)"
                },
                "filing_number": {
                    "type": "string",
                    "description": "State filing or registration number"
                },
                "status": {
                    "type": "string",
                    "description": "Current status (Active, Dissolved, etc.)"
                },
                "formation_date": {
                    "type": "string",
                    "description": "Date the entity was formed"
                },
                "jurisdiction": {
                    "type": "string",
                    "description": "State or jurisdiction of formation"
                },
                "registered_agent": {
                    "type": "object",
                    "properties": {
                        "name": { "type": "string" },
                        "address": { "type": "string" }
                    }
                },
                "principals": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": { "type": "string" },
                            "title": { "type": "string" }
                        }
                    }
                }
            },
            "required": ["entity_name", "entity_type", "filing_number", "status"]
        }
    
    @staticmethod
    def court_case_schema() -> Dict[str, Any]:
        """
        Get the schema for court case data.
        
        Returns:
            JSON schema
        """
        return {
            "type": "object",
            "properties": {
                "case_number": {
                    "type": "string",
                    "description": "The official case identifier"
                },
                "court": {
                    "type": "string",
                    "description": "Court where the case was filed"
                },
                "filing_date": {
                    "type": "string",
                    "description": "Date when the case was filed"
                },
                "parties": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": { "type": "string" },
                            "role": { "type": "string" }
                        }
                    }
                },
                "judges": {
                    "type": "array",
                    "items": { "type": "string" }
                },
                "status": {
                    "type": "string",
                    "description": "Current status of the case"
                },
                "disposition": {
                    "type": "string",
                    "description": "Final judgment or disposition"
                }
            },
            "required": ["case_number", "court", "filing_date", "parties"]
        }
    
    @staticmethod
    def judgment_schema() -> Dict[str, Any]:
        """
        Get the schema for judgment data.
        
        Returns:
            JSON schema
        """
        return {
            "type": "object",
            "properties": {
                "case_number": {
                    "type": "string",
                    "description": "The case identifier"
                },
                "judgment_date": {
                    "type": "string",
                    "description": "Date when the judgment was entered"
                },
                "judgment_type": {
                    "type": "string",
                    "description": "Type of judgment (Default, Summary, etc.)"
                },
                "plaintiff": {
                    "type": "string",
                    "description": "Party awarded the judgment"
                },
                "defendant": {
                    "type": "string",
                    "description": "Party against whom judgment was entered"
                },
                "amount": {
                    "type": "string",
                    "description": "Monetary amount of the judgment"
                },
                "interest_rate": {
                    "type": "string",
                    "description": "Interest rate on the judgment"
                },
                "status": {
                    "type": "string",
                    "description": "Current status (Satisfied, Outstanding, etc.)"
                },
                "filing_location": {
                    "type": "string",
                    "description": "Where the judgment was filed/recorded"
                }
            },
            "required": ["case_number", "judgment_date", "plaintiff", "defendant", "amount"]
        }
    
    @staticmethod
    def get_schema_for_url(url: str) -> Optional[Dict[str, Any]]:
        """
        Get the appropriate schema for a URL based on pattern matching.
        
        Args:
            url: URL to get schema for
            
        Returns:
            JSON schema or None if no matching schema
        """
        url_lower = url.lower()
        
        # Check for business registration sites
        if any(term in url_lower for term in ["sos.", "secretary", "business", "corporation", "entity"]):
            return LegalSchemas.business_registration_schema()
        
        # Check for court sites
        elif any(term in url_lower for term in ["court", "judiciary", "docket", "pacer"]):
            return LegalSchemas.court_case_schema()
        
        # Check for judgment sites
        elif any(term in url_lower for term in ["judgment", "lien", "docket", "nyscef"]):
            return LegalSchemas.judgment_schema()
        
        # No matching schema
        return None