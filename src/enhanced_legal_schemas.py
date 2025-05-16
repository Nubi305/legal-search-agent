"""
Enhanced schemas for BlackBookOnline and NYSCEF integration.

This module provides specialized schemas and extraction logic for 
BlackBookOnline and NYSCEF court records data.
"""

from typing import Dict, List, Any, Optional

# Enhanced schemas for specific legal data sources
class EnhancedLegalSchemas:
    """Enhanced JSON schemas for legal document types from specific sources."""
    
    @staticmethod
    def nyscef_case_schema() -> Dict[str, Any]:
        """
        Get the schema for NYSCEF case data.
        
        Returns:
            JSON schema
        """
        return {
            "type": "object",
            "properties": {
                "index_number": {
                    "type": "string",
                    "description": "The NYSCEF case index number"
                },
                "case_name": {
                    "type": "string",
                    "description": "The name of the case (Caption)"
                },
                "court": {
                    "type": "string",
                    "description": "The court where the case was filed"
                },
                "county": {
                    "type": "string",
                    "description": "The county where the case was filed"
                },
                "case_type": {
                    "type": "string",
                    "description": "The type of case (e.g. Commercial, Tort, etc.)"
                },
                "filing_date": {
                    "type": "string",
                    "description": "Date when the case was filed"
                },
                "status": {
                    "type": "string",
                    "description": "Current status of the case"
                },
                "parties": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": { "type": "string" },
                            "role": { "type": "string" },
                            "attorney": { "type": "string" }
                        }
                    }
                },
                "judge": {
                    "type": "string",
                    "description": "Assigned judge"
                },
                "documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "number": { "type": "string" },
                            "date_filed": { "type": "string" },
                            "description": { "type": "string" },
                            "document_type": { "type": "string" }
                        }
                    }
                },
                "appearances": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": { "type": "string" },
                            "purpose": { "type": "string" },
                            "outcome": { "type": "string" }
                        }
                    }
                }
            },
            "required": ["index_number", "case_name", "court", "county", "filing_date"]
        }
    
    @staticmethod
    def judgment_lien_schema() -> Dict[str, Any]:
        """
        Get the schema for judgment and lien data.
        
        Returns:
            JSON schema
        """
        return {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "description": "Type of document (Judgment, Lien, UCC Filing, etc.)"
                },
                "file_number": {
                    "type": "string",
                    "description": "Filing or document number"
                },
                "filing_date": {
                    "type": "string",
                    "description": "Date when the document was filed"
                },
                "filing_location": {
                    "type": "string",
                    "description": "Where the document was filed (county, office, etc.)"
                },
                "creditor": {
                    "type": "string",
                    "description": "Name of the creditor/plaintiff"
                },
                "debtor": {
                    "type": "string",
                    "description": "Name of the debtor/defendant"
                },
                "amount": {
                    "type": "string",
                    "description": "Monetary amount of the judgment/lien"
                },
                "status": {
                    "type": "string",
                    "description": "Current status (Active, Satisfied, Released, etc.)"
                },
                "satisfaction_date": {
                    "type": "string",
                    "description": "Date when the judgment/lien was satisfied (if applicable)"
                },
                "expiration_date": {
                    "type": "string",
                    "description": "Expiration date of the judgment/lien"
                },
                "property_description": {
                    "type": "string",
                    "description": "Description of property affected (for liens)"
                },
                "additional_info": {
                    "type": "string",
                    "description": "Any additional information"
                }
            },
            "required": ["document_type", "file_number", "filing_date", "creditor", "debtor"]
        }
    
    @staticmethod
    def secretary_of_state_schema() -> Dict[str, Any]:
        """
        Get the schema for Secretary of State business entity data.
        
        Returns:
            JSON schema
        """
        return {
            "type": "object",
            "properties": {
                "entity_name": {
                    "type": "string",
                    "description": "Name of the business entity"
                },
                "entity_type": {
                    "type": "string",
                    "description": "Type of entity (LLC, Corporation, etc.)"
                },
                "entity_number": {
                    "type": "string",
                    "description": "State entity/filing number"
                },
                "state": {
                    "type": "string",
                    "description": "State of registration"
                },
                "status": {
                    "type": "string",
                    "description": "Current status (Active, Inactive, etc.)"
                },
                "formation_date": {
                    "type": "string",
                    "description": "Date when the entity was formed"
                },
                "good_standing": {
                    "type": "boolean",
                    "description": "Whether the entity is in good standing"
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
                "mailing_address": {
                    "type": "string",
                    "description": "Mailing address of the entity"
                },
                "physical_address": {
                    "type": "string",
                    "description": "Physical address of the entity"
                },
                "last_report_filed": {
                    "type": "string",
                    "description": "Date of the last report filed"
                },
                "next_report_due": {
                    "type": "string",
                    "description": "Date when the next report is due"
                }
            },
            "required": ["entity_name", "entity_type", "entity_number", "state", "status"]
        }
    
    @staticmethod
    def get_schema_for_url(url: str) -> Optional[Dict[str, Any]]:
        """
        Get the appropriate schema for a URL based on specific sources.
        
        Args:
            url: URL to get schema for
            
        Returns:
            JSON schema or None if no matching schema
        """
        if not url:
            return None
            
        url_lower = url.lower()
        
        # NYSCEF case search
        if "nyscef" in url_lower or "courts.state.ny.us" in url_lower:
            return EnhancedLegalSchemas.nyscef_case_schema()
        
        # BlackBook Secretary of State
        if "blackbookonline" in url_lower and "secretary" in url_lower:
            return EnhancedLegalSchemas.secretary_of_state_schema()
        
        # BlackBook UCC or county records (likely to contain judgments/liens)
        if "blackbookonline" in url_lower and ("ucc" in url_lower or "county" in url_lower or "public-records" in url_lower):
            return EnhancedLegalSchemas.judgment_lien_schema()
        
        # No specific schema for this URL
        return None

# Search prompt templates for specific legal research
class LegalSearchPrompts:
    """Custom prompts for legal data extraction."""
    
    @staticmethod
    def nyscef_case_extraction() -> str:
        """
        Get prompt for extracting NYSCEF case data.
        
        Returns:
            Extraction prompt
        """
        return """
        Extract the following information from this NY Courts NYSCEF case page:
        1. Index Number - Look for a format like "123456/2023"
        2. Case Name/Caption - Usually in format "Plaintiff v. Defendant"
        3. Filing Date
        4. Case Type
        5. Court and County
        6. Current Status
        7. Judge assigned
        8. All parties involved and their roles (plaintiff, defendant, etc.)
        9. List of filed documents with their filing dates
        10. Any monetary amounts mentioned in judgments
        
        For each document listed, note whether it's a judgment, lien, or other important filing.
        """
    
    @staticmethod
    def judgment_lien_extraction() -> str:
        """
        Get prompt for extracting judgment and lien data.
        
        Returns:
            Extraction prompt
        """
        return """
        Extract the following information from this judgment or lien record:
        1. Document type (Judgment, Tax Lien, Mechanics Lien, UCC Filing, etc.)
        2. File/Case Number
        3. Filing Date
        4. Filing Location (County, Office)
        5. Creditor/Plaintiff name
        6. Debtor/Defendant name
        7. Monetary amount
        8. Current status (Active, Satisfied, Released)
        9. Satisfaction date (if applicable)
        10. Property description (for property liens)
        
        Be specific about whether this is an active judgment/lien or if it has been satisfied.
        """
    
    @staticmethod
    def business_entity_extraction() -> str:
        """
        Get prompt for extracting business entity data.
        
        Returns:
            Extraction prompt
        """
        return """
        Extract the following information about this business entity:
        1. Entity Name (exact legal name)
        2. Entity Type (LLC, Corporation, etc.)
        3. Entity/Filing Number
        4. State of Registration
        5. Current Status (Active, Inactive, Dissolved)
        6. Formation/Registration Date
        7. Registered Agent name and address
        8. Principal officers/members and their titles
        9. Business addresses (both mailing and physical if available)
        10. Last annual report filed and next due date
        11. Whether the entity is in good standing
        
        Note any DBAs (Doing Business As) names and the names of individuals associated with the business.
        """