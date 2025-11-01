# AlignAI Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- [Groq API key](https://console.groq.com/) (free)
- [Pinecone API key](https://www.pinecone.io/) (free tier)
- (Optional) [Ollama](https://ollama.ai/) for local LLM

---

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  
pip install -r requirements.txt
```

### 2. Configure Environment

```env
# LLM Configuration
LLM_PROVIDER=groq              # "groq" or "ollama"
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama3-70b-8192

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=alignai-resumes

# Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:5173
```

### 3. Run Backend

```bash
python -m app.main
```

Backend runs at `http://localhost:8000`

---

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment


```env
VITE_API_URL=http://localhost:8000
```

### 3. Run Frontend

```bash
npm run dev
```

Frontend runs at `http://localhost:5173`




## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload-projects` | Upload projects PDF |
| `GET` | `/api/projects` | List stored projects |
| `DELETE` | `/api/projects/{title}` | Delete project |
| `POST` | `/api/analyze` | Analyze resume |
| `GET/POST` | `/api/llm-provider` | Get/set LLM provider |

All endpoints require `X-Workspace-ID` header.

---

## Project Structure

```
alignai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # Data models
│   │   └── services/
│   │       ├── pdf_parser.py    # PDF parsing
│   │       ├── llm_service.py   # LLM integration
│   │       ├── rag_service.py   # Vector DB
│   │       └── analyzer.py      # Analysis logic
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── App.jsx
    │   └── main.jsx
    └── package.json
```