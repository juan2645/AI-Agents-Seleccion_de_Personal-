#!/usr/bin/env python3
"""
Script de prueba para verificar el análisis de CVs
"""

import os
from dotenv import load_dotenv
from src.cv_analyzer import CandidateMatcherAgent
from src.models import JobProfile

# Cargar variables de entorno
load_dotenv()

def test_cv_analysis():
    """Prueba el análisis de un CV"""
    
    # Verificar API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY no configurada")
        return
    
    print("✅ API Key configurada")
    
    # Crear perfil de trabajo de ejemplo
    job_profile = JobProfile(
        title="Desarrollador Python Senior",
        requirements=[
            "Experiencia mínima de 2 años en desarrollo Python",
            "Conocimientos sólidos en APIs REST",
            "Conocimientos de bases de datos SQL y NoSQL",
            "Experiencia con Docker y CI/CD"
        ],
        skills=["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "Git", "AWS"],
        experience_years=5,
        languages=["Español", "Inglés"],
        location="Remoto",
        salary_range="$3000 - $5000 USD",
        description="Buscamos un desarrollador Python senior para unirse a nuestro equipo de desarrollo."
    )
    
    # CV de ejemplo
    cv_text = """
    CARLOS RODRÍGUEZ
    Email: juan2645@gmail.com
    Teléfono: +54 11 5555-1234
    
    EXPERIENCIA PROFESIONAL:
    - Desarrollador Python en DataTech (2022-2024)
      * Análisis de datos con Python y pandas
      * Desarrollo de scripts de automatización
      * Experiencia básica con APIs
    
    - Analista de Datos en AnalyticsCorp (2020-2022)
      * Procesamiento de datos con Python
      * Creación de reportes y dashboards
    
    HABILIDADES TÉCNICAS:
    - Python, pandas, numpy, matplotlib, SQL
    - Jupyter Notebooks, Excel
    
    EDUCACIÓN:
    - Licenciatura en Estadística, Universidad de Córdoba (2020)
    
    IDIOMAS:
    - Español (Nativo)
    - Inglés (Básico)
    """
    
    print("🔍 Iniciando análisis de CV...")
    print(f"📄 CV: {cv_text[:100]}...")
    
    # Crear analizador
    analyzer = CandidateMatcherAgent(api_key)
    
    try:
        # Analizar CV
        candidate = analyzer.analyze_cv(cv_text, job_profile)
        
        print("\n✅ ANÁLISIS COMPLETADO:")
        print(f"Nombre: {candidate.name}")
        print(f"Email: {candidate.email}")
        print(f"Teléfono: {candidate.phone}")
        print(f"Experiencia: {candidate.experience_years} años")
        print(f"Habilidades: {candidate.skills}")
        print(f"Idiomas: {candidate.languages}")
        print(f"Puntaje: {candidate.match_score}/100")
        print(f"Notas: {candidate.notes}")
        
    except Exception as e:
        print(f"❌ Error en análisis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cv_analysis()
