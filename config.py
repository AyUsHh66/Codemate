import os

# Directory Paths
PDF_DIRECTORY = "./data"  # Where your PDF files are stored
DATA_DIR = "./data"  # Alias for compatibility
MARKDOWN_DIR = "./output_parsed_markdown"  # Where Nougat outputs markdown files
OUTPUT_DIR = "./output_parsed_markdown"  # Alias for compatibility
STORAGE_DIR = "./storage"  # Where index and docstore are persisted
QDRANT_PATH = os.path.join(STORAGE_DIR, "qdrant_db")
DOCSTORE_PATH = os.path.join(STORAGE_DIR, "docstore.json")

# Model Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "models/gemini-2.5-flash")
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")

# Chunking Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# Retrieval Configuration
VECTOR_TOP_K = int(os.getenv("VECTOR_TOP_K", "10"))  # Number of results from vector search
BM25_TOP_K = int(os.getenv("BM25_TOP_K", "10"))    # Number of results from BM25 search
RERANKER_TOP_N = int(os.getenv("RERANKER_TOP_N", "5"))  # Final number of results after re-ranking
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "colbert-ir/colbertv2.0")

# Agent Configuration
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "10"))
VERBOSE = os.getenv("VERBOSE", "True").lower() == "true"

# Ensure directories exist
os.makedirs(PDF_DIRECTORY, exist_ok=True)
os.makedirs(MARKDOWN_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)