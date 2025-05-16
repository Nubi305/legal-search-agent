"""
LangFlow integration for the legal search agent.
"""

import os
import json
import logging
import subprocess
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('langflow_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LangFlowIntegration')

class LangFlowIntegration:
    """Class for integrating LangFlow with the legal search agent."""
    
    def __init__(self, flows_dir: str = "flows"):
        """
        Initialize LangFlow integration.
        
        Args:
            flows_dir: Directory for storing flows
        """
        self.flows_dir = flows_dir
        
        # Create flows directory if it doesn't exist
        if not os.path.exists(flows_dir):
            os.makedirs(flows_dir)
    
    def start_langflow_server(self, host: str = "localhost", port: int = 7860) -> None:
        """
        Start the LangFlow server.
        
        Args:
            host: Host to run the server on
            port: Port to run the server on
        """
        logger.info(f"Starting LangFlow server on {host}:{port}")
        
        try:
            # Start LangFlow server
            cmd = f"langflow run --host {host} --port {port}"
            
            # Use subprocess.Popen to run the command in the background
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit to check if the process started successfully
            returncode = process.poll()
            if returncode is not None:
                stdout, stderr = process.communicate()
                logger.error(f"LangFlow server failed to start: {stderr}")
                raise RuntimeError(f"LangFlow server failed to start: {stderr}")
            
            logger.info(f"LangFlow server started successfully. Access at http://{host}:{port}")
            
        except Exception as e:
            logger.error(f"Error starting LangFlow server: {str(e)}")
            raise
    
    def save_flow(self, flow_data: Dict[str, Any], flow_name: str) -> str:
        """
        Save a flow to a file.
        
        Args:
            flow_data: Flow data
            flow_name: Name of the flow
            
        Returns:
            Path to the saved flow file
        """
        # Ensure flow name has .json extension
        if not flow_name.endswith('.json'):
            flow_name = f"{flow_name}.json"
        
        # Create flow path
        flow_path = os.path.join(self.flows_dir, flow_name)
        
        # Save flow data to file
        with open(flow_path, 'w', encoding='utf-8') as f:
            json.dump(flow_data, f, indent=2)
        
        logger.info(f"Flow saved to {flow_path}")
        
        return flow_path
    
    def load_flow(self, flow_name: str) -> Dict[str, Any]:
        """
        Load a flow from a file.
        
        Args:
            flow_name: Name of the flow
            
        Returns:
            Flow data
        """
        # Ensure flow name has .json extension
        if not flow_name.endswith('.json'):
            flow_name = f"{flow_name}.json"
        
        # Create flow path
        flow_path = os.path.join(self.flows_dir, flow_name)
        
        # Check if flow exists
        if not os.path.exists(flow_path):
            logger.error(f"Flow not found: {flow_path}")
            raise FileNotFoundError(f"Flow not found: {flow_path}")
        
        # Load flow data from file
        with open(flow_path, 'r', encoding='utf-8') as f:
            flow_data = json.load(f)
        
        logger.info(f"Flow loaded from {flow_path}")
        
        return flow_data
    
    def list_flows(self) -> list:
        """
        List all available flows.
        
        Returns:
            List of flow names
        """
        flows = []
        
        # List all JSON files in the flows directory
        for file in os.listdir(self.flows_dir):
            if file.endswith('.json'):
                flows.append(file)
        
        return flows


# Pre-defined flow templates
class LegalFlowTemplates:
    """Pre-defined flow templates for legal use cases."""
    
    @staticmethod
    def get_basic_qa_flow() -> Dict[str, Any]:
        """
        Get a basic QA flow template.
        
        Returns:
            Flow data
        """
        flow = {
            "name": "Legal QA Flow",
            "description": "A basic question-answering flow for legal documents",
            "nodes": [
                {
                    "id": "vectorstore",
                    "type": "VectorStore",
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "type": "Chroma",
                        "params": {
                            "persist_directory": "vector_stores",
                            "embedding": "OpenAIEmbeddings"
                        }
                    }
                },
                {
                    "id": "retriever",
                    "type": "Retriever",
                    "position": {"x": 300, "y": 100},
                    "data": {
                        "search_type": "similarity",
                        "search_kwargs": {"k": 5}
                    }
                },
                {
                    "id": "qa_chain",
                    "type": "RetrievalQA",
                    "position": {"x": 500, "y": 100},
                    "data": {
                        "chain_type": "stuff",
                        "llm": {
                            "type": "ChatOpenAI",
                            "params": {
                                "model_name": "gpt-3.5-turbo",
                                "temperature": 0
                            }
                        }
                    }
                }
            ],
            "edges": [
                {
                    "source": "vectorstore",
                    "target": "retriever",
                    "sourceHandle": "retriever",
                    "targetHandle": "vectorstore"
                },
                {
                    "source": "retriever",
                    "target": "qa_chain",
                    "sourceHandle": "output",
                    "targetHandle": "retriever"
                }
            ]
        }
        
        return flow
    
    @staticmethod
    def get_conversational_qa_flow() -> Dict[str, Any]:
        """
        Get a conversational QA flow template.
        
        Returns:
            Flow data
        """
        flow = {
            "name": "Legal Conversational QA Flow",
            "description": "A conversational question-answering flow for legal documents",
            "nodes": [
                {
                    "id": "vectorstore",
                    "type": "VectorStore",
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "type": "Chroma",
                        "params": {
                            "persist_directory": "vector_stores",
                            "embedding": "OpenAIEmbeddings"
                        }
                    }
                },
                {
                    "id": "retriever",
                    "type": "Retriever",
                    "position": {"x": 300, "y": 100},
                    "data": {
                        "search_type": "similarity",
                        "search_kwargs": {"k": 5}
                    }
                },
                {
                    "id": "memory",
                    "type": "ConversationBufferMemory",
                    "position": {"x": 300, "y": 250},
                    "data": {
                        "memory_key": "chat_history",
                        "return_messages": True
                    }
                },
                {
                    "id": "conversational_chain",
                    "type": "ConversationalRetrievalChain",
                    "position": {"x": 500, "y": 175},
                    "data": {
                        "llm": {
                            "type": "ChatOpenAI",
                            "params": {
                                "model_name": "gpt-3.5-turbo",
                                "temperature": 0
                            }
                        }
                    }
                }
            ],
            "edges": [
                {
                    "source": "vectorstore",
                    "target": "retriever",
                    "sourceHandle": "retriever",
                    "targetHandle": "vectorstore"
                },
                {
                    "source": "retriever",
                    "target": "conversational_chain",
                    "sourceHandle": "output",
                    "targetHandle": "retriever"
                },
                {
                    "source": "memory",
                    "target": "conversational_chain",
                    "sourceHandle": "output",
                    "targetHandle": "memory"
                }
            ]
        }
        
        return flow
    
    @staticmethod
    def get_legal_research_flow() -> Dict[str, Any]:
        """
        Get a legal research flow template.
        
        Returns:
            Flow data
        """
        flow = {
            "name": "Legal Research Flow",
            "description": "A flow for comprehensive legal research",
            "nodes": [
                {
                    "id": "vectorstore",
                    "type": "VectorStore",
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "type": "Chroma",
                        "params": {
                            "persist_directory": "vector_stores",
                            "embedding": "OpenAIEmbeddings"
                        }
                    }
                },
                {
                    "id": "retriever",
                    "type": "Retriever",
                    "position": {"x": 300, "y": 100},
                    "data": {
                        "search_type": "similarity",
                        "search_kwargs": {"k": 10}
                    }
                },
                {
                    "id": "compressor",
                    "type": "LLMChainExtractor",
                    "position": {"x": 300, "y": 250},
                    "data": {
                        "llm": {
                            "type": "ChatOpenAI",
                            "params": {
                                "model_name": "gpt-3.5-turbo",
                                "temperature": 0
                            }
                        }
                    }
                },
                {
                    "id": "compression_retriever",
                    "type": "ContextualCompressionRetriever",
                    "position": {"x": 500, "y": 175},
                    "data": {}
                },
                {
                    "id": "research_chain",
                    "type": "RetrievalQA",
                    "position": {"x": 700, "y": 175},
                    "data": {
                        "chain_type": "map_reduce",
                        "llm": {
                            "type": "ChatOpenAI",
                            "params": {
                                "model_name": "gpt-4",
                                "temperature": 0
                            }
                        }
                    }
                }
            ],
            "edges": [
                {
                    "source": "vectorstore",
                    "target": "retriever",
                    "sourceHandle": "retriever",
                    "targetHandle": "vectorstore"
                },
                {
                    "source": "retriever",
                    "target": "compression_retriever",
                    "sourceHandle": "output",
                    "targetHandle": "base_retriever"
                },
                {
                    "source": "compressor",
                    "target": "compression_retriever",
                    "sourceHandle": "output",
                    "targetHandle": "base_compressor"
                },
                {
                    "source": "compression_retriever",
                    "target": "research_chain",
                    "sourceHandle": "output",
                    "targetHandle": "retriever"
                }
            ]
        }
        
        return flow