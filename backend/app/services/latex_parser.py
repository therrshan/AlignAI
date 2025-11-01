import re
from typing import List
from pylatexenc.latex2text import LatexNodes2Text
from app.models import Project, ParsedResume


class LaTeXParser:
    def __init__(self):
        self.latex_converter = LatexNodes2Text()
    
    def parse_resume(self, latex_content: str) -> ParsedResume:
        """Parse LaTeX resume and extract structured information."""
        plain_text = self.latex_converter.latex_to_text(latex_content)
        projects = self._extract_projects(latex_content)
        skills = self._extract_skills(latex_content)
        
        return ParsedResume(
            raw_text=plain_text,
            projects=projects,
            skills=skills
        )
    
    def _extract_projects(self, latex_content: str) -> List[Project]:
        """Extract project information from LaTeX resume."""
        projects = []
        
        # Pattern 1: \project{Title}{Tech}{Description}
        project_pattern = r'\\project\{([^}]+)\}\{([^}]+)\}\{([^}]+)\}'
        matches = re.finditer(project_pattern, latex_content, re.DOTALL)
        
        for match in matches:
            title = self.latex_converter.latex_to_text(match.group(1)).strip()
            tech_raw = match.group(2).strip()
            description = self.latex_converter.latex_to_text(match.group(3)).strip()
            technologies = self._parse_technologies(tech_raw)
            
            projects.append(Project(
                title=title,
                description=description,
                technologies=technologies
            ))
        
        # Pattern 2: \subsection{Project Title} (fallback)
        if not projects:
            projects = self._extract_projects_subsection(latex_content)
        
        return projects
    
    def _extract_projects_subsection(self, latex_content: str) -> List[Project]:
        """Extract projects from subsection format."""
        projects = []
        pattern = r'\\subsection\{([^}]+)\}(.*?)(?=\\subsection|\\section|$)'
        matches = re.finditer(pattern, latex_content, re.DOTALL)
        
        for match in matches:
            title = self.latex_converter.latex_to_text(match.group(1)).strip()
            content = match.group(2).strip()
            description = self.latex_converter.latex_to_text(content).strip()
            technologies = self._extract_tech_from_content(content)
            
            if title and description:
                projects.append(Project(
                    title=title,
                    description=description,
                    technologies=technologies
                ))
        
        return projects
    
    def _parse_technologies(self, tech_string: str) -> List[str]:
        """Parse technology string into list."""
        tech_text = self.latex_converter.latex_to_text(tech_string)
        techs = re.split(r'[,;|•]', tech_text)
        return [t.strip() for t in techs if t.strip()]
    
    def _extract_tech_from_content(self, content: str) -> List[str]:
        """Extract technologies from content text."""
        patterns = [
            r'\\textbf\{Technologies?:?\}\s*([^\\]+)',
            r'\\textit\{Technologies?:?\}\s*([^\\]+)',
            r'Technologies?:?\s*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                tech_text = self.latex_converter.latex_to_text(match.group(1))
                return self._parse_technologies(tech_text)
        
        return []
    
    def _extract_skills(self, latex_content: str) -> List[str]:
        """Extract skills from resume."""
        pattern = r'\\section\{Skills?\}(.*?)(?=\\section|$)'
        match = re.search(pattern, latex_content, re.DOTALL | re.IGNORECASE)
        
        if match:
            skills_content = self.latex_converter.latex_to_text(match.group(1))
            skills = re.split(r'[,;•\n]', skills_content)
            return [s.strip() for s in skills if s.strip() and len(s.strip()) > 2]
        
        return []