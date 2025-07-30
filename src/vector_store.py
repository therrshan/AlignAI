"""
Vector store operations using Pinecone for semantic search and storage
Handles embedding generation, storage, and retrieval for resumes and projects
"""

import logging
import time
from typing import List, Dict, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from config.settings import (
    PINECONE_API_KEY,
    RESUME_INDEX_NAME,
    PROJECTS_INDEX_NAME,
    EMBEDDING_MODEL,
    SIMILARITY_THRESHOLD,
    TOP_K_PROJECTS
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    """Manages vector embeddings and Pinecone operations"""
    
    def __init__(self):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Get index connections (without specifying namespace initially)
        self.resume_index = self.pc.Index(RESUME_INDEX_NAME)
        self.projects_index = self.pc.Index(PROJECTS_INDEX_NAME)
        
        logger.info("Vector store initialized successfully")
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def store_resume_chunks(self, resume_id: str, chunks: List[Dict], resume_metadata: Dict = None):
        """Store resume chunks in Pinecone"""
        try:
            # Extract text content for embedding
            texts = [chunk['content'] for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{resume_id}_chunk_{i}"
                
                # Combine chunk metadata with resume metadata
                metadata = {
                    **chunk['metadata'],
                    **(resume_metadata or {}),
                    'content': chunk['content'][:1000],  # Pinecone metadata limit
                    'resume_id': resume_id
                }
                
                vectors.append({
                    'id': vector_id,
                    'values': embedding.tolist(),
                    'metadata': metadata
                })
            
            # Upsert to Pinecone
            self.resume_index.upsert(vectors)
            logger.info(f"Stored {len(vectors)} resume chunks for {resume_id}")
            
        except Exception as e:
            logger.error(f"Error storing resume chunks: {e}")
            raise
    
    def store_project_chunks(self, project_chunks: List[Dict], projects_metadata: List[Dict] = None):
        """Store project chunks in Pinecone with better error handling"""
        try:
            # Extract text content for embedding
            texts = [chunk['content'] for chunk in project_chunks]
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(project_chunks, embeddings)):
                vector_id = f"project_{chunk['metadata']['project_index']}_chunk_{i}_{int(time.time())}"
                
                # Ensure metadata fits Pinecone limits
                metadata = {
                    **chunk['metadata'],
                    'content': chunk['content'][:1000],  # Pinecone metadata limit
                }
                
                # Remove any None values that might cause issues
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                vectors.append({
                    'id': vector_id,
                    'values': embedding.tolist(),
                    'metadata': metadata
                })
            
            # Upsert to Pinecone in smaller batches to avoid issues
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                try:
                    self.projects_index.upsert(vectors=batch)
                    logger.info(f"Stored batch {i//batch_size + 1}: {len(batch)} vectors")
                except Exception as batch_error:
                    logger.error(f"Error storing batch {i//batch_size + 1}: {batch_error}")
                    # Continue with next batch instead of failing completely
                    continue
            
            logger.info(f"Successfully stored {len(vectors)} project chunks")
            
        except Exception as e:
            logger.error(f"Error storing project chunks: {e}")
            # Don't raise the error, just log it so the application continues
            logger.info("Continuing without storing project vectors...")
            return
    
    def search_resume_content(self, query: str, resume_id: str = None, top_k: int = 5) -> List[Dict]:
        """Search resume content using semantic similarity"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Prepare filter
            filter_dict = {}
            if resume_id:
                filter_dict['resume_id'] = resume_id
            
            # Search in Pinecone
            search_results = self.resume_index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )
            
            # Process results
            results = []
            for match in search_results['matches']:
                if match['score'] >= SIMILARITY_THRESHOLD:
                    results.append({
                        'content': match['metadata'].get('content', ''),
                        'score': match['score'],
                        'metadata': match['metadata']
                    })
            
            logger.info(f"Found {len(results)} relevant resume chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error searching resume content: {e}")
            raise
    
    def search_project_alternatives(self, job_requirements: str, current_projects: List[str] = None) -> List[Dict]:
        """Find alternative projects that might be better matches for job requirements"""
        try:
            # Generate query embedding from job requirements
            query_embedding = self.generate_embeddings([job_requirements])[0]
            
            # Search in projects index
            search_results = self.projects_index.query(
                vector=query_embedding.tolist(),
                top_k=TOP_K_PROJECTS * 2,  # Get more results to filter
                include_metadata=True
            )
            
            # Process and rank results
            alternative_projects = []
            seen_projects = set(current_projects or [])
            
            for match in search_results['matches']:
                project_name = match['metadata'].get('project_name', '')
                
                # Skip if this project is already in the resume
                if project_name.lower() in [p.lower() for p in seen_projects]:
                    continue
                
                if match['score'] >= SIMILARITY_THRESHOLD:
                    alternative_projects.append({
                        'project_name': project_name,
                        'description': match['metadata'].get('content', ''),
                        'relevance_score': match['score'],
                        'project_index': match['metadata'].get('project_index'),
                        'metadata': match['metadata']
                    })
            
            # Remove duplicates and limit results
            unique_projects = {}
            for project in alternative_projects:
                project_key = project['project_name'].lower()
                if project_key not in unique_projects or project['relevance_score'] > unique_projects[project_key]['relevance_score']:
                    unique_projects[project_key] = project
            
            # Sort by relevance and return top results
            final_results = sorted(unique_projects.values(), key=lambda x: x['relevance_score'], reverse=True)[:TOP_K_PROJECTS]
            
            logger.info(f"Found {len(final_results)} alternative projects")
            return final_results
            
        except Exception as e:
            logger.error(f"Error searching project alternatives: {e}")
            raise
    
    def find_similar_sections(self, section_content: str, section_type: str, top_k: int = 3) -> List[Dict]:
        """Find similar sections across all resumes for benchmarking"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embeddings([section_content])[0]
            
            # Search with section type filter
            search_results = self.resume_index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True,
                filter={'document_type': 'resume'}
            )
            
            results = []
            for match in search_results['matches']:
                if match['score'] >= SIMILARITY_THRESHOLD:
                    results.append({
                        'content': match['metadata'].get('content', ''),
                        'score': match['score'],
                        'resume_id': match['metadata'].get('resume_id'),
                        'metadata': match['metadata']
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar sections: {e}")
            raise
    
    def get_resume_statistics(self, resume_id: str) -> Dict:
        """Get statistics about a stored resume"""
        try:
            # Query all chunks for this resume
            query_results = self.resume_index.query(
                vector=[0] * 384,  # Dummy vector
                top_k=1000,  # Large number to get all chunks
                include_metadata=True,
                filter={'resume_id': resume_id}
            )
            
            chunks = query_results['matches']
            
            # Calculate statistics
            stats = {
                'total_chunks': len(chunks),
                'total_characters': sum(len(chunk['metadata'].get('content', '')) for chunk in chunks),
                'sections_found': len(set(chunk['metadata'].get('section_type', 'unknown') for chunk in chunks)),
                'file_name': chunks[0]['metadata'].get('file_name', 'unknown') if chunks else 'unknown'
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting resume statistics: {e}")
            return {}
    
    def delete_resume(self, resume_id: str):
        """Delete all chunks for a specific resume"""
        try:
            # Get all vector IDs for this resume
            query_results = self.resume_index.query(
                vector=[0] * 384,  # Dummy vector
                top_k=1000,
                include_metadata=True,
                filter={'resume_id': resume_id}
            )
            
            # Extract IDs and delete
            vector_ids = [match['id'] for match in query_results['matches']]
            
            if vector_ids:
                self.resume_index.delete(ids=vector_ids)
                logger.info(f"Deleted {len(vector_ids)} chunks for resume {resume_id}")
            
        except Exception as e:
            logger.error(f"Error deleting resume: {e}")
            raise
    
    def clear_all_projects(self):
        """Clear all project data (use with caution!)"""
        try:
            # For newer Pinecone versions, we need to delete by filter or fetch all IDs
            # First, try to get some stats to see if there are any vectors
            stats = self.projects_index.describe_index_stats()
            
            if stats.get('total_vector_count', 0) > 0:
                logger.info(f"Found {stats['total_vector_count']} vectors to clear")
                
                # Delete all vectors using delete_all (if supported) or by filter
                try:
                    self.projects_index.delete(delete_all=True)
                    logger.info("Cleared all project data using delete_all")
                except Exception as e:
                    logger.warning(f"delete_all failed: {e}, trying alternative method")
                    
                    # Alternative: delete by fetching IDs in batches
                    try:
                        # Query to get all vector IDs
                        query_result = self.projects_index.query(
                            vector=[0.0] * EMBEDDING_DIMENSION,
                            top_k=10000,  # Large number to get all
                            include_metadata=False
                        )
                        
                        if query_result.get('matches'):
                            vector_ids = [match['id'] for match in query_result['matches']]
                            if vector_ids:
                                self.projects_index.delete(ids=vector_ids)
                                logger.info(f"Cleared {len(vector_ids)} project vectors")
                    except Exception as e2:
                        logger.warning(f"Alternative delete method also failed: {e2}")
                        logger.info("Proceeding without clearing (new data will be added)")
            else:
                logger.info("No project vectors to clear")
            
        except Exception as e:
            logger.warning(f"Error clearing projects (this may be normal for empty index): {e}")
            logger.info("Proceeding with project upload...")
    
    def get_index_stats(self) -> Dict:
        """Get statistics about both indexes"""
        try:
            resume_stats = self.resume_index.describe_index_stats()
            projects_stats = self.projects_index.describe_index_stats()
            
            return {
                'resume_index': {
                    'total_vectors': resume_stats['total_vector_count'],
                    'dimension': resume_stats['dimension']
                },
                'projects_index': {
                    'total_vectors': projects_stats['total_vector_count'],
                    'dimension': projects_stats['dimension']
                }
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}

# Usage example and testing
if __name__ == "__main__":
    # Test vector store initialization
    try:
        vs = VectorStore()
        stats = vs.get_index_stats()
        print(f"Vector store initialized successfully")
        print(f"Resume vectors: {stats.get('resume_index', {}).get('total_vectors', 0)}")
        print(f"Project vectors: {stats.get('projects_index', {}).get('total_vectors', 0)}")
    except Exception as e:
        print(f"Error initializing vector store: {e}")