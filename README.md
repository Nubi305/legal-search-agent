# Legal Search Agent

A specialized web search agent designed to crawl legal websites, extract important data, and provide efficient retrieval functionality using advanced language models.

## Features

- **Web Crawling**: Crawl legal websites and databases to collect documents
- **Document Processing**: Extract structured data from legal documents (HTML, PDF, text)
- **Smart Indexing**: Store and index legal information for quick retrieval using vector embeddings
- **Natural Language Search**: Search through collected data with natural language queries
- **Advanced AI Integration**: 
  - LangChain integration for powerful question-answering capabilities
  - ChatGPT-powered legal assistant for interactive conversations
- **Visual Workflow Creation**: LangFlow integration for visually creating and modifying workflows
- **User-Friendly Interface**: Streamlit web application for easy interaction

## Installation

```bash
# Clone the repository
git clone https://github.com/Nubi305/legal-search-agent.git
cd legal-search-agent

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Usage

### Data Collection Pipeline

```bash
# Crawl legal websites
python main.py crawl --config configs/crawler_config.json

# Process documents
python main.py process

# Index documents
python main.py index
```

### Search and Query

```bash
# Basic search
python main.py search --query "copyright infringement cases 2024" --type basic

# Advanced search using LangChain
python main.py search --query "Explain the precedent set by the Fair Use doctrine in copyright law" --type langchain

# Interactive chat mode
python main.py chat
```

### Visual Workflow Creation with LangFlow

```bash
# Start LangFlow server
python main.py langflow

# Save default flow templates
python main.py langflow --save-template
```

### Web Application

```bash
# Start the Streamlit web application
python main.py webapp
```

## Component Overview

### Core Modules

- **Configuration Module (`config.py`)**: Manages all settings for the agent
- **Crawler Module (`crawler.py`)**: Crawls legal websites to download documents
- **Processor Module (`processor.py`)**: Processes and structures raw data
- **Indexer Module (`indexer.py`)**: Creates searchable vector indices
- **Search Module (`search.py`)**: Enables basic search functionality
- **LangChain Integration (`langchain_integration.py`)**: Advanced language model capabilities
- **LangFlow Integration (`langflow_integration.py`)**: Visual workflow creation
- **Web Interface (`web_app.py`)**: Streamlit web application

### AI-Powered Features

- **Smart Document Retrieval**: Uses OpenAI embeddings for semantic search
- **Legal Question Answering**: Custom-trained QA chain using LangChain
- **Conversational Legal Assistant**: Chat with an AI about legal topics
- **Legal Prompt Templates**: Specialized prompts for legal domain tasks

## Customization

- Configure which websites to crawl in `configs/crawler_config.json`
- Adjust extraction rules in the processor module
- Create custom LangFlow workflows for specific legal tasks
- Fine-tune search parameters for better results

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for web crawling
- Sufficient storage for indexed documents

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.