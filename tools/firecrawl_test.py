"""
Firecrawl tester tool for the legal search agent.

This tool demonstrates the capabilities of the Firecrawl integration
for extracting legal data from websites.
"""

import os
import sys
import json
import argparse
import time
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.firecrawl_integration import FirecrawlClient, LegalSchemas
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    print("Firecrawl integration not available. Make sure firecrawl-py is installed.")

def scrape_url(args):
    """Scrape a URL using Firecrawl."""
    client = FirecrawlClient(api_key=args.api_key)
    
    formats = args.formats.split(',')
    
    # Determine if we should use a schema
    schema = None
    if args.extract_data:
        if args.url_type:
            # Get schema based on URL type
            if args.url_type == "business":
                schema = LegalSchemas.business_registration_schema()
                print("Using business registration schema")
            elif args.url_type == "court":
                schema = LegalSchemas.court_case_schema()
                print("Using court case schema")
            elif args.url_type == "judgment":
                schema = LegalSchemas.judgment_schema()
                print("Using judgment schema")
        else:
            # Auto-detect schema
            schema = LegalSchemas.get_schema_for_url(args.url)
            if schema:
                print(f"Auto-detected schema for URL: {args.url}")
    
    # Add JSON format if using schema
    if schema and "json" not in formats:
        formats.append("json")
    
    print(f"Scraping URL: {args.url}")
    print(f"Formats: {formats}")
    
    result = client.scrape_url(args.url, formats=formats, json_schema=schema)
    
    # Print results
    if 'markdown' in formats and 'markdown' in result:
        print("\n=== MARKDOWN CONTENT ===")
        print(result['markdown'][:500] + "..." if len(result['markdown']) > 500 else result['markdown'])
    
    if 'json' in formats and 'json' in result:
        print("\n=== STRUCTURED DATA ===")
        print(json.dumps(result['json'], indent=2))
    
    # Save output if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\nOutput saved to {args.output}")
    
    return result

def crawl_url(args):
    """Crawl a URL and its subpages using Firecrawl."""
    client = FirecrawlClient(api_key=args.api_key)
    
    formats = args.formats.split(',')
    
    # Determine if we should use a schema
    schema = None
    if args.extract_data:
        if args.url_type:
            # Get schema based on URL type
            if args.url_type == "business":
                schema = LegalSchemas.business_registration_schema()
                print("Using business registration schema")
            elif args.url_type == "court":
                schema = LegalSchemas.court_case_schema()
                print("Using court case schema")
            elif args.url_type == "judgment":
                schema = LegalSchemas.judgment_schema()
                print("Using judgment schema")
        else:
            # Auto-detect schema
            schema = LegalSchemas.get_schema_for_url(args.url)
            if schema:
                print(f"Auto-detected schema for URL: {args.url}")
    
    # Add JSON format if using schema
    if schema and "json" not in formats:
        formats.append("json")
    
    # Parse excludes and includes
    excludes = args.excludes.split(',') if args.excludes else []
    includes = args.includes.split(',') if args.includes else []
    
    print(f"Crawling URL: {args.url}")
    print(f"Formats: {formats}")
    print(f"Limit: {args.limit}")
    print(f"Max depth: {args.max_depth}")
    if excludes:
        print(f"Excluding: {excludes}")
    if includes:
        print(f"Including only: {includes}")
    
    wait_for_completion = not args.no_wait
    
    result = client.crawl_url(
        args.url,
        limit=args.limit,
        max_depth=args.max_depth,
        formats=formats,
        excludes=excludes,
        includes=includes,
        wait_for_completion=wait_for_completion,
        timeout=args.timeout,
        json_schema=schema
    )
    
    # If we're not waiting, print the job ID
    if not wait_for_completion:
        print(f"\nCrawl job started with ID: {result.get('id')}")
        print(f"Check status with: python tools/firecrawl_test.py check-status --job-id {result.get('id')}")
        return result
    
    # Print results summary
    print(f"\nCrawl completed, found {len(result.get('data', []))} pages")
    
    # Print details of first result if available
    if result.get('data') and len(result['data']) > 0:
        first_result = result['data'][0]
        print("\n=== FIRST PAGE DETAILS ===")
        if 'metadata' in first_result:
            print(f"Title: {first_result['metadata'].get('title', 'No title')}")
            print(f"URL: {first_result['metadata'].get('sourceURL', 'No URL')}")
        
        if 'markdown' in formats and 'markdown' in first_result:
            print("\n=== FIRST PAGE MARKDOWN PREVIEW ===")
            preview = first_result['markdown'][:500] + "..." if len(first_result['markdown']) > 500 else first_result['markdown']
            print(preview)
    
    # Save output if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\nOutput saved to {args.output}")
    
    return result

def check_status(args):
    """Check the status of a crawl job."""
    client = FirecrawlClient(api_key=args.api_key)
    
    print(f"Checking status of job: {args.job_id}")
    
    result = client.check_crawl_status(args.job_id)
    
    print(f"\nStatus: {result.get('status', 'Unknown')}")
    print(f"Total pages: {result.get('total', 0)}")
    print(f"Credits used: {result.get('creditsUsed', 0)}")
    
    if result.get('status') == 'completed' and args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\nOutput saved to {args.output}")
    
    return result

def map_website(args):
    """Map a website to get all URLs."""
    client = FirecrawlClient(api_key=args.api_key)
    
    print(f"Mapping website: {args.url}")
    if args.search:
        print(f"Filtering by: {args.search}")
    
    result = client.map_website(args.url, args.search)
    
    print(f"\nFound {len(result)} URLs")
    
    # Print the first 10 URLs
    for i, url in enumerate(result[:10]):
        print(f"{i+1}. {url}")
    
    if len(result) > 10:
        print(f"... and {len(result) - 10} more")
    
    # Save output if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\nOutput saved to {args.output}")
    
    return result

def search_web(args):
    """Search the web using Firecrawl."""
    client = FirecrawlClient(api_key=args.api_key)
    
    print(f"Searching for: {args.query}")
    print(f"Limit: {args.limit}")
    print(f"Scrape results: {args.scrape_results}")
    
    formats = args.formats.split(',') if args.formats else ["markdown"]
    
    result = client.search_web(
        args.query, 
        limit=args.limit, 
        scrape_results=args.scrape_results,
        formats=formats
    )
    
    print(f"\nFound {len(result.get('data', []))} results")
    
    # Print the results
    for i, item in enumerate(result.get('data', [])[:args.limit]):
        print(f"\n{i+1}. {item.get('title', 'No title')}")
        print(f"   URL: {item.get('url', 'No URL')}")
        if item.get('description'):
            print(f"   Description: {item['description']}")
        
        # If we scraped the results, show a preview
        if args.scrape_results and 'markdown' in item:
            print(f"   Content preview: {item['markdown'][:200]}...")
    
    # Save output if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\nOutput saved to {args.output}")
    
    return result

def extract_data(args):
    """Extract structured data from URLs."""
    client = FirecrawlClient(api_key=args.api_key)
    
    # Parse URLs
    urls = args.urls.split(',')
    print(f"Extracting data from {len(urls)} URLs:")
    for url in urls[:5]:
        print(f"- {url}")
    if len(urls) > 5:
        print(f"... and {len(urls) - 5} more")
    
    # Determine schema to use
    schema = None
    if args.url_type:
        if args.url_type == "business":
            schema = LegalSchemas.business_registration_schema()
            print("Using business registration schema")
        elif args.url_type == "court":
            schema = LegalSchemas.court_case_schema()
            print("Using court case schema")
        elif args.url_type == "judgment":
            schema = LegalSchemas.judgment_schema()
            print("Using judgment schema")
    
    # Use prompt if provided, otherwise use schema
    if args.prompt:
        print(f"Using prompt: {args.prompt}")
        result = client.extract_structured_data(urls, prompt=args.prompt)
    else:
        if not schema:
            print("No schema or prompt provided. Using auto-detection.")
            # Try to auto-detect schema for the first URL
            schema = LegalSchemas.get_schema_for_url(urls[0])
            if schema:
                print("Auto-detected schema based on URL pattern")
        
        if not schema:
            # Still no schema, use a general prompt
            print("No suitable schema found, using general extraction prompt")
            prompt = "Extract all important legal information from this page, including entities, dates, case numbers, and status information."
            result = client.extract_structured_data(urls, prompt=prompt)
        else:
            result = client.extract_structured_data(urls, schema=schema)
    
    # Print results
    if 'data' in result:
        print("\n=== EXTRACTED DATA ===")
        print(json.dumps(result['data'], indent=2))
    else:
        print("\n=== JOB SUBMITTED ===")
        print(f"Job ID: {result.get('id')}")
    
    # Save output if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"\nOutput saved to {args.output}")
    
    return result

def main():
    """Main function."""
    # Load environment variables
    load_dotenv()
    
    # Check if Firecrawl is available
    if not FIRECRAWL_AVAILABLE:
        print("Error: Firecrawl integration not available.")
        print("Please install firecrawl-py: pip install firecrawl-py")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="Firecrawl Integration Tester")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--api-key", help="Firecrawl API key (defaults to FIRECRAWL_API_KEY env var)")
    common_parser.add_argument("--output", help="Output file to save results")
    
    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape a single URL", parents=[common_parser])
    scrape_parser.add_argument("url", help="URL to scrape")
    scrape_parser.add_argument("--formats", default="markdown,html", help="Comma-separated list of output formats")
    scrape_parser.add_argument("--extract-data", action="store_true", help="Extract structured data")
    scrape_parser.add_argument("--url-type", choices=["business", "court", "judgment"], help="Type of URL for schema selection")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl a website", parents=[common_parser])
    crawl_parser.add_argument("url", help="URL to crawl")
    crawl_parser.add_argument("--limit", type=int, default=10, help="Maximum number of pages to crawl")
    crawl_parser.add_argument("--max-depth", type=int, default=2, help="Maximum crawl depth")
    crawl_parser.add_argument("--formats", default="markdown", help="Comma-separated list of output formats")
    crawl_parser.add_argument("--excludes", help="Comma-separated list of URL patterns to exclude")
    crawl_parser.add_argument("--includes", help="Comma-separated list of URL patterns to include")
    crawl_parser.add_argument("--no-wait", action="store_true", help="Don't wait for crawl to complete")
    crawl_parser.add_argument("--timeout", type=int, default=600, help="Maximum time to wait for completion (seconds)")
    crawl_parser.add_argument("--extract-data", action="store_true", help="Extract structured data")
    crawl_parser.add_argument("--url-type", choices=["business", "court", "judgment"], help="Type of URL for schema selection")
    
    # Check status command
    status_parser = subparsers.add_parser("check-status", help="Check crawl job status", parents=[common_parser])
    status_parser.add_argument("--job-id", required=True, help="Crawl job ID")
    
    # Map command
    map_parser = subparsers.add_parser("map", help="Map a website", parents=[common_parser])
    map_parser.add_argument("url", help="URL to map")
    map_parser.add_argument("--search", help="Search term to filter URLs")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search the web", parents=[common_parser])
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    search_parser.add_argument("--scrape-results", action="store_true", help="Scrape search results")
    search_parser.add_argument("--formats", help="Comma-separated list of output formats for scraped results")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract structured data", parents=[common_parser])
    extract_parser.add_argument("urls", help="Comma-separated list of URLs")
    extract_parser.add_argument("--url-type", choices=["business", "court", "judgment"], help="Type of URL for schema selection")
    extract_parser.add_argument("--prompt", help="Natural language prompt for extraction")
    
    args = parser.parse_args()
    
    # Process commands
    if args.command == "scrape":
        scrape_url(args)
    elif args.command == "crawl":
        crawl_url(args)
    elif args.command == "check-status":
        check_status(args)
    elif args.command == "map":
        map_website(args)
    elif args.command == "search":
        search_web(args)
    elif args.command == "extract":
        extract_data(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()