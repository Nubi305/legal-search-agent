"""
Document processor module for the legal search agent.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import re

import PyPDF2
from bs4 import BeautifulSoup
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DocumentProcessor')

class DocumentProcessor:
    """Processor for legal documents."""
    
    def __init__(self):
        """Initialize the document processor."""
        pass
    
    def process_directory(self, input_dir: str, output_dir: str) -> None:
        """
        Process all documents in a directory.
        
        Args:
            input_dir: Input directory with raw documents
            output_dir: Output directory for processed documents
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Discover all documents
        documents = []
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.endswith(('.txt', '.html', '.pdf', '.doc', '.docx')) and not file.endswith('.meta.json'):
                    file_path = os.path.join(root, file)
                    documents.append(file_path)
        
        logger.info(f"Found {len(documents)} documents to process")
        
        # Process each document
        for document in tqdm(documents, desc="Processing documents"):
            try:
                self.process_document(document, output_dir)
            except Exception as e:
                logger.error(f"Error processing document {document}: {str(e)}")
    
    def process_document(self, file_path: str, output_dir: str) -> None:
        """
        Process a single document.
        
        Args:
            file_path: Path to the document
            output_dir: Output directory for processed document
        """
        # Load metadata if available
        metadata = self.load_metadata(file_path)
        
        # Extract content based on file type
        if file_path.endswith('.txt'):
            content = self.process_text_file(file_path)
        elif file_path.endswith('.html'):
            content = self.process_html_file(file_path)
        elif file_path.endswith('.pdf'):
            content = self.process_pdf_file(file_path)
        elif file_path.endswith(('.doc', '.docx')):
            content = self.process_word_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_path}")
            return
        
        # Structure the extracted content
        structured_content = self.structure_content(content, file_path, metadata)
        
        # Save processed document
        self.save_processed_document(structured_content, file_path, output_dir)
    
    def load_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Load metadata for a document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Metadata dictionary
        """
        metadata_path = f"{file_path}.meta.json"
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {}
    
    def process_text_file(self, file_path: str) -> str:
        """
        Process a text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Extracted content
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def process_html_file(self, file_path: str) -> str:
        """
        Process an HTML file.
        
        Args:
            file_path: Path to the HTML file
            
        Returns:
            Extracted content
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text(separator=' ')
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def process_pdf_file(self, file_path: str) -> str:
        """
        Process a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted content
        """
        text = ""
        
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        
        return text
    
    def process_word_file(self, file_path: str) -> str:
        """
        Process a Word document.
        
        Args:
            file_path: Path to the Word document
            
        Returns:
            Extracted content
        """
        # Note: This is a placeholder. You would need additional libraries
        # like python-docx to handle Word documents properly.
        logger.warning(f"Word document processing not fully implemented: {file_path}")
        return f"[Content of Word document: {file_path}]"
    
    def structure_content(self, content: str, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Structure the extracted content.
        
        Args:
            content: Extracted content
            file_path: Path to the document
            metadata: Document metadata
            
        Returns:
            Structured content dictionary
        """
        # Extract key information
        title = self.extract_title(content, file_path)
        sections = self.extract_sections(content)
        entities = self.extract_entities(content)
        
        # Create structured content
        structured_content = {
            'title': title,
            'source': metadata.get('url', file_path),
            'content': content,
            'sections': sections,
            'entities': entities,
            'metadata': metadata
        }
        
        return structured_content
    
    def extract_title(self, content: str, file_path: str) -> str:
        """
        Extract the title from the content.
        
        Args:
            content: Document content
            file_path: Path to the document
            
        Returns:
            Extracted title
        """
        # Simple heuristic: Use the first non-empty line as the title
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line:
                return line
        
        # Fallback to file name
        return os.path.basename(file_path)
    
    def extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract sections from the content.
        
        Args:
            content: Document content
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        # Simple section detection: Look for capitalized lines followed by text
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if line is a potential section heading
            if re.match(r'^[A-Z\s]+$', line) and len(line) < 100:
                # Save previous section if exists
                if current_section:
                    sections.append({
                        'heading': current_section,
                        'content': '\n'.join(current_content)
                    })
                
                # Start new section
                current_section = line
                current_content = []
            else:
                # Add line to current section content
                if current_section:
                    current_content.append(line)
                else:
                    # Line is not part of any section
                    pass
        
        # Save last section if exists
        if current_section:
            sections.append({
                'heading': current_section,
                'content': '\n'.join(current_content)
            })
        
        return sections
    
    def extract_entities(self, content: str) -> Dict[str, List[str]]:
        """
        Extract entities from the content.
        
        Args:
            content: Document content
            
        Returns:
            Dictionary of entity types and lists of entities
        """
        entities = {
            'case_numbers': [],
            'dates': [],
            'courts': [],
            'judges': [],
            'parties': []
        }
        
        # Simple pattern matching for case numbers
        case_pattern = r'\b\d+\s*-\s*[a-zA-Z0-9]+\b'
        case_matches = re.findall(case_pattern, content)
        entities['case_numbers'] = case_matches
        
        # Simple pattern matching for dates
        date_pattern = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
        date_matches = re.findall(date_pattern, content)
        entities['dates'] = date_matches
        
        # Note: For more sophisticated entity extraction, you would want to use
        # named entity recognition (NER) from a library like spaCy.
        
        return entities
    
    def save_processed_document(self, structured_content: Dict[str, Any], original_path: str, output_dir: str) -> None:
        """
        Save processed document.
        
        Args:
            structured_content: Structured content dictionary
            original_path: Original document path
            output_dir: Output directory
        """
        # Generate output path
        rel_path = os.path.relpath(original_path, os.path.dirname(original_path))
        output_path = os.path.join(output_dir, f"{os.path.splitext(rel_path)[0]}.json")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save structured content
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structured_content, f, indent=2)
        
        logger.debug(f"Saved processed document: {output_path}")