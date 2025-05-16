"""
Company status research tool using the legal search agent.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.crawler import LegalCrawler
from src.processor import DocumentProcessor
from src.indexer import DocumentIndexer
from src.langchain_integration import LegalLangChain
from src.search import LegalSearchEngine

def main():
    """Run the company status research tool."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Company Status Research Tool")
    parser.add_argument("--company", required=True, help="Company name to research")
    parser.add_argument("--state", help="State abbreviation (e.g., FL, NY, CA)")
    parser.add_argument("--refresh", action="store_true", help="Refresh data (recrawl)")
    parser.add_argument("--output", default="company_research", help="Output directory")
    args = parser.parse_args()
    
    # Set up directories
    data_dir = os.path.join(args.output, "data")
    processed_dir = os.path.join(args.output, "processed")
    index_dir = os.path.join(args.output, "index")
    
    for directory in [data_dir, processed_dir, index_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Step 1: Crawl (if refresh is requested or data doesn't exist)
    if args.refresh or not os.listdir(data_dir):
        print(f"\n--- Collecting data for {args.company} ---")
        
        # Load configuration
        config = Config.from_file("configs/enhanced_business_research.json")
        crawler = LegalCrawler(config)
        
        # Modify crawler behavior to target specific company
        # This is a simple approach - you might want to implement more sophisticated targeting
        company_query = args.company
        if args.state:
            company_query += f" {args.state}"
        
        print(f"Searching for: {company_query}")
        
        # Here we'd ideally modify the crawler to search specifically for the company
        # This would require extending the crawler class to support search queries
        # For now, we'll just crawl the standard sources
        
        print("Crawling sources for company information...")
        crawler.crawl(output_dir=data_dir)
        print(f"Crawling complete. Data saved to {data_dir}")
    else:
        print(f"Using existing data in {data_dir}. Use --refresh to update data.")
    
    # Step 2: Process
    print("\n--- Processing company data ---")
    processor = DocumentProcessor()
    processor.process_directory(data_dir, processed_dir)
    print(f"Processing complete. Processed data saved to {processed_dir}")
    
    # Step 3: Index
    print("\n--- Indexing company data ---")
    indexer = DocumentIndexer()
    indexer.index_directory(processed_dir, index_dir)
    print(f"Indexing complete. Index saved to {index_dir}")
    
    # Step 4: Search
    print(f"\n--- Researching {args.company} ---")
    
    # Basic company status queries
    queries = [
        f"Is {args.company} an active corporation",
        f"{args.company} business registration status",
        f"{args.company} corporate status" + (f" in {args.state}" if args.state else ""),
        f"{args.company} legal standing",
        f"{args.company} incorporation date"
    ]
    
    # Use LangChain for more sophisticated research
    try:
        if os.getenv("OPENAI_API_KEY"):
            print("\n=== Company Status Report ===\n")
            
            legal_langchain = LegalLangChain(index_dir)
            
            # Comprehensive query
            comprehensive_query = f"""
            Provide a comprehensive status report on the company named {args.company}
            {f'in {args.state}' if args.state else ''}. Include the following information if available:
            1. Current registration status (active, inactive, dissolved)
            2. State of incorporation
            3. Registration/filing date
            4. Any recent legal actions or filings
            5. Corporate officers or directors
            6. Registered agent information
            """
            
            print("Generating company status report...\n")
            response = legal_langchain.query(comprehensive_query)
            
            print("Company Status Report:")
            print("-" * 50)
            print(response["answer"])
            print("-" * 50)
            print("\nSources:")
            for i, source in enumerate(response["sources"][:3]):
                print(f"{i+1}. {source.get('source', 'Unknown')}")
            
        else:
            print("\nFor more detailed analysis, set your OPENAI_API_KEY in the .env file.")
            
            # Fallback to basic search
            search_engine = LegalSearchEngine(index_dir)
            
            print("\n=== Basic Company Information ===\n")
            
            for query in queries:
                print(f"Query: {query}")
                results = search_engine.search(query, k=2)
                
                if results:
                    for i, result in enumerate(results):
                        print(f"\nResult {i+1}:")
                        print(f"Source: {result['source']}")
                        print(f"Content: {result['content'][:200]}...")
                else:
                    print("No results found for this query.")
                
                print("\n" + "-" * 50)
    
    except Exception as e:
        print(f"Error during search: {str(e)}")
    
    print("\nResearch complete!")
    print(f"\nAll data is stored in: {os.path.abspath(args.output)}")
    print("\nTo conduct more specific searches:")
    print(f"python main.py search --query \"your query about {args.company}\" --index {index_dir}")

if __name__ == "__main__":
    main()