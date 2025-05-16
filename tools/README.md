# Legal Search Agent Tools

This directory contains specialized tools built on top of the legal search agent for specific research needs.

## Company Research Tool

The company research tool helps you find information about a company's legal status, registration, and history.

### Usage

```bash
python tools/company_research.py --company "Acme Corporation" --state FL
```

### Options

- `--company`: Company name to research (required)
- `--state`: State abbreviation (e.g., FL, NY, CA)
- `--refresh`: Refresh data by recrawling sources
- `--output`: Output directory (default: company_research)

### Example

```bash
# Research a company in Florida
python tools/company_research.py --company "Sunshine Enterprises LLC" --state FL

# Research with fresh data
python tools/company_research.py --company "Tech Innovations Inc" --refresh
```

## Person Research Tool

The person research tool helps you find information about a person's professional licenses, legal history, and background.

### Usage

```bash
python tools/person_research.py --name "John Smith" --state FL --profession lawyer
```

### Options

- `--name`: Person's name (required)
- `--state`: State abbreviation (e.g., FL, NY, CA)
- `--profession`: Professional context (e.g., lawyer, doctor, business)
- `--refresh`: Refresh data by recrawling sources
- `--output`: Output directory (default: person_research)

### Example

```bash
# Research a lawyer in California
python tools/person_research.py --name "Jane Doe" --state CA --profession lawyer

# Research with fresh data
python tools/person_research.py --name "Robert Johnson" --profession "business executive" --refresh
```

## Advanced Usage

These tools use the legal search agent's core modules for data collection, processing, and analysis. You can further enhance your research by:

1. **Modifying configuration files**: Edit the JSON files in the configs directory to target specific sources
2. **Using the web interface**: Start the Streamlit web app to interact with your research data
3. **Custom LangChain prompts**: Modify the LangChain queries in the tools for more specialized research

## Notes

- These tools require the same dependencies as the main legal search agent
- For advanced LangChain features, you'll need an OpenAI API key in your .env file
- Results will be stored in the specified output directories for future reference
