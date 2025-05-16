"""
Crawler module for the legal search agent.
"""

import os
import re
import time
import hashlib
import json
import logging
import requests
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from tqdm import tqdm
from requests.exceptions import RequestException, Timeout, HTTPError, ConnectionError

from src.config import Config
from src.error_handler import CrawlerError, ValidationError, setup_logger, safe_execute

# Set up logger
logger = setup_logger('LegalCrawler', 'crawler.log')

class LegalCrawler:
    """Crawler for legal websites."""
    
    # Constants for security and stability
    MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10 MB
    REQUEST_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    UNSAFE_EXTENSIONS = {'exe', 'dll', 'bat', 'sh', 'command', 'js', 'jsp', 'php', 'asp', 'aspx'}
    MIN_REQUEST_DELAY = 0.5  # minimum delay between requests in seconds
    
    def __init__(self, config: Config):
        """
        Initialize the crawler.
        
        Args:
            config: Configuration object
            
        Raises:
            CrawlerError: If configuration is invalid for crawling
        """
        try:
            self.config = config
            self.headers = config.get_headers()
            
            # Ensure the request delay is at least the minimum
            self.request_delay = max(config.get_request_delay(), self.MIN_REQUEST_DELAY)
            
            self.max_pages = min(config.get_max_pages(), 1000)  # Cap at 1000 pages for safety
            self.max_depth = min(config.get_max_depth(), 5)  # Cap at depth 5 for safety
            
            # Filter out unsafe document types
            self.document_types = [
                doc_type for doc_type in config.get_document_types()
                if doc_type.lower() not in self.UNSAFE_EXTENSIONS
            ]
            
            self.visited_urls: Set[str] = set()
            self.urls_to_visit: List[Tuple[str, int]] = []  # (url, depth)
            self.document_count = 0
            
            # Validate configuration
            self._validate_crawler_config()
            
            logger.info("Crawler initialized successfully")
        except (ValidationError, ValueError) as e:
            logger.error(f"Invalid crawler configuration: {str(e)}")
            raise CrawlerError(f"Invalid crawler configuration: {str(e)}")
    
    def _validate_crawler_config(self) -> None:
        """
        Validate crawler configuration.
        
        Raises:
            ValidationError: If configuration is invalid
        """
        # Check if sources are available
        sources = self.config.get_sources()
        if not sources:
            raise ValidationError("No sources defined in configuration")
        
        # Validate each source URL
        for source in sources:
            url = source.get('url', '')
            if not url:
                raise ValidationError(f"Empty URL in source: {source.get('name', 'unknown')}")
            
            # Validate URL
            parsed_url = urlparse(url)
            if parsed_url.scheme not in ('http', 'https'):
                raise ValidationError(f"Invalid URL scheme in source {source.get('name', 'unknown')}: {url}")
        
        # Validate request delay
        if self.request_delay < self.MIN_REQUEST_DELAY:
            raise ValidationError(f"Request delay must be at least {self.MIN_REQUEST_DELAY} seconds")
        
        # Validate max_pages
        if self.max_pages <= 0:
            raise ValidationError("max_pages must be a positive integer")
        
        # Validate document types
        if not self.document_types:
            raise ValidationError("No valid document types defined")
        
        logger.debug("Crawler configuration validated successfully")
    
    def crawl(self, output_dir: str = "downloaded_docs") -> None:
        """
        Crawl the legal websites.
        
        Args:
            output_dir: Directory to save downloaded documents
            
        Raises:
            CrawlerError: If there's an error during crawling
        """
        try:
            # Validate and create output directory with proper error handling
            if not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir)
                except OSError as e:
                    raise CrawlerError(f"Failed to create output directory {output_dir}: {str(e)}")
            
            sources = self.config.get_sources()
            
            for source in sources:
                source_name = source.get('name', 'unknown')
                source_url = source.get('url')
                source_selectors = source.get('selectors', {})
                
                # Create a safe directory name
                safe_source_name = re.sub(r'[^\w\-]', '_', source_name)
                source_output_dir = os.path.join(output_dir, safe_source_name)
                
                if not os.path.exists(source_output_dir):
                    try:
                        os.makedirs(source_output_dir)
                    except OSError as e:
                        logger.error(f"Failed to create source directory {source_output_dir}: {str(e)}")
                        continue
                
                logger.info(f"Crawling source: {source_name} ({source_url})")
                
                # Reset for each source
                self.visited_urls = set()
                self.urls_to_visit = [(source_url, 0)]
                self.document_count = 0
                
                with tqdm(total=self.max_pages, desc=f"Crawling {source_name}") as pbar:
                    while self.urls_to_visit and self.document_count < self.max_pages:
                        url, depth = self.urls_to_visit.pop(0)
                        
                        if url in self.visited_urls:
                            continue
                        
                        # Use safe execution pattern
                        success = safe_execute(
                            func=self._process_url_safely,
                            error_message=f"Error processing URL {url}",
                            logger=logger,
                            default_return=False,
                            error_class=CrawlerError,
                            url=url,
                            depth=depth,
                            selectors=source_selectors,
                            output_dir=source_output_dir
                        )
                        
                        if success:
                            self.visited_urls.add(url)
                            pbar.update(1)
                        
                        # Add delay between requests
                        time.sleep(self.request_delay)
                
                logger.info(f"Completed crawling source: {source_name}, downloaded {self.document_count} documents")
        
        except Exception as e:
            logger.error(f"Crawling failed: {str(e)}")
            raise CrawlerError(f"Crawling failed: {str(e)}")
    
    def _process_url_safely(self, url: str, depth: int, selectors: Dict, output_dir: str) -> bool:
        """
        Process a URL safely with retries and error handling.
        
        Args:
            url: URL to process
            depth: Current crawl depth
            selectors: CSS selectors for extraction
            output_dir: Directory to save downloaded documents
            
        Returns:
            True if processing was successful, False otherwise
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                self.process_url(url, depth, selectors, output_dir)
                return True
            except (Timeout, ConnectionError) as e:
                # Retriable errors
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"Retrying URL {url} after error: {str(e)}. Attempt {attempt + 1}/{self.MAX_RETRIES}")
                    time.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Failed to process URL {url} after {self.MAX_RETRIES} attempts: {str(e)}")
                    return False
            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                return False
        
        return False
    
    def process_url(self, url: str, depth: int, selectors: Dict, output_dir: str) -> None:
        """
        Process a URL: download content and extract links.
        
        Args:
            url: URL to process
            depth: Current crawl depth
            selectors: CSS selectors for extraction
            output_dir: Directory to save downloaded documents
            
        Raises:
            RequestException: If there's an error downloading the content
            ValueError: If the content is invalid or too large
        """
        logger.debug(f"Processing URL: {url} (depth: {depth})")
        
        # Validate URL before making the request
        if not self._is_safe_url(url):
            logger.warning(f"Skipping unsafe URL: {url}")
            return
        
        # Download content with proper error handling
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.REQUEST_TIMEOUT,
                stream=True  # Use streaming to check content size before downloading
            )
            response.raise_for_status()
            
            # Check content size
            content_length = int(response.headers.get('Content-Length', 0))
            if content_length > self.MAX_CONTENT_SIZE:
                logger.warning(f"Skipping URL {url}: Content too large ({content_length} bytes)")
                return
            
            # Read content with size limit
            content = b''
            for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                content += chunk
                if len(content) > self.MAX_CONTENT_SIZE:
                    logger.warning(f"Skipping URL {url}: Content too large (exceeded {self.MAX_CONTENT_SIZE} bytes)")
                    return
            
            # Determine content type
            content_type = response.headers.get('Content-Type', '').lower()
            
        except (RequestException, Timeout, ConnectionError, HTTPError) as e:
            logger.error(f"Failed to download {url}: {str(e)}")
            raise
        
        # Process based on content type
        if 'text/html' in content_type:
            try:
                # Decode content with error handling
                html_text = content.decode('utf-8', errors='replace')
                self.process_html_page(url, html_text, depth, selectors, output_dir)
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode HTML content from {url}: {str(e)}")
                raise ValueError(f"Failed to decode HTML content: {str(e)}")
        elif any(doc_type in content_type for doc_type in ['pdf', 'msword', 'vnd.openxmlformats-officedocument']):
            self.save_document(url, content, output_dir)
        else:
            logger.debug(f"Skipping unsupported content type: {content_type}")
    
    def _is_safe_url(self, url: str) -> bool:
        """
        Check if a URL is safe to crawl.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is safe, False otherwise
        """
        # Basic URL validation
        if not url or not isinstance(url, str):
            return False
        
        # Parse URL
        try:
            parsed_url = urlparse(url)
        except Exception:
            return False
        
        # Check scheme
        if parsed_url.scheme not in ('http', 'https'):
            return False
        
        # Check for unsafe paths or query parameters
        unsafe_patterns = [
            r'\.\./',  # Directory traversal
            r'^\/',    # Absolute paths
            r'^~/',    # Home directory
            r';\s*',   # Command injection
            r'<\s*script'  # XSS attempts
        ]
        
        path = parsed_url.path.lower()
        
        for pattern in unsafe_patterns:
            if re.search(pattern, path):
                return False
        
        # Check file extension for unsafe types
        for ext in self.UNSAFE_EXTENSIONS:
            if path.endswith(f'.{ext}'):
                return False
        
        return True
    
    def process_html_page(self, url: str, html_content: str, depth: int, selectors: Dict, output_dir: str) -> None:
        """
        Process an HTML page: extract content and links.
        
        Args:
            url: Current URL
            html_content: HTML content
            depth: Current crawl depth
            selectors: CSS selectors for extraction
            output_dir: Directory to save downloaded documents
            
        Raises:
            ValueError: If there's an error parsing the HTML content
        """
        try:
            # Parse HTML with error handling
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract relevant content based on selectors
            content_selector = selectors.get('content')
            if content_selector:
                try:
                    content_elements = soup.select(content_selector)
                    if content_elements:
                        # Save the content
                        content = "\n".join([elem.get_text(strip=True) for elem in content_elements])
                        self.save_text_content(url, content, output_dir)
                    else:
                        logger.debug(f"No content found using selector '{content_selector}' for URL: {url}")
                except Exception as e:
                    logger.error(f"Error extracting content from {url}: {str(e)}")
                    # Save whole page as fallback
                    self.save_text_content(url, soup.get_text(strip=True), output_dir)
            else:
                # If no content selector is specified, save the whole page
                self.save_text_content(url, soup.get_text(strip=True), output_dir)
            
            # Extract links if not at max depth
            if depth < self.max_depth:
                self.extract_links(url, soup, depth, selectors)
        
        except Exception as e:
            logger.error(f"Error processing HTML page {url}: {str(e)}")
            raise ValueError(f"Error processing HTML page: {str(e)}")
    
    def extract_links(self, base_url: str, soup: BeautifulSoup, depth: int, selectors: Dict) -> None:
        """
        Extract links from a page.
        
        Args:
            base_url: Current URL
            soup: BeautifulSoup object
            depth: Current crawl depth
            selectors: CSS selectors for extraction
        """
        # Get the link selector if specified, otherwise use all links
        link_selector = selectors.get('links', 'a')
        
        try:
            # Extract links with error handling
            links = soup.select(link_selector)
            
            # Limit number of links to prevent explosion
            max_links = 100
            if len(links) > max_links:
                logger.warning(f"Found {len(links)} links on {base_url}, limiting to {max_links}")
                links = links[:max_links]
            
            # Process each link
            for link in links:
                href = link.get('href')
                
                if not href:
                    continue
                
                # Skip certain links
                if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                    continue
                
                # Normalize URL
                try:
                    if not href.startswith(('http://', 'https://')):
                        href = urljoin(base_url, href)
                except Exception as e:
                    logger.error(f"Error normalizing URL {href} from {base_url}: {str(e)}")
                    continue
                
                # Check if URL is valid, safe, and not already visited
                if self.is_valid_url(href) and self._is_safe_url(href) and href not in self.visited_urls:
                    self.urls_to_visit.append((href, depth + 1))
        
        except Exception as e:
            logger.error(f"Error extracting links from {base_url}: {str(e)}")
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid and allowed for crawling.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is valid, False otherwise
        """
        try:
            # Parse URL
            parsed_url = urlparse(url)
            
            # Check scheme
            if parsed_url.scheme not in ('http', 'https'):
                return False
            
            # Check if URL is a document type we want to download
            for doc_type in self.document_types:
                if url.lower().endswith(f'.{doc_type}'):
                    return True
            
            # Check netloc
            sources = self.config.get_sources()
            allowed_domains = [urlparse(source.get('url', '')).netloc for source in sources]
            
            # Filter out empty domains
            allowed_domains = [domain for domain in allowed_domains if domain]
            
            # Check if the domain or its subdomains are allowed
            return any(
                parsed_url.netloc == domain or parsed_url.netloc.endswith(f'.{domain}')
                for domain in allowed_domains
            )
        
        except Exception:
            return False
    
    def save_document(self, url: str, content: bytes, output_dir: str) -> None:
        """
        Save a binary document.
        
        Args:
            url: Source URL
            content: Binary content
            output_dir: Directory to save downloaded documents
            
        Raises:
            IOError: If there's an error saving the document
        """
        try:
            # Generate filename from URL
            filename = self.get_filename_from_url(url)
            
            # Validate filename
            if not self._is_safe_filename(filename):
                logger.warning(f"Unsafe filename generated for {url}, using hash instead")
                # Use hash as a safe alternative
                filename = f"{hashlib.md5(url.encode()).hexdigest()}.bin"
            
            # Save the document
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'wb') as f:
                f.write(content)
            
            # Save metadata
            self.save_metadata(url, output_path)
            
            self.document_count += 1
            logger.debug(f"Saved document: {output_path}")
        
        except IOError as e:
            logger.error(f"Error saving document from {url}: {str(e)}")
            raise
    
    def save_text_content(self, url: str, content: str, output_dir: str) -> None:
        """
        Save text content.
        
        Args:
            url: Source URL
            content: Text content
            output_dir: Directory to save downloaded documents
            
        Raises:
            IOError: If there's an error saving the content
        """
        try:
            # Generate filename from URL
            filename = self.get_filename_from_url(url, extension='txt')
            
            # Validate filename
            if not self._is_safe_filename(filename):
                logger.warning(f"Unsafe filename generated for {url}, using hash instead")
                filename = f"{hashlib.md5(url.encode()).hexdigest()}.txt"
            
            # Save the content
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(content)
            
            # Save metadata
            self.save_metadata(url, output_path)
            
            self.document_count += 1
            logger.debug(f"Saved text content: {output_path}")
        
        except IOError as e:
            logger.error(f"Error saving text content from {url}: {str(e)}")
            raise
    
    def _is_safe_filename(self, filename: str) -> bool:
        """
        Check if a filename is safe to use.
        
        Args:
            filename: Filename to check
            
        Returns:
            True if filename is safe, False otherwise
        """
        # Check for absolute paths
        if os.path.isabs(filename):
            return False
        
        # Check for directory traversal
        if '..' in filename:
            return False
        
        # Check for unsafe characters
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ';', '&']
        if any(char in filename for char in unsafe_chars):
            return False
        
        # Check for hidden files
        if filename.startswith('.'):
            return False
        
        # Check file extension
        _, ext = os.path.splitext(filename)
        if ext.lower()[1:] in self.UNSAFE_EXTENSIONS:
            return False
        
        return True
    
    def save_metadata(self, url: str, file_path: str) -> None:
        """
        Save metadata for a document.
        
        Args:
            url: Source URL
            file_path: Path to the saved file
            
        Raises:
            IOError: If there's an error saving the metadata
        """
        try:
            metadata_path = f"{file_path}.meta.json"
            metadata = {
                'url': url,
                'timestamp': time.time(),
                'headers': dict(self.headers),
                'file_path': file_path
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        
        except (IOError, TypeError) as e:
            logger.error(f"Error saving metadata for {url}: {str(e)}")
            raise
    
    def get_filename_from_url(self, url: str, extension: Optional[str] = None) -> str:
        """
        Generate a filename from a URL.
        
        Args:
            url: Source URL
            extension: Optional file extension override
            
        Returns:
            Generated filename
        """
        try:
            # Get the path from the URL
            path = urlparse(url).path
            
            # Extract the filename from the path
            filename = os.path.basename(path)
            
            # If filename is empty or doesn't have an extension, generate a hash-based name
            if not filename or '.' not in filename:
                # Generate a hash of the URL
                url_hash = hashlib.md5(url.encode()).hexdigest()
                
                # Use the extension if provided, otherwise default to 'html'
                ext = extension or 'html'
                filename = f"{url_hash}.{ext}"
            elif extension:
                # Replace the extension if provided
                filename = f"{os.path.splitext(filename)[0]}.{extension}"
            
            # Clean the filename
            filename = re.sub(r'[^\w\-\.]', '_', filename)
            
            # Limit filename length
            if len(filename) > 255:
                name, ext = os.path.splitext(filename)
                filename = f"{name[:245]}{ext}"
            
            return filename
        
        except Exception as e:
            logger.error(f"Error generating filename for URL {url}: {str(e)}")
            # Return a safe default
            return f"{hashlib.md5(url.encode()).hexdigest()}.{extension or 'html'}"
