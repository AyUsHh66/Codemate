# /deep-researcher-agent/main.py
import os
from dotenv import load_dotenv
import logging
import sys

# LlamaIndex Imports (only what's needed for settings)
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import config

# Try to import enhanced features
try:
    from Enhanced_features import ResearchSession, export_conversation_history, generate_research_summary
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

# Setup logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger()

# Load environment variables from .env file
load_dotenv()

def initialize_settings():
    """Initializes global LlamaIndex settings with Gemini and local embeddings."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please create a .env file.")
    
    log.info("Initializing models...")
    Settings.llm = Gemini(model=config.LLM_MODEL, api_key=api_key)
    Settings.embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL)
    log.info("✅ Settings initialized.")

def show_menu():
    """Display the options menu."""
    print("\n" + "="*60)
    print("📋 Research Tools:")
    print("1. Export conversation history (Markdown/PDF)")
    print("2. Generate research summary report")
    print("3. Add research note")
    print("4. Continue asking questions")
    print("="*60)

def main():
    """Main function to run the deep researcher agent."""
    
    try:
        initialize_settings()
    except Exception as e:
        log.error(f"Failed to initialize settings: {e}")
        return
    
    # Check if the knowledge base has been created by the ingestion script
    if not os.path.exists(config.QDRANT_PATH):
        log.error(f"Error: The Qdrant storage path '{config.QDRANT_PATH}' was not found.")
        log.error("Please run the data ingestion process first by executing: python ingestion.py")
        return
    
    # Import agent AFTER settings are initialized to ensure correct model loading
    from agent import setup_agent
    
    try:
        log.info("Setting up the Deep Researcher Agent...")
        agent = setup_agent()
        
        # Initialize research session for tracking
        session = ResearchSession() if ENHANCED_AVAILABLE else None
        
        print("\n" + "="*50) 
        print("🛡️ Deep Researcher Agent is ready!")
        print("You can now ask complex questions about your documents.")
        print("The agent will perform multi-step reasoning to find answers.")
        if ENHANCED_AVAILABLE:
            print("\n💡 Tip: Press Enter without typing to see research tools menu")
        print("Type 'quit' or 'exit' to stop.")
        print("="*50 + "\n")
        
        while True:
            try:
                user_input = input("Ask a question: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    # Auto-export on exit if session has content
                    if ENHANCED_AVAILABLE and session and (session.conversation_history or session.research_notes):
                        try:
                            filepath = session.export_to_markdown()
                            print(f"📁 Session auto-exported to: {filepath}")
                        except:
                            pass
                    print("Goodbye!")
                    break
                
                # Show menu if user presses enter without typing
                if not user_input and ENHANCED_AVAILABLE:
                    show_menu()
                    choice = input("Select option (1-4): ").strip()
                    
                    if choice == "1":
                        # Export conversation history
                        if session and session.conversation_history:
                            try:
                                filepath = session.export_to_markdown()
                                print(f"✅ Conversation exported to: {filepath}")
                            except Exception as e:
                                print(f"❌ Export failed: {e}")
                        else:
                            print("📭 No conversation history to export yet.")
                        continue
                    
                    elif choice == "2":
                        # Generate research summary
                        topic = input("Enter topic to summarize (or press Enter for general summary): ").strip()
                        if not topic:
                            topic = "all research findings and key concepts from the documents"
                        
                        print(f"\n🔍 Generating research summary for: {topic}")
                        print("This may take a moment...\n")
                        
                        try:
                            summary_query = f"Provide a comprehensive research summary of {topic}, including key methodologies, findings, and implications"
                            response = agent.chat(summary_query)
                            print(f"📊 Research Summary:\n{response}")
                            
                            if session:
                                session.add_interaction(f"Research Summary: {topic}", str(response))
                                
                        except Exception as e:
                            if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                                print("⚠️ Rate limit reached. Please wait a moment before trying again.")
                            else:
                                print(f"❌ Error generating summary: {e}")
                        continue
                    
                    elif choice == "3":
                        # Add research note
                        note = input("Enter your research note: ").strip()
                        if note:
                            category = input("Enter category (or press Enter for 'general'): ").strip() or "general"
                            if session:
                                session.add_research_note(note, category)
                                print(f"✅ Note added to category '{category}'")
                            else:
                                print("✅ Note recorded (enhanced features not available)")
                        continue
                    
                    elif choice == "4":
                        # Continue asking questions
                        print("💬 Continue with your research questions...\n")
                        continue
                    else:
                        print("❌ Invalid option. Please select 1-4.")
                        continue
                
                elif not user_input:
                    # If enhanced features not available, just continue
                    continue
                
                # Regular research query
                print("\nThinking...")
                response = agent.chat(user_input)
                print(f"\nAnswer: {response}")
                
                # Track conversation if enhanced features available
                if ENHANCED_AVAILABLE and session:
                    session.add_interaction(user_input, str(response))
                
                print("\n" + "-"*50 + "\n")
                
            except KeyboardInterrupt:
                # Auto-export on keyboard interrupt
                if ENHANCED_AVAILABLE and session and (session.conversation_history or session.research_notes):
                    try:
                        filepath = session.export_to_markdown()
                        print(f"\n📁 Session auto-exported to: {filepath}")
                    except:
                        pass
                print("\nGoodbye!")
                break
            except Exception as e:
                if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    log.warning("Rate limit reached. Please wait a moment before trying again.")
                else:
                    log.error(f"An error occurred: {e}")
                continue
                
    except Exception as e:
        log.error(f"Failed to set up the agent: {e}")

if __name__ == "__main__":
    main()