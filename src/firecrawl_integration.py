"""
Firecrawl integration module for the legal search agent.

This module provides functionality to integrate Firecrawl's advanced web scraping,
crawling, and data extraction capabilities into our legal search agent.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from urllib.parse import urlparse

# Import error handlers
from src.error_handler import APIError, ValidationError, setup_logger, safe_execute

# Set up logger
logger = setup_logger('FirecrawlIntegration', 'firecrawl_integration.log')

# Import Firecrawl SDK
try:
    from firecrawl.firecrawl import FirecrawlApp
    from firecrawl.types import ScrapeParams, CrawlParams, JsonConfig
    from firecrawl.exceptions import FirecrawlError, FirecrawlAPIError, FirecrawlTimeoutError
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    logger.warning("Firecrawl SDK not found. To install, run: pip install firecrawl-py")
    FirecrawlError = Exception
    FirecrawlAPIError = Exception
    FirecrawlTimeoutError = Exception

class FirecrawlClient:
    """Client for interacting with the Firecrawl API."""
    
    # Constants
    MAX_URL_LIMIT = 100  # Maximum URLs to extract in one batch
    MAX_BATCH_SIZE = 20  # Maximum URLs to process in one batch
    DEFAULT_TIMEOUT = 600  # Default timeout for API calls (10 minutes)
    MAX_RETRIES = 3  # Maximum number of retries for API calls
    RETRY_DELAY = 5  # Delay between retries in seconds
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Firecrawl client.
        
        Args:
            api_key: Firecrawl API key (optional, can also be set via FIRECRAWL_API_KEY env var)
            
        Raises:
            ImportError: If Firecrawl SDK is not installed
            APIError: If API key is not provided or invalid
        """
        self.api_key = api_key or os.environ.get("FIRECRAWL_API_KEY")
        
        if not self.api_key:
            logger.warning("No Firecrawl API key provided. Set FIRECRAWL_API_KEY environment variable or pass api_key parameter.")
        
        if not FIRECRAWL_AVAILABLE:
            logger.error("Firecrawl SDK not installed. Install it with: pip install firecrawl-py")
            raise ImportError("Firecrawl SDK not installed")
        
        try:
            # Initialize the FirecrawlApp
            self.client = FirecrawlApp(api_key=self.api_key)
            logger.info("Firecrawl client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Firecrawl client: {str(e)}")
            raise APIError(f"Failed to initialize Firecrawl client: {str(e)}")
    
    def _retry_api_call(self, func: callable, *args, **kwargs) -> Any:
        """
        Retry an API call with exponential backoff.
        
        Args:
            func: Function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            API call response
            
        Raises:
            APIError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except FirecrawlTimeoutError as e:
                # Handle timeout errors specifically
                logger.warning(f"Timeout error on attempt {attempt + 1}/{self.MAX_RETRIES}: {str(e)}")
                last_error = e
                # Use exponential backoff
                delay = self.RETRY_DELAY * (2 ** attempt)
                time.sleep(delay)
            except (FirecrawlAPIError, FirecrawlError) as e:
                # Handle API errors
                logger.warning(f"API error on attempt {attempt + 1}/{self.MAX_RETRIES}: {str(e)}")
                last_error = e
                # Use exponential backoff
                delay = self.RETRY_DELAY * (2 ** attempt)
                time.sleep(delay)
            except Exception as e:
                # Don't retry other types of errors
                logger.error(f"Unexpected error: {str(e)}")
                raise APIError(f"Unexpected error in Firecrawl API call: {str(e)}")
        
        # If we get here, all retries failed
        logger.error(f"All retries failed: {str(last_error)}")
        raise APIError(f"Firecrawl API call failed after {self.MAX_RETRIES} attempts: {str(last_error)}")
    
    def _validate_url(self, url: str) -> bool:
        """
        Validate a URL.
        
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
    
    def _validate_batch(self, urls: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a batch of URLs.
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            Tuple of (valid_urls, invalid_urls)
        """
        valid_urls = []
        invalid_urls = []
        
        for url in urls:
            if self._validate_url(url):
                valid_urls.append(url)
            else:
                invalid_urls.append(url)
        
        return valid_urls, invalid_urls
    
    def scrape_url(self, 
                  url: str, 
                  formats: List[str] = ["markdown", "html"], 
                  json_schema: Optional[Dict[str, Any]] = None,
                  timeout: int = None) -> Dict[str, Any]:
        """
        Scrape a URL using Firecrawl.
        
        Args:
            url: URL to scrape
            formats: List of output formats to request (markdown, html, json, links, screenshot)
            json_schema: Optional schema for structured data extraction
            timeout: Optional timeout in seconds (overrides default)
            
        Returns:
            Scraped data
            
        Raises:
            ValidationError: If URL is invalid
            APIError: If there's an error in the API call
        """
        # Validate URL
        if not self._validate_url(url):
            raise ValidationError(f"Invalid URL: {url}")
        
        # Validate formats
        valid_formats = {"markdown", "html", "json", "links", "screenshot"}
        if not all(fmt in valid_formats for fmt in formats):
            logger.warning(f"Some formats are invalid. Valid formats are: {valid_formats}")
            formats = [fmt for fmt in formats if fmt in valid_formats]
        
        logger.info(f"Scraping URL: {url} (formats: {formats})")
        
        try:
            # Make the API call with retries
            if json_schema and "json" in formats:
                json_config = JsonConfig(schema=json_schema)
                response = self._retry_api_call(
                    self.client.scrape_url,
                    url,
                    formats=formats,
                    json_options=json_config,
                    timeout=timeout or self.DEFAULT_TIMEOUT
                )
            else:
                response = self._retry_api_call(
                    self.client.scrape_url,
                    url,
                    formats=formats,
                    timeout=timeout or self.DEFAULT_TIMEOUT
                )
            
            logger.info(f"Successfully scraped URL: {url}")
            return response
        
        except APIError:
            # Re-raise APIError
            raise
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            raise APIError(f"Error scraping URL: {str(e)}")
    
    def crawl_url(
        self, 
        url: str, 
        limit: int = 100, 
        max_depth: int = 3,
        formats: List[str] = ["markdown"],
        excludes: List[str] = [], 
        includes: List[str] = [],
        wait_for_completion: bool = True,
        timeout: int = None,
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
            
        Raises:
            ValidationError: If URL is invalid or parameters are invalid
            APIError: If there's an error in the API call
        """
        # Validate URL
        if not self._validate_url(url):
            raise ValidationError(f"Invalid URL: {url}")
        
        # Validate and sanitize parameters
        limit = max(1, min(500, limit))  # Cap limit between 1 and 500
        max_depth = max(1, min(5, max_depth))  # Cap depth between 1 and 5
        
        # Validate formats
        valid_formats = {"markdown", "html", "json", "links", "screenshot"}
        formats = [fmt for fmt in formats if fmt in valid_formats]
        
        if not formats:
            formats = ["markdown"]  # Default to markdown if no valid formats
        
        # Set up timeout
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        logger.info(f"Crawling URL: {url} (limit: {limit}, depth: {max_depth}, formats: {formats})")
        
        try:
            # Construct crawl parameters
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
            
            # Submit the crawl job with retries
            response = self._retry_api_call(
                self.client.crawl_url,
                url, 
                params=crawl_params, 
                wait_until_done=wait_for_completion,
                timeout=timeout
            )
            
            if wait_for_completion:
                data_count = len(response.get('data', []))
                logger.info(f"Completed crawl of {url}, found {data_count} pages")
            else:
                logger.info(f"Started crawl of {url}, job ID: {response.get('id')}")
            
            return response
        
        except APIError:
            # Re-raise APIError
            raise
        except Exception as e:
            logger.error(f"Error crawling URL {url}: {str(e)}")
            raise APIError(f"Error crawling URL: {str(e)}")
    
    def check_crawl_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a crawl job.
        
        Args:
            job_id: Crawl job ID
            
        Returns:
            Crawl job status
            
        Raises:
            ValidationError: If job ID is invalid
            APIError: If there's an error in the API call
        """
        # Validate job ID
        if not job_id or not isinstance(job_id, str):
            raise ValidationError(f"Invalid job ID: {job_id}")
        
        logger.info(f"Checking status of crawl job: {job_id}")
        
        try:
            # Make the API call with retries
            status = self._retry_api_call(
                self.client.check_crawl_status,
                job_id
            )
            
            logger.info(f"Crawl job {job_id} status: {status.get('status')}")
            return status
        
        except APIError:
            # Re-raise APIError
            raise
        except Exception as e:
            logger.error(f"Error checking crawl status for job {job_id}: {str(e)}")
            raise APIError(f"Error checking crawl status: {str(e)}")
    
    def map_website(self, 
                   url: str, 
                   search: Optional[str] = None,
                   timeout: int = None) -> List[str]:
        """
        Map a website to get all URLs.
        
        Args:
            url: URL to map
            search: Optional search term to filter URLs
            timeout: Optional timeout in seconds (overrides default)
            
        Returns:
            List of URLs
            
        Raises:
            ValidationError: If URL is invalid
            APIError: If there's an error in the API call
        """
        # Validate URL
        if not self._validate_url(url):
            raise ValidationError(f"Invalid URL: {url}")
        
        logger.info(f"Mapping website: {url}" + (f" (search: {search})" if search else ""))
        
        try:
            # Make the API call with retries
            response = self._retry_api_call(
                self.client.map_url,
                url, 
                search,
                timeout=timeout or self.DEFAULT_TIMEOUT
            )
            
            links = response.get("links", [])
            
            # Limit the number of links
            if len(links) > self.MAX_URL_LIMIT:
                logger.warning(f"Found {len(links)} URLs, limiting to {self.MAX_URL_LIMIT}")
                links = links[:self.MAX_URL_LIMIT]
            
            # Validate links
            valid_links, invalid_links = self._validate_batch(links)
            
            if invalid_links:
                logger.warning(f"Found {len(invalid_links)} invalid URLs")
            
            logger.info(f"Mapped website {url}, found {len(valid_links)} valid URLs")
            
            return valid_links
        
        except APIError:
            # Re-raise APIError
            raise
        except Exception as e:
            logger.error(f"Error mapping website {url}: {str(e)}")
            raise APIError(f"Error mapping website: {str(e)}")
            
    def search_web(self, 
                  query: str, 
                  limit: int = 10, 
                  scrape_results: bool = False, 
                  formats: List[str] = ["markdown"],
                  timeout: int = None) -> Dict[str, Any]:
        """
        Search the web using Firecrawl.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            scrape_results: Whether to scrape the search results
            formats: List of output formats for scraped results
            timeout: Optional timeout in seconds (overrides default)
            
        Returns:
            Search results
            
        Raises:
            ValidationError: If query is invalid or parameters are invalid
            APIError: If there's an error in the API call
        """
        # Validate query
        if not query or not isinstance(query, str):
            raise ValidationError(f"Invalid search query: {query}")
        
        # Validate and sanitize parameters
        limit = max(1, min(50, limit))  # Cap limit between 1 and 50
        
        # Validate formats if scraping results
        if scrape_results:
            valid_formats = {"markdown", "html", "json", "links", "screenshot"}
            formats = [fmt for fmt in formats if fmt in valid_formats]
            
            if not formats:
                formats = ["markdown"]  # Default to markdown if no valid formats
        
        logger.info(f"Searching for: {query} (limit: {limit}, scrape_results: {scrape_results})")
        
        try:
            # Make the API call with retries
            response = self._retry_api_call(
                self.client.search,
                query,
                limit=limit,
                scrape_results=scrape_results,
                formats=formats,
                timeout=timeout or self.DEFAULT_TIMEOUT
            )
            
            result_count = len(response.get('data', []))
            logger.info(f"Searched for '{query}', found {result_count} results")
            return response
        
        except APIError:
            # Re-raise APIError
            raise
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            raise APIError(f"Error searching for '{query}': {str(e)}")
    
    def extract_structured_data(
        self, 
        urls: Union[str, List[str]], 
        schema: Optional[Dict[str, Any]] = None,
        prompt: Optional[str] = None,
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from one or more URLs.
        
        Args:
            urls: URL or list of URLs to extract data from
            schema: JSON schema for the structured data
            prompt: Natural language prompt for extraction
            timeout: Optional timeout in seconds (overrides default)
            
        Returns:
            Extracted structured data
            
        Raises:
            ValidationError: If URLs are invalid or parameters are invalid
            APIError: If there's an error in the API call
        """
        # Validate and normalize URLs
        if isinstance(urls, str):
            urls = [urls]
        
        if not urls:
            raise ValidationError("No URLs provided")
        
        # Validate URLs and filter out invalid ones
        valid_urls, invalid_urls = self._validate_batch(urls)
        
        if not valid_urls:
            raise ValidationError(f"No valid URLs provided. Invalid URLs: {invalid_urls}")
        
        if invalid_urls:
            logger.warning(f"Found {len(invalid_urls)} invalid URLs, skipping them")
        
        # Ensure we have either a schema or a prompt
        if not schema and not prompt:
            raise ValidationError("Either schema or prompt must be provided")
        
        # Limit the number of URLs
        if len(valid_urls) > self.MAX_BATCH_SIZE:
            logger.warning(f"Too many URLs provided ({len(valid_urls)}), limiting to {self.MAX_BATCH_SIZE}")
            valid_urls = valid_urls[:self.MAX_BATCH_SIZE]
        
        logger.info(f"Extracting data from {len(valid_urls)} URLs")
        
        try:
            # Make the API call with retries
            response = self._retry_api_call(
                self.client.extract,
                valid_urls,
                schema=schema,
                prompt=prompt,
                timeout=timeout or self.DEFAULT_TIMEOUT
            )
            
            logger.info(f"Successfully extracted data from {len(valid_urls)} URLs")
            return response
        
        except APIError:
            # Re-raise APIError
            raise
        except Exception as e:
            logger.error(f"Error extracting data from URLs: {str(e)}")
            raise APIError(f"Error extracting data from URLs: {str(e)}")
    
    def batch_process(self, 
                     urls: List[str], 
                     process_func: callable, 
                     batch_size: int = None,
                     **kwargs) -> List[Dict[str, Any]]:
        """
        Process a batch of URLs in smaller chunks to avoid rate limiting.
        
        Args:
            urls: List of URLs to process
            process_func: Function to call for each batch of URLs
            batch_size: Batch size (defaults to MAX_BATCH_SIZE)
            **kwargs: Additional arguments to pass to process_func
            
        Returns:
            List of results from each batch
            
        Raises:
            ValidationError: If URLs are invalid
            APIError: If there's an error in the API calls
        """
        # Validate URLs
        if not urls:
            raise ValidationError("No URLs provided")
        
        valid_urls, invalid_urls = self._validate_batch(urls)
        
        if not valid_urls:
            raise ValidationError(f"No valid URLs provided. Invalid URLs: {invalid_urls}")
        
        if invalid_urls:
            logger.warning(f"Found {len(invalid_urls)} invalid URLs, skipping them")
        
        # Set batch size
        batch_size = batch_size or self.MAX_BATCH_SIZE
        
        # Split URLs into batches
        batches = [valid_urls[i:i + batch_size] for i in range(0, len(valid_urls), batch_size)]
        
        logger.info(f"Processing {len(valid_urls)} URLs in {len(batches)} batches")
        
        results = []
        
        # Process each batch
        for i, batch in enumerate(batches):
            try:
                logger.info(f"Processing batch {i+1}/{len(batches)} ({len(batch)} URLs)")
                
                # Process batch and add results
                batch_result = process_func(batch, **kwargs)
                results.append(batch_result)
                
                # Add delay between batches to avoid rate limiting
                if i < len(batches) - 1:
                    time.sleep(self.RETRY_DELAY)
            
            except APIError as e:
                logger.error(f"Error processing batch {i+1}: {str(e)}")
                # Continue with next batch
                continue
        
        return results


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
                },
                "annual_report_due": {
                    "type": "string",
                    "description": "Next annual report due date"
                },
                "good_standing": {
                    "type": "boolean",
                    "description": "Whether the entity is in good standing"
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
                },
                "docket_entries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": { "type": "string" },
                            "description": { "type": "string" }
                        }
                    }
                },
                "nature_of_suit": {
                    "type": "string",
                    "description": "Category or nature of the lawsuit"
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
                },
                "satisfaction_date": {
                    "type": "string",
                    "description": "Date when the judgment was satisfied, if applicable"
                },
                "enforcement_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": { "type": "string" },
                            "action": { "type": "string" }
                        }
                    }
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
        if not url:
            return None
            
        url_lower = url.lower()
        
        # Check for business registration sites
        if any(term in url_lower for term in ["sos.", "secretary", "business", "corporation", "entity", "llc", "corp"]):
            return LegalSchemas.business_registration_schema()
        
        # Check for court sites
        elif any(term in url_lower for term in ["court", "judiciary", "docket", "pacer", "justia", "caselaw", "opinion"]):
            return LegalSchemas.court_case_schema()
        
        # Check for judgment sites
        elif any(term in url_lower for term in ["judgment", "lien", "nyscef", "clerk", "records", "ucc"]):
            return LegalSchemas.judgment_schema()
        
        # No matching schema
        return None
