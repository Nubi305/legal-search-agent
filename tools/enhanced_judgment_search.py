"""
Enhanced judgment and lien search tool using the legal search agent.

This tool is specialized for searching judgments, liens, and legal claims against 
businesses and individuals with improved handling of BlackBookOnline and NYSCEF data.
"""

import os
import sys
import argparse
from typing import Dict, List, Any, Optional
import json
import time
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.crawler import LegalCrawler
from src.processor import DocumentProcessor
from src.indexer import DocumentIndexer
from src.langchain_integration import LegalLangChain
from src.search import LegalSearchEngine
from src.enhanced_legal_schemas import EnhancedLegalSchemas, LegalSearchPrompts

# Try to import Firecrawl integration
try:
    from src.firecrawl_integration import FirecrawlClient
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    print("Note: Firecrawl integration not available. Some features will be limited.")

def search_judgments(args):
    """Search for judgments and liens against a specific entity."""
    # Set up directories
    data_dir = os.path.join(args.output, "data")
    processed_dir = os.path.join(args.output, "processed")
    index_dir = os.path.join(args.output, "index")
    results_dir = os.path.join(args.output, "results")
    
    for directory in [data_dir, processed_dir, index_dir, results_dir]:
        os.makedirs(directory, exist_ok=True)
    
    print(f"\n=== Judgment & Lien Search for: {args.name} ===")
    print(f"Entity Type: {args.type}")
    if args.state:
        print(f"State: {args.state}")
    if args.county:
        print(f"County: {args.county}")
    
    # Step 1: Build search parameters
    entity_type = "business" if args.type == "business" else "individual" if args.type == "person" else "entity"
    location_context = f"in {args.state}" if args.state else ""
    if args.county:
        location_context += f", {args.county} County"
    
    # Step 2: Search using standard crawler or Firecrawl
    if FIRECRAWL_AVAILABLE and args.use_firecrawl:
        search_with_firecrawl(args, entity_type, location_context, results_dir)
    else:
        search_with_standard_crawler(args, data_dir, processed_dir, index_dir)
    
    # Step 3: Generate summary report
    if os.getenv("OPENAI_API_KEY"):
        generate_judgment_summary(args, index_dir, entity_type, location_context, results_dir)
    else:
        print("\nTo generate a summarized report, please set OPENAI_API_KEY in your .env file.")
    
    print("\nJudgment search completed successfully!")
    print(f"Results are saved in: {os.path.abspath(results_dir)}")

def search_with_firecrawl(args, entity_type, location_context, results_dir):
    """Use Firecrawl to extract structured judgment data."""
    client = FirecrawlClient(api_key=args.api_key)
    
    print("\n--- Using Firecrawl for advanced extraction ---")
    
    # Target URLs based on search parameters
    target_urls = []
    
    # NYSCEF search (for NY state)
    if not args.state or args.state.upper() == "NY":
        target_urls.append("https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name")
        print("Added NYSCEF case search to targets")
    
    # BlackBookOnline searches
    target_urls.append("https://www.blackbookonline.info/USA-Corporations.aspx")
    print("Added BlackBookOnline corporate search to targets")
    
    if args.state:
        state_abbr = args.state.upper()
        state_url = f"https://www.blackbookonline.info/{state_abbr}-Counties.aspx"
        target_urls.append(state_url)
        print(f"Added {state_abbr} county records search to targets")
    else:
        target_urls.append("https://www.blackbookonline.info/USA-County-Public-Records.aspx")
        print("Added nationwide county records search to targets")
    
    target_urls.append("https://www.blackbookonline.info/USA-UCC-Filings.aspx")
    print("Added UCC filings search to targets")
    
    # Batch process the URLs
    results = []
    search_name = args.name.replace(" ", "+")
    
    print(f"\nSearching for: {args.name}")
    
    for url in target_urls:
        print(f"\nProcessing: {url}")
        
        # Determine the appropriate schema or prompt
        schema = None
        prompt = None
        
        if "nyscef" in url.lower() or "courts.state.ny.us" in url.lower():
            schema = EnhancedLegalSchemas.nyscef_case_schema()
            prompt = LegalSearchPrompts.nyscef_case_extraction()
            search_url = f"{url}&PartyName={search_name}"
        elif "corporations" in url.lower() or "secretary" in url.lower():
            schema = EnhancedLegalSchemas.secretary_of_state_schema()
            prompt = LegalSearchPrompts.business_entity_extraction()
            search_url = url  # Will map and search from landing page
        else:
            schema = EnhancedLegalSchemas.judgment_lien_schema()
            prompt = LegalSearchPrompts.judgment_lien_extraction()
            search_url = url  # Will map and search from landing page
        
        try:
            # First try to map the website to find relevant links
            print("Mapping site for relevant links...")
            site_links = client.map_website(url, search=args.name)
            
            # If we found relevant links, process them
            if site_links and len(site_links) > 0:
                print(f"Found {len(site_links)} relevant links")
                
                # Limit to first 5 most relevant links
                process_links = site_links[:min(5, len(site_links))]
                
                # Extract data from each link
                for link in process_links:
                    print(f"Extracting data from: {link}")
                    
                    try:
                        # Use either schema or prompt-based extraction
                        if args.prefer_prompts:
                            result = client.extract_structured_data([link], prompt=prompt)
                        else:
                            result = client.extract_structured_data([link], schema=schema)
                        
                        if result and 'data' in result:
                            results.append(result['data'])
                    except Exception as e:
                        print(f"Error extracting data from {link}: {str(e)}")
            else:
                # If no relevant links found, try direct extraction
                print("No relevant links found, trying direct extraction...")
                
                if "nyscef" in url.lower() or "courts.state.ny.us" in url.lower():
                    # NYSCEF requires a direct search
                    print(f"Searching NYSCEF for: {args.name}")
                    result = client.extract_structured_data([search_url], schema=schema)
                    
                    if result and 'data' in result:
                        results.append(result['data'])
                else:
                    # For BlackBookOnline, try to scrape the main page
                    print(f"Scraping main page: {url}")
                    result = client.scrape_url(url, formats=["markdown", "json"], json_schema=schema)
                    
                    if result and 'json' in result:
                        results.append(result['json'])
        
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
    
    # Save results
    if results:
        results_file = os.path.join(results_dir, f"{args.name.replace(' ', '_')}_judgment_search.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nExtracted {len(results)} data points")
        print(f"Results saved to: {results_file}")
    else:
        print("\nNo structured data could be extracted")

def search_with_standard_crawler(args, data_dir, processed_dir, index_dir):
    """Use standard crawler to search for judgments."""
    # Step 1: Crawl (if refresh is requested or data doesn't exist)
    if args.refresh or not os.listdir(data_dir):
        print("\n--- Collecting judgment data ---")
        
        # Load configuration
        config = Config.from_file("configs/enhanced_judgment_research.json")
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
    
    # Perform basic search
    search_engine = LegalSearchEngine(index_dir)
    all_results = []
    
    print("\n=== Basic Judgment Information ===\n")
    
    for query in queries:
        print(f"Query: {query}")
        results = search_engine.search(query, k=3)
        
        if results:
            for i, result in enumerate(results):
                print(f"\nResult {i+1}:")
                print(f"Source: {result['source']}")
                print(f"Content: {result['content'][:200]}...")
                all_results.append(result)
        else:
            print("No results found for this query.")
        
        print("\n" + "-" * 50)
    
    # Save basic search results
    if all_results:
        results_file = os.path.join(args.output, "results", f"{args.name.replace(' ', '_')}_search_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\nSaved search results to: {results_file}")

def generate_judgment_summary(args, index_dir, entity_type, location_context, results_dir):
    """Generate a comprehensive summary report using LangChain."""
    print("\n--- Generating Comprehensive Judgment Report ---")
    
    legal_langchain = LegalLangChain(index_dir)
    
    # Comprehensive query
    comprehensive_query = f"""
    Provide a comprehensive report on all judgments, liens, and legal claims against {args.name} ({entity_type}) {location_context}.
    Include the following information if available:
    1. Civil judgments (include case numbers, courts, dates, and amounts)
    2. Tax liens (include filing dates, amounts, and status)
    3. UCC filings that indicate secured debt
    4. Any recent court cases that could lead to judgments
    5. Status of each judgment (satisfied, open, appealed)
    
    Pay special attention to New York State courts (NYSCEF) filings if applicable.
    
    Format the report with clear sections for:
    - Summary of Findings
    - Active Judgments & Liens
    - Satisfied/Released Judgments & Liens
    - Pending Legal Actions
    - Total Monetary Exposure
    
    For each judgment or lien, list:
    * Case/File Number
    * Court/Filing Location
    * Date
    * Amount
    * Status
    * Creditor/Plaintiff
    """
    
    print("Generating judgment report...\n")
    response = legal_langchain.query(comprehensive_query)
    
    # Save the report
    report_file = os.path.join(results_dir, f"{args.name.replace(' ', '_')}_judgment_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Judgment & Lien Report for {args.name}\n\n")
        f.write(f"**Entity Type:** {entity_type}\n")
        if location_context:
            f.write(f"**Location:** {location_context}\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d')}\n\n")
        f.write(response["answer"])
        
        # Add sources
        f.write("\n\n## Sources\n\n")
        for i, source in enumerate(response["sources"][:5]):
            f.write(f"{i+1}. {source.get('source', 'Unknown')}\n")
    
    print(f"Report saved to: {report_file}")
    
    # Print a short summary to the console
    print("\nSummary of Findings:")
    print("-" * 50)
    
    # Extract and print just the first section (summary)
    lines = response["answer"].split('\n')
    in_summary = False
    summary_lines = []
    
    for line in lines:
        if "Summary" in line and not in_summary:
            in_summary = True
            continue
        elif in_summary and (line.startswith('#') or line.startswith('##') or line.startswith('**')):
            break
        elif in_summary:
            summary_lines.append(line)
    
    if summary_lines:
        print('\n'.join(summary_lines))
    else:
        # If we couldn't extract just the summary, print the first 10 lines
        print('\n'.join(lines[:10]) + "\n...")
    
    print("-" * 50)
    print(f"\nFull report saved to: {report_file}")

def main():
    """Run the enhanced judgment and lien search tool."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Enhanced Judgment & Lien Search Tool")
    parser.add_argument("--name", required=True, help="Business or person name to search")
    parser.add_argument("--type", choices=["business", "person", "both"], default="both", 
                        help="Type of entity to search (business, person, or both)")
    parser.add_argument("--state", help="State abbreviation (e.g., NY, FL, CA)")
    parser.add_argument("--county", help="County name (for more targeted searches)")
    parser.add_argument("--refresh", action="store_true", help="Refresh data (recrawl)")
    parser.add_argument("--output", default="enhanced_judgment_search", help="Output directory")
    
    # Firecrawl-specific options
    if FIRECRAWL_AVAILABLE:
        parser.add_argument("--use-firecrawl", action="store_true", help="Use Firecrawl for enhanced extraction")
        parser.add_argument("--api-key", help="Firecrawl API key (defaults to FIRECRAWL_API_KEY env var)")
        parser.add_argument("--prefer-prompts", action="store_true", 
                          help="Prefer prompt-based extraction over schema-based extraction")
    
    args = parser.parse_args()
    
    # Run the search
    search_judgments(args)
    
    # Print additional guidance
    print("\nNYSCEF Direct Search Instructions:")
    print("-" * 30)
    print("For direct NYSCEF searches:")
    print("1. Visit: https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name")
    print(f"2. Search for: {args.name}")
    print("3. Try both the business name and owner names for comprehensive results")
    print("4. Check both 'Name Contains' and 'Exact Match' options")
    
    print("\nBlackBookOnline Direct Search Instructions:")
    print("-" * 30)
    print("For direct BlackBookOnline searches:")
    print("1. Visit: https://www.blackbookonline.info/USA-Corporations.aspx")
    print(f"2. Search for Secretary of State records for {args.name}")
    print("3. Visit: https://www.blackbookonline.info/USA-County-Public-Records.aspx")
    print(f"4. Search for county records for {args.name}")
    print("5. Visit: https://www.blackbookonline.info/USA-UCC-Filings.aspx")
    print(f"6. Search for UCC filings for {args.name}")

if __name__ == "__main__":
    main()