"""
Utility functions for the AI Resume Feedback Tool
"""

import re
import logging
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

logger = logging.getLogger(__name__)

def calculate_similarity_score(text1: str, text2: str) -> float:
    """Calculate cosine similarity between two texts using TF-IDF"""
    try:
        if not text1 or not text2:
            return 0.0
            
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(similarity)
    except Exception as e:
        logger.warning(f"Error calculating similarity: {e}")
        return 0.0

def extract_keywords_from_text(text: str, max_keywords: int = 25) -> List[str]:
    """Extract important keywords from text using TF-IDF and NLTK"""
    if not text:
        return []
    
    try:
        # Get English stopwords
        stop_words = set(stopwords.words('english'))
        
        # Add domain-specific stopwords
        domain_stopwords = {
            'experience', 'work', 'job', 'role', 'position', 'team', 'company',
            'project', 'projects', 'using', 'used', 'use', 'including', 'include',
            'requirements', 'required', 'prefer', 'preferred', 'skills', 'skill',
            'ability', 'knowledge', 'understanding', 'working', 'development',
            'years', 'year', 'minimum', 'plus', 'strong', 'excellent', 'good',
            'experience', 'responsible', 'responsibilities', 'duties'
        }
        stop_words.update(domain_stopwords)
        
        # Tokenize and clean text
        tokens = word_tokenize(text.lower())
        
        # Filter tokens: only alphabetic, length > 2, not stopwords
        filtered_tokens = [
            token for token in tokens 
            if token.isalpha() and len(token) > 2 and token not in stop_words
        ]
        
        # Lemmatize tokens
        lemmatizer = WordNetLemmatizer()
        lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]
        
        # Use TF-IDF to find important terms
        if len(lemmatized_tokens) < 5:
            return lemmatized_tokens
        
        # Create document from tokens
        doc_text = ' '.join(lemmatized_tokens)
        
        # Use TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            max_features=max_keywords * 2,
            ngram_range=(1, 2),  # Include both single words and bigrams
            stop_words=None  # Already filtered
        )
        
        tfidf_matrix = vectorizer.fit_transform([doc_text])
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = tfidf_matrix.toarray()[0]
        
        # Get top keywords by TF-IDF score
        keyword_scores = list(zip(feature_names, tfidf_scores))
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Extract technical keywords with higher priority
        tech_keywords = _extract_technical_keywords(text)
        
        # Combine technical keywords with TF-IDF keywords
        result_keywords = []
        
        # Add technical keywords first
        for keyword in tech_keywords:
            if keyword not in result_keywords:
                result_keywords.append(keyword)
        
        # Add TF-IDF keywords
        for keyword, score in keyword_scores:
            if keyword not in result_keywords and score > 0:
                result_keywords.append(keyword)
            
            if len(result_keywords) >= max_keywords:
                break
        
        return result_keywords[:max_keywords]
        
    except Exception as e:
        logger.warning(f"Error extracting keywords with NLTK: {e}")
        # Fallback to simple extraction
        return _simple_keyword_extraction(text, max_keywords)

def _extract_technical_keywords(text: str) -> List[str]:
    """Extract technical keywords using regex patterns"""
    tech_patterns = [
        r'\b(?:python|java|javascript|typescript|c\+\+|c#|go|rust|swift|kotlin|scala|ruby|php)\b',
        r'\b(?:react|angular|vue|django|flask|spring|express|fastapi|streamlit|nextjs)\b',
        r'\b(?:aws|azure|gcp|docker|kubernetes|jenkins|git|github|gitlab|terraform)\b',
        r'\b(?:mysql|postgresql|mongodb|redis|elasticsearch|pinecone|snowflake)\b',
        r'\b(?:tensorflow|pytorch|scikit-learn|pandas|numpy|langchain|ollama|openai)\b',
        r'\b(?:html|css|sass|bootstrap|tailwind|material-ui)\b',
        r'\b(?:node\.?js|npm|yarn|webpack|babel|vite)\b',
        r'\b(?:linux|ubuntu|macos|windows|bash|shell)\b',
        r'\b(?:api|rest|graphql|microservices|serverless|rag|llm|ai|ml|nlp|devops|ci/cd)\b'
    ]
    
    tech_keywords = []
    text_lower = text.lower()
    
    for pattern in tech_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        tech_keywords.extend(matches)
    
    return list(set(tech_keywords))  # Remove duplicates

def _simple_keyword_extraction(text: str, max_keywords: int) -> List[str]:
    """Simple fallback keyword extraction"""
    # Remove special characters and split
    clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = clean_text.split()
    
    # Filter words
    filtered_words = [
        word for word in words 
        if len(word) > 2 and word.isalpha()
    ]
    
    # Count frequency
    word_counts = Counter(filtered_words)
    
    # Return most common words
    return [word for word, count in word_counts.most_common(max_keywords)]

def extract_project_names(resume_text: str) -> List[str]:
    """Extract actual project names from resume text with smart filtering"""
    projects = []
    
    if not resume_text:
        return projects
    
    # First, identify potential project sections
    project_sections = _find_project_sections(resume_text)
    
    # Extract projects from identified sections
    for section in project_sections:
        section_projects = _extract_projects_from_section(section)
        projects.extend(section_projects)
    
    # If no clear project sections found, try global patterns
    if not projects:
        projects = _extract_projects_global_fallback(resume_text)
    
    # Clean and validate projects
    cleaned_projects = []
    for project in projects:
        cleaned = _clean_and_validate_project_name(project)
        if cleaned and cleaned not in cleaned_projects:
            cleaned_projects.append(cleaned)
    
    return cleaned_projects[:6]  # Return up to 6 projects

def _find_project_sections(text: str) -> List[str]:
    """Find sections in resume that likely contain projects"""
    sections = []
    
    # Look for project section headers
    project_headers = [
        r'(?:^|\n)\s*(?:PROJECTS?|KEY PROJECTS?|NOTABLE PROJECTS?|PROJECT EXPERIENCE|PERSONAL PROJECTS?)\s*(?:\n|$)',
        r'(?:^|\n)\s*(?:TECHNICAL PROJECTS?|SOFTWARE PROJECTS?|DEVELOPMENT PROJECTS?)\s*(?:\n|$)',
    ]
    
    for header_pattern in project_headers:
        matches = list(re.finditer(header_pattern, text, re.IGNORECASE | re.MULTILINE))
        
        for match in matches:
            start_pos = match.end()
            
            # Find the end of this section (next major section or end of text)
            next_section_pattern = r'(?:\n\s*(?:EXPERIENCE|EDUCATION|SKILLS|CERTIFICATIONS|WORK HISTORY|EMPLOYMENT|ABOUT|SUMMARY)\s*(?:\n|$))'
            next_section = re.search(next_section_pattern, text[start_pos:], re.IGNORECASE | re.MULTILINE)
            
            if next_section:
                end_pos = start_pos + next_section.start()
            else:
                end_pos = len(text)
            
            section_content = text[start_pos:end_pos].strip()
            if len(section_content) > 50:  # Must have substantial content
                sections.append(section_content)
    
    return sections

def _extract_projects_from_section(section_text: str) -> List[str]:
    """Extract project names from a specific project section"""
    projects = []
    
    # Split into potential project blocks
    project_blocks = re.split(r'\n\s*(?=[•·▪▫]|\d+\.|\n)', section_text)
    
    for block in project_blocks:
        block = block.strip()
        if len(block) < 30:  # Too short to be a meaningful project
            continue
        
        # Extract project name from the beginning of the block
        project_name = _extract_project_name_from_block(block)
        if project_name:
            projects.append(project_name)
    
    return projects

def _extract_project_name_from_block(block: str) -> Optional[str]:
    """Extract project name from a project description block"""
    lines = block.split('\n')
    first_line = lines[0].strip()
    
    # Remove bullet points and numbering from first line
    first_line = re.sub(r'^[•·▪▫]\s*', '', first_line)
    first_line = re.sub(r'^\d+\.\s*', '', first_line)
    first_line = first_line.strip()
    
    # Pattern 1: "Project Name: Description" or "Project Name - Description"
    title_desc_match = re.match(r'^([^:\-–—\n]{8,60})(?:\s*[-–—:]\s*)', first_line)
    if title_desc_match:
        project_name = title_desc_match.group(1).strip()
        if _is_valid_project_name(project_name):
            return project_name
    
    # Pattern 2: Bold or emphasized project names
    if re.match(r'^[A-Z][a-zA-Z\s]{5,50}(?:\s|$)', first_line):
        project_name = re.split(r'[-–—:;]', first_line)[0].strip()
        if _is_valid_project_name(project_name):
            return project_name
    
    return None

def _extract_projects_global_fallback(text: str) -> List[str]:
    """Fallback method when no clear project sections are found"""
    projects = []
    
    patterns = [
        r'(?:Built|Developed|Created|Implemented|Designed|Engineered)\s+(?:a\s+|an\s+|the\s+)?([A-Z][^.]{10,60?})\s+(?:using|with|that|to)',
        r'(?:Project|System|Tool|Platform|Application)(?:\s+Name)?[:\s-]+([A-Z][^\n]{8,50}?)(?:\s*[-–—]\s*|\n|$)',
        r'github\.com/[^/]+/([a-zA-Z0-9\-_]{3,30})',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            cleaned = _clean_and_validate_project_name(match)
            if cleaned and cleaned not in projects:
                projects.append(cleaned)
    
    return projects

def _is_valid_project_name(name: str) -> bool:
    """Check if a string is a valid project name"""
    if not name or len(name) < 5 or len(name) > 80:
        return False
    
    # Exclude common non-project phrases
    invalid_starters = [
        'using', 'with', 'in', 'for', 'that', 'to', 'and', 'or', 'but',
        'the', 'a', 'an', 'this', 'these', 'those', 'my', 'our', 'their',
        'experience', 'work', 'job', 'role', 'position', 'responsibilities',
        'skills', 'technologies', 'tools', 'languages', 'frameworks'
    ]
    
    name_lower = name.lower().strip()
    for invalid in invalid_starters:
        if name_lower.startswith(invalid + ' '):
            return False
    
    # Must contain at least one letter
    if not re.search(r'[a-zA-Z]', name):
        return False
    
    # Shouldn't be all caps (likely a section header)
    if name.isupper() and len(name) > 20:
        return False
    
    # Shouldn't be mostly numbers
    if len(re.findall(r'\d', name)) / len(name) > 0.5:
        return False
    
    return True

def _clean_and_validate_project_name(name: str) -> Optional[str]:
    """Clean and validate a project name"""
    if not name:
        return None
    
    # Clean up the name
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
    
    # Remove trailing punctuation
    name = re.sub(r'[.,:;!?]+$', '', name)
    
    # Remove leading/trailing quotes
    name = re.sub(r'^["\']|["\']$', '', name)
    
    if _is_valid_project_name(name):
        return name
    
    return None

def extract_skills_from_text(text: str) -> List[str]:
    """Extract technical skills and keywords from text using NLTK"""
    if not text:
        return []
    
    # Use the main keyword extraction function
    keywords = extract_keywords_from_text(text, max_keywords=20)
    
    # Filter for more technical terms
    technical_terms = _extract_technical_keywords(text)
    
    # Combine and prioritize technical terms
    skills = []
    for term in technical_terms:
        if term not in skills:
            skills.append(term)
    
    for keyword in keywords:
        if keyword not in skills and len(skills) < 20:
            skills.append(keyword)
    
    return skills

def clean_text(text: str) -> str:
    """Clean and normalize text for processing"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', ' ', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def format_score(score: Any) -> int:
    """Convert various score formats to integer 0-100"""
    if isinstance(score, (int, float)):
        return max(0, min(100, int(score)))
    elif isinstance(score, str):
        try:
            # Try to extract number from string
            numbers = re.findall(r'\d+', score)
            if numbers:
                return max(0, min(100, int(numbers[0])))
        except:
            pass
    return 0

def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length while preserving word boundaries"""
    if not text or len(text) <= max_length:
        return text
    
    # Find the last space before max_length
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If we can preserve most of the text
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."

def extract_contact_info(resume_text: str) -> Dict[str, Optional[str]]:
    """Extract contact information from resume text"""
    contact_info = {
        'email': None,
        'phone': None,
        'linkedin': None,
        'github': None
    }
    
    if not resume_text:
        return contact_info
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, resume_text)
    if email_match:
        contact_info['email'] = email_match.group()
    
    # Phone pattern
    phone_pattern = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    phone_match = re.search(phone_pattern, resume_text)
    if phone_match:
        contact_info['phone'] = phone_match.group()
    
    # LinkedIn pattern
    linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/profile/view\?id=)([A-Za-z0-9\-]+)'
    linkedin_match = re.search(linkedin_pattern, resume_text, re.IGNORECASE)
    if linkedin_match:
        contact_info['linkedin'] = linkedin_match.group()
    
    # GitHub pattern
    github_pattern = r'github\.com/([A-Za-z0-9\-]+)'
    github_match = re.search(github_pattern, resume_text, re.IGNORECASE)
    if github_match:
        contact_info['github'] = github_match.group()
    
    return contact_info

def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate if file has allowed extension"""
    if not filename:
        return False
    
    file_extension = filename.lower().split('.')[-1]
    return f".{file_extension}" in [ext.lower() for ext in allowed_extensions]

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.1f}s"

# Usage examples and testing
if __name__ == "__main__":
    # Test the functions
    sample_resume = """
    John Doe
    john.doe@email.com
    (555) 123-4567
    linkedin.com/in/johndoe
    github.com/johndoe
    
    PROJECTS:
    • AI Resume Feedback Tool - Built using Python, LangChain, and Pinecone
    • E-commerce Platform - Developed with React and Node.js
    • Data Analysis Dashboard - Created using Python and Tableau
    """
    
    projects = extract_project_names(sample_resume)
    print(f"Extracted projects: {projects}")
    
    contact = extract_contact_info(sample_resume)
    print(f"Contact info: {contact}")
    
    skills = extract_skills_from_text(sample_resume)
    print(f"Skills found: {skills}")
    
    keywords = extract_keywords_from_text(sample_resume)
    print(f"Keywords: {keywords}")
    
    print(f"Text similarity test: {calculate_similarity_score('python programming', 'python development')}")