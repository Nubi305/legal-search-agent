"""
Crawler module for the legal search agent.
"""

import os
import re
import time
import hashlib
import logging
from typing import Dict, List, Set, Tuple, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LegalCrawler')

class LegalCrawler:
    """Crawler for legal websites."""
    
    def __init__(self, config: Config):
        """
        Initialize the crawler.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.headers = config.get_headers()
        self.request_delay = config.get_request_delay()
        self.max_pages = config.get_max_pages()
        self.max_depth = config.get_max_depth()
        self.document_types = config.get_document_types()
        self.visited_urls: Set[str] = set()
        self.urls_to_visit: List[Tuple[str, int]] = []  # (url, depth)
        self.document_count = 0
    
    def crawl(self, output_dir: str = "downloaded_docs") -> None:
        """
        Crawl the legal websites.
        
        Args:
            output_dir: Directory to save downloaded documents
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        sources = self.config.get_sources()
        
        for source in sources:
            source_name = source.get('name', 'unknown')
            source_url = source.get('url')
            source_selectors = source.get('selectors', {})
            source_output_dir = os.path.join(output_dir, source_name)
            
            if not os.path.exists(source_output_dir):
                os.makedirs(source_output_dir)
            
            logger.info(f"Crawling source: {source_name} ({source_url})")
            
            self.visited_urls = set()
            self.urls_to_visit = [(source_url, 0)]
            self.document_count = 0
            
            with tqdm(total=self.max_pages, desc=f"Crawling {source_name}") as pbar:
                while self.urls_to_visit and self.document_count < self.max_pages:
                    url, depth = self.urls_to_visit.pop(0)
                    
                    if url in self.visited_urls:
                        continue
                    
                    try:
                        self.process_url(url, depth, source_selectors, source_output_dir)
                        self.visited_urls.add(url)
                        pbar.update(1)
                        
                        # Add delay between requests
                        time.sleep(self.request_delay)
                    
                    except Exception as e:
                        logger.error(f"Error processing URL {url}: {str(e)}")
    
    def process_url(self, url: str, depth: int, selectors: Dict, output_dir: str) -> None:
        """
        Process a URL: download content and extract links.
        
        Args:
            url: URL to process
            depth: Current crawl depth
            selectors: CSS selectors for extraction
            output_dir: Directory to save downloaded documents
        """
        logger.debug(f"Processing URL: {url} (depth: {depth})")
        
        # Download content
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to download {url}: {str(e)}")
            return
        
        # Determine content type
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Process based on content type
        if 'text/html' in content_type:
            self.process_html_page(url, response.text, depth, selectors, output_dir)
        elif any(doc_type in content_type for doc_type in ['pdf', 'msword', 'vnd.openxmlformats-officedocument']):
            self.save_document(url, response.content, output_dir)
        else:
            logger.debug(f"Skipping unsupported content type: {content_type}")
    
    def process_html_page(self, url: str, html_content: str, depth: int, selectors: Dict, output_dir: str) -> None:
        """
        Process an HTML page: extract content and links.
        
        Args:
            url: Current URL
            html_content: HTML content
            depth: Current crawl depth
            selectors: CSS selectors for extraction
            output_dir: Directory to save downloaded documents
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract relevant content based on selectors
        content_selector = selectors.get('content')
        if content_selector:
            content_elements = soup.select(content_selector)
            if content_elements:
                # Save the content
                content = "\n".join([elem.get_text(strip=True) for elem in content_elements])
                self.save_text_content(url, content, output_dir)
        else:
            # If no content selector is specified, save the whole page
            self.save_text_content(url, soup.get_text(strip=True), output_dir)
        
        # Extract links if not at max depth
        if depth < self.max_depth:
            self.extract_links(url, soup, depth, selectors)
    
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
        
        # Extract links
        for link in soup.select(link_selector):
            href = link.get('href')
            
            if not href:
                continue
            
            # Normalize URL
            if not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
            
            # Check if URL is valid and not already visited
            if self.is_valid_url(href) and href not in self.visited_urls:
                self.urls_to_visit.append((href, depth + 1))
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is valid, False otherwise
        """
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
        
        return parsed_url.netloc in allowed_domains
    
    def save_document(self, url: str, content: bytes, output_dir: str) -> None:
        """
        Save a binary document.
        
        Args:
            url: Source URL
            content: Binary content
            output_dir: Output directory
        """
        # Generate filename from URL
        filename = self.get_filename_from_url(url)
        
        # Save the document
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'wb') as f:
            f.write(content)
        
        # Save metadata
        self.save_metadata(url, output_path)
        
        self.document_count += 1
        logger.debug(f"Saved document: {output_path}")
    
    def save_text_content(self, url: str, content: str, output_dir: str) -> None:
        """
        Save text content.
        
        Args:
            url: Source URL
            content: Text content
            output_dir: Output directory
        """
        # Generate filename from URL
        filename = self.get_filename_from_url(url, extension='txt')
        
        # Save the content
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Save metadata
        self.save_metadata(url, output_path)
        
        self.document_count += 1
        logger.debug(f"Saved text content: {output_path}")
    
    def save_metadata(self, url: str, file_path: str) -> None:
        """
        Save metadata for a document.
        
        Args:
            url: Source URL
            file_path: Path to the saved file
        """
        metadata_path = f"{file_path}.meta.json"
        metadata = {
            'url': url,
            'timestamp': time.time(),
            'headers': dict(self.headers),
            'file_path': file_path
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def get_filename_from_url(self, url: str, extension: Optional[str] = None) -> str:
        """
        Generate a filename from a URL.
        
        Args:
            url: Source URL
            extension: Optional file extension override
            
        Returns:
            Generated filename
        """
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
        
        return filename