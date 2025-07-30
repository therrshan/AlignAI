"""
LaTeX parser for structured project data
Parses resume projects from LaTeX format for direct analysis
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsedProject:
    """Structured representation of a parsed project"""
    name: str
    tech_stack: List[str]
    date_range: str
    github_link: Optional[str]
    description_points: List[str]
    raw_latex: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for easy serialization"""
        return {
            'name': self.name,
            'tech_stack': self.tech_stack,
            'date_range': self.date_range,
            'github_link': self.github_link,
            'description_points': self.description_points,
            'raw_latex': self.raw_latex
        }
    
    def get_full_description(self) -> str:
        """Get concatenated description for analysis"""
        return ' '.join(self.description_points)

class LaTeXProjectParser:
    """Parser for LaTeX resume projects in resumeProjectHeading format"""
    
    def __init__(self):
        # More flexible regex patterns
        self.project_pattern = r'\\resumeProjectHeading\s*\{(.*?)\}\{([^}]*)\}\s*\\resumeItemListStart(.*?)\\resumeItemListEnd'
        self.header_pattern = r'\\textbf\{([^}]*)\}\s*\$\|\$\s*\\emph\{(.*?)\}'
        self.link_pattern = r'\\href\{([^}]*)\}\{[^}]*\}'
        self.item_pattern = r'\\resumeItem\{(.*?)\}'
        self.bold_pattern = r'\\textbf\{([^}]*)\}'
    
    def parse_projects_from_latex(self, latex_content: str) -> List[ParsedProject]:
        """Parse all projects from LaTeX content with detailed debugging"""
        projects = []
        
        print(f"🔍 Parsing LaTeX content ({len(latex_content)} characters)")
        print(f"📄 First 200 chars: {latex_content[:200]}...")
        
        # Find all project blocks with debugging
        project_matches = list(re.finditer(self.project_pattern, latex_content, re.DOTALL))
        print(f"🎯 Found {len(project_matches)} project matches")
        
        if not project_matches:
            # Try different patterns for debugging
            print("🔧 Trying alternative patterns...")
            
            # Check if resumeProjectHeading exists at all
            if '\\resumeProjectHeading' in latex_content:
                print("✅ Found \\resumeProjectHeading in text")
                
                # Try simpler pattern
                simple_pattern = r'\\resumeProjectHeading.*?\\resumeItemListEnd'
                simple_matches = re.findall(simple_pattern, latex_content, re.DOTALL)
                print(f"🔍 Simple pattern found {len(simple_matches)} matches")
                
                if simple_matches:
                    print(f"📝 First match preview: {simple_matches[0][:300]}...")
            else:
                print("❌ No \\resumeProjectHeading found in text")
                return projects
        
        for i, match in enumerate(project_matches):
            try:
                print(f"\n🏗️ Processing project {i+1}:")
                
                header_content = match.group(1).strip()
                date_range = match.group(2).strip()
                items_content = match.group(3).strip()
                raw_latex = match.group(0)
                
                print(f"📋 Header: {header_content[:100]}...")
                print(f"📅 Date: {date_range}")
                print(f"📝 Items: {items_content[:100]}...")
                
                # Parse the header
                project_name, tech_stack, github_link = self._parse_header(header_content)
                print(f"🏷️ Parsed name: '{project_name}'")
                print(f"🛠️ Tech stack: {tech_stack}")
                print(f"🔗 GitHub: {github_link}")
                
                # Parse the description items
                description_points = self._parse_items(items_content)
                print(f"📄 Description points: {len(description_points)}")
                
                if project_name and description_points:
                    project = ParsedProject(
                        name=project_name,
                        tech_stack=tech_stack,
                        date_range=date_range,
                        github_link=github_link,
                        description_points=description_points,
                        raw_latex=raw_latex
                    )
                    projects.append(project)
                    print(f"✅ Successfully parsed project: {project_name}")
                else:
                    print(f"❌ Failed to parse project - name: '{project_name}', points: {len(description_points)}")
                
            except Exception as e:
                print(f"❌ Error parsing project block {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n🎉 Successfully parsed {len(projects)} projects from LaTeX")
        return projects
    
    def _parse_header(self, header_content: str) -> Tuple[str, List[str], Optional[str]]:
        """Parse project header to extract name, tech stack, and GitHub link with debugging"""
        project_name = ""
        tech_stack = []
        github_link = None
        
        print(f"🔍 Parsing header: {header_content}")
        
        # Extract GitHub link first
        link_match = re.search(self.link_pattern, header_content)
        if link_match:
            github_link = link_match.group(1)
            print(f"🔗 Found GitHub link: {github_link}")
            # Remove link from header for cleaner parsing
            header_content = re.sub(self.link_pattern, '', header_content)
        
        # Parse the main header pattern
        header_match = re.search(self.header_pattern, header_content, re.DOTALL)
        if header_match:
            project_name = header_match.group(1).strip()
            tech_stack_raw = header_match.group(2).strip()
            
            print(f"🏷️ Found project name: '{project_name}'")
            print(f"🛠️ Raw tech stack: '{tech_stack_raw}'")
            
            # Parse tech stack (comma-separated technologies)
            tech_stack = [tech.strip() for tech in tech_stack_raw.split(',') if tech.strip()]
            
            # Clean up any remaining LaTeX commands in tech stack
            tech_stack = [self._clean_latex_text(tech) for tech in tech_stack]
            
            print(f"🔧 Cleaned tech stack: {tech_stack}")
        else:
            print(f"❌ Header pattern didn't match. Pattern: {self.header_pattern}")
            print(f"❌ Header content: {header_content}")
            
            # Try to extract at least the project name
            textbf_match = re.search(r'\\textbf\{([^}]*)\}', header_content)
            if textbf_match:
                project_name = textbf_match.group(1).strip()
                print(f"🔧 Fallback: extracted name from \\textbf: '{project_name}'")
        
        return project_name, tech_stack, github_link
    
    def _parse_items(self, items_content: str) -> List[str]:
        """Parse resumeItem blocks to extract description points with debugging"""
        description_points = []
        
        print(f"🔍 Parsing items content: {items_content[:200]}...")
        
        # Find all resumeItem blocks
        item_matches = list(re.finditer(self.item_pattern, items_content, re.DOTALL))
        print(f"📝 Found {len(item_matches)} resumeItem matches")
        
        if not item_matches:
            # Try alternative patterns
            print("🔧 No matches found, trying simpler patterns...")
            
            # Check if resumeItem exists
            if '\\resumeItem' in items_content:
                print("✅ Found \\resumeItem in content")
                
                # Try to extract with simpler regex
                simple_items = re.findall(r'\\resumeItem\{([^}]+)\}', items_content)
                print(f"🔍 Simple pattern found {len(simple_items)} items")
                
                for item in simple_items:
                    cleaned = self._clean_latex_text(item.strip())
                    if cleaned:
                        description_points.append(cleaned)
                        print(f"✅ Added item: {cleaned[:50]}...")
            else:
                print("❌ No \\resumeItem found in content")
        else:
            for i, match in enumerate(item_matches):
                item_content = match.group(1).strip()
                print(f"📄 Item {i+1}: {item_content[:100]}...")
                
                # Clean up LaTeX formatting
                cleaned_content = self._clean_latex_text(item_content)
                
                if cleaned_content:
                    description_points.append(cleaned_content)
                    print(f"✅ Cleaned item {i+1}: {cleaned_content[:50]}...")
        
        print(f"📋 Final description points: {len(description_points)}")
        return description_points
    
    def _clean_latex_text(self, text: str) -> str:
        """Clean LaTeX formatting from text"""
        if not text:
            return ""
        
        # Remove textbf but keep the content
        text = re.sub(r'\\textbf\{([^}]*)\}', r'\1', text)
        
        # Remove emph but keep the content
        text = re.sub(r'\\emph\{([^}]*)\}', r'\1', text)
        
        # Remove href but keep the display text
        text = re.sub(r'\\href\{[^}]*\}\{([^}]*)\}', r'\1', text)
        
        # Remove underline but keep content
        text = re.sub(r'\\underline\{([^}]*)\}', r'\1', text)
        
        # Remove other common LaTeX commands
        text = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^}]*)\}', r'\1', text)
        
        # Clean up math mode
        text = re.sub(r'\$([^$]*)\$', r'\1', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def extract_keywords_from_project(self, project: ParsedProject) -> List[str]:
        """Extract technical keywords from a project"""
        keywords = set()
        
        # Add tech stack items
        keywords.update([tech.lower() for tech in project.tech_stack])
        
        # Extract keywords from description
        full_description = project.get_full_description().lower()
        
        # Common technical keywords to look for
        tech_patterns = [
            r'\b(?:python|java|javascript|typescript|c\+\+|c#|go|rust|swift|kotlin)\b',
            r'\b(?:react|angular|vue|django|flask|spring|express|fastapi|streamlit)\b',
            r'\b(?:aws|azure|gcp|docker|kubernetes|jenkins|git|github)\b',
            r'\b(?:mysql|postgresql|mongodb|redis|elasticsearch|pinecone)\b',
            r'\b(?:tensorflow|pytorch|scikit-learn|pandas|numpy|langchain|ollama)\b',
            r'\b(?:html|css|sass|less|bootstrap|tailwind)\b',
            r'\b(?:node\.js|npm|yarn|webpack|babel)\b',
            r'\b(?:linux|ubuntu|macos|windows|bash|shell)\b',
            r'\b(?:api|rest|graphql|microservices|rag|llm|ai|ml)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, full_description, re.IGNORECASE)
            keywords.update([match.lower() for match in matches])
        
        return list(keywords)
    
    def score_project_for_job(self, project: ParsedProject, job_description: str) -> Dict:
        """Score how well a project matches a job description"""
        job_desc_lower = job_description.lower()
        project_keywords = self.extract_keywords_from_project(project)
        project_text = (project.name + " " + project.get_full_description()).lower()
        
        # Count keyword matches
        keyword_matches = sum(1 for keyword in project_keywords if keyword in job_desc_lower)
        keyword_score = min(100, (keyword_matches / max(len(project_keywords), 1)) * 100)
        
        # Calculate text similarity (simple word overlap)
        job_words = set(re.findall(r'\b\w+\b', job_desc_lower))
        project_words = set(re.findall(r'\b\w+\b', project_text))
        
        common_words = job_words.intersection(project_words)
        similarity_score = min(100, (len(common_words) / max(len(job_words), 1)) * 100)
        
        # Overall relevance score
        overall_score = (keyword_score * 0.7 + similarity_score * 0.3)
        
        return {
            'project_name': project.name,
            'overall_score': round(overall_score, 1),
            'keyword_score': round(keyword_score, 1),
            'similarity_score': round(similarity_score, 1),
            'matched_keywords': [kw for kw in project_keywords if kw in job_desc_lower],
            'tech_stack': project.tech_stack
        }

    def rank_projects_for_job(self, projects: List[ParsedProject], job_description: str, top_k: int = 5) -> List[Dict]:
        """Rank all projects by relevance to job description"""
        scored_projects = []
        
        for project in projects:
            score_data = self.score_project_for_job(project, job_description)
            scored_projects.append(score_data)
        
        # Sort by overall score (descending)
        scored_projects.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return scored_projects[:top_k]

    def format_project_for_resume(self, project: ParsedProject, target_keywords: List[str] = None) -> str:
        """Format project for resume with optional keyword optimization"""
        formatted = f"**{project.name}**\n"
        formatted += f"*Technologies: {', '.join(project.tech_stack)}*\n"
        formatted += f"*Timeline: {project.date_range}*\n"
        
        if project.github_link:
            formatted += f"*Link: {project.github_link}*\n"
        
        formatted += "\n"
        
        for point in project.description_points:
            formatted += f"• {point}\n"
        
        return formatted

# Usage and testing
if __name__ == "__main__":
    # Test with your sample project
    sample_latex = """
    \\resumeProjectHeading
      {\\textbf{AI-Based Resume Feedback Tool} $|$ \\emph{Python, LangChain, Ollama, LLaMA 3, Pinecone, Streamlit, \\href{https://github.com/therrshan/resume-ai-feedback}{\\underline{Link}}}}{Jul 2025 -- Present}
      \\resumeItemListStart
        \\resumeItem{Built a \\textbf{modular LLM pipeline} leveraging LangChain and LLaMa 3 to analyze resumes across clarity, role alignment, and tone dimensions using structured prompt chaining.}
        \\resumeItem{Implemented a \\textbf{retrieval-augmented generation (RAG)} system using Pinecone to enable semantic matching between resume content and job descriptions, improving contextual grounding and factual alignment.}
        \\resumeItem{Engineered \\textbf{task-specialized prompt templates} and few-shot exemplars for section-wise evaluation (skills, experience, education), with support for dynamic role conditioning via system messages.}
        \\resumeItem{Integrated internal evaluation metrics to assess model performance on criteria like hallucination rate, response consistency, and content coverage across a curated benchmark of annotated resumes.}
      \\resumeItemListEnd
    """
    
    parser = LaTeXProjectParser()
    projects = parser.parse_projects_from_latex(sample_latex)
    
    if projects:
        project = projects[0]
        print(f"✅ Parsed project: {project.name}")
        print(f"📚 Tech stack: {project.tech_stack}")
        print(f"📅 Date: {project.date_range}")
        print(f"🔗 GitHub: {project.github_link}")
        print(f"📝 Description points: {len(project.description_points)}")
        
        # Test keyword extraction
        keywords = parser.extract_keywords_from_project(project)
        print(f"🔍 Keywords: {keywords}")
        
        # Test job matching
        sample_job = "Looking for a Python developer with experience in AI, machine learning, and LangChain"
        score = parser.score_project_for_job(project, sample_job)
        print(f"🎯 Job match score: {score}")
    else:
        print("❌ Failed to parse project")