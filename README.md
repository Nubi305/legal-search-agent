# Legal Search Agent

A specialized web search agent designed to crawl legal websites, extract important data, and provide efficient retrieval functionality.

## Features

- Crawl legal websites and databases
- Extract structured data from legal documents
- Store and index legal information for quick retrieval
- Search through collected data with natural language queries
- Export and analyze legal data

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

```bash
# Crawl legal websites
python src/crawler.py --config configs/crawler_config.json

# Search for legal information
python src/search.py --query "copyright infringement cases 2024"

# Export data
python src/exporter.py --format csv --output legal_data.csv
```

## Documentation

See the [docs](docs/) directory for detailed documentation.

## License

MIT