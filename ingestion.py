import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import logging
import sys

# Import qdrant_client and its models correctly
import qdrant_client
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# LlamaIndex Imports
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings,
)
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Configuration Import
import config

# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger()

# Load environment variables
load_dotenv()

def setup_paths():
    """Create necessary directories if they don't exist."""
    os.makedirs(config.PDF_DIRECTORY, exist_ok=True)
    os.makedirs(config.MARKDOWN_DIR, exist_ok=True)
    os.makedirs(config.STORAGE_DIR, exist_ok=True)
    log.info("Directories are set up.")

def parse_documents_with_nougat():
    """
    Parses all PDFs in the data directory using the Nougat parser.
    Nougat is a vision model trained on academic papers, providing high-quality parsing.
    """
    pdf_files = list(Path(config.PDF_DIRECTORY).glob("*.pdf"))
    if not pdf_files:
        log.error(f"No PDF files found in {config.PDF_DIRECTORY}. Please add your academic papers to this directory.")
        return False

    log.info(f"Found {len(pdf_files)} PDF(s) to process with Nougat.")
    
    # Check if Nougat has already processed these files to avoid re-running
    processed_files = [p.stem for p in Path(config.MARKDOWN_DIR).glob("*.mmd")]
    all_processed = all(p.stem in processed_files for p in pdf_files)

    if all_processed and processed_files:
        log.info("All PDFs have already been parsed by Nougat. Skipping parsing.")
        return True

    log.info("Starting Nougat to parse semantic structure... This can take a while.")
    command = ["nougat", str(config.PDF_DIRECTORY), "-o", config.MARKDOWN_DIR]
    
    try:
        subprocess.run(command, check=True)
        log.info("Nougat processing complete.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log.warning(f"Nougat parsing failed: {e}")
        log.info("Falling back to direct PDF parsing...")
        return True  # Continue with fallback

def build_and_persist_index():
    """
    Builds a vector index from documents and properly persists everything including the docstore.
    """
    log.info("Starting to build and persist the index...")
    
    # Configure models
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    
    Settings.llm = Gemini(model=config.LLM_MODEL, api_key=api_key)
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)
    log.info(f"Using LLM: {config.LLM_MODEL}")
    log.info(f"Using embedding model: {config.EMBED_MODEL}")
    
    # Try loading from markdown directory first (if Nougat succeeded)
    markdown_files = list(Path(config.MARKDOWN_DIR).glob("*.mmd"))
    if markdown_files:
        log.info(f"Loading from parsed markdown files in {config.MARKDOWN_DIR}")
        documents = SimpleDirectoryReader(config.MARKDOWN_DIR, filename_as_id=True).load_data()
    else:
        # Fallback: Load directly from PDFs
        log.info(f"Loading directly from PDF files in {config.PDF_DIRECTORY}")
        documents = SimpleDirectoryReader(config.PDF_DIRECTORY, filename_as_id=True).load_data()
    
    if not documents:
        raise ValueError("No documents could be loaded. Check your PDF files.")
    
    log.info(f"Loaded {len(documents)} document(s).")
    
    # Parse documents into nodes using SentenceWindowNodeParser
    log.info("Parsing documents into nodes...")
    node_parser = SentenceWindowNodeParser.from_defaults(
        window_size=3,
        window_metadata_key="window",
        original_text_metadata_key="original_text",
    )
    
    # Parse all documents into nodes
    nodes = []
    for doc in documents:
        doc_nodes = node_parser.get_nodes_from_documents([doc])
        nodes.extend(doc_nodes)
    
    log.info(f"Created {len(nodes)} nodes from documents.")
    
    if not nodes:
        raise ValueError("No nodes were created from documents. Documents might be empty.")
    
    # Create fresh docstore and explicitly add all nodes
    log.info("Creating document store and adding nodes...")
    docstore = SimpleDocumentStore()
    docstore.add_documents(nodes)
    
    # Verify docstore has documents
    doc_count = len(docstore.docs)
    log.info(f"Document store now contains {doc_count} nodes.")
    
    # Setup Qdrant vector store
    log.info("Setting up Qdrant vector store...")
    client = QdrantClient(path=config.QDRANT_PATH)
    
    # Recreate collection to ensure clean state
    try:
        client.delete_collection(collection_name="document_collection")
    except:
        pass  # Collection might not exist
    
    # Create collection with correct imports
    client.recreate_collection(
        collection_name="document_collection",
        vectors_config=VectorParams(
            size=384,  # BGE-small-en-v1.5 dimension
            distance=Distance.COSINE,
        ),
    )
    
    vector_store = QdrantVectorStore(client=client, collection_name="document_collection")
    
    # Create storage context with both vector store and docstore
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        docstore=docstore
    )
    
    # Build index from nodes (not documents) to ensure docstore is used
    log.info("Building vector index from nodes...")
    index = VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
        show_progress=True,
    )
    
    # Persist everything
    log.info(f"Persisting index and docstore to {config.STORAGE_DIR}")
    index.storage_context.persist(persist_dir=config.STORAGE_DIR)
    
    # Verify persistence
    verify_persistence()
    
    log.info("✅ Index, docstore, and vector store have been successfully persisted!")

def verify_persistence():
    """Verify that storage files are properly created and contain data."""
    import json
    
    log.info("\nVerifying persistence...")
    log.info("-" * 40)
    
    # Check docstore
    docstore_path = os.path.join(config.STORAGE_DIR, "docstore.json")
    if os.path.exists(docstore_path):
        with open(docstore_path, 'r') as f:
            data = json.load(f)
            if "docstore/data" in data:
                doc_count = len(data["docstore/data"])
                log.info(f"✓ Docstore: {doc_count} documents stored")
                if doc_count == 0:
                    log.error("⚠️  WARNING: Docstore is empty!")
            else:
                log.error("⚠️  WARNING: Docstore has wrong structure!")
    else:
        log.error("✗ Docstore file not found!")
    
    # Check index store
    index_path = os.path.join(config.STORAGE_DIR, "index_store.json")
    if os.path.exists(index_path):
        size = os.path.getsize(index_path)
        log.info(f"✓ Index store: {size} bytes")
    else:
        log.error("✗ Index store not found!")
    
    # Check Qdrant
    if os.path.exists(config.QDRANT_PATH):
        log.info(f"✓ Qdrant database exists")
    else:
        log.error("✗ Qdrant database not found!")
    
    log.info("-" * 40)

if __name__ == "__main__":
    setup_paths()
    
    # Try Nougat parsing (optional)
    parse_documents_with_nougat()
    
    # Build and persist index
    try:
        build_and_persist_index()
        log.info("\n" + "=" * 60)
        log.info("INGESTION PROCESS COMPLETE!")
        log.info("=" * 60)
    except Exception as e:
        log.error(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)