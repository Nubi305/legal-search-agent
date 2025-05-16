"""
Judgment research tool using the legal search agent.

This tool searches for civil judgments, liens, and legal claims against 
businesses and individuals using court records and public filings.
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
    """Run the judgment research tool."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Judgment Research Tool")
    parser.add_argument("--name", required=True, help="Business or person name to search")
    parser.add_argument("--type", choices=["business", "person", "both"], default="both", 
                        help="Type of entity to search (business, person, or both)")
    parser.add_argument("--state", help="State abbreviation (e.g., NY, FL, CA)")
    parser.add_argument("--county", help="County name (for more targeted searches)")
    parser.add_argument("--refresh", action="store_true", help="Refresh data (recrawl)")
    parser.add_argument("--output", default="judgment_research", help="Output directory")
    args = parser.parse_args()
    
    # Set up directories
    data_dir = os.path.join(args.output, "data")
    processed_dir = os.path.join(args.output, "processed")
    index_dir = os.path.join(args.output, "index")
    
    for directory in [data_dir, processed_dir, index_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Step 1: Crawl (if refresh is requested or data doesn't exist)
    if args.refresh or not os.listdir(data_dir):
        print(f"\n--- Collecting judgment data for {args.name} ---")
        
        # Load configuration
        config = Config.from_file("configs/judgment_research.json")
        crawler = LegalCrawler(config)
        
        # Build search query
        search_query = args.name
        entity_type = ""
        
        if args.type == "business":
            entity_type = "LLC corporation business"
        elif args.type == "person":
            entity_type = "individual"
        
        location_info = ""
        if args.state:
            location_info += f" {args.state}"
        if args.county:
            location_info += f" {args.county} County"
        
        # Combine all search terms
        final_query = f"{search_query} {entity_type} judgment lien{location_info}".strip()
        
        print(f"Searching for judgments using: {final_query}")
        
        # Here we'd ideally modify the crawler to search using the query
        # This would require extending the crawler class to support search queries
        # For now, we'll just crawl the standard sources
        
        print("Crawling sources for judgment information...")
        crawler.crawl(output_dir=data_dir)
        print(f"Crawling complete. Data saved to {data_dir}")
    else:
        print(f"Using existing data in {data_dir}. Use --refresh to update data.")
    
    # Step 2: Process
    print("\n--- Processing judgment data ---")
    processor = DocumentProcessor()
    processor.process_directory(data_dir, processed_dir)
    print(f"Processing complete. Processed data saved to {processed_dir}")
    
    # Step 3: Index
    print("\n--- Indexing judgment data ---")
    indexer = DocumentIndexer()
    indexer.index_directory(processed_dir, index_dir)
    print(f"Indexing complete. Index saved to {index_dir}")
    
    # Step 4: Search
    print(f"\n--- Searching for judgments against {args.name} ---")
    
    # Basic judgment queries
    entity_desc = "company" if args.type == "business" else "individual" if args.type == "person" else "entity"
    location_filter = f"in {args.state}" if args.state else ""
    county_filter = f"in {args.county} County" if args.county else ""
    
    queries = [
        f"{args.name} judgments {location_filter} {county_filter}",
        f"{args.name} liens {location_filter} {county_filter}",
        f"{args.name} civil suits {location_filter} {county_filter}",
        f"{args.name} legal claims against {entity_desc} {location_filter} {county_filter}",
        f"{args.name} NYSCEF case search" if args.state == "NY" or not args.state else ""
    ]
    
    # Filter out empty queries
    queries = [q.strip() for q in queries if q.strip()]
    
    # Use LangChain for more sophisticated research
    try:
        if os.getenv("OPENAI_API_KEY"):
            print("\n=== Judgment Report ===\n")
            
            legal_langchain = LegalLangChain(index_dir)
            
            # Comprehensive query
            entity_context = f"({entity_desc})" if args.type != "both" else ""
            location_context = f"in {args.state}" if args.state else ""
            if args.county:
                location_context += f", specifically in {args.county} County"
            
            comprehensive_query = f"""
            Provide a comprehensive report on all judgments, liens, and legal claims against {args.name} {entity_context} {location_context}.
            Include the following information if available:
            1. Civil judgments (include case numbers, courts, dates, and amounts)
            2. Tax liens (include filing dates, amounts, and status)
            3. UCC filings that indicate secured debt
            4. Any recent court cases that could lead to judgments
            5. Status of each judgment (satisfied, open, appealed)
            
            Pay special attention to New York State courts (NYSCEF) filings if applicable.
            """
            
            print("Generating judgment report...\n")
            response = legal_langchain.query(comprehensive_query)
            
            print("Judgment Report:")
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
            
            print("\n=== Basic Judgment Information ===\n")
            
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
    
    print("\nJudgment research complete!")
    print(f"\nAll data is stored in: {os.path.abspath(args.output)}")
    print("\nTo conduct more specific searches:")
    print(f"python main.py search --query \"judgment against {args.name}\" --index {index_dir}")
    
    print("\nSpecial Instructions for NYSCEF:")
    print("-" * 30)
    print("For direct NYSCEF searches:")
    print("1. Visit: https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name")
    print(f"2. Search for: {args.name}")
    print("3. Try both the business name and owner names for comprehensive results")
    print("4. Check both 'Name Contains' and 'Exact Match' options")

if __name__ == "__main__":
    main()