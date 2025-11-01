import os
import hashlib
from typing import List, Dict, Optional
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer


class RAGService:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "alignai-resumes")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self._init_index()
        self.index = self.pc.Index(self.index_name)
    
    def _init_index(self):
        """Initialize Pinecone index if it doesn't exist."""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # all-MiniLM-L6-v2 dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
                )
            )
    
    def store_resume(self, user_id: str, resume_text: str, projects: List[Dict], namespace: Optional[str] = None):
        """Store resume chunks in vector database with namespace isolation."""
        chunks = self._chunk_resume(resume_text, projects)
        vectors = []
        
        for i, chunk in enumerate(chunks):
            embedding = self.embedding_model.encode(chunk["text"]).tolist()
            
            vectors.append({
                "id": f"{user_id}_chunk_{i}",
                "values": embedding,
                "metadata": {
                    "resume_id": user_id,
                    "chunk_type": chunk["type"],
                    "text": chunk["text"],
                    "project_title": chunk.get("project_title", "")
                }
            })
        
        # Upsert in batches with namespace
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            # Use namespace for isolation
            self.index.upsert(vectors=batch, namespace=namespace or "default")
    
    def _chunk_resume(self, resume_text: str, projects: List[Dict]) -> List[Dict]:
        """Chunk resume into meaningful segments."""
        chunks = []
        
        # Full resume chunk
        chunks.append({
            "type": "full_resume",
            "text": resume_text
        })
        
        # Individual project chunks
        for project in projects:
            project_text = f"{project['title']}\n{project['description']}\nTechnologies: {', '.join(project['technologies'])}"
            chunks.append({
                "type": "project",
                "text": project_text,
                "project_title": project['title']
            })
        
        return chunks
    
    def semantic_search(self, query: str, user_id: str = None, top_k: int = 5, namespace: Optional[str] = None) -> List[Dict]:
        """Perform semantic search on resume chunks with namespace isolation."""
        query_embedding = self.embedding_model.encode(query).tolist()
        
        filter_dict = {"resume_id": user_id} if user_id else {}
        
        # Query with namespace for isolation
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None,
            namespace=namespace or "default"
        )
        
        return [
            {
                "text": match.metadata["text"],
                "score": match.score,
                "chunk_type": match.metadata["chunk_type"],
                "project_title": match.metadata.get("project_title", "")
            }
            for match in results.matches
        ]
    
    def find_relevant_projects(self, job_description: str, user_id: str, top_k: int = 3, namespace: Optional[str] = None) -> List[str]:
        """Find most relevant projects for a job description with namespace isolation."""
        results = self.semantic_search(job_description, user_id, top_k * 2, namespace=namespace)
        
        # Filter for project chunks only
        project_results = [r for r in results if r["chunk_type"] == "project"]
        
        # Return unique project titles
        seen = set()
        projects = []
        for r in project_results:
            if r["project_title"] not in seen:
                seen.add(r["project_title"])
                projects.append(r["project_title"])
        
        return projects[:top_k]
    
    def get_resume_id(self, resume_text: str) -> str:
        """Generate unique resume ID from content."""
        return hashlib.md5(resume_text.encode()).hexdigest()[:16]
    
    def delete_resume(self, user_id: str, namespace: Optional[str] = None):
        """Delete all chunks for a resume with namespace isolation."""
        self.index.delete(filter={"resume_id": user_id}, namespace=namespace or "default")
    
    def delete_namespace(self, namespace: str):
        """Delete entire namespace (all user data)."""
        self.index.delete(delete_all=True, namespace=namespace)