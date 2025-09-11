#!/usr/bin/env python3
"""
Script de prueba para verificar el procesamiento de CVs
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio src al path
sys.path.append('src')

from src.models import JobProfile
from src.hr_workflow import HRWorkflowAgent

def test_cv_processing():
    """Prueba el procesamiento de CVs"""
    
    # Verificar que la API key esté configurada
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY no está configurada en el archivo .env")
        return False
    
    print("✅ API Key de OpenAI configurada")
    
    # Configuración SMTP
    smtp_config = {
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "email_user": os.getenv("EMAIL_USER", ""),
        "email_password": os.getenv("EMAIL_PASSWORD", "")
    }
    
    # Crear perfil de trabajo de prueba
    job_profile = JobProfile(
        title="Desarrollador Python",
        requirements=[
            "Experiencia en Python",
            "Conocimientos de bases de datos",
            "Experiencia con APIs REST"
        ],
        skills=["Python", "Django", "PostgreSQL", "FastAPI"],
        experience_years=2,
        languages=["Español", "Inglés"],
        location="Remoto",
        salary_range="$2000 - $4000 USD",
        description="Desarrollador Python con experiencia en desarrollo web"
    )
    
    # Textos de CV de prueba
    cv_texts = [
        """
        Juan Pérez
        juan.perez@email.com
        +34 123 456 789
        
        EXPERIENCIA PROFESIONAL
        Desarrollador Python - Empresa ABC (2022-2024)
        - Desarrollo de aplicaciones web con Django
        - Trabajo con bases de datos PostgreSQL
        - Creación de APIs REST con FastAPI
        
        HABILIDADES
        - Python
        - Django
        - PostgreSQL
        - FastAPI
        - Git
        - Docker
        
        EDUCACIÓN
        Ingeniería en Sistemas - Universidad XYZ (2020)
        
        IDIOMAS
        - Español (nativo)
        - Inglés (intermedio)
        """,
        
        """
        María García
        maria.garcia@email.com
        +34 987 654 321
        
        EXPERIENCIA
        Programadora Junior - Empresa DEF (2023-2024)
        - Desarrollo de scripts en Python
        - Trabajo con bases de datos MySQL
        - Mantenimiento de aplicaciones web
        
        HABILIDADES
        - Python
        - MySQL
        - HTML/CSS
        - JavaScript
        
        EDUCACIÓN
        Técnico en Programación - Instituto ABC (2022)
        
        IDIOMAS
        - Español (nativo)
        """
    ]
    
    try:
        # Crear workflow
        print("🔧 Inicializando workflow...")
        workflow = HRWorkflowAgent(api_key, smtp_config)
        print("✅ Workflow inicializado correctamente")
        
        # Procesar CVs
        print(f"📄 Procesando {len(cv_texts)} CVs...")
        result = workflow.run_workflow(job_profile, cv_texts)
        
        print("\n📊 RESULTADOS:")
        print(f"Total de candidatos: {len(result['candidates'])}")
        print(f"Candidatos seleccionados: {len(result['selected_candidates'])}")
        print(f"Candidatos rechazados: {len(result['rejected_candidates'])}")
        
        print("\n👥 CANDIDATOS SELECCIONADOS:")
        for candidate in result['selected_candidates']:
            print(f"  - {candidate.name} (Score: {candidate.match_score})")
            print(f"    Email: {candidate.email}")
            print(f"    Habilidades: {', '.join(candidate.skills)}")
            print(f"    Notas: {candidate.notes}")
            print()
        
        print("\n❌ CANDIDATOS RECHAZADOS:")
        for candidate in result['rejected_candidates']:
            print(f"  - {candidate.name} (Score: {candidate.match_score})")
            print(f"    Email: {candidate.email}")
            print(f"    Notas: {candidate.notes}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Iniciando prueba de procesamiento de CVs...")
    success = test_cv_processing()
    
    if success:
        print("\n✅ Prueba completada exitosamente")
    else:
        print("\n❌ La prueba falló")
