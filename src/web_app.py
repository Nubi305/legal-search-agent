"""
Streamlit web interface for the legal search agent.
"""

import os
import streamlit as st
import pandas as pd
from typing import Dict, List, Any
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.crawler import LegalCrawler
from src.processor import DocumentProcessor
from src.indexer import DocumentIndexer
from src.search import LegalSearchEngine
from src.langchain_integration import LegalLangChain

# Set page config
st.set_page_config(
    page_title="Legal Search Agent",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global variables
VECTOR_STORE_DIR = "vector_stores"
CONFIG_DIR = "configs"

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_sources" not in st.session_state:
    st.session_state.current_sources = []

# Functions
def load_crawler_configs() -> List[str]:
    """
    Load available crawler configurations.
    
    Returns:
        List of configuration file names
    """
    configs = []
    if os.path.exists(CONFIG_DIR):
        for file in os.listdir(CONFIG_DIR):
            if file.endswith('.json'):
                configs.append(file)
    return configs

def run_crawler(config_file: str, output_dir: str) -> None:
    """
    Run the crawler with the selected configuration.
    
    Args:
        config_file: Path to configuration file
        output_dir: Output directory for downloaded documents
    """
    config_path = os.path.join(CONFIG_DIR, config_file)
    config = Config.from_file(config_path)
    crawler = LegalCrawler(config)
    
    with st.spinner(f"Crawling legal websites using {config_file}..."):
        crawler.crawl(output_dir=output_dir)
    
    st.success(f"Crawling completed. Documents saved to {output_dir}")

def process_documents(input_dir: str, output_dir: str) -> None:
    """
    Process the downloaded documents.
    
    Args:
        input_dir: Input directory with raw documents
        output_dir: Output directory for processed documents
    """
    processor = DocumentProcessor()
    
    with st.spinner(f"Processing documents from {input_dir}..."):
        processor.process_directory(input_dir, output_dir)
    
    st.success(f"Processing completed. Processed documents saved to {output_dir}")

def index_documents(input_dir: str, output_dir: str) -> None:
    """
    Index the processed documents.
    
    Args:
        input_dir: Input directory with processed documents
        output_dir: Output directory for the index
    """
    indexer = DocumentIndexer()
    
    with st.spinner(f"Indexing documents from {input_dir}..."):
        indexer.index_directory(input_dir, output_dir)
    
    st.success(f"Indexing completed. Index saved to {output_dir}")

def search_documents(query: str, index_dir: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search for documents matching a query.
    
    Args:
        query: Search query
        index_dir: Directory containing the index
        k: Number of results to return
        
    Returns:
        List of search results
    """
    search_engine = LegalSearchEngine(index_dir)
    
    with st.spinner(f"Searching for: {query}"):
        results = search_engine.search(query, k=k)
    
    return results

def langchain_query(query: str, index_dir: str) -> Dict[str, Any]:
    """
    Query using LangChain.
    
    Args:
        query: User query
        index_dir: Directory containing the index
        
    Returns:
        LangChain response
    """
    legal_langchain = LegalLangChain(index_dir)
    
    with st.spinner(f"Processing query with LangChain: {query}"):
        response = legal_langchain.query(query)
    
    return response

def langchain_chat(query: str, index_dir: str) -> Dict[str, Any]:
    """
    Chat using LangChain.
    
    Args:
        query: User query
        index_dir: Directory containing the index
        
    Returns:
        LangChain response
    """
    legal_langchain = LegalLangChain(index_dir)
    
    with st.spinner(f"Processing chat with LangChain: {query}"):
        response = legal_langchain.chat(query)
    
    # Add the query and response to chat history
    st.session_state.chat_history.append({"role": "user", "content": query})
    st.session_state.chat_history.append({"role": "assistant", "content": response["answer"]})
    
    # Store current sources
    st.session_state.current_sources = response["sources"]
    
    return response

# UI components
def render_sidebar() -> None:
    """Render the sidebar."""
    st.sidebar.title("Legal Search Agent")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Search", "Chat", "Data Collection", "Settings", "About"]
    )
    
    return page

def render_search_page() -> None:
    """Render the search page."""
    st.title("Legal Search")
    st.write("Search for legal information using the indexed documents.")
    
    # Search form
    with st.form(key="search_form"):
        query = st.text_input("Search Query", placeholder="Enter your legal question...")
        num_results = st.slider("Number of Results", min_value=1, max_value=20, value=5)
        search_type = st.radio("Search Type", ["Basic", "Advanced (LangChain)"])
        submit_button = st.form_submit_button("Search")
    
    # Process search
    if submit_button and query:
        if search_type == "Basic":
            results = search_documents(query, VECTOR_STORE_DIR, k=num_results)
            
            # Display results
            for i, result in enumerate(results):
                with st.expander(f"Result {i+1}: {result['title']}"):
                    st.write(f"**Source:** {result['source']}")
                    st.write(f"**Relevance Score:** {result['score']:.2f}")
                    st.write("**Content:**")
                    st.write(result['content'])
        
        else:  # Advanced (LangChain)
            response = langchain_query(query, VECTOR_STORE_DIR)
            
            # Display answer
            st.markdown("### Answer")
            st.write(response["answer"])
            
            # Display sources
            st.markdown("### Sources")
            for i, source in enumerate(response["sources"]):
                with st.expander(f"Source {i+1}: {source.get('title', 'Unknown')}"):
                    st.write(f"**Source:** {source.get('source', 'Unknown')}")
                    st.write(f"**Document Path:** {source.get('document_path', 'Unknown')}")

def render_chat_page() -> None:
    """Render the chat page."""
    st.title("Legal Chat")
    st.write("Have a conversation about legal topics with the AI assistant.")
    
    # Chat container
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    user_query = st.chat_input("Ask a legal question...")
    
    # Process chat input
    if user_query:
        with st.chat_message("user"):
            st.write(user_query)
        
        # Get response from LangChain
        response = langchain_chat(user_query, VECTOR_STORE_DIR)
        
        with st.chat_message("assistant"):
            st.write(response["answer"])
    
    # Sources
    if st.session_state.current_sources:
        st.markdown("### Sources for the Last Response")
        for i, source in enumerate(st.session_state.current_sources):
            with st.expander(f"Source {i+1}: {source.get('title', 'Unknown')}"):
                st.write(f"**Source:** {source.get('source', 'Unknown')}")
                st.write(f"**Document Path:** {source.get('document_path', 'Unknown')}")

def render_data_collection_page() -> None:
    """Render the data collection page."""
    st.title("Data Collection")
    st.write("Collect and process legal data from various sources.")
    
    # Tabs for different data collection steps
    tab1, tab2, tab3 = st.tabs(["Crawl", "Process", "Index"])
    
    with tab1:
        st.header("Web Crawler")
        st.write("Crawl legal websites to collect documents.")
        
        # Config selection
        configs = load_crawler_configs()
        if configs:
            config_file = st.selectbox("Select Configuration", configs)
            output_dir = st.text_input("Output Directory", "downloaded_docs")
            
            if st.button("Start Crawling"):
                run_crawler(config_file, output_dir)
        else:
            st.warning("No crawler configurations found. Please add a configuration file to the configs directory.")
    
    with tab2:
        st.header("Document Processor")
        st.write("Process the downloaded documents to extract structured information.")
        
        input_dir = st.text_input("Input Directory", "downloaded_docs", key="process_input")
        output_dir = st.text_input("Output Directory", "processed_docs", key="process_output")
        
        if st.button("Start Processing"):
            process_documents(input_dir, output_dir)
    
    with tab3:
        st.header("Document Indexer")
        st.write("Index the processed documents for efficient search.")
        
        input_dir = st.text_input("Input Directory", "processed_docs", key="index_input")
        output_dir = st.text_input("Output Directory", VECTOR_STORE_DIR, key="index_output")
        
        if st.button("Start Indexing"):
            index_documents(input_dir, output_dir)

def render_settings_page() -> None:
    """Render the settings page."""
    st.title("Settings")
    st.write("Configure the legal search agent.")
    
    # API Keys
    st.header("API Keys")
    openai_api_key = st.text_input("OpenAI API Key", os.getenv("OPENAI_API_KEY", ""), type="password")
    
    if st.button("Save API Keys"):
        os.environ["OPENAI_API_KEY"] = openai_api_key
        st.success("API keys saved")
    
    # Vector Store Settings
    st.header("Vector Store Settings")
    vector_store_dir = st.text_input("Vector Store Directory", VECTOR_STORE_DIR)
    
    if st.button("Save Vector Store Settings"):
        global VECTOR_STORE_DIR
        VECTOR_STORE_DIR = vector_store_dir
        st.success("Vector store settings saved")
    
    # Reset Chat History
    st.header("Chat")
    if st.button("Clear Chat History"):
        st.session_state.chat_history = []
        st.success("Chat history cleared")

def render_about_page() -> None:
    """Render the about page."""
    st.title("About Legal Search Agent")
    st.write("""
    The Legal Search Agent is a specialized tool designed to help legal professionals find and analyze legal information efficiently.
    
    It combines web crawling, document processing, and advanced language models to provide a powerful legal research assistant.
    
    **Features:**
    
    - Crawl legal websites to collect documents
    - Process and structure legal information
    - Index documents for efficient search
    - Search for legal information using natural language
    - Chat with an AI assistant about legal topics
    
    **Technology Stack:**
    
    - Python
    - LangChain
    - OpenAI GPT Models
    - Chroma Vector Store
    - Streamlit Web Interface
    
    **Repository:**
    
    [GitHub - Legal Search Agent](https://github.com/Nubi305/legal-search-agent)
    """)

# Main app
def main():
    page = render_sidebar()
    
    if page == "Search":
        render_search_page()
    elif page == "Chat":
        render_chat_page()
    elif page == "Data Collection":
        render_data_collection_page()
    elif page == "Settings":
        render_settings_page()
    elif page == "About":
        render_about_page()

if __name__ == "__main__":
    main()