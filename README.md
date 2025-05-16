# Legal Search Agent

A specialized web search agent designed to crawl legal websites, extract important data, and provide efficient retrieval functionality using advanced language models.

## Features

- **Web Crawling**: Crawl legal websites and databases to collect documents with robust error handling
- **Document Processing**: Extract structured data from legal documents (HTML, PDF, text)
- **Smart Indexing**: Store and index legal information for quick retrieval using vector embeddings
- **Natural Language Search**: Search through collected data with natural language queries
- **Advanced AI Integration**: 
  - LangChain integration for powerful question-answering capabilities
  - ChatGPT-powered legal assistant for interactive conversations
- **Visual Workflow Creation**: LangFlow integration for visually creating and modifying workflows
- **User-Friendly Interface**: Streamlit web application for easy interaction
- **Session Management**: Track research across sessions with full history and context
- **Enhanced Security**: Comprehensive input validation and secure file handling
- **Improved Error Handling**: Robust error management with detailed logging
- **Advanced Firecrawl Integration**: Enhanced web scraping and structured data extraction with batch processing

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

### Session Management

```bash
# List research sessions
python tools/session_management.py --list

# Continue a previous session
python tools/session_management.py --load SESSION_ID
```

### Advanced Firecrawl Search

For Firecrawl features, you need a [Firecrawl API key](https://firecrawl.dev).

```bash
# Extract structured data from a legal website
python tools/firecrawl_test.py extract https://iapps.courts.state.ny.us/nyscef/CaseSearch?TAB=name --url-type judgment

# Crawler a Secretary of State website
python tools/firecrawl_test.py crawl https://sos.gov.state/business-search --limit 50

# Batch process multiple websites with retry logic
python tools/firecrawl_test.py extract "url1,url2,url3" --url-type business
```

## Specialized Research Tools

The repository includes specialized research tools in the `tools/` directory:

- **Company Research**: Research business entities across state databases
- **Person Research**: Find information about people's professional licenses and legal history
- **Judgment Research**: Search for civil judgments and liens against businesses and individuals
- **Firecrawl Integration**: Extract structured data from complex legal websites
- **Session Management**: Track and continue research across sessions

## Component Overview

### Core Modules

- **Error Handler (`error_handler.py`)**: Centralized error handling and validation
- **Configuration Module (`config.py`)**: Manages all settings for the agent with validation
- **Crawler Module (`crawler.py`)**: Crawls legal websites with enhanced security measures
- **Processor Module (`processor.py`)**: Processes and structures raw data
- **Indexer Module (`indexer.py`)**: Creates searchable vector indices
- **Search Module (`search.py`)**: Enables basic search functionality
- **LangChain Integration (`langchain_integration.py`)**: Advanced language model capabilities
- **LangFlow Integration (`langflow_integration.py`)**: Visual workflow creation
- **Web Interface (`web_app.py`)**: Streamlit web application
- **Session Manager (`session_manager.py`)**: Manages research session history and context
- **Firecrawl Integration (`firecrawl_integration.py`)**: Enhanced web scraping with retry logic

### AI-Powered Features

- **Smart Document Retrieval**: Uses OpenAI embeddings for semantic search
- **Legal Question Answering**: Custom-trained QA chain using LangChain
- **Conversational Legal Assistant**: Chat with an AI about legal topics
- **Legal Prompt Templates**: Specialized prompts for legal domain tasks
- **Structured Data Extraction**: Schema-based extraction of legal information with validation

## Testing

```bash
# Run unit tests
pytest

# Run tests with coverage report
pytest --cov=src tests/
```

## Requirements

- Python 3.8+
- OpenAI API key (for AI features)
- Firecrawl API key (for enhanced scraping)
- Internet connection for web crawling
- Sufficient storage for indexed documents

## API Keys

For full functionality, add the following to your `.env` file:

```
OPENAI_API_KEY=sk-your-openai-key
FIRECRAWL_API_KEY=fc-your-firecrawl-key
```

## Security Features

- Input validation for all user inputs and configuration files
- URL validation and sanitization before crawling
- Safe filename generation to prevent path traversal
- Content size limits to prevent resource exhaustion
- Retry logic with exponential backoff for resilience
- Comprehensive error handling with detailed logging
- Secure HTTP requests with timeouts and proper headers

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request
