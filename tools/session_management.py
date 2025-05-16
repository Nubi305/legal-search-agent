"""
Session management tool for the legal search agent.

This tool allows users to manage research sessions, review past searches,
and continue previous research topics.
"""

import os
import sys
import argparse
import json
import time
import datetime
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.session_manager import SessionManager
from src.langchain_integration import LegalLangChain

def format_timestamp(timestamp):
    """Format a timestamp as a human-readable date and time."""
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_duration(seconds):
    """Format a duration in seconds as a human-readable duration."""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} hours, {minutes} minutes"

def list_sessions(session_manager):
    """List all available sessions."""
    sessions = session_manager.list_sessions()
    
    if not sessions:
        print("No sessions found.")
        return
    
    print("\nAvailable Sessions:")
    print("-" * 80)
    print(f"{'ID':<20} {'Name':<30} {'Date':<20} {'Entities':<8} {'Queries':<8}")
    print("-" * 80)
    
    for session in sessions:
        session_id = session["id"]
        name = session.get("name", "Unnamed Session")
        date = format_timestamp(session["start_time"])
        entity_count = session.get("entity_count", 0)
        query_count = session.get("query_count", 0)
        
        print(f"{session_id:<20} {name[:30]:<30} {date:<20} {entity_count:<8} {query_count:<8}")

def show_session_details(session_manager, session_id):
    """Show detailed information about a session."""
    try:
        # Try to summarize the session
        summary = session_manager.summarize_session(session_id)
        
        if not summary:
            print(f"Session not found: {session_id}")
            return
        
        print("\nSession Details:")
        print("-" * 80)
        print(f"ID:         {summary['id']}")
        print(f"Name:       {summary['name']}")
        print(f"Started:    {summary['start_time']}")
        print(f"Duration:   {format_duration(summary['duration'])}")
        print(f"Entities:   {summary['entity_count']}")
        print(f"Queries:    {summary['query_count']}")
        print(f"Messages:   {summary['message_count']}")
        
        # Entity types
        if summary['entity_types']:
            print("\nEntity Types:")
            for entity_type, count in summary['entity_types'].items():
                print(f"  {entity_type}: {count}")
        
        # Tool usage
        if summary['tool_usage']:
            print("\nTool Usage:")
            for tool, count in summary['tool_usage'].items():
                print(f"  {tool}: {count}")
        
        # Entities
        if summary['entities']:
            print("\nEntities Researched:")
            for entity in summary['entities']:
                print(f"  - {entity}")
        
        # Recent queries
        if summary['last_queries']:
            print("\nRecent Queries:")
            for query in summary['last_queries']:
                print(f"  - {query}")
        
        print("\nUse --load to continue this session.")
    
    except Exception as e:
        print(f"Error showing session details: {str(e)}")

def search_sessions(session_manager, search_term):
    """Search for sessions containing a specific term."""
    results = session_manager.search_sessions(search_term)
    
    if not results:
        print(f"No sessions found containing '{search_term}'.")
        return
    
    print(f"\nSessions containing '{search_term}':")
    print("-" * 80)
    
    for result in results:
        session_id = result["id"]
        name = result.get("name", "Unnamed Session")
        
        print(f"Session: {name} ({session_id})")
        
        # Entity matches
        if result["entity_matches"]:
            print("\n  Entity matches:")
            for entity in result["entity_matches"]:
                print(f"    - {entity}")
        
        # Query matches
        if result["query_matches"]:
            print("\n  Query matches:")
            for query in result["query_matches"]:
                print(f"    - {query}")
        
        # Message matches
        if result["message_matches"]:
            print("\n  Message matches:")
            for message in result["message_matches"]:
                print(f"    [{message['role']}] {message['snippet']}")
        
        print("-" * 80)

def load_session(session_manager, session_id):
    """Load and interact with a session."""
    try:
        session_data = session_manager.load_session(session_id)
        
        if not session_data:
            print(f"Session not found: {session_id}")
            return
        
        print(f"\nLoaded session: {session_data.get('name', 'Unnamed Session')} ({session_id})")
        
        # Show session history
        messages = session_data.get("messages", [])
        if messages:
            print("\nConversation History:")
            print("-" * 80)
            
            for message in messages:
                role = message["role"]
                timestamp = format_timestamp(message["timestamp"])
                content = message["content"]
                
                if len(content) > 100:
                    content = content[:97] + "..."
                
                print(f"[{timestamp}] {role.upper()}: {content}")
        
        # Show entities
        entities = session_data.get("entities", [])
        if entities:
            print("\nResearched Entities:")
            print("-" * 80)
            
            for entity in entities:
                entity_type = entity["type"]
                name = entity["name"]
                timestamp = format_timestamp(entity["timestamp"])
                
                print(f"[{timestamp}] {entity_type.upper()}: {name}")
        
        # Interactive mode
        print("\nEntering interactive mode. Type 'exit' to quit.")
        print("-" * 80)
        
        while True:
            command = input("\nEnter a command or search query (help, exit): ")
            
            if command.lower() in ["exit", "quit", "q"]:
                break
            elif command.lower() in ["help", "h", "?"]:
                print("\nAvailable commands:")
                print("  help      - Show this help")
                print("  exit      - Exit interactive mode")
                print("  summary   - Show session summary")
                print("  entities  - List all entities in this session")
                print("  queries   - List all queries in this session")
                print("  continue  - Continue research with LangChain")
                print("  [query]   - Any other input will be treated as a search query")
            elif command.lower() == "summary":
                summary = session_manager.summarize_session()
                print("\nSession Summary:")
                print(f"Name:       {summary['name']}")
                print(f"Started:    {summary['start_time']}")
                print(f"Duration:   {format_duration(summary['duration'])}")
                print(f"Entities:   {summary['entity_count']}")
                print(f"Queries:    {summary['query_count']}")
                print(f"Messages:   {summary['message_count']}")
            elif command.lower() == "entities":
                entities = session_manager.get_session_entities()
                print("\nEntities in this session:")
                for entity in entities:
                    print(f"  - {entity['name']} ({entity['type']})")
            elif command.lower() == "queries":
                queries = session_manager.get_session_queries()
                print("\nQueries in this session:")
                for query in queries:
                    print(f"  - {query['query']} ({query['tool']})")
            elif command.lower() == "continue":
                if os.getenv("OPENAI_API_KEY"):
                    # Get all entities and recent queries
                    entities = session_manager.get_session_entities()
                    queries = session_manager.get_session_queries()
                    messages = session_manager.get_session_history()
                    
                    # Extract names and recent queries
                    entity_names = [entity["name"] for entity in entities]
                    recent_queries = [query["query"] for query in queries[-5:]] if queries else []
                    
                    # Construct context
                    context = "Based on our previous research on "
                    if entity_names:
                        if len(entity_names) == 1:
                            context += f"{entity_names[0]}"
                        else:
                            context += ", ".join(entity_names[:-1]) + f" and {entity_names[-1]}"
                    
                    context += ", suggest the next steps for my research. "
                    
                    if recent_queries:
                        context += "I have recently been interested in: "
                        context += ", ".join(f'"{q}"' for q in recent_queries)
                    
                    print("\nGenerating research suggestions based on your session history...")
                    
                    # Use LangChain to generate suggestions
                    try:
                        # First, find an index directory if one exists
                        index_dirs = []
                        for query in queries:
                            if "parameters" in query and "index" in query["parameters"]:
                                index_dir = query["parameters"]["index"]
                                if os.path.exists(index_dir) and index_dir not in index_dirs:
                                    index_dirs.append(index_dir)
                        
                        if index_dirs:
                            # Use the most recent index
                            index_dir = index_dirs[-1]
                            legal_langchain = LegalLangChain(index_dir)
                            
                            response = legal_langchain.query(context)
                            
                            print("\nResearch Suggestions:")
                            print("-" * 80)
                            print(response["answer"])
                        else:
                            print("\nNo index directories found. Please run a search first to create an index.")
                    
                    except Exception as e:
                        print(f"Error generating suggestions: {str(e)}")
                
                else:
                    print("\nFor research suggestions, set your OPENAI_API_KEY in the .env file.")
            else:
                # Treat as search query
                print(f"\nSearching for: {command}")
                
                # This is where you'd integrate with your search functionality
                # For now, just echo the query
                print(f"This would search for '{command}' using your legal search agent.")
                print("To perform actual searches, please use the specific research tools.")
                
                # Record the query in the session
                session_manager.add_query(command, "session_search", {"query": command})
                session_manager.add_message("user", command)
                session_manager.add_message("assistant", f"Searched for '{command}'")
    
    except Exception as e:
        print(f"Error loading session: {str(e)}")

def delete_session(session_manager, session_id):
    """Delete a session."""
    # Confirm deletion
    confirm = input(f"Are you sure you want to delete session {session_id}? (y/n): ")
    
    if confirm.lower() != "y":
        print("Deletion cancelled.")
        return
    
    success = session_manager.delete_session(session_id)
    
    if success:
        print(f"Session {session_id} deleted.")
    else:
        print(f"Failed to delete session {session_id}.")

def main():
    """Main function."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Session Management Tool")
    parser.add_argument("--list", action="store_true", help="List all sessions")
    parser.add_argument("--show", help="Show details for a specific session")
    parser.add_argument("--search", help="Search for sessions containing a term")
    parser.add_argument("--load", help="Load and interact with a session")
    parser.add_argument("--delete", help="Delete a session")
    parser.add_argument("--create", help="Create a new session with the given name")
    parser.add_argument("--dir", default="sessions", help="Directory for storing sessions")
    
    args = parser.parse_args()
    
    # Initialize session manager
    session_manager = SessionManager(sessions_dir=args.dir)
    
    # Process commands
    if args.list:
        list_sessions(session_manager)
    elif args.show:
        show_session_details(session_manager, args.show)
    elif args.search:
        search_sessions(session_manager, args.search)
    elif args.load:
        load_session(session_manager, args.load)
    elif args.delete:
        delete_session(session_manager, args.delete)
    elif args.create:
        session_id = session_manager.create_session(args.create)
        print(f"Created new session: {args.create} ({session_id})")
        print(f"Use --load {session_id} to start using this session.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()