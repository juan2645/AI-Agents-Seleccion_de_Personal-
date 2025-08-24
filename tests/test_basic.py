import pytest
import os
import sys
from unittest.mock import Mock, patch
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import JobProfile, Candidate, CandidateStatus
from cv_analyzer import CVAnalyzer
from email_manager import EmailManager
from report_generator import ReportGenerator

class TestJobProfile:
    """Tests para el modelo JobProfile"""
    
    def test_job_profile_creation(self):
        """Test creación de perfil de trabajo"""
        job_profile = JobProfile(
            title="Desarrollador Python",
            requirements=["Python", "Django"],
            skills=["Python", "Django", "PostgreSQL"],
            experience_years=3,
            languages=["Español", "Inglés"],
            location="Remoto",
            description="Desarrollador Python para startup"
        )
        
        assert job_profile.title == "Desarrollador Python"
        assert len(job_profile.skills) == 3
        assert job_profile.experience_years == 3
        assert "Español" in job_profile.languages

class TestCandidate:
    """Tests para el modelo Candidate"""
    
    def test_candidate_creation(self):
        """Test creación de candidato"""
        candidate = Candidate(
            id="test_123",
            name="Juan Pérez",
            email="juan@test.com",
            cv_text="CV de prueba",
            experience_years=5,
            skills=["Python", "Django"],
            languages=["Español"],
            education=["Ingeniería"],
            match_score=85.5
        )
        
        assert candidate.name == "Juan Pérez"
        assert candidate.match_score == 85.5
        assert candidate.status == CandidateStatus.PENDING

class TestCVAnalyzer:
    """Tests para el analizador de CVs"""
    
    @patch('cv_analyzer.ChatOpenAI')
    def test_cv_analyzer_initialization(self, mock_llm):
        """Test inicialización del analizador"""
        mock_llm.return_value = Mock()
        
        analyzer = CVAnalyzer("fake_api_key")
        assert analyzer is not None
        assert analyzer.llm is not None
    
    def test_generate_candidate_id(self):
        """Test generación de ID de candidato"""
        analyzer = CVAnalyzer("fake_api_key")
        candidate_id = analyzer._generate_candidate_id("Juan Pérez")
        
        assert "juanperez" in candidate_id
        assert len(candidate_id) > 10
    
    def test_rank_candidates(self):
        """Test ranking de candidatos"""
        analyzer = CVAnalyzer("fake_api_key")
        
        candidates = [
            Candidate(id="1", name="A", email="a@test.com", cv_text="", 
                     experience_years=1, skills=[], languages=[], education=[], match_score=70),
            Candidate(id="2", name="B", email="b@test.com", cv_text="", 
                     experience_years=1, skills=[], languages=[], education=[], match_score=90),
            Candidate(id="3", name="C", email="c@test.com", cv_text="", 
                     experience_years=1, skills=[], languages=[], education=[], match_score=80)
        ]
        
        ranked = analyzer.rank_candidates(candidates, top_n=2)
        
        assert len(ranked) == 2
        assert ranked[0].match_score == 90  # Mayor puntaje primero
        assert ranked[1].match_score == 80
    
    def test_filter_candidates(self):
        """Test filtrado de candidatos"""
        analyzer = CVAnalyzer("fake_api_key")
        
        candidates = [
            Candidate(id="1", name="A", email="a@test.com", cv_text="", 
                     experience_years=1, skills=[], languages=[], education=[], match_score=60),
            Candidate(id="2", name="B", email="b@test.com", cv_text="", 
                     experience_years=1, skills=[], languages=[], education=[], match_score=80),
            Candidate(id="3", name="C", email="c@test.com", cv_text="", 
                     experience_years=1, skills=[], languages=[], education=[], match_score=75)
        ]
        
        filtered = analyzer.filter_candidates(candidates, min_score=70)
        
        assert len(filtered) == 2
        assert all(c.match_score >= 70 for c in filtered)

class TestEmailManager:
    """Tests para el gestor de emails"""
    
    @patch('email_manager.ChatOpenAI')
    def test_email_manager_initialization(self, mock_llm):
        """Test inicialización del gestor de emails"""
        mock_llm.return_value = Mock()
        
        smtp_config = {
            "smtp_server": "smtp.test.com",
            "smtp_port": 587,
            "email_user": "test@test.com",
            "email_password": "password"
        }
        
        email_manager = EmailManager("fake_api_key", smtp_config)
        assert email_manager is not None
        assert email_manager.smtp_config == smtp_config
    
    def test_generate_highlight_reasons(self):
        """Test generación de razones destacadas"""
        email_manager = EmailManager("fake_api_key", {})
        
        # Candidato con alto puntaje
        candidate_high = Candidate(
            id="1", name="Test", email="test@test.com", cv_text="",
            experience_years=5, skills=["Python", "Django", "FastAPI", "PostgreSQL", "Docker"],
            languages=[], education=[], match_score=95
        )
        
        reasons = email_manager._generate_highlight_reasons(candidate_high)
        assert "excelente perfil técnico" in reasons
        assert "amplia experiencia profesional" in reasons
        assert "diversidad de habilidades técnicas" in reasons
        
        # Candidato con puntaje bajo
        candidate_low = Candidate(
            id="2", name="Test2", email="test2@test.com", cv_text="",
            experience_years=1, skills=["Python"], languages=[], education=[], match_score=50
        )
        
        reasons = email_manager._generate_highlight_reasons(candidate_low)
        assert reasons == "tu perfil profesional"

class TestReportGenerator:
    """Tests para el generador de reportes"""
    
    def test_report_generator_initialization(self):
        """Test inicialización del generador de reportes"""
        generator = ReportGenerator()
        assert generator is not None
        assert "summary" in generator.report_templates
        assert "detailed" in generator.report_templates
        assert "excel" in generator.report_templates
    
    def test_calculate_score_distribution(self):
        """Test cálculo de distribución de puntajes"""
        generator = ReportGenerator()
        
        candidates = [
            Candidate(id="1", name="A", email="a@test.com", cv_text="",
                     experience_years=1, skills=[], languages=[], education=[], match_score=95),
            Candidate(id="2", name="B", email="b@test.com", cv_text="",
                     experience_years=1, skills=[], languages=[], education=[], match_score=85),
            Candidate(id="3", name="C", email="c@test.com", cv_text="",
                     experience_years=1, skills=[], languages=[], education=[], match_score=75),
            Candidate(id="4", name="D", email="d@test.com", cv_text="",
                     experience_years=1, skills=[], languages=[], education=[], match_score=55)
        ]
        
        distribution = generator._calculate_score_distribution(candidates)
        
        assert distribution["90-100"] == 1
        assert distribution["80-89"] == 1
        assert distribution["70-79"] == 1
        assert distribution["0-59"] == 1
        assert distribution["60-69"] == 0
    
    def test_generate_recommendations(self):
        """Test generación de recomendaciones"""
        generator = ReportGenerator()
        
        # Caso: sin candidatos seleccionados
        from models import RecruitmentReport, ProcessingState
        
        job_profile = JobProfile(
            title="Test", requirements=[], skills=[], experience_years=1,
            languages=[], location="Test", description="Test"
        )
        
        report_no_selected = RecruitmentReport(
            job_profile=job_profile,
            total_candidates=5,
            selected_candidates=0,
            rejected_candidates=5,
            average_match_score=45.0,
            top_candidates=[],
            processing_time=1.0
        )
        
        recommendations = generator._generate_recommendations(report_no_selected)
        assert any("criterios mínimos" in rec for rec in recommendations)
        
        # Caso: puntaje promedio bajo
        report_low_score = RecruitmentReport(
            job_profile=job_profile,
            total_candidates=5,
            selected_candidates=2,
            rejected_candidates=3,
            average_match_score=45.0,
            top_candidates=[],
            processing_time=1.0
        )
        
        recommendations = generator._generate_recommendations(report_low_score)
        assert any("puntaje promedio es bajo" in rec for rec in recommendations)

def test_integration_basic():
    """Test básico de integración"""
    # Crear perfil de trabajo
    job_profile = JobProfile(
        title="Desarrollador Python",
        requirements=["Python", "Django"],
        skills=["Python", "Django", "PostgreSQL"],
        experience_years=3,
        languages=["Español"],
        location="Remoto",
        description="Test"
    )
    
    # Crear candidatos de prueba
    candidates = [
        Candidate(
            id="1", name="Juan", email="juan@test.com", cv_text="CV de Juan",
            experience_years=5, skills=["Python", "Django"], languages=["Español"],
            education=["Ingeniería"], match_score=85
        ),
        Candidate(
            id="2", name="María", email="maria@test.com", cv_text="CV de María",
            experience_years=2, skills=["Python"], languages=["Español"],
            education=["Licenciatura"], match_score=65
        )
    ]
    
    # Verificar que los datos son consistentes
    assert job_profile.title == "Desarrollador Python"
    assert len(candidates) == 2
    assert candidates[0].match_score > candidates[1].match_score

if __name__ == "__main__":
    pytest.main([__file__])
