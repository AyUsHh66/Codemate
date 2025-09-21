# Codemate Deployment Guide

## Quick Deployment on Render

### Prerequisites
- GitHub account
- Render account (free at render.com)
- Google API key for Gemini
- LlamaCloud API key

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### Step 2: Create Render Service
1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect your GitHub repository: `AyUsHh66/Codemate`
4. Render will auto-detect the configuration from `render.yaml`

### Step 3: Configure Environment Variables
In your Render service dashboard, add these environment variables:

**Required:**
- `GOOGLE_API_KEY`: Your Google Gemini API key
- `LLAMA_CLOUD_API_KEY`: Your LlamaCloud API key

**Auto-configured:**
- `PORT`: 8080 (already set)
- `PYTHONPATH`: /app (already set)
- `FLASK_ENV`: production (already set)

### Step 4: Deploy
1. Click "Create Web Service"
2. Render will:
   - Build your Docker container
   - Install dependencies
   - Start the Flask app with Gunicorn
   - Provide a public URL

### Step 5: Set Up Your Knowledge Base
After deployment, you need to upload documents and run ingestion:

**Option A: Via Git (Recommended)**
1. Add your PDF files to the `data/` directory
2. Commit and push:
   ```bash
   git add data/*.pdf
   git commit -m "Add research documents"
   git push origin main
   ```
3. Render will auto-redeploy

**Option B: Via API**
1. Upload PDFs to your deployed service's `data/` directory
2. Trigger ingestion by sending a POST request to `/ingest`

### Step 6: Test Your Deployment
```bash
# Health check
curl https://your-app-name.onrender.com/

# Chat with your agent
curl -X POST https://your-app-name.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main topics in the documents?"}'
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `POST /chat` - Send queries to the research agent
- `POST /ingest` - Process documents and build knowledge base

## Troubleshooting

**Build fails:**
- Check that all requirements are in `requirements.txt`
- Verify environment variables are set correctly

**Agent not initialized:**
- Run the `/ingest` endpoint first
- Check that PDF files are in the `data/` directory

**Rate limiting:**
- Gemini API has rate limits
- Consider upgrading your Google AI API quota

**Memory issues:**
- Use Render's higher-tier plans for larger document sets
- Optimize chunk sizes in `config.py`

## Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.template .env
# Edit .env with your API keys

# Run ingestion
python ingestion.py

# Start server
python server.py
```

## Configuration Options
Edit these environment variables in Render dashboard:

- `CHUNK_SIZE`: Document chunk size (default: 512)
- `VECTOR_TOP_K`: Vector search results (default: 10)
- `MAX_ITERATIONS`: Agent max iterations (default: 10)
- `LLM_MODEL`: Gemini model to use (default: models/gemini-2.5-flash)

## Support
- Check Render logs for deployment issues
- Monitor `/health` endpoint for runtime status
- Review application logs in Render dashboard