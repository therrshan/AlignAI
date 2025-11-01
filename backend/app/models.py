from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


class ScoreCategory(str, Enum):
    CLARITY = "clarity"
    ALIGNMENT = "role_alignment"
    TONE = "tone"


class Score(BaseModel):
    category: ScoreCategory
    score: float = Field(ge=0, le=100)
    feedback: str


class Project(BaseModel):
    title: str
    description: str
    technologies: List[str]
    relevance_score: Optional[float] = None


class MissingKeyword(BaseModel):
    keyword: str
    priority: str  # "high", "medium", "low"
    context: str


class EnhancedDescription(BaseModel):
    original: str
    enhanced: str
    improvements: List[str]


class AnalysisRequest(BaseModel):
    resume_text: str
    job_description: str
    selected_projects: Optional[List[str]] = None


class AnalysisResponse(BaseModel):
    overall_score: float
    category_scores: List[Score]
    ats_keywords: Dict[str, List[str]]  # {"matched": [...], "missing": [...]}
    missing_keywords: List[MissingKeyword]
    projects: List[Project]
    recommended_projects: List[str]
    enhanced_descriptions: Optional[List[EnhancedDescription]] = None
    professional_feedback: str


class ParsedResume(BaseModel):
    raw_text: str
    projects: List[Project]
    skills: List[str]
    experience_years: Optional[int] = None