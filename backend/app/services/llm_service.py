import os
import json
from groq import Groq
import ollama
from typing import List, Dict


class LLMService:
    def __init__(self, provider: str = None):
        # Use provider from parameter, env var, or default to groq
        self.provider = provider or os.getenv("LLM_PROVIDER", "groq")
        
        # Initialize both clients
        if self.provider == "groq":
            self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            self.groq_model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        else:  # ollama
            self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    
    def _call_llm(self, prompt: str, system_prompt: str) -> str:
        """Call LLM based on provider."""
        if self.provider == "groq":
            return self._call_groq(prompt, system_prompt)
        else:
            return self._call_ollama(prompt, system_prompt)
    
    def _call_groq(self, prompt: str, system_prompt: str) -> str:
        """Call Groq API."""
        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq error: {e}")
            raise Exception(f"Groq API error: {str(e)}. Make sure GROQ_API_KEY is set in .env")
    
    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        """Call Ollama API."""
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response['message']['content']
        except Exception as e:
            print(f"Ollama error: {e}")
            raise Exception(f"Ollama API error: {str(e)}. Make sure Ollama is running with 'ollama run llama3'")
    
    def _extract_json(self, response: str) -> dict:
        """Extract JSON from response, handling markdown code blocks."""
        response = response.strip()
        
        # Remove markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        response = response.strip()
        
        # Try to parse
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON. Response was: {response[:500]}")
            raise Exception(f"LLM returned invalid JSON: {str(e)}")
    
    def analyze_resume(self, resume_text: str, job_description: str) -> Dict:
        """Comprehensive resume analysis."""
        system_prompt = "You are an expert resume analyst. You MUST respond with ONLY valid JSON, no other text."
        
        prompt = f"""Analyze this resume against the job description.

Resume (first 2000 chars):
{resume_text[:2000]}

Job Description (first 1500 chars):
{job_description[:1500]}

Respond with ONLY this JSON structure (no markdown, no explanation):
{{
    "overall_score": 75,
    "clarity_score": 80,
    "alignment_score": 70,
    "tone_score": 75,
    "clarity_feedback": "Resume is well-structured and easy to read.",
    "alignment_feedback": "Skills match 70% of job requirements.",
    "tone_feedback": "Professional tone maintained throughout.",
    "professional_feedback": "Focus on quantifying achievements and adding relevant keywords.",
    "matched_keywords": ["Python", "FastAPI", "React"],
    "missing_keywords": [
        {{"keyword": "Docker", "priority": "high", "context": "Required for deployment"}},
        {{"keyword": "AWS", "priority": "medium", "context": "Cloud platform experience"}}
    ]
}}"""

        response = self._call_llm(prompt, system_prompt)
        return self._extract_json(response)
    
    def rank_projects(self, projects: List[Dict], job_description: str) -> Dict:
        """Rank projects by relevance to job description."""
        system_prompt = "You are an expert at matching projects to jobs. Respond with ONLY valid JSON."
        
        projects_text = "\n\n".join([
            f"Project: {p['title']}\nTech: {', '.join(p.get('technologies', []))}\nDesc: {p.get('description', '')[:200]}"
            for p in projects[:10]
        ])
        
        prompt = f"""Rank these projects by relevance to the job.

Projects:
{projects_text}

Job (first 1000 chars):
{job_description[:1000]}

Respond with ONLY this JSON (no markdown):
{{
    "rankings": [
        {{"title": "Project 1", "relevance_score": 85, "reason": "Matches key skills"}},
        {{"title": "Project 2", "relevance_score": 70, "reason": "Related domain"}}
    ],
    "recommended_projects": ["Project 1", "Project 2", "Project 3"]
}}"""

        response = self._call_llm(prompt, system_prompt)
        return self._extract_json(response)
    
    def enhance_description(self, description: str, job_context: str) -> Dict:
        """Enhance project description."""
        system_prompt = "You are a resume writer. Respond with ONLY valid JSON."
        
        prompt = f"""Improve this description for the job context.

Description: {description[:500]}
Job Context: {job_context[:500]}

Respond with ONLY this JSON (no markdown):
{{
    "enhanced": "Improved description here with action verbs and metrics",
    "improvements": ["Added metrics", "Stronger verbs", "Relevant keywords"]
}}"""

        response = self._call_llm(prompt, system_prompt)
        return self._extract_json(response)
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        system_prompt = "You extract technical keywords. Respond with ONLY valid JSON."
        
        prompt = f"""Extract technical keywords from this text.

Text: {text[:1500]}

Respond with ONLY this JSON (no markdown): {{"keywords": ["keyword1", "keyword2"]}}"""

        response = self._call_llm(prompt, system_prompt)
        result = self._extract_json(response)
        return result.get("keywords", [])