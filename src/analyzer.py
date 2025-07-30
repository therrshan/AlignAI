"""
Core analysis engine that orchestrates the complete resume feedback pipeline
Combines document processing, vector search, and LLM analysis
"""

import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import time
from dataclasses import dataclass

from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from .llm_pipeline import LLMPipeline, extract_keywords_from_text
from .utils import calculate_similarity_score, extract_project_names

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Structured result from complete resume analysis"""
    overall_score: int
    resume_analysis: Dict
    project_recommendations: List[Dict]
    missing_keywords: List[Dict]
    improved_projects: List[Dict]
    section_scores: Dict
    processing_time: float
    metadata: Dict

class ResumeAnalyzer:
    """Main analyzer that orchestrates the complete feedback pipeline"""
    
    def __init__(self):
        # Initialize components
        logger.info("Initializing Resume Analyzer...")
        
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
        self.llm_pipeline = LLMPipeline()
        
        # Test connections
        self._verify_components()
        
        logger.info("Resume Analyzer initialized successfully")
    
    def _verify_components(self):
        """Verify all components are working"""
        try:
            # Test LLM connection
            if not self.llm_pipeline.test_connection():
                raise ConnectionError("LLM connection failed")
            
            # Test vector store
            stats = self.vector_store.get_index_stats()
            if not stats:
                raise ConnectionError("Vector store connection failed")
            
            logger.info("All components verified successfully")
            
        except Exception as e:
            logger.error(f"Component verification failed: {e}")
            raise
    
    def upload_resume(self, file_path: Path, resume_id: str) -> Dict:
        """Process and store a new resume"""
        start_time = time.time()
        
        try:
            logger.info(f"Uploading resume: {file_path}")
            
            # Process the resume
            full_text, sections, chunks = self.document_processor.process_resume(file_path, resume_id)
            
            # Store in vector database
            resume_metadata = {
                'file_name': file_path.name,
                'upload_time': time.time(),
                'sections_count': len(sections)
            }
            
            self.vector_store.store_resume_chunks(resume_id, chunks, resume_metadata)
            
            processing_time = time.time() - start_time
            
            result = {
                'resume_id': resume_id,
                'file_name': file_path.name,
                'sections_found': list(sections.keys()),
                'total_chunks': len(chunks),
                'character_count': len(full_text),
                'processing_time': processing_time,
                'status': 'success'
            }
            
            logger.info(f"Resume uploaded successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error uploading resume: {e}")
            return {
                'resume_id': resume_id,
                'status': 'error',
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def upload_projects_latex(self, latex_content: str) -> Dict:
        """Process and store projects from LaTeX content (better than PDF parsing)"""
        start_time = time.time()
        
        try:
            logger.info("Processing projects from LaTeX content...")
            
            # Import LaTeX parser
            from .latex_parser import LaTeXProjectParser
            parser = LaTeXProjectParser()
            
            # Parse projects from LaTeX
            parsed_projects = parser.parse_projects_from_latex(latex_content)
            
            if not parsed_projects:
                raise ValueError("No projects found in LaTeX content")
            
            # Clear existing projects (optional)
            self.vector_store.clear_all_projects()
            
            # Convert to chunks for vector storage
            all_chunks = []
            project_metadata = []
            
            for i, project in enumerate(parsed_projects):
                # Create comprehensive project description for embedding
                project_text = f"{project.name}. Technologies: {', '.join(project.tech_stack)}. {project.get_full_description()}"
                
                # Create chunks
                chunks = self.document_processor.chunk_text_for_embedding(
                    project_text,
                    metadata={
                        'document_type': 'project',
                        'project_name': project.name,
                        'project_index': i,
                        'tech_stack': project.tech_stack,
                        'date_range': project.date_range,
                        'github_link': project.github_link,
                        'source': 'latex'
                    }
                )
                all_chunks.extend(chunks)
                
                # Store project metadata for easy retrieval
                project_metadata.append(project.to_dict())
            
            # Store in vector database
            self.vector_store.store_project_chunks(all_chunks)
            
            processing_time = time.time() - start_time
            
            result = {
                'projects_count': len(parsed_projects),
                'total_chunks': len(all_chunks),
                'project_names': [p.name for p in parsed_projects],
                'tech_stacks': [p.tech_stack for p in parsed_projects],
                'processing_time': processing_time,
                'status': 'success',
                'source': 'latex'
            }
            
            logger.info(f"LaTeX projects processed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing LaTeX projects: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def analyze_resume_latex_only(self, resume_id: str, job_description: str, projects_latex: str) -> AnalysisResult:
        """Enhanced analysis using LaTeX projects without Pinecone storage issues"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting LaTeX-only analysis for resume {resume_id}")
            
            # Step 1: Get resume content (try different approaches)
            resume_content = ""
            try:
                resume_chunks = self.vector_store.search_resume_content("", resume_id, top_k=20)
                resume_content = "\n".join([chunk['content'] for chunk in resume_chunks])
            except Exception as e:
                logger.warning(f"Vector search failed: {e}, trying alternative approach")
            
            # Fallback: try to get resume content directly from recent uploads
            if not resume_content:
                logger.info("Trying alternative resume content retrieval...")
                # This is a simplified fallback - in practice you might store content temporarily
                resume_content = "Resume content placeholder - analysis will focus on LaTeX projects"
            
            # Step 2: Basic resume analysis (if we have content)
            resume_analysis = {}
            if len(resume_content) > 50:  # Only if we have substantial content
                try:
                    resume_analysis = self.llm_pipeline.analyze_resume(resume_content, job_description)
                except Exception as e:
                    logger.warning(f"Resume analysis failed: {e}")
                    resume_analysis = {
                        'overall_score': 70,  # Default score
                        'clarity': {'score': 70, 'feedback': 'Analysis focused on project matching', 'suggestions': []},
                        'role_alignment': {'score': 75, 'feedback': 'See project recommendations below', 'suggestions': []},
                        'tone': {'score': 70, 'feedback': 'Professional tone assumed', 'suggestions': []}
                    }
            
            # Step 3: LaTeX project analysis (main focus)
            project_recommendations = []
            improved_projects = []
            
            if projects_latex:
                from .latex_parser import LaTeXProjectParser
                parser = LaTeXProjectParser()
                
                # Parse LaTeX projects
                parsed_projects = parser.parse_projects_from_latex(projects_latex)
                logger.info(f"Parsed {len(parsed_projects)} projects from LaTeX")
                
                if parsed_projects:
                    # Rank projects by job relevance
                    ranked_projects = parser.rank_projects_for_job(parsed_projects, job_description, top_k=8)
                    logger.info(f"Ranked {len(ranked_projects)} projects by relevance")
                    
                    # Create project recommendations (top relevant projects)
                    for ranked_project in ranked_projects:
                        if ranked_project['overall_score'] > 50:  # Good relevance threshold
                            project_recommendations.append({
                                'project_name': ranked_project['project_name'],
                                'relevance_score': ranked_project['overall_score'],
                                'why_better': f"High relevance ({ranked_project['overall_score']:.1f}%) with matching technologies: {', '.join(ranked_project['matched_keywords'][:5])}",
                                'key_skills': ranked_project['matched_keywords'],
                                'tech_stack': ranked_project['tech_stack']
                            })
                    
                    # Get top 3 projects for phrasing improvement
                    top_3_projects = ranked_projects[:3]
                    if top_3_projects:
                        # Find the actual project objects for detailed descriptions
                        top_project_descriptions = []
                        for ranked_proj in top_3_projects:
                            for parsed_proj in parsed_projects:
                                if parsed_proj.name == ranked_proj['project_name']:
                                    top_project_descriptions.append(f"{parsed_proj.name}: {parsed_proj.get_full_description()}")
                                    break
                        
                        # Get missing keywords for improvement
                        job_keywords = extract_keywords_from_text(job_description)
                        project_keywords = []
                        for proj in parsed_projects:
                            project_keywords.extend(parser.extract_keywords_from_project(proj))
                        
                        missing_keywords = [kw for kw in job_keywords if kw not in project_keywords][:10]
                        
                        # Improve project phrasing
                        if top_project_descriptions and missing_keywords:
                            try:
                                phrasing_result = self.llm_pipeline.improve_project_phrasing(
                                    top_project_descriptions,
                                    missing_keywords,
                                    job_description
                                )
                                improved_projects = phrasing_result.get('improved_projects', [])
                            except Exception as e:
                                logger.warning(f"Project phrasing improvement failed: {e}")
            
            # Step 4: Keyword analysis
            missing_keywords = []
            try:
                # Extract keywords from job description
                job_keywords = extract_keywords_from_text(job_description)
                
                # Extract keywords from projects
                project_keywords = []
                if projects_latex:
                    for proj in parsed_projects:
                        project_keywords.extend(parser.extract_keywords_from_project(proj))
                
                # Find missing keywords
                missing = [kw for kw in job_keywords if kw not in project_keywords][:15]
                missing_keywords = [
                    {
                        'keyword': kw,
                        'category': 'Technical',
                        'importance': 'high' if kw in job_keywords[:5] else 'medium',
                        'context': 'Add to relevant project descriptions'
                    }
                    for kw in missing
                ]
            except Exception as e:
                logger.warning(f"Keyword analysis failed: {e}")
            
            # Calculate overall score based on project relevance
            overall_score = 70  # Default
            if project_recommendations:
                avg_project_score = sum(p['relevance_score'] for p in project_recommendations[:3]) / min(3, len(project_recommendations))
                overall_score = int(avg_project_score)
            
            # Update resume analysis with calculated score
            if 'overall_score' not in resume_analysis:
                resume_analysis['overall_score'] = overall_score
            
            processing_time = time.time() - start_time
            
            # Create structured result
            result = AnalysisResult(
                overall_score=overall_score,
                resume_analysis=resume_analysis,
                project_recommendations=project_recommendations,
                missing_keywords=missing_keywords,
                improved_projects=improved_projects,
                section_scores={},  # Skip section analysis for now
                processing_time=processing_time,
                metadata={
                    'resume_id': resume_id,
                    'job_description_length': len(job_description),
                    'projects_parsed': len(parsed_projects) if 'parsed_projects' in locals() else 0,
                    'analysis_type': 'latex_only',
                    'analysis_timestamp': time.time()
                }
            )
            
            logger.info(f"LaTeX-only analysis finished in {processing_time:.2f}s")
            logger.info(f"Overall score: {overall_score}/100")
            logger.info(f"Project recommendations: {len(project_recommendations)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in LaTeX-only analysis: {e}")
            
            # Return minimal error result
            return AnalysisResult(
                overall_score=0,
                resume_analysis={'error': str(e)},
                project_recommendations=[],
                missing_keywords=[],
                improved_projects=[],
                section_scores={},
                processing_time=time.time() - start_time,
                metadata={'error': str(e), 'analysis_type': 'latex_only_failed'}
            )
        """Enhanced analysis using LaTeX projects for better project matching"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting enhanced analysis with LaTeX projects for resume {resume_id}")
            
            # Step 1: Get resume content
            resume_chunks = self.vector_store.search_resume_content("", resume_id, top_k=20)
            resume_content = "\n".join([chunk['content'] for chunk in resume_chunks])
            
            if not resume_content:
                raise ValueError(f"No content found for resume {resume_id}")
            
            # Step 2: Basic resume analysis
            logger.info("Performing resume analysis...")
            resume_analysis = self.llm_pipeline.analyze_resume(resume_content, job_description)
            
            # Step 3: LaTeX project analysis (if provided)
            project_recommendations = []
            improved_projects = []
            
            if projects_latex:
                from .latex_parser import LaTeXProjectParser
                parser = LaTeXProjectParser()
                
                # Parse LaTeX projects
                parsed_projects = parser.parse_projects_from_latex(projects_latex)
                
                if parsed_projects:
                    # Rank projects by job relevance
                    ranked_projects = parser.rank_projects_for_job(parsed_projects, job_description, top_k=8)
                    
                    # Get current projects from resume (fallback to simple extraction)
                    current_project_names = extract_project_names(resume_content)
                    
                    # Find better alternatives
                    for ranked_project in ranked_projects:
                        # Check if this project is better than current ones
                        if ranked_project['overall_score'] > 60:  # Good relevance threshold
                            # Check if not already in resume
                            is_new = True
                            for current_proj in current_project_names:
                                if current_proj.lower() in ranked_project['project_name'].lower():
                                    is_new = False
                                    break
                            
                            if is_new:
                                project_recommendations.append({
                                    'project_name': ranked_project['project_name'],
                                    'relevance_score': ranked_project['overall_score'],
                                    'why_better': f"High relevance ({ranked_project['overall_score']:.1f}%) with matching technologies: {', '.join(ranked_project['matched_keywords'])}",
                                    'key_skills': ranked_project['matched_keywords'],
                                    'tech_stack': ranked_project['tech_stack']
                                })
                    
                    # Get top 3 projects for phrasing improvement
                    top_3_projects = ranked_projects[:3]
                    if top_3_projects:
                        # Find the actual project objects for detailed descriptions
                        top_project_descriptions = []
                        for ranked_proj in top_3_projects:
                            for parsed_proj in parsed_projects:
                                if parsed_proj.name == ranked_proj['project_name']:
                                    top_project_descriptions.append(f"{parsed_proj.name}: {parsed_proj.get_full_description()}")
                                    break
                        
                        # Get missing keywords for improvement
                        current_keywords = extract_keywords_from_text(resume_content)
                        keyword_analysis = self.llm_pipeline.extract_missing_keywords(job_description, current_keywords)
                        missing_keywords = [kw['keyword'] for kw in keyword_analysis.get('missing_keywords', [])[:10]]
                        
                        # Improve project phrasing
                        if top_project_descriptions and missing_keywords:
                            phrasing_result = self.llm_pipeline.improve_project_phrasing(
                                top_project_descriptions,
                                missing_keywords,
                                job_description
                            )
                            improved_projects = phrasing_result.get('improved_projects', [])
            
            # Step 4: Regular keyword analysis
            logger.info("Analyzing keywords...")
            current_keywords = extract_keywords_from_text(resume_content)
            keyword_analysis = self.llm_pipeline.extract_missing_keywords(job_description, current_keywords)
            missing_keywords = keyword_analysis.get('missing_keywords', [])
            
            # Step 5: Section-wise analysis
            section_scores = {}
            try:
                sections_to_analyze = ['experience', 'skills', 'projects']
                for section_type in sections_to_analyze:
                    section_content = self.vector_store.search_resume_content(
                        f"{section_type} section", resume_id, top_k=3
                    )
                    
                    if section_content:
                        section_text = "\n".join([chunk['content'] for chunk in section_content])
                        section_analysis = self.llm_pipeline.evaluate_resume_section(
                            section_type, section_text, job_description
                        )
                        section_scores[section_type] = section_analysis
            except Exception as e:
                logger.warning(f"Section analysis failed: {e}")
                section_scores = {}
            
            # Calculate overall score
            overall_score = resume_analysis.get('overall_score', 0)
            if isinstance(overall_score, str):
                try:
                    overall_score = int(overall_score)
                except:
                    overall_score = 0
            
            processing_time = time.time() - start_time
            
            # Create structured result
            result = AnalysisResult(
                overall_score=overall_score,
                resume_analysis=resume_analysis,
                project_recommendations=project_recommendations,
                missing_keywords=missing_keywords,
                improved_projects=improved_projects,
                section_scores=section_scores,
                processing_time=processing_time,
                metadata={
                    'resume_id': resume_id,
                    'job_description_length': len(job_description),
                    'resume_content_length': len(resume_content),
                    'latex_projects_used': bool(projects_latex),
                    'analysis_timestamp': time.time()
                }
            )
            
            logger.info(f"Enhanced analysis finished in {processing_time:.2f}s")
            logger.info(f"Overall score: {overall_score}/100")
            logger.info(f"Project recommendations: {len(project_recommendations)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced analysis: {e}")
            
            # Return error result
            return AnalysisResult(
                overall_score=0,
                resume_analysis={'error': str(e)},
                project_recommendations=[],
                missing_keywords=[],
                improved_projects=[],
                section_scores={},
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    def analyze_resume_against_job(self, resume_id: str, job_description: str) -> AnalysisResult:
        """Complete analysis pipeline for resume vs job description"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting complete analysis for resume {resume_id}")
            
            # Step 1: Get resume content
            resume_chunks = self.vector_store.search_resume_content("", resume_id, top_k=20)
            resume_content = "\n".join([chunk['content'] for chunk in resume_chunks])
            
            if not resume_content:
                raise ValueError(f"No content found for resume {resume_id}")
            
            # Step 2: Basic resume analysis
            logger.info("Performing resume analysis...")
            resume_analysis = self.llm_pipeline.analyze_resume(resume_content, job_description)
            
            # Step 3: Extract current projects from resume
            current_project_names = extract_project_names(resume_content)
            
            # Step 4: Find alternative projects
            logger.info("Searching for alternative projects...")
            alternative_projects = self.vector_store.search_project_alternatives(
                job_description, 
                current_project_names
            )
            
            # Step 5: Get better project matches using LLM
            project_recommendations = []
            if alternative_projects:
                project_matching_result = self.llm_pipeline.find_better_project_matches(
                    current_project_names,
                    alternative_projects,
                    job_description
                )
                project_recommendations = project_matching_result.get('better_matches', [])
            
            # Step 6: Extract keywords and find missing ones
            logger.info("Analyzing keywords...")
            current_keywords = extract_keywords_from_text(resume_content)
            keyword_analysis = self.llm_pipeline.extract_missing_keywords(
                job_description,
                current_keywords
            )
            missing_keywords = keyword_analysis.get('missing_keywords', [])
            
            # Step 7: Improve project phrasing
            logger.info("Improving project phrasing...")
            target_keywords = [kw['keyword'] for kw in missing_keywords[:10]]
            
            if current_project_names:
                phrasing_result = self.llm_pipeline.improve_project_phrasing(
                    current_project_names,
                    target_keywords,
                    job_description
                )
                improved_projects = phrasing_result.get('improved_projects', [])
            else:
                improved_projects = []
            
            # Step 8: Section-wise analysis (if we have structured sections)
            section_scores = {}
            try:
                sections_to_analyze = ['experience', 'skills', 'projects']
                for section_type in sections_to_analyze:
                    section_content = self.vector_store.search_resume_content(
                        f"{section_type} section", 
                        resume_id, 
                        top_k=3
                    )
                    
                    if section_content:
                        section_text = "\n".join([chunk['content'] for chunk in section_content])
                        section_analysis = self.llm_pipeline.evaluate_resume_section(
                            section_type,
                            section_text,
                            job_description
                        )
                        section_scores[section_type] = section_analysis
            except Exception as e:
                logger.warning(f"Section analysis failed: {e}")
                section_scores = {}
            
            # Calculate overall score
            overall_score = resume_analysis.get('overall_score', 0)
            if isinstance(overall_score, str):
                try:
                    overall_score = int(overall_score)
                except:
                    overall_score = 0
            
            processing_time = time.time() - start_time
            
            # Create structured result
            result = AnalysisResult(
                overall_score=overall_score,
                resume_analysis=resume_analysis,
                project_recommendations=project_recommendations,
                missing_keywords=missing_keywords,
                improved_projects=improved_projects,
                section_scores=section_scores,
                processing_time=processing_time,
                metadata={
                    'resume_id': resume_id,
                    'job_description_length': len(job_description),
                    'resume_content_length': len(resume_content),
                    'alternative_projects_found': len(alternative_projects),
                    'analysis_timestamp': time.time()
                }
            )
            
            logger.info(f"Complete analysis finished in {processing_time:.2f}s")
            logger.info(f"Overall score: {overall_score}/100")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in complete analysis: {e}")
            
            # Return error result
            return AnalysisResult(
                overall_score=0,
                resume_analysis={'error': str(e)},
                project_recommendations=[],
                missing_keywords=[],
                improved_projects=[],
                section_scores={},
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    def get_resume_list(self) -> List[Dict]:
        """Get list of all uploaded resumes"""
        try:
            stats = self.vector_store.get_index_stats()
            # This is a simplified version - in practice, you'd want to store resume metadata separately
            
            # For now, return basic stats
            return [{
                'resume_count': stats.get('resume_index', {}).get('total_vectors', 0),
                'projects_count': stats.get('projects_index', {}).get('total_vectors', 0)
            }]
            
        except Exception as e:
            logger.error(f"Error getting resume list: {e}")
            return []
    
    def delete_resume(self, resume_id: str) -> bool:
        """Delete a resume from the system"""
        try:
            self.vector_store.delete_resume(resume_id)
            logger.info(f"Resume {resume_id} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting resume {resume_id}: {e}")
            return False
    
    def get_system_status(self) -> Dict:
        """Get system health and status"""
        try:
            # Test all components
            llm_status = self.llm_pipeline.test_connection()
            vector_stats = self.vector_store.get_index_stats()
            
            return {
                'llm_status': 'connected' if llm_status else 'disconnected',
                'vector_store_status': 'connected' if vector_stats else 'disconnected',
                'resume_vectors': vector_stats.get('resume_index', {}).get('total_vectors', 0),
                'project_vectors': vector_stats.get('projects_index', {}).get('total_vectors', 0),
                'model_info': self.llm_pipeline.get_model_info(),
                'timestamp': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'error': str(e),
                'status': 'error',
                'timestamp': time.time()
            }

# Usage example
if __name__ == "__main__":
    # Test the analyzer
    try:
        analyzer = ResumeAnalyzer()
        status = analyzer.get_system_status()
        print("System Status:", status)
    except Exception as e:
        print(f"Error: {e}")