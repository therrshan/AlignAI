"""
Configuration settings for the AI Resume Feedback Tool
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RESUMES_DIR = DATA_DIR / "resumes"
PROJECTS_DIR = DATA_DIR / "projects"
TEMP_DIR = DATA_DIR / "temp"

# Create directories if they don't exist
for directory in [DATA_DIR, RESUMES_DIR, PROJECTS_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp-free")
RESUME_INDEX_NAME = "resume-analysis"
PROJECTS_INDEX_NAME = "projects-portfolio"

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3")

# Embedding Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Document Processing Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_FILE_SIZE_MB = 10

# Analysis Configuration
SIMILARITY_THRESHOLD = 0.75
TOP_K_PROJECTS = 5
MAX_KEYWORDS = 15

# Streamlit Configuration
PAGE_TITLE = "AI Resume Feedback Tool"
PAGE_ICON = "📄"
LAYOUT = "wide"

# Evaluation Metrics Thresholds
HALLUCINATION_THRESHOLD = 0.05
CONSISTENCY_THRESHOLD = 0.90
COVERAGE_THRESHOLD = 0.95

# Supported file formats
SUPPORTED_RESUME_FORMATS = [".pdf", ".docx"]
SUPPORTED_PROJECT_FORMATS = [".pdf"]

# Resume Section Headers (for parsing)
RESUME_SECTIONS = {
    "experience": ["experience", "work experience", "professional experience", "employment", "work history"],
    "education": ["education", "academic background", "qualifications"],
    "skills": ["skills", "technical skills", "core competencies", "expertise"],
    "projects": ["projects", "key projects", "notable projects", "project experience"],
    "certifications": ["certifications", "certificates", "licenses"],
    "summary": ["summary", "profile", "objective", "about"]
}

# Industry Keywords (expandable)
TECH_KEYWORDS = [
    "python", "javascript", "react", "node.js", "aws", "docker", "kubernetes",
    "machine learning", "ai", "data science", "sql", "mongodb", "git", "agile",
    "microservices", "api", "cloud", "devops", "ci/cd", "tensorflow", "pytorch"
]

DATA_KEYWORDS = [
    "sql", "python", "r", "tableau", "power bi", "excel", "statistics",
    "machine learning", "data visualization", "etl", "big data", "hadoop",
    "spark", "pandas", "numpy", "scikit-learn", "data mining", "analytics"
]

# Prompt Templates Configuration
MAX_CONTEXT_LENGTH = 4000
TEMPERATURE = 0.3
MAX_TOKENS = 1000