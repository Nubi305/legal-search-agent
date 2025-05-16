# Firecrawl Integration Plan for Legal Search Agent

This document outlines the plan for integrating Firecrawl capabilities into our legal search agent to enhance its web scraping, data extraction, and processing abilities.

## 1. Overview of Firecrawl Benefits

Firecrawl provides several advantages over our current crawler implementation:

- **Advanced Web Scraping**: Better handling of JavaScript-rendered content, anti-bot mechanisms, and dynamic websites
- **Structured Data Extraction**: Direct extraction of structured data with schema definitions
- **LLM-Ready Output**: Multiple output formats optimized for language models
- **Site Mapping**: Fast discovery of all pages on a website
- **Batch Processing**: Process hundreds or thousands of URLs simultaneously
- **Interactive Scraping**: Perform actions like clicking, scrolling, and form filling before extraction
- **PDF and Document Parsing**: Enhanced capability to extract from non-HTML sources

## 2. Implementation Strategy

### Phase 1: Basic Integration (2-3 days)

1. **Add Firecrawl SDK**: 
   - Install the Python SDK: `pip install firecrawl-py`
   - Create a new module that wraps the SDK functionality

2. **Create Firecrawl Crawler Class**:
   - Implement a new crawler that extends our base crawler
   - Ensure it maintains the same interface for seamless switching

3. **Configuration Updates**:
   - Add Firecrawl API key configuration
   - Add crawler type selector in config files
   - Create fallback mechanism to our existing crawler if API limits reached

### Phase 2: Advanced Features (1 week)

1. **Structured Legal Data Extraction**:
   - Create JSON schemas for different legal document types:
     - Court cases
     - Statutes
     - Legal articles
     - Business registrations
     - Judgments and liens

2. **Batch Processing for Multiple Sites**:
   - Implement batch crawling for SOS websites across multiple states
   - Create aggregation functionality for cross-state searches

3. **Interactive Scraping for Auth Walls**:
   - Implement login sequences for sites requiring authentication
   - Create form submission logic for search forms
   - Store session cookies for continued access

### Phase 3: Interface Updates and Analytics (3-4 days)

1. **Web UI Updates**:
   - Add structured data viewing options
   - Create schema selection interface
   - Provide extraction template library

2. **Session Enhancement**:
   - Store extraction schemas with sessions
   - Create template sharing between sessions
   - Add batch job monitoring and resumption

3. **Analytics Dashboard**:
   - Track crawl success rates with different methods
   - Monitor API usage and credit consumption
   - Analyze data quality metrics

## 3. Technical Architecture

### Core Components

1. **FirecrawlClient (src/firecrawl_integration.py)**:
   - Wrapper for the Firecrawl SDK
   - Error handling and retry logic
   - Rate limiting and quota management

2. **FirecrawlCrawler (src/firecrawl_crawler.py)**:
   - Implementation of our crawler interface using Firecrawl
   - Translation between our formats and Firecrawl formats
   - Result caching and persistence

3. **SchemaManager (src/schema_manager.py)**:
   - Repository of legal document schemas
   - Schema selection logic based on URL patterns
   - Schema validation and transformation

4. **BatchProcessor (src/batch_processor.py)**:
   - Handling of multi-site crawling jobs
   - Job monitoring and result aggregation
   - Parallelization and orchestration

### Data Flow

1. User initiates search or session creates crawl job
2. System determines if Firecrawl is appropriate for the target
3. FirecrawlClient submits job with appropriate configuration
4. BatchProcessor monitors job progress
5. Results are transformed into our internal format
6. Data is indexed and linked to session metadata

## 4. Schemas for Legal Data

### Example: Court Case Schema

```json
{
  "type": "object",
  "properties": {
    "case_number": {
      "type": "string",
      "description": "The official case identifier"
    },
    "court": {
      "type": "string",
      "description": "Court where the case was filed"
    },
    "filing_date": {
      "type": "string",
      "description": "Date when the case was filed"
    },
    "parties": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string" }
        }
      }
    },
    "judges": {
      "type": "array",
      "items": { "type": "string" }
    },
    "status": {
      "type": "string",
      "description": "Current status of the case"
    },
    "disposition": {
      "type": "string",
      "description": "Final judgment or disposition"
    },
    "amount": {
      "type": "string",
      "description": "Monetary amount involved if applicable"
    }
  },
  "required": ["case_number", "court", "filing_date", "parties", "status"]
}
```

### Example: Business Registration Schema

```json
{
  "type": "object",
  "properties": {
    "entity_name": {
      "type": "string",
      "description": "Legal name of the business entity"
    },
    "entity_type": {
      "type": "string",
      "description": "Type of entity (LLC, Corporation, etc.)"
    },
    "filing_number": {
      "type": "string",
      "description": "State filing or registration number"
    },
    "status": {
      "type": "string",
      "description": "Current status (Active, Dissolved, etc.)"
    },
    "formation_date": {
      "type": "string",
      "description": "Date the entity was formed"
    },
    "jurisdiction": {
      "type": "string",
      "description": "State or jurisdiction of formation"
    },
    "registered_agent": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "address": { "type": "string" }
      }
    },
    "principals": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "title": { "type": "string" }
        }
      }
    },
    "annual_report_due": {
      "type": "string",
      "description": "Next annual report due date"
    }
  },
  "required": ["entity_name", "entity_type", "filing_number", "status", "jurisdiction"]
}
```

## 5. Cost Analysis

### API Costs
- Firecrawl API pricing: Based on credits per URL processed
- Estimated monthly costs based on usage:
  - Light usage (100 searches/day): $20-50/month
  - Medium usage (500 searches/day): $100-200/month
  - Heavy usage (1000+ searches/day): $300+/month
- Consider implementing credit-based user limits

### Development Costs
- Initial integration: 40-60 developer hours
- Advanced features: 60-80 developer hours
- UI/UX updates: 30-40 developer hours
- Testing and QA: 30-40 developer hours

## 6. Timeline

- **Week 1**: Phase 1 implementation and basic testing
- **Week 2-3**: Phase 2 development of advanced features
- **Week 3-4**: Phase 3 interface updates and testing
- **Week 4**: Documentation, training, and production deployment

## 7. Fallback Strategy

In case of Firecrawl API issues or rate limiting:
1. Automatically fall back to our existing crawler for non-critical requests
2. Implement local caching of frequently requested content
3. Create a hybrid approach that uses our crawler for simple sites and Firecrawl for complex ones
4. Develop circuit breaker pattern to avoid cascading failures

## 8. Success Metrics

- Increase in successful extractions by at least 40%
- Reduction in crawl failures by at least 60%
- Structured data available for at least 80% of legal websites
- User satisfaction increase measured by feedback and usage patterns
- Reduction in manual research time by at least 30%

## 9. Next Steps

1. Create proof of concept with basic Firecrawl integration
2. Test on challenging legal websites (courts, SOS sites)
3. Develop specific schemas for high-value legal document types
4. Implement session-aware batch processing
5. Update user interface to support new capabilities