"""
Search module for the legal search agent.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import pickle

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.chat_models import ChatOpenAI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LegalSearchEngine')

class LegalSearchEngine:
    """Search engine for legal documents."""
    
    def __init__(self, index_dir: str):
        """
        Initialize the search engine.
        
        Args:
            index_dir: Directory containing the index
        """
        self.index_dir = index_dir
        self.embedding_model = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0)
        
        # Load the vector store
        self.vector_store = self.load_vector_store()
        
        # Set up the retriever with contextual compression
        compressor = LLMChainExtractor.from_llm(self.llm)
        self.retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=self.vector_store.as_retriever(search_kwargs={"k": 10})
        )
    
    def load_vector_store(self) -> Chroma:
        """
        Load the vector store from disk.
        
        Returns:
            Loaded vector store
        """
        if not os.path.exists(self.index_dir):
            raise FileNotFoundError(f"Index directory not found: {self.index_dir}")
        
        # Load the vector store
        vector_store = Chroma(
            persist_directory=self.index_dir,
            embedding_function=self.embedding_model
        )
        
        return vector_store
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents matching a query.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for: {query}")
        
        # Get the raw documents
        docs = self.retriever.get_relevant_documents(query)
        
        # Format the results
        results = []
        for i, doc in enumerate(docs[:k]):
            # Extract document metadata
            metadata = doc.metadata
            source = metadata.get('source', 'Unknown')
            title = metadata.get('title', 'Untitled')
            document_path = metadata.get('document_path', '')
            
            # Calculate a simple relevance score
            # In a production system, you would want to use the actual similarity score
            score = 1.0 - (i * 0.1)  # Simple decreasing score based on position
            
            # Get the document content
            content = doc.page_content
            
            # Get the original document if available
            original_doc = self.get_original_document(document_path)
            
            # Add result
            results.append({
                'source': source,
                'title': title,
                'score': score,
                'content': content,
                'document_path': document_path,
                'original_document': original_doc
            })
        
        return results
    
    def get_original_document(self, document_path: str) -> Optional[Dict[str, Any]]:
        """
        Get the original document.
        
        Args:
            document_path: Path to the original document
            
        Returns:
            Original document or None if not found
        """
        if not document_path or not os.path.exists(document_path):
            return None
        
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading original document {document_path}: {str(e)}")
            return None
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query to extract key information.
        
        Args:
            query: Search query
            
        Returns:
            Analysis results
        """
        # This is a simple implementation that could be expanded
        # with more sophisticated NLP techniques
        analysis = {
            'query': query,
            'length': len(query),
            'is_question': query.endswith('?'),
            'keywords': self.extract_keywords(query)
        }
        
        return analysis
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Input text
            
        Returns:
            List of keywords
        """
        # This is a very simple keyword extraction algorithm
        # In a production system, you would want to use a more sophisticated approach
        
        # Remove punctuation and convert to lowercase
        cleaned_text = ''.join(c.lower() if c.isalnum() else ' ' for c in text)
        
        # Split into words
        words = cleaned_text.split()
        
        # Filter out common stopwords
        stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                    'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 
                    'by', 'about', 'as', 'of', 'that', 'this', 'these', 'those'}
        
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        return keywords
    
    def explain_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        Generate an explanation of the search results.
        
        Args:
            query: Search query
            results: Search results
            
        Returns:
            Explanation text
        """
        if not results:
            return "No results found for your query."
        
        explanation = f"Found {len(results)} documents related to your query: '{query}'\n\n"
        
        for i, result in enumerate(results):
            title = result.get('title', 'Untitled')
            source = result.get('source', 'Unknown')
            score = result.get('score', 0.0)
            
            explanation += f"{i+1}. {title} (from {source}, relevance: {score:.2f})\n"
        
        return explanation