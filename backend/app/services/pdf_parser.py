from PyPDF2 import PdfReader
from typing import List, Dict
import re


class PDFParser:
    def __init__(self):
        pass
    
    def parse_resume(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF resume."""
        try:
            from io import BytesIO
            pdf_file = BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    def parse_projects(self, pdf_bytes: bytes) -> List[Dict]:
        """
        Parse projects from a PDF file.
        Expected format: 
        Project Title |Tech1, Tech2, Tech3
        • Bullet point 1
        • Bullet point 2
        """
        text = self.parse_resume(pdf_bytes)
        projects = self._extract_projects_from_text(text)
        return projects
    
    def _extract_projects_from_text(self, text: str) -> List[Dict]:
        """
        Extract projects with title, tech stack, and bullet points.
        Pattern: Title |Tech, Tech, Tech followed by bullet points (•)
        """
        projects = []
        lines = text.split('\n')
        
        current_project = None
        current_description = []
        current_technologies = []
        
        for line in lines:
            line = line.strip()
            if not line or line.lower() == 'projects':
                continue
            
            # Check if line is a project title (contains |Tech)
            if '|' in line and not line.startswith('•'):
                # Save previous project
                if current_project:
                    projects.append({
                        'title': current_project,
                        'description': '\n'.join(current_description),
                        'technologies': current_technologies
                    })
                
                # Parse new project
                parts = line.split('|')
                current_project = parts[0].strip()
                
                # Extract technologies from after |
                if len(parts) > 1:
                    tech_string = parts[1].strip()
                    # Split by comma and clean
                    current_technologies = [t.strip() for t in tech_string.split(',') if t.strip()]
                else:
                    current_technologies = []
                
                current_description = []
                
            elif line.startswith('•') and current_project:
                # This is a bullet point for current project
                # Remove bullet and add to description
                bullet_text = line[1:].strip()  # Remove •
                current_description.append(bullet_text)
        
        # Save last project
        if current_project:
            projects.append({
                'title': current_project,
                'description': '\n'.join(current_description),
                'technologies': current_technologies
            })
        
        return projects