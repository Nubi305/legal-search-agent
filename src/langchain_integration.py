"""
LangChain integration module for the legal search agent.
"""

import os
import logging
from typing import Dict, List, Any, Optional

from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAI, ChatOpenAI
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('langchain_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LangChainIntegration')

class LegalLangChain:
    """LangChain integration for the legal search agent."""
    
    def __init__(self, vector_store_path: str, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize the LangChain integration.
        
        Args:
            vector_store_path: Path to the vector store
            model_name: OpenAI model name to use
        """
        self.vector_store_path = vector_store_path
        self.model_name = model_name
        
        # Initialize components
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model_name=model_name, temperature=0)
        self.vector_store = self._load_vector_store()
        self.retriever = self._setup_retriever()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize chains
        self.qa_chain = self._setup_qa_chain()
        self.conversational_chain = self._setup_conversational_chain()
    
    def _load_vector_store(self) -> Chroma:
        """
        Load the vector store.
        
        Returns:
            Loaded vector store
        """
        logger.info(f"Loading vector store from {self.vector_store_path}")
        
        # Check if vector store exists
        if not os.path.exists(self.vector_store_path):
            logger.error(f"Vector store not found at {self.vector_store_path}")
            raise FileNotFoundError(f"Vector store not found at {self.vector_store_path}")
        
        # Load the vector store
        vector_store = Chroma(
            persist_directory=self.vector_store_path,
            embedding_function=self.embeddings
        )
        
        return vector_store
    
    def _setup_retriever(self) -> ContextualCompressionRetriever:
        """
        Set up the retriever with contextual compression.
        
        Returns:
            Configured retriever
        """
        # Set up the base retriever
        base_retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 10}
        )
        
        # Add LLM chain extractor for better context extraction
        compressor = LLMChainExtractor.from_llm(self.llm)
        retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_retriever
        )
        
        return retriever
    
    def _setup_qa_chain(self) -> RetrievalQA:
        """
        Set up the QA chain.
        
        Returns:
            Configured QA chain
        """
        # Define prompt template for legal questions
        template = """
        You are a legal research assistant with expertise in legal documents and case law.
        Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Use multiple sentences and cite specific cases, statutes, or regulations when possible.
        Keep the answer focused and relevant to the legal question.
        
        Context: {context}
        
        Question: {question}
        
        Answer:
        """
        
        QA_PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Create the chain
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": QA_PROMPT},
            return_source_documents=True
        )
        
        return chain
    
    def _setup_conversational_chain(self) -> ConversationalRetrievalChain:
        """
        Set up the conversational chain.
        
        Returns:
            Configured conversational chain
        """
        # Create the conversational chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.retriever,
            memory=self.memory,
            return_source_documents=True
        )
        
        return chain
    
    def query(self, query: str) -> Dict[str, Any]:
        """
        Query the QA chain.
        
        Args:
            query: User query
            
        Returns:
            QA chain response
        """
        logger.info(f"Querying QA chain: {query}")
        
        try:
            # Execute the query
            response = self.qa_chain({"query": query})
            
            # Format the response
            result = {
                "answer": response["result"],
                "sources": [doc.metadata for doc in response["source_documents"]]
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error querying QA chain: {str(e)}")
            return {"answer": f"Error: {str(e)}", "sources": []}
    
    def chat(self, query: str) -> Dict[str, Any]:
        """
        Query the conversational chain.
        
        Args:
            query: User query
            
        Returns:
            Conversational chain response
        """
        logger.info(f"Querying conversational chain: {query}")
        
        try:
            # Execute the query
            response = self.conversational_chain({"question": query})
            
            # Format the response
            result = {
                "answer": response["answer"],
                "sources": [doc.metadata for doc in response["source_documents"]]
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error querying conversational chain: {str(e)}")
            return {"answer": f"Error: {str(e)}", "sources": []}
    
    def reset_conversation(self) -> None:
        """Reset the conversation memory."""
        self.memory.clear()


class LegalPromptTemplates:
    """Prompt templates for legal domain."""
    
    # Template for legal case analysis
    CASE_ANALYSIS_TEMPLATE = """
    You are a legal expert analyzing a case. Based on the provided information, analyze the following aspects:
    
    Case Information: {case_info}
    
    1. Identify the key legal issues presented in this case.
    2. What precedents or legal principles are relevant to this case?
    3. What are the arguments likely to be made by each party?
    4. What is the likely outcome based on existing legal precedent?
    5. What broader implications might this case have for jurisprudence?
    
    Provide a comprehensive analysis with references to relevant statutes and case law.
    """
    
    # Template for statute interpretation
    STATUTE_INTERPRETATION_TEMPLATE = """
    You are a legal expert interpreting a statute. Based on the provided text, analyze the following:
    
    Statute Text: {statute_text}
    
    1. What is the plain meaning of this statutory language?
    2. What was the likely legislative intent behind this statute?
    3. How have courts interpreted similar language in the past?
    4. Are there any ambiguities or potential constitutional issues?
    5. How would this statute likely be applied in the context of: {context}
    
    Provide a detailed interpretation with references to relevant case law and principles of statutory construction.
    """
    
    # Template for legal research query
    LEGAL_RESEARCH_TEMPLATE = """
    You are a legal researcher helping to find relevant information. Based on the following query, identify the most relevant legal resources:
    
    Research Question: {research_question}
    Jurisdiction: {jurisdiction}
    
    1. What key cases should be reviewed for this question?
    2. What statutes or regulations are most relevant?
    3. Are there any secondary sources (law review articles, treatises) that would be helpful?
    4. What search terms would be most effective for further research?
    5. Are there any specific legal databases that would be particularly useful for this query?
    
    Provide a comprehensive research plan with specific citations where possible.
    """
    
    @classmethod
    def get_prompt_template(cls, template_name: str) -> PromptTemplate:
        """
        Get a prompt template by name.
        
        Args:
            template_name: Name of the template
            
        Returns:
            PromptTemplate
        """
        if template_name == "case_analysis":
            return PromptTemplate(
                template=cls.CASE_ANALYSIS_TEMPLATE,
                input_variables=["case_info"]
            )
        elif template_name == "statute_interpretation":
            return PromptTemplate(
                template=cls.STATUTE_INTERPRETATION_TEMPLATE,
                input_variables=["statute_text", "context"]
            )
        elif template_name == "legal_research":
            return PromptTemplate(
                template=cls.LEGAL_RESEARCH_TEMPLATE,
                input_variables=["research_question", "jurisdiction"]
            )
        else:
            raise ValueError(f"Unknown template name: {template_name}")
