from typing import List, Dict, Any
from src.models import JobProfile, Candidate
from .email_manager import EmailAgent
from .report_generator import ReportAgent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import os, json
import re
import uuid

# ------------------------------
# Estado del proceso
# ------------------------------
class ProcessingState:
    def __init__(self):
        self.emails_sent = 0
        self.interviews_scheduled = 0
        self.candidates_processed = 0

# ------------------------------
# Agentes
# ------------------------------
class CVReaderAgent:
    """Extrae información de los CVs"""
    def process(self, cv_texts: List[str]) -> List[Dict[str, Any]]:
        processed = []
        for cv_text in cv_texts:
            processed.append({
                "cv_text": cv_text,
                "name": self.extract_name(cv_text),
                "email": self.extract_email(cv_text),
                "phone": self.extract_phone(cv_text),
                "skills": self.extract_skills(cv_text),
                "education": self.extract_education(cv_text),
                "languages": self.extract_languages(cv_text),
                "experience_years": self.extract_experience_years(cv_text)
            })
        return processed

    # ------------------------------
    # Extractores
    # ------------------------------
    def extract_name(self, text: str) -> str:
        for line in text.splitlines():
            l = line.strip()
            if l:
                return l
        return "Candidato sin nombre"

    def extract_email(self, text: str) -> str:
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        return match.group(0) if match else ""

    def extract_phone(self, text: str) -> str:
        match = re.search(r'\+?\d[\d\s\-\(\)]{7,}', text)
        return match.group(0) if match else ""

    def extract_section(self, text: str, start_label: str, end_labels: List[str]) -> str:
        t = text
        up = t.upper()
        start = up.find(start_label.upper())
        if start == -1:
            return ""
        after = t[start + len(start_label):]
        up_after = up[start + len(start_label):]
        cut_positions = []
        for end in end_labels:
            pos = up_after.find(end.upper())
            if pos != -1:
                cut_positions.append(pos)
        if cut_positions:
            end_pos = min(cut_positions)
            return after[:end_pos].strip()
        else:
            return after.strip()

    def clean_bullets(self, lines: List[str]) -> List[str]:
        cleaned = []
        for l in lines:
            s = l.strip()
            if not s:
                continue
            s = s.lstrip("-•*·").strip()
            if s:
                cleaned.append(s)
        return cleaned

    def extract_skills(self, text: str) -> List[str]:
        section = self.extract_section(text, "HABILIDADES", ["EDUCACIÓN", "IDIOMAS", "EXPERIENCIA", "EXPERIENCIA PROFESIONAL"])
        if not section:
            section = self.extract_section(text, "HABILIDADES TÉCNICAS", ["EDUCACIÓN", "IDIOMAS", "EXPERIENCIA", "EXPERIENCIA PROFESIONAL"])
        lines = [l for l in section.splitlines() if l.strip()]
        if len(lines) == 1 and "," in lines[0]:
            return [s.strip() for s in lines[0].split(",") if s.strip()]
        return self.clean_bullets(lines)

    def extract_education(self, text: str) -> List[str]:
        section = self.extract_section(text, "EDUCACIÓN", ["IDIOMAS", "HABILIDADES", "EXPERIENCIA", "EXPERIENCIA PROFESIONAL"])
        lines = [l for l in section.splitlines() if l.strip()]
        return self.clean_bullets(lines)

    def extract_languages(self, text: str) -> List[str]:
        section = self.extract_section(text, "IDIOMAS", ["EDUCACIÓN", "HABILIDADES", "EXPERIENCIA", "EXPERIENCIA PROFESIONAL"])
        lines = [l for l in section.splitlines() if l.strip()]
        lines = self.clean_bullets(lines)
        if len(lines) == 1:
            parts = re.split(r"[,/•\-–;]| y ", lines[0])
            langs = [p.strip() for p in parts if p.strip()]
            langs = [re.sub(r"\(.*?\)", "", l).strip() for l in langs]
            return [l for l in langs if l]
        return [re.sub(r"\(.*?\)", "", l).strip() for l in lines]

    def extract_experience_years(self, text: str) -> int:
        """
        Extrae los años de experiencia laboral del texto del CV.
        
        Busca rangos de fechas en la sección de experiencia profesional
        y calcula la duración total de experiencia laboral.
        """
        years = 0
        
        # Buscar la sección de experiencia profesional
        experience_section = self.extract_section(text, "EXPERIENCIA PROFESIONAL", 
                                                ["EDUCACIÓN", "IDIOMAS", "HABILIDADES", "FORMACIÓN"])
        
        if not experience_section:
            # Si no encuentra "EXPERIENCIA PROFESIONAL", buscar "EXPERIENCIA"
            experience_section = self.extract_section(text, "EXPERIENCIA", 
                                                    ["EDUCACIÓN", "IDIOMAS", "HABILIDADES", "FORMACIÓN"])
        
        if experience_section:
            # Buscar rangos de años en la sección de experiencia
            ranges = re.findall(r'(\d{4})\s*[-–—]\s*(\d{4})', experience_section)
            for a, b in ranges:
                try:
                    ai = int(a)
                    bi = int(b)
                    # Validar que sea un rango razonable (máximo 50 años)
                    if bi >= ai and (bi - ai) <= 50:
                        years += (bi - ai)
                except:
                    pass
        
        # Si no encontró rangos, buscar menciones explícitas de años
        if years == 0:
            # Buscar en toda la sección de experiencia
            search_text = experience_section if experience_section else text
            m = re.search(r'(\d+)\s*(?:años?|anios?|anos?)\s*(?:de\s*)?(?:experiencia|exp)', search_text.lower())
            if m:
                try:
                    years = int(m.group(1))
                    # Validar que sea un número razonable
                    if years > 50:
                        years = 0
                except:
                    years = 0
        
        # Si aún no encuentra nada, intentar calcular desde el primer trabajo
        if years == 0 and experience_section:
            # Buscar el año más antiguo en la experiencia
            years_found = re.findall(r'\b(19|20)\d{2}\b', experience_section)
            if years_found:
                try:
                    oldest_year = min([int(year) for year in years_found])
                    current_year = 2024
                    years = current_year - oldest_year
                    # Limitar a un máximo razonable
                    if years > 50:
                        years = 0
                except:
                    years = 0
        
        return years

# ------------------------------
# Agente de Matching y Scoring con IA
# ------------------------------
class CandidateMatcherAgent:
    """Analizador de CVs usando LangChain y GPT-4"""
    
    def __init__(self, job_profile: JobProfile, openai_api_key: str):
        self.job_profile = job_profile
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=openai_api_key
        )
        
        self.cv_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un experto en análisis de CVs. Analiza el CV del candidato y responde ÚNICAMENTE con un JSON válido.

INSTRUCCIONES:
1. Extrae la información del CV
2. Calcula un puntaje de 0-100 basado en qué tan bien se ajusta al perfil del trabajo
3. Responde SOLO con el JSON, sin texto adicional

CAMPOS REQUERIDOS:
- name: nombre completo del candidato
- email: email del candidato
- phone: teléfono (si existe, sino "")
- experience_years: años de experiencia laboral (número entero)
- skills: lista de habilidades técnicas encontradas
- languages: lista de idiomas
- education: lista de títulos académicos
- match_score: puntaje de 0-100 (número entero)
- match_reasons: lista de razones por las que califica
- mismatch_reasons: lista de razones por las que no califica

FORMATO JSON EXACTO:
{
  "name": "Nombre Completo",
  "email": "email@ejemplo.com",
  "phone": "teléfono o vacío",
  "experience_years": 3,
  "skills": ["Python", "Django", "PostgreSQL"],
  "languages": ["Español", "Inglés"],
  "education": ["Ingeniería en Sistemas"],
  "match_score": 85,
  "match_reasons": ["Tiene experiencia en Python", "Conoce Django"],
  "mismatch_reasons": ["Falta experiencia en AWS"]
}"""),
            ("human", """PERFIL DEL TRABAJO:
Título: {job_title}
Requisitos: {job_requirements}
Habilidades requeridas: {job_skills}
Años de experiencia requeridos: {job_experience_years}
Idiomas requeridos: {job_languages}

CV DEL CANDIDATO:
{cv_text}

Responde con el JSON de análisis:""")
        ])

    def analyze_cv(self, cv_text: str) -> Candidate:
        """Analiza un CV y retorna un objeto Candidate con IA"""
        
        try:
            # Preparar el prompt con la información del perfil
            prompt_vars = {
                "job_title": self.job_profile.title,
                "job_requirements": ", ".join(self.job_profile.requirements),
                "job_skills": ", ".join(self.job_profile.skills),
                "job_experience_years": str(self.job_profile.experience_years),
                "job_languages": ", ".join(self.job_profile.languages),
                "cv_text": cv_text
            }
            
            # Generar respuesta del LLM
            messages = self.cv_analysis_prompt.format_messages(**prompt_vars)
            response = self.llm.invoke(messages)
            
            print(f"🔍 Analizando CV con IA...")
            
            # Limpiar la respuesta para extraer solo el JSON
            content = response.content.strip()
            print(f"📝 Respuesta del LLM: {content[:200]}...")
            
            # Buscar el JSON en la respuesta
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No se encontró JSON válido en la respuesta")
            
            json_str = content[start_idx:end_idx]
            print(f"🔍 JSON extraído: {json_str[:200]}...")
            
            # Limpiar el JSON de caracteres problemáticos
            json_str = json_str.replace('\n', '').replace('\r', '').strip()
            
            # Intentar parsear la respuesta JSON
            try:
                analysis = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"⚠️ Error parseando JSON: {e}")
                # Intentar con una limpieza más agresiva
                import re
                # Remover caracteres no válidos para JSON
                json_str = re.sub(r'[^\x20-\x7E]', '', json_str)
                analysis = json.loads(json_str)
            
            # Validar que todos los campos requeridos estén presentes
            required_fields = ["name", "email", "experience_years", "skills", "languages", "education", "match_score", "match_reasons", "mismatch_reasons"]
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = "" if field in ["phone"] else [] if field in ["skills", "languages", "education", "match_reasons", "mismatch_reasons"] else 0
            
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
            print(f"❌ Error en análisis IA: {str(e)}")
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
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
        return f"{clean_name}_{str(uuid.uuid4())[:8]}"
    
    def process(self, candidates: List[Candidate], threshold: float = 70.0) -> Dict[str, List[Candidate]]:
        """Procesa candidatos con análisis IA y los clasifica"""
        print(f"🤖 Procesando {len(candidates)} candidatos con IA...")
        
        # Analizar cada candidato con IA
        analyzed_candidates = []
        for i, candidate in enumerate(candidates, 1):
            print(f"  📊 Analizando candidato {i}/{len(candidates)}: {candidate.name}")
            analyzed_candidate = self.analyze_cv(candidate.cv_text)
            analyzed_candidates.append(analyzed_candidate)
        
        # Ordenar por puntaje de match
        candidates_sorted = sorted(analyzed_candidates, key=lambda c: c.match_score, reverse=True)
        
        # Clasificar en seleccionados y rechazados
        selected = [c for c in candidates_sorted if c.match_score >= threshold]
        rejected = [c for c in candidates_sorted if c.match_score < threshold]
        
        print(f"✅ Análisis completado: {len(selected)} seleccionados, {len(rejected)} rechazados")
        
        return {"all": candidates_sorted, "selected": selected, "rejected": rejected}

# ------------------------------
# Workflow principal
# ------------------------------
class HRWorkflowAgent:
    def __init__(self, openai_api_key: str, smtp_config: Dict[str, Any], calendar_config: Dict[str, Any] = None):
        self.openai_api_key = openai_api_key
        self.smtp_config = smtp_config
        self.calendar_config = calendar_config
        self._id_counter = 1
        self.cv_agent = CVReaderAgent()
        self.email_manager = EmailAgent(openai_api_key, smtp_config)
        self.report_agent = ReportAgent()

    def _next_id(self) -> int:
        val = self._id_counter
        self._id_counter += 1
        return val

    def run_workflow(self, job_profile: JobProfile, cv_texts: List[str]) -> Dict[str, Any]:
        processing_state = ProcessingState()

        # ------------------------------
        # Extracción de CVs
        # ------------------------------
        raw_candidates = self.cv_agent.process(cv_texts)
        candidates: List[Candidate] = []
        for rc in raw_candidates:
            candidate = Candidate(
                id=str(self._next_id()),
                name=rc["name"],
                email=rc["email"],
                phone=rc["phone"],
                cv_text=rc["cv_text"],
                skills=rc["skills"],
                experience_years=rc["experience_years"],
                languages=rc["languages"],
                education=rc["education"],
                match_score=0
            )
            candidates.append(candidate)
            processing_state.candidates_processed += 1

        # ------------------------------
        # Scoring y selección con IA
        # ------------------------------
        matcher = CandidateMatcherAgent(job_profile, self.openai_api_key)
        matched = matcher.process(candidates)

        # ------------------------------
        # Envío de emails
        # ------------------------------
        email_results = self.email_manager.send_bulk_emails(
            matched["selected"], template_type="selected", job_title=job_profile.title
        )
        processing_state.emails_sent = sum(email_results.values())

        # ------------------------------
        # Generación de reportes
        # ------------------------------
        os.makedirs("reports", exist_ok=True)
        report = self.report_agent.generate_report(matched["all"], job_profile, processing_state)

        # TXT
        summary = self.report_agent._generate_summary_report(report)
        with open("reports/reporte_resumen.txt", "w", encoding="utf-8") as f:
            f.write(summary)

        # JSON
        detailed = self.report_agent._generate_detailed_report(report)
        with open("reports/reporte_detallado.json", "w", encoding="utf-8") as f:
            json.dump(detailed, f, ensure_ascii=False, indent=4)

        # Excel
        excel_file = self.report_agent._generate_excel_report(report)

        return {
            "candidates": matched["all"],
            "selected_candidates": matched["selected"],
            "rejected_candidates": matched["rejected"],
            "processing_state": processing_state,
            "report_files": {
                "summary": "reports/reporte_resumen.txt",
                "detailed": "reports/reporte_detallado.json",
                "excel": excel_file
            }
        }
