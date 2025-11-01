import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional
import json
import hashlib

from app.models import AnalysisRequest, AnalysisResponse, Project
from app.services.pdf_parser import PDFParser
from app.services.analyzer import ResumeAnalyzer
from app.services.rag_service import RAGService

# Load environment variables
load_dotenv()

app = FastAPI(title="AlignAI API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
pdf_parser = PDFParser()
analyzer = ResumeAnalyzer()
rag_service = RAGService()


def hash_workspace_id(workspace_id: str) -> str:
    """Convert workspace password to valid Pinecone namespace."""
    # Hash to ensure valid namespace format
    return "ws-" + hashlib.sha256(workspace_id.encode()).hexdigest()[:40]


@app.get("/")
async def root():
    return {"message": "AlignAI API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/llm-provider")
async def get_llm_provider():
    """Get current LLM provider."""
    return {
        "provider": os.getenv("LLM_PROVIDER", "groq")
    }


@app.post("/api/llm-provider")
async def set_llm_provider(provider: str = Form(...)):
    """Set LLM provider (groq or ollama)."""
    if provider not in ["groq", "ollama"]:
        raise HTTPException(status_code=400, detail="Provider must be 'groq' or 'ollama'")
    
    # Update environment variable
    os.environ["LLM_PROVIDER"] = provider
    
    # Reinitialize the analyzer with new provider
    global analyzer
    analyzer = ResumeAnalyzer()
    
    return {
        "success": True,
        "provider": provider
    }


@app.post("/api/upload-projects")
async def upload_projects(
    file: UploadFile = File(...),
    workspace_id: str = Header(None, alias="X-Workspace-ID")
):
    """Upload projects PDF and store in Pinecone with workspace isolation."""
    try:
        if not workspace_id:
            raise HTTPException(status_code=400, detail="Workspace ID required")
        
        # Hash workspace password to valid namespace
        namespace = hash_workspace_id(workspace_id)
        
        # Read PDF
        content = await file.read()
        
        # Parse projects
        projects = pdf_parser.parse_projects(content)
        
        if not projects:
            raise HTTPException(status_code=400, detail="No projects found in PDF")
        
        # Store in Pinecone with namespace
        user_id = "default_user"
        projects_text = "\n\n".join([
            f"Project: {p['title']}\nTechnologies: {', '.join(p['technologies'])}\nDescription: {p['description']}"
            for p in projects
        ])
        
        rag_service.store_resume(user_id, projects_text, projects, namespace=namespace)
        
        return {
            "success": True,
            "message": f"Stored {len(projects)} projects successfully",
            "projects": projects
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error uploading projects: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error uploading projects: {str(e)}")


@app.get("/api/projects")
async def get_projects(
    workspace_id: str = Header(None, alias="X-Workspace-ID")
):
    """Get all stored projects for this workspace."""
    try:
        if not workspace_id:
            raise HTTPException(status_code=400, detail="Workspace ID required")
        
        # Hash workspace password to valid namespace
        namespace = hash_workspace_id(workspace_id)
        
        user_id = "default_user"
        # Use semantic search with empty query to get all projects from this namespace
        results = rag_service.semantic_search("", user_id, top_k=50, namespace=namespace)
        
        # Filter for project chunks only
        projects = [r for r in results if r["chunk_type"] == "project"]
        
        return {
            "success": True,
            "projects": projects
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {str(e)}")


@app.delete("/api/projects/{project_title}")
async def delete_project(
    project_title: str,
    workspace_id: str = Header(None, alias="X-Workspace-ID")
):
    """Delete a specific project from Pinecone in this workspace."""
    try:
        if not workspace_id:
            raise HTTPException(status_code=400, detail="Workspace ID required")
        
        # Hash workspace password to valid namespace
        namespace = hash_workspace_id(workspace_id)
        
        user_id = "default_user"
        
        # Get all project chunks from this namespace
        results = rag_service.semantic_search("", user_id, top_k=100, namespace=namespace)
        
        # Find and delete chunks matching the project title
        deleted_count = 0
        for result in results:
            if result.get("project_title") == project_title:
                # Delete this chunk from Pinecone
                chunk_id = f"{user_id}_chunk_{results.index(result)}"
                try:
                    rag_service.index.delete(ids=[chunk_id], namespace=namespace)
                    deleted_count += 1
                except:
                    pass
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} chunks for project '{project_title}'"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...),
    workspace_id: str = Header(None, alias="X-Workspace-ID")
):
    """Analyze resume against job description using workspace projects."""
    try:
        if not workspace_id:
            raise HTTPException(status_code=400, detail="Workspace ID required")
        
        # Hash workspace password to valid namespace
        namespace = hash_workspace_id(workspace_id)
        
        # Parse resume PDF
        content = await resume_file.read()
        resume_text = pdf_parser.parse_resume(content)
        
        # Get relevant projects from Pinecone based on job description (from this workspace)
        user_id = "default_user"
        relevant_project_titles = rag_service.find_relevant_projects(
            job_description,
            user_id,
            top_k=10,
            namespace=namespace
        )
        
        # Get full project details from this workspace
        all_results = rag_service.semantic_search("", user_id, top_k=50, namespace=namespace)
        project_results = [r for r in all_results if r["chunk_type"] == "project"]
        
        # Build project objects
        projects = []
        for result in project_results:
            # Parse the stored project text
            text = result["text"]
            title = result.get("project_title", "Unknown Project")
            
            # Extract description and technologies from text
            parts = text.split("\n")
            description = ""
            technologies = []
            
            for part in parts:
                if part.startswith("Description:"):
                    description = part.replace("Description:", "").strip()
                elif part.startswith("Technologies:"):
                    tech_str = part.replace("Technologies:", "").strip()
                    technologies = [t.strip() for t in tech_str.split(",")]
            
            projects.append(Project(
                title=title,
                description=description,
                technologies=technologies
            ))
        
        # Perform analysis
        result = await analyzer.analyze(
            resume_text=resume_text,
            job_description=job_description,
            projects=projects,
            selected_projects=None
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", 8000))
    )