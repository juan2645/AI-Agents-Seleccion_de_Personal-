from typing import List, Dict, Any
from src.models import JobProfile, Candidate
from .email_manager import EmailAgent
from .report_generator import ReportAgent
import os, json
import re

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
# Agente de Matching y Scoring
# ------------------------------
class CandidateMatcherAgent:
    """Calcula score y selecciona candidatos"""
    def __init__(self, job_profile: JobProfile):
        self.job_profile = job_profile

    def score_candidate(self, cv_text: str, experience_years: int, languages: List[str]) -> int:
        score = 0
        cv_lower = cv_text.lower()

        # Skills
        for skill in self.job_profile.skills or []:
            if skill and skill.lower() in cv_lower:
                score += 10

        # Idiomas
        req_langs = set([l.strip().lower() for l in (self.job_profile.languages or []) if l.strip()])
        cand_langs = set([l.strip().lower() for l in languages if l.strip()])
        score += 5 * len(req_langs.intersection(cand_langs))

        # Experiencia mínima
        if self.job_profile.experience_years and experience_years:
            try:
                if experience_years >= int(self.job_profile.experience_years):
                    score += 15
            except:
                pass
        return score

    def process(self, candidates: List[Candidate], threshold: int = 30) -> Dict[str, List[Candidate]]:
        for c in candidates:
            c.match_score = self.score_candidate(c.cv_text, c.experience_years, c.languages)
        candidates_sorted = sorted(candidates, key=lambda c: c.match_score, reverse=True)
        selected = [c for c in candidates_sorted if c.match_score >= threshold]
        rejected = [c for c in candidates_sorted if c.match_score < threshold]
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
        # Scoring y selección
        # ------------------------------
        matcher = CandidateMatcherAgent(job_profile)
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
