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
            
            INSTRUCCIONES CRÍTICAS:
            1. NOMBRE: Busca el nombre completo al inicio del CV (ej: "CARLOS RODRÍGUEZ")
            2. EMAIL: Busca el email después de "Email:" (ej: "juan2645@gmail.com")
            3. TELÉFONO: Busca el teléfono después de "Teléfono:" o "Phone:"
            4. EXPERIENCIA: Suma los años de experiencia basándote en las fechas (ej: 2022-2024 = 2 años)
            5. HABILIDADES: Extrae todas las tecnologías mencionadas (Python, Django, etc.)
            6. IDIOMAS: Busca idiomas mencionados (Español, Inglés, etc.)
            7. EDUCACIÓN: Extrae títulos académicos mencionados
            
            EVALUACIÓN DE MATCH (0-100):
            - +20 puntos por cada año de experiencia relevante
            - +15 puntos por cada habilidad requerida que tenga
            - +10 puntos por cada idioma requerido que hable
            - -10 puntos por falta de experiencia requerida
            - -5 puntos por cada habilidad requerida que falte
            
            Responde ÚNICAMENTE con un JSON válido:
            {
                "name": "Nombre extraído del CV",
                "email": "Email encontrado",
                "phone": "Teléfono si existe",
                "experience_years": número de años,
                "skills": ["habilidad1", "habilidad2"],
                "languages": ["idioma1", "idioma2"],
                "education": ["título1"],
                "match_score": número de 0-100,
                "match_reasons": ["razón1", "razón2"],
                "mismatch_reasons": ["razón1", "razón2"]
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
