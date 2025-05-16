"""
Test script for the legal search agent.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.crawler import LegalCrawler
from src.processor import DocumentProcessor
from src.indexer import DocumentIndexer
from src.search import LegalSearchEngine
from src.langchain_integration import LegalLangChain

def run_test():
    """Run a test of the legal search agent."""
    print("Starting Legal Search Agent test...")
    
    # Set up directories
    test_dirs = ["test_downloaded", "test_processed", "test_indexed"]
    for directory in test_dirs:
        os.makedirs(directory, exist_ok=True)
    
    # Step 1: Crawl
    print("\n--- Step 1: Crawling ---")
    config = Config.from_file("configs/test_config.json")
    crawler = LegalCrawler(config)
    
    print("Crawling legal websites...")
    crawler.crawl(output_dir=test_dirs[0])
    print(f"Crawling complete. Documents saved to {test_dirs[0]}")
    
    # Check if documents were downloaded
    downloaded_files = []
    for root, _, files in os.walk(test_dirs[0]):
        for file in files:
            if not file.endswith('.meta.json'):
                downloaded_files.append(os.path.join(root, file))
    
    print(f"Downloaded {len(downloaded_files)} documents")
    
    # If no documents were downloaded, use a sample
    if not downloaded_files:
        print("No documents downloaded, creating a sample document for testing...")
        sample_dir = os.path.join(test_dirs[0], "sample")
        os.makedirs(sample_dir, exist_ok=True)
        
        sample_content = """
        SUPREME COURT OF THE UNITED STATES
        
        SAMPLE OPINION
        
        CASE NO. 123-456
        
        In the matter of Legal Search Agent Testing
        
        Delivered by Chief Justice TEST
        
        Opinion of the Court:
        
        This is a sample legal opinion created for testing purposes. The question before this court
        is whether automated legal research tools can effectively crawl, process, and retrieve
        legal information.
        
        The court finds that modern technology, when properly implemented, can significantly
        enhance legal research capabilities. However, human review and judgment remain essential
        components of thorough legal research.
        
        In prior cases such as Technology v. Traditional Methods (2022), we established that
        digital tools serve as a supplement to, not a replacement for, trained legal professionals.
        
        The court hereby rules that the Legal Search Agent, as demonstrated, shows promising
        capabilities for assisting in legal research tasks.
        
        So ordered.
        """
        
        with open(os.path.join(sample_dir, "sample_opinion.txt"), "w") as f:
            f.write(sample_content)
        
        # Add a metadata file
        sample_metadata = """{
            "url": "https://example.com/sample/opinion",
            "timestamp": 1714945995.0,
            "headers": {"User-Agent": "LegalSearchAgent/1.0 (Test Run)"},
            "file_path": "test_downloaded/sample/sample_opinion.txt"
        }"""
        
        with open(os.path.join(sample_dir, "sample_opinion.txt.meta.json"), "w") as f:
            f.write(sample_metadata)
        
        downloaded_files = [os.path.join(sample_dir, "sample_opinion.txt")]
    
    # Step 2: Process
    print("\n--- Step 2: Processing ---")
    processor = DocumentProcessor()
    
    print("Processing documents...")
    processor.process_directory(test_dirs[0], test_dirs[1])
    print(f"Processing complete. Processed documents saved to {test_dirs[1]}")
    
    # Check if documents were processed
    processed_files = []
    for root, _, files in os.walk(test_dirs[1]):
        for file in files:
            processed_files.append(os.path.join(root, file))
    
    print(f"Processed {len(processed_files)} documents")
    
    # Step 3: Index
    print("\n--- Step 3: Indexing ---")
    
    try:
        indexer = DocumentIndexer()
        
        print("Indexing documents...")
        indexer.index_directory(test_dirs[1], test_dirs[2])
        print(f"Indexing complete. Index saved to {test_dirs[2]}")
        
        # Step 4: Search
        print("\n--- Step 4: Basic Search ---")
        search_engine = LegalSearchEngine(test_dirs[2])
        
        test_query = "legal technology effectiveness"
        print(f"Searching for: '{test_query}'")
        results = search_engine.search(test_query, k=3)
        
        print(f"Found {len(results)} results")
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"Source: {result['source']}")
            print(f"Relevance: {result['score']:.2f}")
            print(f"Content preview: {result['content'][:200]}...")
        
        # Step 5: LangChain Search (if OpenAI API key is available)
        print("\n--- Step 5: LangChain Search ---")
        
        if os.getenv("OPENAI_API_KEY"):
            try:
                legal_langchain = LegalLangChain(test_dirs[2])
                
                langchain_query = "How does the court view the role of technology in legal research?"
                print(f"LangChain query: '{langchain_query}'")
                
                response = legal_langchain.query(langchain_query)
                
                print("\nLangChain Answer:")
                print(response["answer"])
                print("\nSources:")
                for i, source in enumerate(response["sources"]):
                    print(f"Source {i+1}: {source.get('title', 'Unknown')}")
            except Exception as e:
                print(f"Error during LangChain search: {str(e)}")
                print("This test requires a valid OpenAI API key to be set in the .env file.")
        else:
            print("Skipping LangChain search - no OpenAI API key available.")
            print("Set OPENAI_API_KEY in your .env file to enable this test.")
    
    except Exception as e:
        print(f"Error during indexing/search: {str(e)}")
    
    print("\nTest completed!")
    
    # Cleanup
    print("\nTest directories:")
    for directory in test_dirs:
        print(f"- {os.path.abspath(directory)}")
    
    print("\nYou can now run more specific searches on the indexed data:")
    print(f"python main.py search --query \"your search query\" --index {test_dirs[2]}")
    print("or")
    print(f"python main.py search --query \"your search query\" --index {test_dirs[2]} --type langchain")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the test
    run_test()