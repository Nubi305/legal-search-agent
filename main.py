"""
Main entry point for the legal search agent.
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.crawler import LegalCrawler
from src.processor import DocumentProcessor
from src.indexer import DocumentIndexer
from src.search import LegalSearchEngine

def main():
    """Main function to run the legal search agent."""
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Legal Search Agent")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl legal websites")
    crawl_parser.add_argument("--config", required=True, help="Path to crawler configuration file")
    crawl_parser.add_argument("--output", default="downloaded_docs", help="Output directory for downloaded documents")
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process downloaded documents")
    process_parser.add_argument("--input", default="downloaded_docs", help="Input directory with downloaded documents")
    process_parser.add_argument("--output", default="processed_docs", help="Output directory for processed documents")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index processed documents")
    index_parser.add_argument("--input", default="processed_docs", help="Input directory with processed documents")
    index_parser.add_argument("--index", default="vector_stores", help="Index directory")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search legal information")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--index", default="vector_stores", help="Index directory")
    search_parser.add_argument("--results", type=int, default=5, help="Number of results to return")
    
    args = parser.parse_args()
    
    if args.command == "crawl":
        config = Config.from_file(args.config)
        crawler = LegalCrawler(config)
        crawler.crawl(output_dir=args.output)
    
    elif args.command == "process":
        processor = DocumentProcessor()
        processor.process_directory(args.input, args.output)
    
    elif args.command == "index":
        indexer = DocumentIndexer()
        indexer.index_directory(args.input, args.index)
    
    elif args.command == "search":
        search_engine = LegalSearchEngine(args.index)
        results = search_engine.search(args.query, k=args.results)
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"Source: {result['source']}")
            print(f"Relevance: {result['score']:.2f}")
            print(f"Content: {result['content'][:200]}...")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()