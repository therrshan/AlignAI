# 🤖 AI Resume Feedback Tool

An intelligent resume optimization system that uses AI to analyze your resume against job descriptions and provides actionable feedback for improving your application success rate.

## ✨ Features

### 🎯 **Smart Resume Analysis**
- **Overall scoring** with detailed breakdowns (Clarity, Role Alignment, Tone)
- **ATS optimization** suggestions for better keyword matching
- **Professional feedback** on resume structure and content

### 🏗️ **LaTeX Project Portfolio Integration**
- **Structured project parsing** from LaTeX resume formats
- **Intelligent project ranking** based on job relevance
- **Technology stack analysis** with automatic keyword extraction

### 🔍 **Job Matching Intelligence**
- **Semantic analysis** using RAG (Retrieval Augmented Generation)
- **Missing keyword identification** with priority ranking
- **Project recommendation** system for optimal resume customization

### ✨ **Content Optimization**
- **Enhanced project descriptions** with improved phrasing
- **Action verb suggestions** for stronger impact
- **Quantifiable metrics** recommendations

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │───▶│  LangChain      │───▶│   Pinecone      │
│                 │    │  Pipeline       │    │   Vector DB     │
│ - Resume Select │    │                 │    │                 │
│ - Project Select│    │ - LaTeX Parser  │    │ - Resume Chunks │
│ - Job Input     │    │ - LLaMA 3 LLM   │    │ - Embeddings    │
│ - Results UI    │    │ - RAG System    │    │ - Semantic Search│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 💼 Usage Workflow

### 1. **Add Your Data**
```bash
# Add resume PDFs
cp your_resume.pdf data/resumes/

# Add individual project LaTeX files
cp ai_project.tex data/projects/
cp web_app.tex data/projects/
```

### 2. **Launch Dashboard**
```bash
streamlit run app_improved.py
```

### 3. **Use the Interface**
1. **Select Resume** - Choose from your uploaded PDFs
2. **Select Projects** - Multi-select relevant projects from your portfolio
3. **Paste Job Description** - Enter the target job posting
4. **Analyze** - Get comprehensive feedback and recommendations

### 4. **Review Results**
- 📊 **Visual scores** with gauge charts
- 🏆 **Project rankings** by relevance to the job
- 🔍 **Missing keywords** to add
- ✨ **Improved project descriptions** with enhanced phrasing

## 🎯 LaTeX Project Format

Your project files should follow this structure:

```latex
\resumeProjectHeading
  {\textbf{AI Resume Feedback Tool} $|$ \emph{Python, LangChain, Ollama, Pinecone, Streamlit, \href{https://github.com/username/repo}{\underline{Link}}}}{Jul 2025 -- Present}
  \resumeItemListStart
    \resumeItem{Built a modular LLM pipeline leveraging LangChain and LLaMA 3 to analyze resumes across clarity, role alignment, and tone dimensions using structured prompt chaining.}
    \resumeItem{Implemented a retrieval-augmented generation (RAG) system using Pinecone to enable semantic matching between resume content and job descriptions.}
    \resumeItem{Engineered task-specialized prompt templates and few-shot exemplars for section-wise evaluation with dynamic role conditioning.}
  \resumeItemListEnd
```

## 🔧 Configuration

### Key Settings (config/settings.py)
- **Vector dimensions**: 384 (sentence-transformers)
- **Similarity threshold**: 0.75 for relevance matching
- **Chunk settings**: 1000 chars with 200 overlap
- **Model settings**: LLaMA 3 via Ollama

### Customizable Components
- **Prompt templates** in `config/prompts.py`
- **Technical keywords** in `src/utils.py`
- **Scoring thresholds** in `config/settings.py`



## 🎯 Example Analysis Output

```
📊 Overall Score: 87/100

🏆 Project Rankings:
1. 🟢 AI Resume Feedback Tool (94%) - Excellent match for ML Engineering role
2. 🟡 E-commerce Platform (73%) - Good full-stack demonstration  
3. 🔴 Data Analysis Tool (45%) - Less relevant for this position

🔍 Missing Keywords:
High Priority: Docker, Kubernetes, MLOps
Medium Priority: FastAPI, PostgreSQL, Redis

✨ Improved Descriptions:
"Built a scalable ML pipeline orchestrator using Python and PyTorch"
→ "Engineered a production-grade ML pipeline orchestrator leveraging Python, PyTorch, and Docker containers, achieving 99.9% uptime and processing 10K+ daily inference requests"
```

Ready to optimize your resume with AI? 🚀