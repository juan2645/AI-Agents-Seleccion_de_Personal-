#!/usr/bin/env python3
"""
Script de prueba simple para verificar el procesamiento de CVs
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio src al path
sys.path.append('src')

def test_basic_imports():
    """Prueba las importaciones básicas"""
    try:
        from src.models import JobProfile, Candidate
        from src.hr_workflow import HRWorkflowAgent
        print("✅ Importaciones exitosas")
        return True
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        return False

def test_workflow_creation():
    """Prueba la creación del workflow"""
    try:
        from src.hr_workflow import HRWorkflowAgent
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY no configurada")
            return False
        
        smtp_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email_user": "",
            "email_password": ""
        }
        
        workflow = HRWorkflowAgent(api_key, smtp_config)
        print("✅ Workflow creado exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando workflow: {e}")
        return False

def test_cv_processing():
    """Prueba el procesamiento de un CV simple"""
    try:
        from src.hr_workflow import HRWorkflowAgent
        from src.models import JobProfile
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY no configurada")
            return False
        
        smtp_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email_user": "",
            "email_password": ""
        }
        
        # Crear workflow
        workflow = HRWorkflowAgent(api_key, smtp_config)
        
        # Crear perfil de trabajo
        job_profile = JobProfile(
            title="Desarrollador Python",
            requirements=["Experiencia en Python", "Conocimientos de bases de datos"],
            skills=["Python", "Django", "PostgreSQL"],
            experience_years=2,
            languages=["Español", "Inglés"],
            location="Remoto",
            salary_range="$2000 - $4000 USD",
            description="Desarrollador Python con experiencia en desarrollo web"
        )
        
        # CV de prueba
        cv_text = """
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
        """
        
        # Procesar CV
        print("📄 Procesando CV de prueba...")
        result = workflow.run_workflow(job_profile, [cv_text])
        
        print(f"\n📊 RESULTADOS:")
        print(f"Total de candidatos: {len(result['candidates'])}")
        print(f"Candidatos seleccionados: {len(result['selected_candidates'])}")
        print(f"Candidatos rechazados: {len(result['rejected_candidates'])}")
        
        if result['selected_candidates']:
            candidate = result['selected_candidates'][0]
            print(f"\n👤 Candidato seleccionado:")
            print(f"  Nombre: {candidate.name}")
            print(f"  Email: {candidate.email}")
            print(f"  Score: {candidate.match_score}")
            print(f"  Habilidades: {', '.join(candidate.skills)}")
            print(f"  Notas: {candidate.notes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en procesamiento: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Iniciando pruebas del sistema...")
    
    # Prueba 1: Importaciones
    print("\n1️⃣ Probando importaciones...")
    if not test_basic_imports():
        sys.exit(1)
    
    # Prueba 2: Creación del workflow
    print("\n2️⃣ Probando creación del workflow...")
    if not test_workflow_creation():
        sys.exit(1)
    
    # Prueba 3: Procesamiento de CV
    print("\n3️⃣ Probando procesamiento de CV...")
    if not test_cv_processing():
        sys.exit(1)
    
    print("\n✅ Todas las pruebas pasaron exitosamente!")
    print("🎉 El sistema está funcionando correctamente")
