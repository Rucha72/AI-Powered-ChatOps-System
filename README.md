# 🤖 AI-Powered ChatOps System for DevOps Automation

**Dissertation Project | BITS Pilani | MTech Software Engineering**
Student:** Vaidya Rucha Sandeep

---

## Project Overview

An AI-enhanced ChatOps system that enables DevOps teams to manage operations through
natural language conversation. Built with GPT-4o, FastAPI, ChromaDB, and Streamlit.

## Features

- 🔍 **Service Health Monitoring** — Query real-time service status via chat
- 📋 **Incident Summarization** — AI-generated summaries of incident logs
- 🧠 **Root Cause Analysis** — Intelligent RCA from log data
- ⚡ **DevOps Action Simulation** — Restart, scale, rollback via chat
- 📚 **Knowledge Base** — Semantic search over past incidents (ChromaDB + embeddings)
- 💬 **Conversational Interface** — Streamlit chat UI with conversation history

---

## Setup Instructions

### 1. Clone / navigate to project directory
```bash
cd chatops
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 5. Start the FastAPI backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 6. Start the Streamlit frontend (new terminal)
```bash
streamlit run frontend/app.py
```

### 7. Open browser
Navigate to `http://localhost:8501`

---

## Project Structure

```
chatops/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── data/
│   │   ├── incidents.json         # Simulated incident data
│   │   └── services.json          # Simulated service catalog
│   └── services/
│       ├── chat_engine.py         # Intent detection + LLM response
│       ├── incident_analyzer.py   # Log summarization & RCA
│       ├── devops_actions.py      # Simulated DevOps operations
│       └── knowledge_base.py      # ChromaDB vector store
├── frontend/
│   └── app.py                     # Streamlit chat UI
├── tests/                         # Test files (to be added)
├── requirements.txt
└── .env.example
```

---

## Sample Queries to Try

| Query | What it does |
|-------|-------------|
| "Show all service statuses" | Lists all services with health info |
| "What's the status of order-service?" | Detailed status for a specific service |
| "Summarize incident INC-001" | AI summary + RCA of an incident |
| "Find incidents similar to Redis cache failure" | Semantic KB search |
| "Restart payment-service" | Simulates a service restart |
| "Scale order-service to 4 replicas" | Simulates scaling |
| "Show all incidents for auth-service" | Lists incidents by service |

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| LLM | GPT-4o (OpenAI) |
| Backend API | FastAPI + Python |
| Frontend | Streamlit |
| Vector DB | ChromaDB |
| Embeddings | OpenAI text-embedding-3-small |
| Data | Simulated JSON (incidents, services) |
=======

