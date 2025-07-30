"""
Data Manager for Resume AI Feedback Tool
Handles one-time processing and caching of resumes and projects
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .document_processor import DocumentProcessor
from .latex_parser import LaTeXProjectParser, ParsedProject
from config.settings import DATA_DIR, RESUMES_DIR, PROJECTS_DIR

logger = logging.getLogger(__name__)

class DataManager:
    """Manages resume and project data with caching for personal use"""
    
    def __init__(self):
        self.processed_dir = DATA_DIR / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
        self.resumes_cache_file = self.processed_dir / "resumes.json"
        self.projects_cache_file = self.processed_dir / "projects.json"
        
        self.document_processor = DocumentProcessor()  
        self.latex_parser = LaTeXProjectParser()
        
        self.cached_resumes = self._load_cached_resumes()
        self.cached_projects = self._load_cached_projects()
        
        logger.info("Data Manager initialized")
    
    def _load_cached_resumes(self) -> Dict:
        """Load cached resume data"""
        try:
            if self.resumes_cache_file.exists():
                with open(self.resumes_cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cached resumes: {e}")
        return {}
    
    def _load_cached_projects(self) -> Dict:
        """Load cached project data"""
        try:
            if self.projects_cache_file.exists():
                with open(self.projects_cache_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cached projects: {e}")
        return {}
    
    def _save_cached_resumes(self):
        """Save resume cache to disk"""
        try:
            with open(self.resumes_cache_file, 'w') as f:
                json.dump(self.cached_resumes, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save resume cache: {e}")
    
    def _save_cached_projects(self):
        """Save project cache to disk"""
        try:
            with open(self.projects_cache_file, 'w') as f:
                json.dump(self.cached_projects, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save project cache: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file for change detection"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def scan_and_process_resumes(self) -> Dict:
        """Scan resume directory and process new/changed files"""
        results = {
            'processed': 0,
            'cached': 0,
            'errors': 0,
            'total': 0
        }
        
        if not RESUMES_DIR.exists():
            logger.warning(f"Resume directory {RESUMES_DIR} does not exist")
            return results
        
        resume_files = list(RESUMES_DIR.glob("*.pdf")) + list(RESUMES_DIR.glob("*.docx"))
        results['total'] = len(resume_files)
        
        logger.info(f"Found {len(resume_files)} resume files")
        
        for resume_file in resume_files:
            try:
                file_hash = self._get_file_hash(resume_file)
                resume_key = resume_file.stem  # filename without extension
                
                # Check if file has changed
                if (resume_key in self.cached_resumes and 
                    self.cached_resumes[resume_key].get('file_hash') == file_hash):
                    results['cached'] += 1
                    logger.debug(f"Using cached data for {resume_file.name}")
                    continue
                
                # Process the resume
                logger.info(f"Processing resume: {resume_file.name}")
                full_text, sections, chunks = self.document_processor.process_resume(
                    resume_file, resume_key
                )
                
                # Store processed data
                self.cached_resumes[resume_key] = {
                    'filename': resume_file.name,
                    'file_path': str(resume_file),
                    'file_hash': file_hash,
                    'processed_date': datetime.now().isoformat(),
                    'full_text': full_text,
                    'sections': sections,
                    'chunks': [chunk for chunk in chunks],  # Convert to serializable format
                    'character_count': len(full_text),
                    'sections_found': list(sections.keys())
                }
                
                results['processed'] += 1
                logger.info(f"Successfully processed {resume_file.name}")
                
            except Exception as e:
                logger.error(f"Error processing {resume_file.name}: {e}")
                results['errors'] += 1
        
        # Save cache
        if results['processed'] > 0:
            self._save_cached_resumes()
            logger.info(f"Saved resume cache with {len(self.cached_resumes)} resumes")
        
        return results
    
    def scan_and_process_projects(self) -> Dict:
        """Scan project directory and process LaTeX files"""
        results = {
            'processed': 0,
            'cached': 0,
            'errors': 0,
            'total': 0
        }
        
        if not PROJECTS_DIR.exists():
            logger.warning(f"Projects directory {PROJECTS_DIR} does not exist")
            return results
        
        project_files = list(PROJECTS_DIR.glob("*.tex")) + list(PROJECTS_DIR.glob("*.txt"))
        results['total'] = len(project_files)
        
        logger.info(f"Found {len(project_files)} project files")
        
        for project_file in project_files:
            try:
                file_hash = self._get_file_hash(project_file)
                project_key = project_file.stem
                
                # Check if file has changed
                if (project_key in self.cached_projects and 
                    self.cached_projects[project_key].get('file_hash') == file_hash):
                    results['cached'] += 1
                    logger.debug(f"Using cached data for {project_file.name}")
                    continue
                
                # Process the project file
                logger.info(f"Processing project: {project_file.name}")
                
                with open(project_file, 'r', encoding='utf-8') as f:
                    latex_content = f.read()
                
                # Parse LaTeX content
                parsed_projects = self.latex_parser.parse_projects_from_latex(latex_content)
                
                if parsed_projects:
                    # Usually one project per file, but handle multiple
                    project_data = []
                    for proj in parsed_projects:
                        project_data.append({
                            'name': proj.name,
                            'tech_stack': proj.tech_stack,
                            'date_range': proj.date_range,
                            'github_link': proj.github_link,
                            'description_points': proj.description_points,
                            'full_description': proj.get_full_description(),
                            'keywords': self.latex_parser.extract_keywords_from_project(proj)
                        })
                    
                    # Store processed data
                    self.cached_projects[project_key] = {
                        'filename': project_file.name,
                        'file_path': str(project_file),
                        'file_hash': file_hash,
                        'processed_date': datetime.now().isoformat(),
                        'latex_content': latex_content,
                        'projects': project_data,
                        'project_count': len(project_data)
                    }
                    
                    results['processed'] += 1
                    logger.info(f"Successfully processed {project_file.name} with {len(project_data)} projects")
                else:
                    logger.warning(f"No projects found in {project_file.name}")
                    results['errors'] += 1
                
            except Exception as e:
                logger.error(f"Error processing {project_file.name}: {e}")
                results['errors'] += 1
        
        # Save cache
        if results['processed'] > 0:
            self._save_cached_projects()
            logger.info(f"Saved project cache with {len(self.cached_projects)} project files")
        
        return results
    
    def get_available_resumes(self) -> List[Dict]:
        """Get list of available resumes"""
        resumes = []
        for resume_key, data in self.cached_resumes.items():
            resumes.append({
                'key': resume_key,
                'filename': data.get('filename', ''),
                'processed_date': data.get('processed_date', ''),
                'character_count': data.get('character_count', 0),
                'sections_found': data.get('sections_found', [])
            })
        
        # Sort by filename
        resumes.sort(key=lambda x: x['filename'])
        return resumes
    
    def get_available_projects(self) -> List[Dict]:
        """Get list of available projects"""
        projects = []
        for project_key, data in self.cached_projects.items():
            for project_data in data.get('projects', []):
                projects.append({
                    'file_key': project_key,
                    'filename': data.get('filename', ''),
                    'name': project_data.get('name', ''),
                    'tech_stack': project_data.get('tech_stack', []),
                    'date_range': project_data.get('date_range', ''),
                    'github_link': project_data.get('github_link'),
                    'keywords': project_data.get('keywords', [])
                })
        
        # Sort by project name
        projects.sort(key=lambda x: x['name'])
        return projects
    
    def get_resume_content(self, resume_key: str) -> Optional[Dict]:
        """Get full resume content by key"""
        return self.cached_resumes.get(resume_key)
    
    def get_project_content(self, project_file_key: str) -> Optional[Dict]:
        """Get project content by file key"""
        return self.cached_projects.get(project_file_key)
    
    def get_selected_projects(self, project_keys: List[str]) -> List[Dict]:
        """Get content for selected projects"""
        selected = []
        for project_key in project_keys:
            # project_key format: "filename_projectname"
            if '_' in project_key:
                file_key, project_name = project_key.split('_', 1)
            else:
                file_key = project_key
                project_name = None
            
            if file_key in self.cached_projects:
                file_data = self.cached_projects[file_key]
                for project_data in file_data.get('projects', []):
                    if not project_name or project_data.get('name') == project_name:
                        selected.append(project_data)
                        break
        
        return selected
    
    def refresh_all_data(self) -> Dict:
        """Refresh both resumes and projects"""
        logger.info("Refreshing all data...")
        
        resume_results = self.scan_and_process_resumes()
        project_results = self.scan_and_process_projects()
        
        return {
            'resumes': resume_results,
            'projects': project_results,
            'total_resumes': len(self.cached_resumes),
            'total_projects': sum(len(data.get('projects', [])) for data in self.cached_projects.values())
        }
    
    def get_system_stats(self) -> Dict:
        """Get statistics about cached data"""
        total_projects = sum(len(data.get('projects', [])) for data in self.cached_projects.values())
        
        return {
            'resumes_cached': len(self.cached_resumes),
            'project_files_cached': len(self.cached_projects),
            'total_projects': total_projects,
            'cache_size_mb': (
                self.resumes_cache_file.stat().st_size + 
                self.projects_cache_file.stat().st_size
            ) / 1024 / 1024 if self.resumes_cache_file.exists() and self.projects_cache_file.exists() else 0
        }

# Usage example
if __name__ == "__main__":
    # Test the data manager
    dm = DataManager()
    
    print("📁 Scanning and processing files...")
    results = dm.refresh_all_data()
    
    print(f"📄 Resume Results: {results['resumes']}")
    print(f"🏗️ Project Results: {results['projects']}")
    
    print(f"\n📊 Available Resumes:")
    for resume in dm.get_available_resumes():
        print(f"  - {resume['filename']} ({resume['character_count']} chars)")
    
    print(f"\n🔧 Available Projects:")
    for project in dm.get_available_projects():
        print(f"  - {project['name']} | {', '.join(project['tech_stack'])}")
    
    print(f"\n📈 System Stats: {dm.get_system_stats()}")