from typing import List, Optional
from app.models import (
    AnalysisResponse, Score, ScoreCategory,
    MissingKeyword, Project, EnhancedDescription
)
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
import os


class ResumeAnalyzer:
    def __init__(self):
        provider = os.getenv("LLM_PROVIDER", "groq")
        self.llm = LLMService(provider=provider)
        self.rag = RAGService()
    
    async def analyze(
        self,
        resume_text: str,
        job_description: str,
        projects: List[Project],
        selected_projects: Optional[List[str]] = None
    ) -> AnalysisResponse:
        """Perform comprehensive resume analysis."""
        
        # Generate resume ID and store in vector DB
        resume_id = self.rag.get_resume_id(resume_text)
        projects_dict = [p.dict() for p in projects]
        self.rag.store_resume(resume_id, resume_text, projects_dict)
        
        # 1. LLM-based resume analysis
        analysis = self.llm.analyze_resume(resume_text, job_description)
        
        # 2. Rank projects by relevance
        project_rankings = self.llm.rank_projects(projects_dict, job_description)
        
        # 3. RAG-based project recommendations
        rag_recommendations = self.rag.find_relevant_projects(
            job_description, 
            resume_id, 
            top_k=3
        )
        
        # Combine LLM and RAG recommendations
        recommended_projects = list(set(
            project_rankings.get("recommended_projects", [])[:3] + 
            rag_recommendations[:2]
        ))[:5]
        
        # 4. Update projects with relevance scores
        ranked_projects = []
        for project in projects:
            relevance = next(
                (r["relevance_score"] for r in project_rankings.get("rankings", []) 
                 if r["title"] == project.title),
                50.0
            )
            project.relevance_score = relevance
            ranked_projects.append(project)
        
        # Sort projects by relevance
        ranked_projects.sort(key=lambda p: p.relevance_score or 0, reverse=True)
        
        # 5. Enhance descriptions for selected projects
        enhanced_descriptions = []
        if selected_projects:
            for project_title in selected_projects[:3]:  # Limit to 3
                project = next((p for p in projects if p.title == project_title), None)
                if project:
                    try:
                        enhanced = self.llm.enhance_description(
                            project.description,
                            job_description
                        )
                        enhanced_descriptions.append(EnhancedDescription(
                            original=project.description,
                            enhanced=enhanced["enhanced"],
                            improvements=enhanced["improvements"]
                        ))
                    except Exception as e:
                        print(f"Error enhancing description: {e}")
        
        # 6. Build category scores
        category_scores = [
            Score(
                category=ScoreCategory.CLARITY,
                score=analysis.get("clarity_score", 75),
                feedback=analysis.get("clarity_feedback", "Resume is reasonably clear.")
            ),
            Score(
                category=ScoreCategory.ALIGNMENT,
                score=analysis.get("alignment_score", 70),
                feedback=analysis.get("alignment_feedback", "Some alignment with role.")
            ),
            Score(
                category=ScoreCategory.TONE,
                score=analysis.get("tone_score", 75),
                feedback=analysis.get("tone_feedback", "Professional tone maintained.")
            )
        ]
        
        # 7. Process missing keywords
        missing_keywords = [
            MissingKeyword(**kw) for kw in analysis.get("missing_keywords", [])
        ]
        
        # 8. Build ATS keywords dict
        ats_keywords = {
            "matched": analysis.get("matched_keywords", []),
            "missing": [kw.keyword for kw in missing_keywords]
        }
        
        return AnalysisResponse(
            overall_score=analysis.get("overall_score", 72),
            category_scores=category_scores,
            ats_keywords=ats_keywords,
            missing_keywords=missing_keywords,
            projects=ranked_projects,
            recommended_projects=recommended_projects,
            enhanced_descriptions=enhanced_descriptions if enhanced_descriptions else None,
            professional_feedback=analysis.get(
                "professional_feedback",
                "Focus on quantifying achievements and tailoring to job requirements."
            )
        )