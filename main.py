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
from src.langchain_integration import LegalLangChain, LegalPromptTemplates
from src.langflow_integration import LangFlowIntegration, LegalFlowTemplates

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
    search_parser.add_argument("--type", choices=["basic", "langchain"], default="basic", help="Search type")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Chat with LangChain")
    chat_parser.add_argument("--index", default="vector_stores", help="Index directory")
    
    # LangFlow command
    langflow_parser = subparsers.add_parser("langflow", help="Start LangFlow server")
    langflow_parser.add_argument("--host", default="localhost", help="Host to run the server on")
    langflow_parser.add_argument("--port", type=int, default=7860, help="Port to run the server on")
    langflow_parser.add_argument("--save-template", action="store_true", help="Save default flow templates")
    langflow_parser.add_argument("--flows-dir", default="flows", help="Directory for storing flows")
    
    # Web app command
    webapp_parser = subparsers.add_parser("webapp", help="Start web application")
    webapp_parser.add_argument("--port", type=int, default=8501, help="Port to run the server on")
    
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
        if args.type == "basic":
            search_engine = LegalSearchEngine(args.index)
            results = search_engine.search(args.query, k=args.results)
            for i, result in enumerate(results):
                print(f"\nResult {i+1}:")
                print(f"Source: {result['source']}")
                print(f"Relevance: {result['score']:.2f}")
                print(f"Content: {result['content'][:200]}...")
        else:  # langchain
            legal_langchain = LegalLangChain(args.index)
            response = legal_langchain.query(args.query)
            print("\nAnswer:")
            print(response["answer"])
            print("\nSources:")
            for i, source in enumerate(response["sources"]):
                print(f"\nSource {i+1}:")
                print(f"Title: {source.get('title', 'Unknown')}")
                print(f"Source: {source.get('source', 'Unknown')}")
    
    elif args.command == "chat":
        legal_langchain = LegalLangChain(args.index)
        print("Legal Chat Assistant. Type 'exit' to quit.")
        
        while True:
            query = input("\nYou: ")
            
            if query.lower() in ["exit", "quit", "q"]:
                break
            
            response = legal_langchain.chat(query)
            print(f"\nAssistant: {response['answer']}")
    
    elif args.command == "langflow":
        langflow = LangFlowIntegration(flows_dir=args.flows_dir)
        
        if args.save_template:
            # Save default flow templates
            os.makedirs(args.flows_dir, exist_ok=True)
            
            # Save basic QA flow
            basic_qa_flow = LegalFlowTemplates.get_basic_qa_flow()
            langflow.save_flow(basic_qa_flow, "basic_qa_flow.json")
            
            # Save conversational QA flow
            conv_qa_flow = LegalFlowTemplates.get_conversational_qa_flow()
            langflow.save_flow(conv_qa_flow, "conversational_qa_flow.json")
            
            # Save legal research flow
            legal_research_flow = LegalFlowTemplates.get_legal_research_flow()
            langflow.save_flow(legal_research_flow, "legal_research_flow.json")
            
            print(f"Default flow templates saved to {args.flows_dir}")
        
        # Start LangFlow server
        langflow.start_langflow_server(host=args.host, port=args.port)
    
    elif args.command == "webapp":
        # Start Streamlit web app
        import subprocess
        
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "web_app.py")
        
        # Run Streamlit
        cmd = f"streamlit run {script_path} --server.port={args.port}"
        subprocess.run(cmd, shell=True)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()