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

## Judgment Research Tool

The judgment research tool helps you find civil judgments, liens, and legal claims against businesses and individuals, with special attention to NY courts (NYSCEF).

### Usage

```bash
python tools/judgment_research.py --name "Acme LLC" --type business --state NY
```

### Options

- `--name`: Business or person name to search (required)
- `--type`: Type of entity to search (business, person, or both)
- `--state`: State abbreviation (e.g., NY, FL, CA)
- `--county`: County name (for more targeted searches)
- `--refresh`: Refresh data by recrawling sources
- `--output`: Output directory (default: judgment_research)

### Example

```bash
# Search for judgments against a business in New York
python tools/judgment_research.py --name "ABC Construction LLC" --type business --state NY

# Search for judgments against a person in a specific county
python tools/judgment_research.py --name "John Smith" --type person --state FL --county Broward

# Search for judgments with fresh data
python tools/judgment_research.py --name "Global Enterprises" --refresh
```

## Session Management Tool

The session management tool helps you track, organize, and continue your legal research across multiple sessions. It provides a way to review past searches, analyze research history, and pick up where you left off.

### Usage

```bash
python tools/session_management.py [options]
```

### Options

- `--list`: List all available sessions
- `--show SESSION_ID`: Show details for a specific session
- `--search TERM`: Search for sessions containing a term
- `--load SESSION_ID`: Load and interact with a session
- `--delete SESSION_ID`: Delete a session
- `--create NAME`: Create a new session with a name
- `--dir DIRECTORY`: Directory for storing sessions (default: sessions)

### Example

```bash
# List all sessions
python tools/session_management.py --list

# Create a new session
python tools/session_management.py --create "Acme Due Diligence"

# Search for sessions about a specific entity
python tools/session_management.py --search "Smith Construction"

# Continue a previous research session
python tools/session_management.py --load session_1715962348
```

### Interactive Mode

When you load a session with `--load`, you'll enter interactive mode where you can:

- Review past searches and entities
- See conversation history
- Continue research with contextual awareness
- Get AI-generated suggestions for next research steps based on previous findings

## Advanced Usage

These tools use the legal search agent's core modules for data collection, processing, and analysis. You can further enhance your research by:

1. **Modifying configuration files**: Edit the JSON files in the configs directory to target specific sources
2. **Using the web interface**: Start the Streamlit web app to interact with your research data
3. **Custom LangChain prompts**: Modify the LangChain queries in the tools for more specialized research
4. **Session continuity**: Use the session management system to maintain context between research sessions

## Notes

- These tools require the same dependencies as the main legal search agent
- For advanced LangChain features, you'll need an OpenAI API key in your .env file
- Results will be stored in the specified output directories for future reference
- The NYSCEF system (https://iapps.courts.state.ny.us/nyscef/CaseSearch) is especially valuable for New York judgments
- Session data is stored in JSON format and can be backed up or transferred between systems