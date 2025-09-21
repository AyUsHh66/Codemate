---
title: Codemate Research Agent
emoji: 🛡️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.26.0
app_file: app.py
pinned: false
license: apache-2.0
---

# 🛡️ Codemate Research Agent

An intelligent research assistant powered by LlamaIndex and Gemini AI that can analyze documents and answer complex research questions.

## 🚀 Quick Start

### Environment Variables
**IMPORTANT**: Set these in your Space Settings → Variables:

- `GOOGLE_API_KEY`: Your Google Gemini API key
- `LLAMA_CLOUD_API_KEY`: Your LlamaCloud API key (optional)

### Usage
1. **Initialize**: Click "Initialize Agent" (takes 2-3 minutes)
2. **Ask Questions**: Type your research questions
3. **Get Insights**: Receive detailed answers

## 📋 Example Questions

- "What are the main findings in the research documents?"
- "Compare methodologies across studies"
- "Summarize key insights and implications"

## 🔧 Technical Details

- **LLM**: Google Gemini 2.5 Flash
- **Embeddings**: BAAI/bge-small-en-v1.5  
- **Vector Store**: Qdrant
- **Framework**: LlamaIndex

    Advanced RAG Pipeline: Implements a robust retrieval system for maximum accuracy:

        Hybrid Search: Combines semantic (vector) search with keyword-based (BM25) search to ensure both contextual relevance and keyword precision.

        ColBERT Re-ranker: Adds a final precision layer that re-ranks retrieved documents to ensure only the most relevant context is passed to the language model.

    Multi-Step Reasoning: Employs the ReAct (Reason and Act) agent framework, allowing the agent to break down complex user queries into a series of smaller, logical sub-questions, which it solves in sequence.

    Fully Local & Private: The entire knowledge base, including the vector store (Qdrant) and embeddings, is created and stored locally. No data ever leaves the user's machine.

Architecture Overview

    Ingestion: PDFs in the /data directory are processed by Nougat. The text is chunked using a sentence-window parser and converted into embeddings (bge-small-en-v1.5). These are stored in a local Qdrant vector database.

    Retrieval & Reasoning: When a user asks a question, the ReAct Agent formulates a plan. It uses its Hybrid Retriever to fetch candidate documents. These are then re-ranked by ColBERT.

    Synthesis: The final, highly-relevant context is passed to the Gemini LLM (gemini-1.5-flash-latest), which generates a grounded, accurate answer.

Setup and Usage

1. Clone the repository:

git clone <your-new-github-repo-url>
cd srm-codemate-researcher-agent

2. Create Environment and Install Dependencies:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

3. Set Up API Key:
Create a .env file in the root directory and add your Google Gemini API key:

GOOGLE_API_KEY="YOUR_API_KEY_HERE"

4. Add Documents:
Place the PDF files you want to query into the /data directory.

5. Run the Ingestion Pipeline:
This is a one-time process to build the local knowledge base.

python ingestion.py

6. Run the Agent:
Start the interactive chat interface.

python main.py

