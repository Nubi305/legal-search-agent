"""
Document indexer module for the legal search agent.
"""

import os
import json
import logging
import pickle
from typing import Dict, List, Any, Optional

import chromadb
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('indexer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DocumentIndexer')

class DocumentIndexer:
    """Indexer for legal documents."""
    
    def __init__(self):
        """Initialize the document indexer."""
        self.embedding_model = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def index_directory(self, input_dir: str, index_dir: str) -> None:
        """
        Index all documents in a directory.
        
        Args:
            input_dir: Input directory with processed documents
            index_dir: Output directory for the index
        """
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        
        # Discover all processed documents
        documents = []
        for root, _, files in os.walk(input_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    documents.append(file_path)
        
        logger.info(f"Found {len(documents)} documents to index")
        
        # Load and process documents
        all_chunks = []
        metadatas = []
        
        for document_path in tqdm(documents, desc="Processing documents for indexing"):
            try:
                chunks, metadata = self.process_document_for_indexing(document_path)
                all_chunks.extend(chunks)
                metadatas.extend(metadata)
            except Exception as e:
                logger.error(f"Error processing document {document_path}: {str(e)}")
        
        logger.info(f"Created {len(all_chunks)} chunks for indexing")
        
        # Create and save the vector store
        self.create_vector_store(all_chunks, metadatas, index_dir)
    
    def process_document_for_indexing(self, document_path: str) -> tuple:
        """
        Process a document for indexing.
        
        Args:
            document_path: Path to the processed document
            
        Returns:
            Tuple of (text chunks, metadata)
        """
        # Load document
        with open(document_path, 'r', encoding='utf-8') as f:
            document = json.load(f)
        
        content = document.get('content', '')
        source = document.get('source', document_path)
        title = document.get('title', os.path.basename(document_path))
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(content)
        
        # Create metadata for each chunk
        metadata = []
        for i, _ in enumerate(chunks):
            metadata.append({
                'source': source,
                'title': title,
                'chunk': i,
                'document_path': document_path
            })
        
        return chunks, metadata
    
    def create_vector_store(self, texts: List[str], metadatas: List[Dict[str, Any]], index_dir: str) -> None:
        """
        Create and save the vector store.
        
        Args:
            texts: List of text chunks
            metadatas: List of metadata dictionaries
            index_dir: Output directory for the index
        """
        # Create the vector store
        vector_store = Chroma.from_texts(
            texts=texts,
            embedding=self.embedding_model,
            metadatas=metadatas,
            persist_directory=index_dir
        )
        
        # Save the text splitter configuration
        with open(os.path.join(index_dir, 'text_splitter.pkl'), 'wb') as f:
            pickle.dump(self.text_splitter, f)
        
        logger.info(f"Vector store created and saved to {index_dir}")
        
    def load_vector_store(self, index_dir: str) -> Chroma:
        """
        Load a vector store from disk.
        
        Args:
            index_dir: Directory containing the index
            
        Returns:
            Loaded vector store
        """
        # Load the vector store
        vector_store = Chroma(
            persist_directory=index_dir,
            embedding_function=self.embedding_model
        )
        
        return vector_store