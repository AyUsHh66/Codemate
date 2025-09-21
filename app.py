import gradio as gr
import os
from dotenv import load_dotenv
import logging
import sys

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger()

# Global agent variable
agent = None

def initialize_agent():
    """Initialize the research agent"""
    global agent
    if agent is not None:
        return "Agent already initialized"
    
    try:
        from llama_index.core import Settings
        from llama_index.llms.gemini import Gemini
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        import config
        from agent import setup_agent
        
        # Initialize settings
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "❌ GOOGLE_API_KEY not found. Please set it in the Space settings."
        
        Settings.llm = Gemini(model=config.LLM_MODEL, api_key=api_key)
        Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)
        
        # Setup agent
        agent = setup_agent()
        return "✅ Agent initialized successfully!"
        
    except Exception as e:
        return f"❌ Error initializing agent: {str(e)}"

def chat_with_agent(message, history):
    """Chat interface for Gradio"""
    global agent
    
    if agent is None:
        return "⚠️ Agent not initialized. Please click 'Initialize Agent' first."
    
    if not message.strip():
        return "Please enter a question."
    
    try:
        response = agent.chat(message)
        return str(response)
    except Exception as e:
        return f"❌ Error: {str(e)}"

def get_agent_status():
    """Get current agent status"""
    global agent
    if agent is None:
        return "❌ Agent not initialized"
    else:
        return "✅ Agent ready"

# Create Gradio interface
with gr.Blocks(title="Codemate Research Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🛡️ Codemate Research Agent
    
    An intelligent research assistant that can analyze documents and answer complex questions.
    
    **Instructions:**
    1. First click "Initialize Agent" (this may take a few minutes)
    2. Once initialized, ask your research questions
    3. The agent will analyze your documents and provide detailed answers
    """)
    
    with gr.Row():
        status_display = gr.Textbox(label="Agent Status", value="❌ Agent not initialized", interactive=False)
        init_btn = gr.Button("Initialize Agent", variant="primary")
    
    # Chat interface
    chatbot = gr.Chatbot(label="Research Chat", height=400)
    msg = gr.Textbox(label="Ask a question", placeholder="What are the main findings in the research documents?")
    
    with gr.Row():
        submit_btn = gr.Button("Send", variant="primary")
        clear_btn = gr.Button("Clear Chat")
    
    # Event handlers
    init_btn.click(
        fn=initialize_agent,
        outputs=status_display
    )
    
    submit_btn.click(
        fn=chat_with_agent,
        inputs=[msg, chatbot],
        outputs=chatbot
    ).then(
        lambda: "",
        outputs=msg
    )
    
    msg.submit(
        fn=chat_with_agent,
        inputs=[msg, chatbot], 
        outputs=chatbot
    ).then(
        lambda: "",
        outputs=msg
    )
    
    clear_btn.click(lambda: [], outputs=chatbot)
    
    # Periodic status update
    demo.load(get_agent_status, outputs=status_display, every=5)

if __name__ == "__main__":
    demo.launch()