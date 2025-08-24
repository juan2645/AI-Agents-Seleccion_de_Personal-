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
            ("system", """Eres un experto en recursos humanos especializado en análisis de CVs.
            Tu tarea es extraer información estructurada de CVs y evaluar la compatibilidad con un perfil de trabajo.
            
            INSTRUCCIONES IMPORTANTES:
            1. Extrae el nombre completo del candidato del CV
            2. Busca el email en el CV (formato: texto@dominio.com)
            3. Calcula los años de experiencia basándote en las fechas de trabajo
            4. Identifica todas las habilidades técnicas mencionadas
            5. Evalúa el match_score de 0-100 basándote en:
               - Experiencia requerida vs experiencia del candidato
               - Habilidades requeridas vs habilidades del candidato
               - Idiomas requeridos vs idiomas del candidato
            
            Responde SOLO con un JSON válido que contenga:
            {
                "name": "Nombre completo extraído del CV",
                "email": "Email encontrado en el CV",
                "phone": "Teléfono si está disponible",
                "experience_years": número calculado de años de experiencia,
                "skills": ["habilidad1", "habilidad2", ...],
                "languages": ["idioma1", "idioma2", ...],
                "education": ["título1", "título2", ...],
                "match_score": puntaje de 0-100,
                "match_reasons": ["razón1", "razón2", ...],
                "mismatch_reasons": ["razón1", "razón2", ...]
            }
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
            
            # Parsear la respuesta JSON
            analysis = json.loads(response.content)
            
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
