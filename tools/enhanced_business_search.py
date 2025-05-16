"""
Enhanced business entity search tool using the legal search agent.

This tool is specialized for searching business entities from Secretary of State
databases and linking them to owners/registered agents, with improved handling
of BlackBookOnline data sources.
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

def search_business_entities(args):
    """Search for business entities and link to owners."""
    # Set up directories
    data_dir = os.path.join(args.output, "data")
    processed_dir = os.path.join(args.output, "processed")
    index_dir = os.path.join(args.output, "index")
    results_dir = os.path.join(args.output, "results")
    
    for directory in [data_dir, processed_dir, index_dir, results_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Display search parameters
    search_term = args.business if args.business else args.owner
    search_type = "Business Name" if args.business else "Owner/Officer Name"
    
    print(f"\n=== Business Entity Search ===")
    print(f"Search Term: {search_term}")
    print(f"Search Type: {search_type}")
    if args.state:
        print(f"State: {args.state}")
    
    # Build search query
    location_context = f"in {args.state}" if args.state else ""
    
    # Use either Firecrawl or standard crawler
    if FIRECRAWL_AVAILABLE and args.use_firecrawl:
        search_with_firecrawl(args, search_term, search_type, location_context, results_dir)
    else:
        search_with_standard_crawler(args, data_dir, processed_dir, index_dir, results_dir)
    
    # Generate summary report
    if os.getenv("OPENAI_API_KEY"):
        generate_business_summary(args, index_dir, search_term, search_type, location_context, results_dir)
    else:
        print("\nTo generate a summarized report, please set OPENAI_API_KEY in your .env file.")
    
    print("\nBusiness entity search completed successfully!")
    print(f"Results are saved in: {os.path.abspath(results_dir)}")

def search_with_firecrawl(args, search_term, search_type, location_context, results_dir):
    """Use Firecrawl to extract structured business entity data."""
    client = FirecrawlClient(api_key=args.api_key)
    
    print("\n--- Using Firecrawl for advanced extraction ---")
    
    # Target URLs based on search parameters
    target_urls = []
    
    # BlackBookOnline main corporate search
    target_urls.append("https://www.blackbookonline.info/USA-Corporations.aspx")
    print("Added BlackBookOnline corporate search to targets")
    
    # State-specific Secretary of State
    if args.state:
        state_abbr = args.state.upper()
        
        # BlackBookOnline state page
        state_url = f"https://www.blackbookonline.info/{state_abbr}-Secretary-of-State.aspx"
        target_urls.append(state_url)
        print(f"Added {state_abbr} Secretary of State search to targets")
        
        # Try direct SOS sites for common states
        if state_abbr == "NY":
            target_urls.append("https://apps.dos.ny.gov/publicInquiry/")
            print("Added NY Department of State search to targets")
        elif state_abbr == "FL":
            target_urls.append("https://dos.myflorida.com/sunbiz/search/")
            print("Added FL Sunbiz search to targets")
        elif state_abbr == "CA":
            target_urls.append("https://businesssearch.sos.ca.gov/")
            print("Added CA SOS business search to targets")
        elif state_abbr == "TX":
            target_urls.append("https://mycpa.cpa.state.tx.us/coa/")
            print("Added TX Comptroller search to targets")
    else:
        # If no state specified, add OpenCorporates
        target_urls.append("https://opencorporates.com/")
        print("Added OpenCorporates search to targets")
    
    # Batch process the URLs
    results = []
    
    # Format search term for URL
    search_param = search_term.replace(" ", "+")
    
    print(f"\nSearching for: {search_term}")
    
    for url in target_urls:
        print(f"\nProcessing: {url}")
        
        # Determine schema and how to search
        schema = EnhancedLegalSchemas.secretary_of_state_schema()
        prompt = LegalSearchPrompts.business_entity_extraction()
        
        try:
            # First try to map the website to find relevant links
            print("Mapping site for relevant links...")
            site_links = client.map_website(url, search=search_term)
            
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
                # If no relevant links found, try direct extraction from search page
                print("No relevant links found, trying direct search...")
                
                if "sos.ny.gov" in url.lower() or "sunbiz" in url.lower() or "businesssearch" in url.lower():
                    # Direct search of state SOS site
                    search_url = f"{url}?q={search_param}"
                    print(f"Searching SOS site: {search_url}")
                    
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
        results_file = os.path.join(results_dir, f"{search_term.replace(' ', '_')}_business_search.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nExtracted {len(results)} business records")
        print(f"Results saved to: {results_file}")
        
        # Print a sample of the data
        print("\nSample of extracted data:")
        for i, result in enumerate(results[:2]):
            print(f"\nBusiness Record {i+1}:")
            
            # Format entity info
            entity_name = result.get('entity_name', 'Unknown')
            entity_type = result.get('entity_type', 'Unknown')
            entity_number = result.get('entity_number', 'N/A')
            status = result.get('status', 'Unknown')
            
            print(f"Name: {entity_name}")
            print(f"Type: {entity_type}")
            print(f"Number: {entity_number}")
            print(f"Status: {status}")
            
            # Show registered agent if available
            if 'registered_agent' in result and result['registered_agent']:
                agent = result['registered_agent']
                if isinstance(agent, dict):
                    agent_name = agent.get('name', 'Unknown')
                    agent_address = agent.get('address', 'Unknown')
                    print(f"Registered Agent: {agent_name}")
                    print(f"Agent Address: {agent_address}")
                else:
                    print(f"Registered Agent: {agent}")
            
            # Show principals if available
            if 'principals' in result and result['principals'] and len(result['principals']) > 0:
                print("Principals/Officers:")
                for principal in result['principals'][:3]:
                    if isinstance(principal, dict):
                        principal_name = principal.get('name', 'Unknown')
                        principal_title = principal.get('title', 'Unknown')
                        print(f"  - {principal_name} ({principal_title})")
                    else:
                        print(f"  - {principal}")
    else:
        print("\nNo structured data could be extracted")

def search_with_standard_crawler(args, data_dir, processed_dir, index_dir, results_dir):
    """Use standard crawler to search for business entities."""
    # Step 1: Crawl (if refresh is requested or data doesn't exist)
    if args.refresh or not os.listdir(data_dir):
        print("\n--- Collecting business entity data ---")
        
        # Load configuration
        config = Config.from_file("configs/enhanced_business_research.json")
        crawler = LegalCrawler(config)
        
        # Build search query
        search_term = args.business if args.business else args.owner
        search_type = "corporation LLC entity" if args.business else "registered agent officer owner"
        
        location_info = ""
        if args.state:
            location_info += f" {args.state}"
        
        # Combine all search terms
        final_query = f"{search_term} {search_type}{location_info}".strip()
        
        print(f"Searching for business entities using: {final_query}")
        
        print("Crawling sources for business entity information...")
        crawler.crawl(output_dir=data_dir)
        print(f"Crawling complete. Data saved to {data_dir}")
    else:
        print(f"Using existing data in {data_dir}. Use --refresh to update data.")
    
    # Step 2: Process
    print("\n--- Processing business entity data ---")
    processor = DocumentProcessor()
    processor.process_directory(data_dir, processed_dir)
    print(f"Processing complete. Processed data saved to {processed_dir}")
    
    # Step 3: Index
    print("\n--- Indexing business entity data ---")
    indexer = DocumentIndexer()
    indexer.index_directory(processed_dir, index_dir)
    print(f"Indexing complete. Index saved to {index_dir}")
    
    # Step 4: Search
    search_term = args.business if args.business else args.owner
    search_type = "business name" if args.business else "owner or registered agent"
    location_filter = f"in {args.state}" if args.state else ""
    
    print(f"\n--- Searching for {search_term} as {search_type} {location_filter} ---")
    
    # Basic entity queries
    queries = []
    
    if args.business:
        queries.extend([
            f"{search_term} LLC corporation {location_filter}",
            f"{search_term} business entity status {location_filter}",
            f"{search_term} secretary of state registration {location_filter}",
            f"{search_term} corporate officers {location_filter}",
            f"{search_term} registered agent {location_filter}"
        ])
    else:  # Owner search
        queries.extend([
            f"{search_term} business owner {location_filter}",
            f"{search_term} registered agent {location_filter}",
            f"{search_term} corporate officer {location_filter}",
            f"{search_term} principal member manager {location_filter}",
            f"{search_term} owns LLC corporation {location_filter}"
        ])
    
    # Filter out empty queries
    queries = [q.strip() for q in queries if q.strip()]
    
    # Perform basic search
    search_engine = LegalSearchEngine(index_dir)
    all_results = []
    
    print("\n=== Basic Business Entity Information ===\n")
    
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
        results_file = os.path.join(results_dir, f"{search_term.replace(' ', '_')}_search_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\nSaved search results to: {results_file}")

def generate_business_summary(args, index_dir, search_term, search_type, location_context, results_dir):
    """Generate a comprehensive business summary report using LangChain."""
    print("\n--- Generating Comprehensive Business Report ---")
    
    legal_langchain = LegalLangChain(index_dir)
    
    # Comprehensive query
    comprehensive_query = ""
    
    if args.business:
        comprehensive_query = f"""
        Provide a comprehensive report on the business entity "{search_term}" {location_context}.
        Include the following information if available:
        1. Business name and any alternative names (DBAs)
        2. Entity type (LLC, Corporation, etc.)
        3. Entity number/filing number
        4. State of registration
        5. Current status (Active, Inactive, Dissolved)
        6. Formation/Registration date
        7. Registered agent name and address
        8. Principal officers, directors, members, or managers
        9. Business addresses (both mailing and physical)
        10. Whether the entity is in good standing
        11. Annual report information
        
        If multiple entities are found with similar names, list them all with their basic information.
        """
    else:  # Owner search
        comprehensive_query = f"""
        Provide a comprehensive report on all business entities associated with "{search_term}" as an owner, registered agent, or officer {location_context}.
        Include the following information for each business entity:
        1. Business name
        2. Entity type (LLC, Corporation, etc.)
        3. Entity number/filing number
        4. State of registration
        5. Current status (Active, Inactive, Dissolved)
        6. Formation/Registration date
        7. Role of "{search_term}" in the business (Owner, Officer, Registered Agent, etc.)
        8. Any other officers, directors, members, or managers
        
        Summarize all the active business entities associated with this person.
        If multiple people with the same name are found, please distinguish between them if possible.
        """
    
    print("Generating business entity report...\n")
    response = legal_langchain.query(comprehensive_query)
    
    # Save the report
    report_file = os.path.join(results_dir, f"{search_term.replace(' ', '_')}_business_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Business Entity Report for {search_term}\n\n")
        f.write(f"**Search Type:** {search_type}\n")
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
    first_section = []
    
    # Get first 10 non-empty lines or until second heading
    count = 0
    for line in lines:
        if line.strip() == "":
            continue
        if count > 0 and (line.startswith('#') or line.startswith('##')):
            break
        first_section.append(line)
        count += 1
        if count >= 10:
            first_section.append("...")
            break
    
    if first_section:
        print('\n'.join(first_section))
    else:
        # If we couldn't extract just the first section, print the first 10 lines
        print('\n'.join(lines[:10]) + "\n...")
    
    print("-" * 50)
    print(f"\nFull report saved to: {report_file}")

def main():
    """Run the enhanced business entity search tool."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Enhanced Business Entity Search Tool")
    parser.add_argument("--business", help="Business name to search")
    parser.add_argument("--owner", help="Owner name to search")
    parser.add_argument("--state", help="State abbreviation (e.g., NY, FL, CA)")
    parser.add_argument("--refresh", action="store_true", help="Refresh data (recrawl)")
    parser.add_argument("--output", default="enhanced_business_search", help="Output directory")
    
    # Firecrawl-specific options
    if FIRECRAWL_AVAILABLE:
        parser.add_argument("--use-firecrawl", action="store_true", help="Use Firecrawl for enhanced extraction")
        parser.add_argument("--api-key", help="Firecrawl API key (defaults to FIRECRAWL_API_KEY env var)")
        parser.add_argument("--prefer-prompts", action="store_true", 
                          help="Prefer prompt-based extraction over schema-based extraction")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.business and not args.owner:
        parser.error("Either --business or --owner is required")
    
    if args.business and args.owner:
        parser.error("Cannot use both --business and --owner at the same time")
    
    # Run the search
    search_business_entities(args)
    
    # Print additional guidance
    print("\nBlackBookOnline Direct Search Instructions:")
    print("-" * 30)
    print("For direct BlackBookOnline searches:")
    print("1. Visit: https://www.blackbookonline.info/USA-Corporations.aspx")
    search_term = args.business if args.business else args.owner
    if args.business:
        print(f"2. Search for Secretary of State records for {search_term}")
    else:
        print(f"2. Search for business entities associated with {search_term}")
    
    if args.state:
        print(f"For {args.state}-specific searches:")
        print(f"1. Visit: https://www.blackbookonline.info/{args.state.upper()}-Secretary-of-State.aspx")
        print(f"2. Follow the links to the official {args.state.upper()} business entity search")

if __name__ == "__main__":
    main()