"""
LLM pipeline using LangChain and Ollama for structured resume analysis
Handles prompt templating, chain creation, and response parsing
"""

import json
import logging
from typing import Dict, List, Optional, Any
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import BaseOutputParser
from config.settings import OLLAMA_BASE_URL, MODEL_NAME, TEMPERATURE, MAX_TOKENS
from config.prompts import (
    RESUME_ANALYSIS_PROMPT,
    PROJECT_MATCHING_PROMPT,
    KEYWORD_EXTRACTION_PROMPT,
    PROJECT_PHRASING_PROMPT,
    SECTION_EVALUATION_PROMPT,
    SYSTEM_MESSAGE
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONOutputParser(BaseOutputParser):
    """Custom parser to extract JSON from LLM responses"""
    
    def parse(self, text: str) -> Dict:
        """Parse JSON from LLM response, handling common formatting issues"""
        try:
            # Remove markdown code blocks if present
            text = text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            
            # Find JSON content between braces
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_text = text[start_idx:end_idx + 1]
                parsed = json.loads(json_text)
                return parsed
            
            # Clean up common issues and try again
            text = text.strip()
            
            # Parse JSON
            parsed = json.loads(text)
            return parsed
        
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            logger.warning(f"Raw response: {text[:500]}...")
            
            # Try to extract score manually if JSON fails
            score_match = re.search(r'"overall_score":\s*(\d+)', text)
            if score_match:
                overall_score = int(score_match.group(1))
                logger.info(f"Extracted overall score from failed JSON: {overall_score}")
                
                return {
                    "overall_score": overall_score,
                    "clarity": {"score": overall_score - 5, "feedback": "Analysis completed but JSON parsing failed", "suggestions": []},
                    "role_alignment": {"score": overall_score, "feedback": "See raw response in logs", "suggestions": []},
                    "tone": {"score": overall_score - 10, "feedback": "Professional tone maintained", "suggestions": []},
                    "json_parse_error": True,
                    "raw_response": text[:1000]
                }
            
            # Return a default structure based on the response type
            if "overall_score" in text:
                return {"error": "JSON parsing failed", "raw_response": text, "type": "resume_analysis"}
            elif "better_matches" in text:
                return {"error": "JSON parsing failed", "raw_response": text, "type": "project_matching"}
            else:
                return {"error": "JSON parsing failed", "raw_response": text, "type": "unknown"}

class LLMPipeline:
    """Manages LLM interactions for resume analysis tasks"""
    
    def __init__(self):
        # Initialize Ollama LLM
        self.llm = OllamaLLM(
            base_url=OLLAMA_BASE_URL,
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            num_ctx=MAX_TOKENS,
            system=SYSTEM_MESSAGE
        )
        
        # Initialize output parser
        self.json_parser = JSONOutputParser()
        
        # Create chains for different tasks
        self._setup_chains()
        
        logger.info(f"LLM pipeline initialized with model: {MODEL_NAME}")
    
    def _setup_chains(self):
        """Setup LangChain chains for different analysis tasks"""
        
        # Resume Analysis Chain (using new syntax)
        self.resume_analysis_prompt = PromptTemplate(
            input_variables=["resume_content", "job_description"],
            template=RESUME_ANALYSIS_PROMPT
        )
        self.resume_analysis_chain = self.resume_analysis_prompt | self.llm | self.json_parser
        
        # Project Matching Chain
        self.project_matching_prompt = PromptTemplate(
            input_variables=["current_projects", "alternative_projects", "job_requirements"],
            template=PROJECT_MATCHING_PROMPT
        )
        self.project_matching_chain = self.project_matching_prompt | self.llm | self.json_parser
        
        # Keyword Extraction Chain
        self.keyword_extraction_prompt = PromptTemplate(
            input_variables=["job_description", "current_keywords"],
            template=KEYWORD_EXTRACTION_PROMPT
        )
        self.keyword_extraction_chain = self.keyword_extraction_prompt | self.llm | self.json_parser
        
        # Project Phrasing Chain
        self.project_phrasing_prompt = PromptTemplate(
            input_variables=["projects_to_improve", "target_keywords", "job_context"],
            template=PROJECT_PHRASING_PROMPT
        )
        self.project_phrasing_chain = self.project_phrasing_prompt | self.llm | self.json_parser
        
        # Section Evaluation Chain
        self.section_evaluation_prompt = PromptTemplate(
            input_variables=["section_type", "section_content", "job_requirements"],
            template=SECTION_EVALUATION_PROMPT
        )
        self.section_evaluation_chain = self.section_evaluation_prompt | self.llm | self.json_parser
    
    def analyze_resume(self, resume_content: str, job_description: str) -> Dict:
        """Perform comprehensive resume analysis"""
        try:
            logger.info("Starting resume analysis...")
            
            # Truncate content if too long to fit context window
            max_resume_length = 3000
            max_job_length = 1000
            
            if len(resume_content) > max_resume_length:
                resume_content = resume_content[:max_resume_length] + "..."
                logger.warning("Resume content truncated to fit context window")
            
            if len(job_description) > max_job_length:
                job_description = job_description[:max_job_length] + "..."
                logger.warning("Job description truncated to fit context window")
            
            # Run analysis using new chain syntax
            result = self.resume_analysis_chain.invoke({
                "resume_content": resume_content,
                "job_description": job_description
            })
            
            logger.info("Resume analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in resume analysis: {e}")
            return {
                "error": str(e),
                "overall_score": 0,
                "clarity": {"score": 0, "feedback": "Analysis failed", "suggestions": []},
                "role_alignment": {"score": 0, "feedback": "Analysis failed", "suggestions": []},
                "tone": {"score": 0, "feedback": "Analysis failed", "suggestions": []}
            }
    
    def find_better_project_matches(self, current_projects: List[str], alternative_projects: List[Dict], job_requirements: str) -> Dict:
        """Find better project matches from portfolio"""
        try:
            logger.info("Analyzing project matches...")
            
            # Format current projects
            current_projects_text = "\n".join([f"- {project}" for project in current_projects])
            
            # Format alternative projects
            alternative_projects_text = "\n".join([
                f"- {proj['project_name']}: {proj['description'][:200]}..."
                for proj in alternative_projects
            ])
            
            # Truncate if too long
            if len(alternative_projects_text) > 2000:
                alternative_projects_text = alternative_projects_text[:2000] + "..."
            
            result = self.project_matching_chain.invoke({
                "current_projects": current_projects_text,
                "alternative_projects": alternative_projects_text,
                "job_requirements": job_requirements[:1000]
            })
            
            logger.info("Project matching analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in project matching: {e}")
            return {"error": str(e), "better_matches": []}
    
    def extract_missing_keywords(self, job_description: str, current_keywords: List[str]) -> Dict:
        """Extract keywords missing from resume"""
        try:
            logger.info("Extracting missing keywords...")
            
            current_keywords_text = ", ".join(current_keywords)
            
            result = self.keyword_extraction_chain.invoke({
                "job_description": job_description[:1500],
                "current_keywords": current_keywords_text
            })
            
            logger.info("Keyword extraction completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in keyword extraction: {e}")
            return {"error": str(e), "missing_keywords": [], "keyword_density_issues": []}
    
    def improve_project_phrasing(self, projects: List[str], keywords: List[str], job_context: str) -> Dict:
        """Improve phrasing of top 3 projects"""
        try:
            logger.info("Improving project phrasing...")
            
            # Take only top 3 projects
            top_projects = projects[:3]
            projects_text = "\n".join([f"{i+1}. {project}" for i, project in enumerate(top_projects)])
            keywords_text = ", ".join(keywords[:10])  # Limit keywords
            
            result = self.project_phrasing_chain.invoke({
                "projects_to_improve": projects_text,
                "target_keywords": keywords_text,
                "job_context": job_context[:800]
            })
            
            logger.info("Project phrasing improvement completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in project phrasing: {e}")
            return {"error": str(e), "improved_projects": []}
    
    def evaluate_resume_section(self, section_type: str, section_content: str, job_requirements: str) -> Dict:
        """Evaluate a specific resume section"""
        try:
            logger.info(f"Evaluating {section_type} section...")
            
            result = self.section_evaluation_chain.invoke({
                "section_type": section_type,
                "section_content": section_content[:1000],
                "job_requirements": job_requirements[:800]
            })
            
            logger.info(f"Section evaluation completed for {section_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating section {section_type}: {e}")
            return {
                "error": str(e),
                "section_scores": {
                    "relevance": {"score": 0, "feedback": "Evaluation failed"},
                    "formatting": {"score": 0, "feedback": "Evaluation failed"},
                    "keywords": {"score": 0, "feedback": "Evaluation failed"},
                    "impact": {"score": 0, "feedback": "Evaluation failed"}
                },
                "improvement_suggestions": []
            }
    
    def test_connection(self) -> bool:
        """Test if LLM connection is working"""
        try:
            test_response = self.llm.invoke("Say 'Connection successful' if you can read this.")
            logger.info(f"LLM test response: {test_response}")
            return "successful" in test_response.lower()
        except Exception as e:
            logger.error(f"LLM connection test failed: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            "model_name": MODEL_NAME,
            "base_url": OLLAMA_BASE_URL,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS
        }

# Utility functions for common operations
def extract_keywords_from_text(text: str) -> List[str]:
    """Simple keyword extraction from text (fallback method)"""
    import re
    from collections import Counter
    
    # Simple keyword extraction logic
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had'}
    
    keywords = [word for word in words if len(word) > 3 and word not in stop_words]
    
    # Return most common words
    return [word for word, count in Counter(keywords).most_common(20)]

# Usage example and testing
if __name__ == "__main__":
    # Test LLM pipeline
    try:
        pipeline = LLMPipeline()
        
        if pipeline.test_connection():
            print("✅ LLM pipeline initialized and connected successfully")
            print(f"Model info: {pipeline.get_model_info()}")
        else:
            print("❌ LLM connection test failed")
            
    except Exception as e:
        print(f"❌ Error initializing LLM pipeline: {e}")
        print("Make sure Ollama is running and llama3 model is installed")