# /deep_researcher_submission/server.py
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import logging
import sys

# --- LlamaIndex and Project Imports ---
# It's important to initialize settings before importing the agent
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import config
from agent import setup_agent

# --- Basic Setup ---
load_dotenv()
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger()

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Global Agent Variable ---
# We initialize the agent once when the server starts.
agent = None

def initialize_agent():
    """
    A one-time function to initialize all settings and the agent itself.
    This is called when the Flask application starts.
    """
    global agent
    if agent is not None:
        log.info("Agent is already initialized.")
        return

    try:
        log.info("Starting agent initialization...")
        # 1. Initialize Settings
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")

        Settings.llm = Gemini(model=config.LLM_MODEL, api_key=api_key)
        Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)
        log.info("✅ Settings initialized.")

        # 2. Check for knowledge base
        if not os.path.exists(config.STORAGE_DIR):
            log.warning(f"Storage directory '{config.STORAGE_DIR}' not found. Creating it...")
            os.makedirs(config.STORAGE_DIR, exist_ok=True)
            
        # Check if the knowledge base needs to be created
        if not os.path.exists(config.QDRANT_PATH):
            log.warning("No existing knowledge base found. The ingestion process may need to be run.")
            log.info("The application will start but may not have document data until ingestion is completed.")

        # 3. Setup Agent
        agent = setup_agent()
        log.info("✅ Agent initialization complete.")

    except Exception as e:
        log.error(f"FATAL: Failed to initialize agent: {e}", exc_info=True)
        # If initialization fails, the server can't work.
        # In a real production app, you might have more robust error handling here.
        raise

@app.route("/")
def health_check():
    """A simple endpoint to confirm the server is running."""
    return jsonify({
        "status": "healthy",
        "message": "Codemate Backend server is running",
        "agent_initialized": agent is not None
    })

@app.route("/health")
def health():
    """Health check endpoint for deployment monitoring."""
    if agent is None:
        return jsonify({"status": "unhealthy", "reason": "Agent not initialized"}), 503
    return jsonify({"status": "healthy"})

@app.route('/ingest', methods=['POST'])
def ingest_data():
    """
    Endpoint to trigger data ingestion.
    This can be used to set up the knowledge base after deployment.
    """
    try:
        # Import ingestion module
        import ingestion
        
        log.info("Starting data ingestion process...")
        # Run the ingestion process
        ingestion.main()
        log.info("Data ingestion completed successfully.")
        
        # Reinitialize agent if needed
        global agent
        if agent is None:
            agent = setup_agent()
            
        return jsonify({"message": "Data ingestion completed successfully"})
        
    except Exception as e:
        log.error(f"Error during data ingestion: {e}", exc_info=True)
        return jsonify({"error": f"Data ingestion failed: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    The main endpoint to interact with the agent.
    Accepts a JSON payload with a 'query' field.
    """
    if agent is None:
        return jsonify({"error": "Agent not initialized. The server may be starting up or encountered an error."}), 503

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    log.info(f"Received query: {query}")

    try:
        # Get the agent's response
        response = agent.chat(query)
        response_text = str(response)
        
        return jsonify({"response": response_text})

    except Exception as e:
        log.error(f"Error processing query: {e}", exc_info=True)
        return jsonify({"error": "An internal error occurred while processing your request."}), 500

if __name__ == '__main__':
    # This block is for local testing. Render will use gunicorn to run the app.
    initialize_agent()
    # Use a port that Render might assign, for consistency. Default to 8080 for local dev.
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
else:
    # This block runs when Gunicorn starts the server on Render
    initialize_agent()
