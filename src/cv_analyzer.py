from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict, Any
import json
import re
from .models import Candidate, JobProfile, CandidateStatus

class CVAnalyzer:
    """Analizador de CVs usando LangChain"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=openai_api_key
        )
        
        self.cv_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Analiza el CV y responde SOLO con un JSON válido. Extrae:
            - name: nombre del candidato
            - email: email del candidato  
            - phone: teléfono si existe
            - experience_years: años de experiencia calculados
            - skills: lista de habilidades técnicas
            - languages: idiomas que habla
            - education: títulos académicos
            - match_score: puntaje de 0-100
            - match_reasons: razones por las que califica
            - mismatch_reasons: razones por las que no califica
            
            Formato JSON requerido:
            {"name": "Nombre", "email": "email@ejemplo.com", "phone": "teléfono", "experience_years": 2, "skills": ["Python"], "languages": ["Español"], "education": ["Título"], "match_score": 75, "match_reasons": ["Tiene Python"], "mismatch_reasons": ["Falta experiencia"]}
            """),
            ("human", """
            Perfil del trabajo:
            Título: {job_title}
            Requisitos: {job_requirements}
            Habilidades requeridas: {job_skills}
            Años de experiencia: {job_experience_years}
            Idiomas: {job_languages}
            
            CV del candidato:
            {cv_text}
            """)
        ])
    
    def analyze_cv(self, cv_text: str, job_profile: JobProfile) -> Candidate:
        """Analiza un CV y retorna un objeto Candidate"""
        
        try:
            # Preparar el prompt con la información del perfil
            prompt_vars = {
                "job_title": job_profile.title,
                "job_requirements": ", ".join(job_profile.requirements),
                "job_skills": ", ".join(job_profile.skills),
                "job_experience_years": str(job_profile.experience_years),
                "job_languages": ", ".join(job_profile.languages),
                "cv_text": cv_text
            }
            
            # Generar respuesta del LLM
            messages = self.cv_analysis_prompt.format_messages(**prompt_vars)
            response = self.llm.invoke(messages)
            
            print(f"🔍 Respuesta del LLM: {response.content[:200]}...")
            
            # Limpiar la respuesta para extraer solo el JSON
            content = response.content.strip()
            
            # Buscar el JSON en la respuesta
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No se encontró JSON válido en la respuesta")
            
            json_str = content[start_idx:end_idx]
            print(f"🔍 JSON extraído: {json_str[:200]}...")
            
            # Parsear la respuesta JSON
            analysis = json.loads(json_str)
            
            # Crear objeto Candidate
            candidate = Candidate(
                id=self._generate_candidate_id(analysis["name"]),
                name=analysis["name"],
                email=analysis["email"],
                phone=analysis.get("phone"),
                cv_text=cv_text,
                experience_years=analysis["experience_years"],
                skills=analysis["skills"],
                languages=analysis["languages"],
                education=analysis["education"],
                match_score=analysis["match_score"],
                notes=f"Razones de match: {', '.join(analysis['match_reasons'])}. "
                      f"Razones de no match: {', '.join(analysis['mismatch_reasons'])}"
            )
            
            return candidate
            
        except Exception as e:
            # En caso de error, crear un candidato básico
            return Candidate(
                id=self._generate_candidate_id("Unknown"),
                name="Unknown",
                email="unknown@example.com",
                cv_text=cv_text,
                experience_years=0,
                skills=[],
                languages=[],
                education=[],
                match_score=0.0,
                notes=f"Error en análisis: {str(e)}"
            )
    
    def _generate_candidate_id(self, name: str) -> str:
        """Genera un ID único para el candidato"""
        import uuid
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
        return f"{clean_name}_{str(uuid.uuid4())[:8]}"
    
    def rank_candidates(self, candidates: List[Candidate], top_n: int = 10) -> List[Candidate]:
        """Rankea candidatos por puntaje de match"""
        sorted_candidates = sorted(candidates, key=lambda x: x.match_score, reverse=True)
        return sorted_candidates[:top_n]
    
    def filter_candidates(self, candidates: List[Candidate], min_score: float = 70.0) -> List[Candidate]:
        """Filtra candidatos por puntaje mínimo"""
        return [c for c in candidates if c.match_score >= min_score]
