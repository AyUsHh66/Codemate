# /deep-researcher-agent/enhanced_features.py
import os
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

# LlamaIndex Imports
from llama_index.core.tools import QueryEngineTool, FunctionTool
from llama_index.core.agent import ReActAgent
from llama_index.core import Settings

# Local Imports
from retrieval import setup_query_engine
import config

log = logging.getLogger()

class ResearchSession:
    """Manages a research session with conversation history and export capabilities."""
    
    def __init__(self):
        self.conversation_history = []
        self.research_notes = []
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def add_interaction(self, question: str, answer: str, sources: List[str] = None):
        """Add a Q&A interaction to the session history."""
        interaction = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "sources": sources or []
        }
        self.conversation_history.append(interaction)
        
    def add_research_note(self, note: str, category: str = "general"):
        """Add a research note with categorization."""
        research_note = {
            "timestamp": datetime.datetime.now().isoformat(),
            "category": category,
            "note": note
        }
        self.research_notes.append(research_note)
        
    def export_to_markdown(self, filename: str = None) -> str:
        """Export the research session to a markdown file."""
        if not filename:
            filename = f"research_session_{self.session_id}.md"
            
        output_dir = Path("./exports")
        output_dir.mkdir(exist_ok=True)
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Research Session Report\n\n")
            f.write(f"**Session ID:** {self.session_id}\n")
            f.write(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if self.research_notes:
                f.write("## Research Notes\n\n")
                for note in self.research_notes:
                    f.write(f"### {note['category'].title()}\n")
                    f.write(f"*{note['timestamp']}*\n\n")
                    f.write(f"{note['note']}\n\n")
            
            if self.conversation_history:
                f.write("## Q&A History\n\n")
                for i, interaction in enumerate(self.conversation_history, 1):
                    f.write(f"### Question {i}\n")
                    f.write(f"**Q:** {interaction['question']}\n\n")
                    f.write(f"**A:** {interaction['answer']}\n\n")
                    if interaction['sources']:
                        f.write("**Sources:**\n")
                        for source in interaction['sources']:
                            f.write(f"- {source}\n")
                        f.write("\n")
                    f.write(f"*Asked at: {interaction['timestamp']}*\n\n")
                    f.write("---\n\n")
        
        return str(filepath)

def create_summarization_tool(query_engine):
    """Create a tool for generating comprehensive summaries."""
    
    def generate_summary(topic: str, focus_areas: str = "") -> str:
        """
        Generate a comprehensive summary on a specific topic.
        
        Args:
            topic: The main topic to summarize
            focus_areas: Specific areas to focus on (comma-separated)
        """
        try:
            # Base query for comprehensive information
            base_query = f"Provide a comprehensive overview of {topic}"
            
            if focus_areas:
                focus_list = [area.strip() for area in focus_areas.split(",")]
                base_query += f", specifically focusing on: {', '.join(focus_list)}"
            
            response = query_engine.query(base_query)
            
            # Follow up with specific aspects
            summary_parts = [f"## Overview of {topic}\n{response}"]
            
            if focus_areas:
                for focus in focus_list:
                    focus_query = f"What are the key points about {focus} in relation to {topic}?"
                    focus_response = query_engine.query(focus_query)
                    summary_parts.append(f"## {focus.title()}\n{focus_response}")
            
            return "\n\n".join(summary_parts)
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    return FunctionTool.from_defaults(
        fn=generate_summary,
        name="generate_summary",
        description="Generate comprehensive summaries on specific topics with optional focus areas"
    )

def create_research_note_tool(session: ResearchSession):
    """Create a tool for adding research notes."""
    
    def add_research_note(note: str, category: str = "general") -> str:
        """
        Add a research note to the current session.
        
        Args:
            note: The research note content
            category: Category for the note (e.g., 'findings', 'questions', 'methodology')
        """
        session.add_research_note(note, category)
        return f"Research note added to category '{category}'"
    
    return FunctionTool.from_defaults(
        fn=add_research_note,
        name="add_research_note",
        description="Add research notes with categorization for later export"
    )

def setup_enhanced_agent():
    """
    Sets up an enhanced ReAct Agent with additional research capabilities.
    """
    # Verify API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    log.info("Setting up enhanced query engine...")
    query_engine = setup_query_engine()
    
    # Create research session
    session = ResearchSession()
    
    # Create tools
    query_engine_tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="local_document_retriever",
        description=(
            "Useful for answering complex questions about the documents you have been provided. "
            "This tool performs retrieval-augmented generation (RAG) on a local knowledge base."
        )
    )
    
    summarization_tool = create_summarization_tool(query_engine)
    research_note_tool = create_research_note_tool(session)
    
    # The enhanced agent with additional capabilities
    agent = ReActAgent.from_tools(
        tools=[query_engine_tool, summarization_tool, research_note_tool],
        llm=Settings.llm,
        verbose=True
    )
    
    log.info("✅ Enhanced ReAct agent with research capabilities is ready.")
    return agent, session

def interactive_research_session():
    """Run an interactive research session with enhanced features."""
    try:
        agent, session = setup_enhanced_agent()
        
        print("\n" + "="*60) 
        print("🔬 Enhanced Deep Researcher Agent")
        print("New features:")
        print("• Type 'summarize [topic]' for comprehensive summaries")
        print("• Type 'note [category]: [content]' to add research notes")
        print("• Type 'export' to save your research session")
        print("• Type 'help' for all commands")
        print("• Type 'quit' to exit")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("Research query: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    # Auto-export on exit
                    if session.conversation_history or session.research_notes:
                        filepath = session.export_to_markdown()
                        print(f"Session exported to: {filepath}")
                    print("Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower().startswith('summarize '):
                    topic = user_input[10:].strip()
                    print(f"\nGenerating summary for: {topic}")
                    response = agent.chat(f"generate_summary('{topic}')")
                    session.add_interaction(f"Summarize: {topic}", str(response))
                    
                elif user_input.lower().startswith('note '):
                    note_content = user_input[5:].strip()
                    if ':' in note_content:
                        category, content = note_content.split(':', 1)
                        category = category.strip()
                        content = content.strip()
                    else:
                        category = "general"
                        content = note_content
                    
                    response = agent.chat(f"add_research_note('{content}', '{category}')")
                    print(f"✓ {response}")
                    continue
                    
                elif user_input.lower() == 'export':
                    filepath = session.export_to_markdown()
                    print(f"✓ Research session exported to: {filepath}")
                    continue
                    
                elif user_input.lower() == 'help':
                    print("\nAvailable commands:")
                    print("• [question] - Ask any research question")
                    print("• summarize [topic] - Generate comprehensive summary")
                    print("• note [category]: [content] - Add research note")
                    print("• export - Export session to markdown")
                    print("• quit - Exit and auto-export\n")
                    continue
                
                # Regular research query
                print("\nThinking...")
                response = agent.chat(user_input)
                session.add_interaction(user_input, str(response))
                print(f"\nAnswer: {response}")
                print("\n" + "-"*50 + "\n")
                
            except KeyboardInterrupt:
                if session.conversation_history or session.research_notes:
                    filepath = session.export_to_markdown()
                    print(f"\nSession exported to: {filepath}")
                print("\nGoodbye!")
                break
            except Exception as e:
                if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                    log.warning("Rate limit reached. Please wait a moment before trying again.")
                else:
                    log.error(f"An error occurred: {e}")
                continue
                
    except Exception as e:
        log.error(f"Failed to set up the enhanced agent: {e}")

def export_conversation_history(session):
    """Export conversation history to markdown."""
    return session.export_to_markdown()

def generate_research_summary(agent, topic="all research findings"):
    """Generate a research summary using the agent."""
    summary_query = f"Provide a comprehensive research summary of {topic}, including key methodologies, findings, and implications"
    return agent.chat(summary_query)

if __name__ == "__main__":
    interactive_research_session()