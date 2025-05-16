"""
Session manager for the legal search agent.

This module provides functionality to store, retrieve, and analyze 
past chat sessions, enabling the agent to maintain context and learn 
from previous interactions.
"""

import os
import json
import time
import datetime
from typing import Dict, List, Any, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('session_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SessionManager')

class SessionManager:
    """Manages chat sessions for the legal search agent."""
    
    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize the session manager.
        
        Args:
            sessions_dir: Directory for storing session data
        """
        self.sessions_dir = sessions_dir
        
        # Create sessions directory if it doesn't exist
        if not os.path.exists(sessions_dir):
            os.makedirs(sessions_dir)
        
        # Initialize session metadata
        self.sessions_index_path = os.path.join(sessions_dir, "sessions_index.json")
        self.sessions_index = self._load_sessions_index()
        
        # Current session
        self.current_session_id = None
        self.current_session = {
            "id": None,
            "start_time": None,
            "entities": [],
            "queries": [],
            "messages": []
        }
    
    def _load_sessions_index(self) -> Dict[str, Any]:
        """
        Load the sessions index file.
        
        Returns:
            Sessions index data
        """
        if os.path.exists(self.sessions_index_path):
            try:
                with open(self.sessions_index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading sessions index: {str(e)}")
                return {"sessions": []}
        else:
            return {"sessions": []}
    
    def _save_sessions_index(self) -> None:
        """Save the sessions index file."""
        try:
            with open(self.sessions_index_path, 'w', encoding='utf-8') as f:
                json.dump(self.sessions_index, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sessions index: {str(e)}")
    
    def create_session(self, session_name: Optional[str] = None) -> str:
        """
        Create a new session.
        
        Args:
            session_name: Optional name for the session
            
        Returns:
            Session ID
        """
        # Generate session ID
        timestamp = int(time.time())
        session_id = f"session_{timestamp}"
        
        # Set session name
        if not session_name:
            # Generate a default name based on date and time
            now = datetime.datetime.now()
            session_name = f"Session {now.strftime('%Y-%m-%d %H:%M')}"
        
        # Create session metadata
        session_meta = {
            "id": session_id,
            "name": session_name,
            "start_time": timestamp,
            "last_updated": timestamp,
            "entity_count": 0,
            "query_count": 0,
            "message_count": 0
        }
        
        # Add to sessions index
        self.sessions_index["sessions"].append(session_meta)
        self._save_sessions_index()
        
        # Initialize current session
        self.current_session_id = session_id
        self.current_session = {
            "id": session_id,
            "name": session_name,
            "start_time": timestamp,
            "entities": [],
            "queries": [],
            "messages": []
        }
        
        # Save the new session
        self._save_current_session()
        
        logger.info(f"Created new session: {session_id} ({session_name})")
        
        return session_id
    
    def load_session(self, session_id: str) -> Dict[str, Any]:
        """
        Load an existing session.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Session data
        """
        session_path = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(session_path):
            logger.error(f"Session not found: {session_id}")
            raise FileNotFoundError(f"Session not found: {session_id}")
        
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Set as current session
            self.current_session_id = session_id
            self.current_session = session_data
            
            logger.info(f"Loaded session: {session_id}")
            
            return session_data
        
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {str(e)}")
            raise
    
    def _save_current_session(self) -> None:
        """Save the current session."""
        if not self.current_session_id:
            logger.error("No active session to save")
            return
        
        session_path = os.path.join(self.sessions_dir, f"{self.current_session_id}.json")
        
        try:
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_session, f, indent=2)
            
            # Update the index
            timestamp = int(time.time())
            for session in self.sessions_index["sessions"]:
                if session["id"] == self.current_session_id:
                    session["last_updated"] = timestamp
                    session["entity_count"] = len(self.current_session["entities"])
                    session["query_count"] = len(self.current_session["queries"])
                    session["message_count"] = len(self.current_session["messages"])
                    break
            
            self._save_sessions_index()
            
            logger.debug(f"Saved session: {self.current_session_id}")
        
        except Exception as e:
            logger.error(f"Error saving session {self.current_session_id}: {str(e)}")
    
    def add_entity(self, entity_type: str, entity_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an entity to the current session.
        
        Args:
            entity_type: Type of entity (e.g., "business", "person")
            entity_name: Name of the entity
            metadata: Additional metadata about the entity
        """
        if not self.current_session_id:
            logger.error("No active session")
            return
        
        timestamp = int(time.time())
        
        entity = {
            "type": entity_type,
            "name": entity_name,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        self.current_session["entities"].append(entity)
        self._save_current_session()
        
        logger.info(f"Added entity to session: {entity_name} ({entity_type})")
    
    def add_query(self, query: str, tool: str, parameters: Optional[Dict[str, Any]] = None, results: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Add a query to the current session.
        
        Args:
            query: Search query
            tool: Tool used for the query (e.g., "company_research", "judgment_research")
            parameters: Parameters used for the query
            results: Results of the query (optional)
        """
        if not self.current_session_id:
            logger.error("No active session")
            return
        
        timestamp = int(time.time())
        
        query_record = {
            "query": query,
            "tool": tool,
            "timestamp": timestamp,
            "parameters": parameters or {},
            "results": results or []
        }
        
        self.current_session["queries"].append(query_record)
        self._save_current_session()
        
        logger.info(f"Added query to session: {query}")
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to the current session.
        
        Args:
            role: Role of the message sender (e.g., "user", "assistant")
            content: Message content
            metadata: Additional metadata about the message
        """
        if not self.current_session_id:
            logger.error("No active session")
            return
        
        timestamp = int(time.time())
        
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "metadata": metadata or {}
        }
        
        self.current_session["messages"].append(message)
        self._save_current_session()
        
        logger.debug(f"Added message to session: {role} ({len(content)} chars)")
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """
        Get the message history for the current session.
        
        Returns:
            List of messages
        """
        if not self.current_session_id:
            logger.error("No active session")
            return []
        
        return self.current_session["messages"]
    
    def get_session_entities(self) -> List[Dict[str, Any]]:
        """
        Get the entities for the current session.
        
        Returns:
            List of entities
        """
        if not self.current_session_id:
            logger.error("No active session")
            return []
        
        return self.current_session["entities"]
    
    def get_session_queries(self) -> List[Dict[str, Any]]:
        """
        Get the queries for the current session.
        
        Returns:
            List of queries
        """
        if not self.current_session_id:
            logger.error("No active session")
            return []
        
        return self.current_session["queries"]
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Returns:
            List of session metadata
        """
        return self.sessions_index["sessions"]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        session_path = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(session_path):
            logger.error(f"Session not found: {session_id}")
            return False
        
        try:
            # Remove from file system
            os.remove(session_path)
            
            # Remove from index
            self.sessions_index["sessions"] = [
                session for session in self.sessions_index["sessions"] 
                if session["id"] != session_id
            ]
            self._save_sessions_index()
            
            # Reset current session if it was deleted
            if self.current_session_id == session_id:
                self.current_session_id = None
                self.current_session = {
                    "id": None,
                    "start_time": None,
                    "entities": [],
                    "queries": [],
                    "messages": []
                }
            
            logger.info(f"Deleted session: {session_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
    
    def summarize_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a summary of a session.
        
        Args:
            session_id: Session ID to summarize (defaults to current session)
            
        Returns:
            Session summary
        """
        target_id = session_id or self.current_session_id
        
        if not target_id:
            logger.error("No session to summarize")
            return {}
        
        # Load the session if it's not the current one
        session_data = self.current_session
        if target_id != self.current_session_id:
            session_path = os.path.join(self.sessions_dir, f"{target_id}.json")
            
            if not os.path.exists(session_path):
                logger.error(f"Session not found: {target_id}")
                return {}
            
            try:
                with open(session_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
            except Exception as e:
                logger.error(f"Error loading session {target_id}: {str(e)}")
                return {}
        
        # Generate summary
        start_time = datetime.datetime.fromtimestamp(session_data["start_time"]).strftime('%Y-%m-%d %H:%M:%S')
        
        # Entity counts by type
        entity_types = {}
        for entity in session_data["entities"]:
            entity_type = entity["type"]
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        # Tool usage counts
        tool_usage = {}
        for query in session_data["queries"]:
            tool = query["tool"]
            tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        # Message counts by role
        message_roles = {}
        for message in session_data["messages"]:
            role = message["role"]
            message_roles[role] = message_roles.get(role, 0) + 1
        
        # Summary
        summary = {
            "id": target_id,
            "name": session_data.get("name", "Unnamed Session"),
            "start_time": start_time,
            "duration": len(session_data["messages"]) > 0 and
                      (session_data["messages"][-1]["timestamp"] - session_data["start_time"]) or 0,
            "entity_count": len(session_data["entities"]),
            "entity_types": entity_types,
            "query_count": len(session_data["queries"]),
            "tool_usage": tool_usage,
            "message_count": len(session_data["messages"]),
            "message_roles": message_roles,
            "entities": [e["name"] for e in session_data["entities"]],
            "last_queries": [q["query"] for q in session_data["queries"][-5:]] if session_data["queries"] else []
        }
        
        return summary
    
    def search_sessions(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search for sessions containing a specific term.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching session IDs and snippets
        """
        results = []
        search_term = search_term.lower()
        
        for session_meta in self.sessions_index["sessions"]:
            session_id = session_meta["id"]
            session_path = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            if not os.path.exists(session_path):
                continue
            
            try:
                with open(session_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Search in entities
                entity_matches = []
                for entity in session_data["entities"]:
                    if search_term in entity["name"].lower():
                        entity_matches.append(entity["name"])
                
                # Search in queries
                query_matches = []
                for query in session_data["queries"]:
                    if search_term in query["query"].lower():
                        query_matches.append(query["query"])
                
                # Search in messages
                message_matches = []
                for message in session_data["messages"]:
                    if search_term in message["content"].lower():
                        # Extract a snippet around the match
                        content = message["content"].lower()
                        start_idx = max(0, content.find(search_term) - 50)
                        end_idx = min(len(content), content.find(search_term) + len(search_term) + 50)
                        snippet = "..." + message["content"][start_idx:end_idx] + "..."
                        message_matches.append({
                            "role": message["role"],
                            "snippet": snippet
                        })
                
                # If any matches, add to results
                if entity_matches or query_matches or message_matches:
                    results.append({
                        "id": session_id,
                        "name": session_data.get("name", "Unnamed Session"),
                        "entity_matches": entity_matches,
                        "query_matches": query_matches,
                        "message_matches": message_matches[:3]  # Limit to 3 message matches
                    })
            
            except Exception as e:
                logger.error(f"Error searching session {session_id}: {str(e)}")
        
        return results