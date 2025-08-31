# src/hr_workflow.py
from typing import List, Dict, Any
from src.models import JobProfile, Candidate
from .email_manager import EmailAgent
import re

class ProcessingState:
    def __init__(self):
        self.emails_sent = 0
        self.interviews_scheduled = 0
        self.candidates_processed = 0

class HRWorkflowAgent:
    def __init__(self, openai_api_key: str, smtp_config: Dict[str, Any], calendar_config: Dict[str, Any] = None):
        self.openai_api_key = openai_api_key
        self.smtp_config = smtp_config
        self.calendar_config = calendar_config
        self._id_counter = 1
        self.email_manager = EmailAgent(openai_api_key, smtp_config)

    # ------------------------------
    # Scoring
    # ------------------------------
    def score_candidate(self, cv_text: str, job_profile: JobProfile, experience_years: int, languages: List[str]) -> int:
        score = 0
        cv_lower = cv_text.lower()

        # Skills
        for skill in job_profile.skills or []:
            if skill and skill.lower() in cv_lower:
                score += 10

        # Idiomas
        req_langs = set([l.strip().lower() for l in (job_profile.languages or []) if l.strip()])
        cand_langs = set([l.strip().lower() for l in languages if l.strip()])
        score += 5 * len(req_langs.intersection(cand_langs))

        # Experiencia mínima
        if job_profile.experience_years and experience_years:
            try:
                if experience_years >= int(job_profile.experience_years):
                    score += 15
            except:
                pass

        return score

    # ------------------------------
    # Workflow principal
    # ------------------------------
    def run_workflow(self, job_profile: JobProfile, cv_texts: List[str]) -> Dict[str, Any]:
        processing_state = ProcessingState()
        candidates: List[Candidate] = []

        for cv_text in cv_texts:
            processing_state.candidates_processed += 1

            # Extracciones
            name = self.extract_name(cv_text)
            email = self.extract_email(cv_text)
            phone = self.extract_phone(cv_text)
            skills = self.extract_skills(cv_text)
            education = self.extract_education(cv_text)
            languages = self.extract_languages(cv_text)
            experience_years = self.extract_experience_years(cv_text)

            # Score
            score = self.score_candidate(cv_text, job_profile, experience_years, languages)

            candidate = Candidate(
                id=str(self._next_id()),
                name=name,
                email=email,
                phone=phone,
                cv_text=cv_text,
                skills=skills,
                experience_years=experience_years,
                languages=languages,
                education=education,
                match_score=score
            )

            candidates.append(candidate)

        # Ordenar por score descendente
        candidates = sorted(candidates, key=lambda c: c.match_score, reverse=True)

        # Selección por umbral
        threshold = 30
        selected_candidates = [c for c in candidates if c.match_score >= threshold]
        rejected_candidates = [c for c in candidates if c.match_score < threshold]

        # Enviar emails a seleccionados
        email_results = self.email_manager.send_bulk_emails(
            selected_candidates, template_type="selected", job_title=job_profile.title
        )
        processing_state.emails_sent = sum(email_results.values())

        return {
            "candidates": candidates,
            "selected_candidates": selected_candidates,
            "rejected_candidates": rejected_candidates,
            "processing_state": processing_state
        }

    def _next_id(self) -> int:
        val = self._id_counter
        self._id_counter += 1
        return val

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
        years = 0
        ranges = re.findall(r'(\d{4})\s*[-–—]\s*(\d{4})', text)
        for a, b in ranges:
            try:
                ai = int(a)
                bi = int(b)
                if bi >= ai:
                    years += (bi - ai)
            except:
                pass
        if years == 0:
            m = re.search(r'(\d+)\s*(?:años|anios|anos)', text.lower())
            if m:
                try:
                    years = int(m.group(1))
                except:
                    years = 0
        return years
