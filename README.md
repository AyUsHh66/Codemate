Deep Researcher Agent
A project for the #SRMHacksWithCodemate Challenge

This project is a sophisticated, offline-first AI agent designed to perform deep, multi-step reasoning on a local collection of academic documents. It leverages a powerful Retrieval-Augmented Generation (RAG) pipeline to answer complex questions by synthesizing information exclusively from the provided texts, without relying on any external web APIs.
Live Demonstration

(Optional but highly recommended: You can embed your project video or a GIF of it working here)
A short video demonstrating the agent answering simple and complex queries.
核心功能

    High-Fidelity Document Parsing: Utilizes the Nougat vision-based model to accurately parse complex, multi-column academic PDF layouts into clean markdown, preserving the document's structure and content.

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

