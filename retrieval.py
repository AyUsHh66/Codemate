import os
from dotenv import load_dotenv
import logging
import sys
import json

# LlamaIndex Imports
from llama_index.core import (
    StorageContext,
    load_index_from_storage,
    QueryBundle,
    Settings
)
from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.postprocessor.colbert_rerank import ColbertRerank
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.storage.docstore import SimpleDocumentStore
import qdrant_client

# Configuration Import
import config

# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger()

# Load environment variables
load_dotenv()

class HybridRetriever(BaseRetriever):
    """Custom retriever that fuses results from vector and keyword search."""
    def __init__(self, vector_retriever, bm25_retriever):
        self._vector_retriever = vector_retriever
        self._bm25_retriever = bm25_retriever
        super().__init__()
    
    def _retrieve(self, query_bundle: QueryBundle):
        """Retrieve nodes from both retrievers and combine them."""
        vector_nodes = self._vector_retriever.retrieve(query_bundle)
        bm25_nodes = self._bm25_retriever.retrieve(query_bundle)
        
        # Combine and de-duplicate nodes with score weighting
        node_dict = {}
        
        # Add vector search results with weight
        for node in vector_nodes:
            node_id = node.node.node_id
            if node_id not in node_dict:
                node_dict[node_id] = node
            else:
                # Combine scores if node appears in both
                node_dict[node_id].score = (node_dict[node_id].score + node.score) / 2
        
        # Add BM25 results with weight
        for node in bm25_nodes:
            node_id = node.node.node_id
            if node_id not in node_dict:
                node_dict[node_id] = node
            else:
                # Combine scores if node appears in both
                node_dict[node_id].score = (node_dict[node_id].score + node.score) / 2
        
        # Sort by score and return
        all_nodes = list(node_dict.values())
        all_nodes.sort(key=lambda x: x.score if x.score else 0, reverse=True)
        
        return all_nodes

def verify_storage():
    """Verify that storage files exist and contain data."""
    if not os.path.exists(config.STORAGE_DIR):
        raise FileNotFoundError(f"Storage directory '{config.STORAGE_DIR}' not found. Run 'python ingestion.py' first.")
    
    # Check docstore
    docstore_path = config.DOCSTORE_PATH
    if not os.path.exists(docstore_path):
        raise FileNotFoundError(f"Docstore file not found at '{docstore_path}'. Run 'python ingestion.py' first.")
    
    # Verify docstore has data
    with open(docstore_path, 'r') as f:
        data = json.load(f)
        if "docstore/data" not in data or len(data.get("docstore/data", {})) == 0:
            raise ValueError(
                "Docstore exists but contains no documents. "
                "Please delete the ./storage directory and re-run 'python ingestion.py'."
            )
    
    log.info(f"✓ Storage verification passed")

def setup_query_engine():
    """
    Loads the persisted index and sets up the query engine with a hybrid retriever
    and a ColBERT re-ranker for advanced retrieval.
    """
    # First verify storage
    verify_storage()
    
    # Configure global settings
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    Settings.llm = Gemini(model=config.LLM_MODEL, api_key=api_key)
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)
    
    # Load the docstore explicitly
    log.info(f"Loading docstore from: {config.DOCSTORE_PATH}")
    docstore = SimpleDocumentStore.from_persist_path(config.DOCSTORE_PATH)
    
    # Verify docstore has documents
    doc_count = len(docstore.docs)
    log.info(f"Loaded docstore with {doc_count} documents")
    
    if doc_count == 0:
        raise ValueError(
            "Docstore loaded but contains no documents. "
            "Please delete ./storage directory and re-run ingestion."
        )
    
    # Initialize Qdrant and vector store
    client = qdrant_client.QdrantClient(path=config.QDRANT_PATH)
    vector_store = QdrantVectorStore(client=client, collection_name="document_collection")
    
    # Load index with the loaded docstore
    log.info("Loading index from storage...")
    storage_context = StorageContext.from_defaults(
        persist_dir=config.STORAGE_DIR,
        vector_store=vector_store,
        docstore=docstore,
    )
    index = load_index_from_storage(storage_context)
    
    # Setup Hybrid Retriever
    log.info("Setting up Hybrid Retriever (Vector + BM25)...")
    
    # Vector retriever
    vector_retriever = VectorIndexRetriever(
        index=index, 
        similarity_top_k=config.VECTOR_TOP_K
    )
    
    # BM25 retriever using nodes from docstore
    nodes = list(docstore.docs.values())
    log.info(f"Initializing BM25 retriever with {len(nodes)} nodes")
    
    bm25_retriever = BM25Retriever.from_defaults(
        nodes=nodes, 
        similarity_top_k=config.BM25_TOP_K
    )
    
    # Combine into hybrid retriever
    hybrid_retriever = HybridRetriever(vector_retriever, bm25_retriever)
    
    # Setup ColBERT Re-ranker
    log.info("Setting up ColBERT Re-ranker...")
    reranker = ColbertRerank(
        top_n=config.RERANKER_TOP_N,
        model=config.RERANKER_MODEL,
        tokenizer=config.RERANKER_MODEL,
        keep_retrieval_score=True,
    )
    
    # Assemble the Query Engine
    query_engine = RetrieverQueryEngine.from_args(
        retriever=hybrid_retriever,
        node_postprocessors=[reranker],
    )
    
    log.info("✅ Advanced query engine with Hybrid Retriever and ColBERT re-ranker is ready!")
    log.info(f"   - Vector search top-k: {config.VECTOR_TOP_K}")
    log.info(f"   - BM25 search top-k: {config.BM25_TOP_K}")
    log.info(f"   - Re-ranker top-n: {config.RERANKER_TOP_N}")
    
    return query_engine

# Test function for direct usage
if __name__ == "__main__":
    try:
        engine = setup_query_engine()
        
        # Test query
        test_query = "What are the main findings of the research?"
        log.info(f"\nTest Query: {test_query}")
        response = engine.query(test_query)
        log.info(f"Response: {response}")
        
    except Exception as e:
        log.error(f"Failed to setup query engine: {e}")
        sys.exit(1)