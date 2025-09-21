# /deep-researcher-agent/agent.py
import os
from dotenv import load_dotenv
import logging
import sys

# LlamaIndex Imports
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent import ReActAgent
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Local Imports
from retrieval import setup_query_engine
import config

# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger()

# Load environment variables
load_dotenv()

def setup_agent():
    """
    Sets up a ReAct Agent with a single tool for querying the local knowledge base.
    This agent is designed for multi-step reasoning over the indexed documents.
    """
    # Verify API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    # Configure global settings if not already done
    if not hasattr(Settings, 'llm') or Settings.llm is None:
        Settings.llm = Gemini(model=config.LLM_MODEL, api_key=api_key)
    if not hasattr(Settings, 'embed_model') or Settings.embed_model is None:
        Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)
    
    log.info("Setting up query engine...")
    query_engine = setup_query_engine()
    
    # Define the tool for the agent
    query_engine_tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="local_document_retriever",
        description=(
            "Useful for answering complex questions about the documents you have been provided. "
            "This tool performs retrieval-augmented generation (RAG) on a local knowledge base."
        )
    )
   
    # The agent is now purely local, with no external search capabilities
    agent = ReActAgent.from_tools(
        tools=[query_engine_tool],
        llm=Settings.llm,
        verbose=True
    )
   
    log.info("✅ ReAct agent for deep research is ready.")
    return agent
