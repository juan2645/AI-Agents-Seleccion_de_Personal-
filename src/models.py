from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class CandidateStatus(str, Enum):
    PENDING = "pending"
    SELECTED = "selected"
    REJECTED = "rejected"
    INTERVIEW_SCHEDULED = "interview_scheduled"

class JobProfile(BaseModel):
    """Perfil del puesto de trabajo"""
    title: str
    requirements: List[str]
    skills: List[str]
    experience_years: int
    languages: List[str]
    location: str
    salary_range: Optional[str] = None
    description: str

class Candidate(BaseModel):
    """Información del candidato"""
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    cv_text: str
    experience_years: int
    skills: List[str]
    languages: List[str]
    education: List[str]
    match_score: float = Field(ge=0, le=100)
    status: CandidateStatus = CandidateStatus.PENDING
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class EmailTemplate(BaseModel):
    """Plantilla de email"""
    subject: str
    body: str
    template_type: str  # "selected", "rejected", "interview_invitation"

class InterviewSchedule(BaseModel):
    """Programación de entrevista"""
    candidate_id: str
    date: datetime
    duration_minutes: int = 60
    interview_type: str = "technical"  # "technical", "hr", "final"
    interviewer: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class RecruitmentReport(BaseModel):
    """Reporte de reclutamiento"""
    job_profile: JobProfile
    total_candidates: int
    selected_candidates: int
    rejected_candidates: int
    average_match_score: float
    top_candidates: List[Candidate]
    processing_time: float
    generated_at: datetime = Field(default_factory=datetime.now)

class ProcessingState(BaseModel):
    """Estado del procesamiento"""
    current_step: str
    total_steps: int
    candidates_processed: int
    emails_sent: int
    interviews_scheduled: int
    errors: List[str] = Field(default_factory=list)
