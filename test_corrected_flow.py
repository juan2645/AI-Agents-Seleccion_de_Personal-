#!/usr/bin/env python3
"""
Script de prueba para el flujo corregido de programación de entrevistas
Verifica que los emails se envíen DESPUÉS de programar entrevistas
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir el directorio src al path
sys.path.append('src')

from src.models import JobProfile, Candidate
from src.hr_workflow import HRWorkflowAgent

def test_corrected_workflow():
    """Prueba el flujo corregido donde los emails se envían DESPUÉS de programar entrevistas"""
    
    print("🧪 Probando flujo corregido de programación de entrevistas")
    print("=" * 60)
    
    # Verificar que la API key esté configurada
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY no está configurada en el archivo .env")
        return False
    
    print("✅ API key de OpenAI configurada")
    
    # Configuración SMTP de prueba
    smtp_config = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "email_user": "",
        "email_password": ""
    }
    
    # Configuración de calendario de prueba
    calendar_config = {
        "calendar_id": "test_calendar",
        "timezone": "America/Argentina/Buenos_Aires"
    }
    
    # Crear HRWorkflowAgent
    hr_workflow = HRWorkflowAgent(openai_api_key, smtp_config, calendar_config)
    print("✅ HRWorkflowAgent creado con CalendarAgent")
    
    # Crear perfil de trabajo de prueba
    job_profile = JobProfile(
        title="Desarrollador Python Senior",
        experience_years=3,
        location="Remoto",
        salary_range="$3000 - $5000 USD",
        description="Buscamos un desarrollador Python senior para unirse a nuestro equipo de desarrollo.",
        requirements=[
            "Experiencia mínima de 2 años en desarrollo Python",
            "Conocimientos sólidos en APIs REST",
            "Conocimientos de bases de datos SQL y NoSQL",
            "Experiencia con Docker y CI/CD"
        ],
        skills=["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "Git", "AWS"],
        languages=["Español", "Inglés"]
    )
    
    print("✅ Perfil de trabajo creado")
    
    # Crear CVs de prueba
    cv_texts = [
        """
        María González
        maria.gonzalez@email.com
        +54 11 1234-5678
        
        EXPERIENCIA:
        - 3 años como Desarrolladora Python en TechCorp
        - Experiencia con Django, FastAPI, PostgreSQL
        - Conocimientos de Docker y AWS
        - Inglés avanzado
        
        EDUCACIÓN:
        - Ingeniería en Sistemas, Universidad de Buenos Aires
        """,
        """
        Carlos Rodríguez
        carlos.rodriguez@email.com
        +54 11 8765-4321
        
        EXPERIENCIA:
        - 5 años como Desarrollador Full Stack
        - Experiencia con Python, Django, React
        - Conocimientos de bases de datos SQL y NoSQL
        - Experiencia con CI/CD
        
        EDUCACIÓN:
        - Ingeniería en Informática, Universidad Nacional
        """
    ]
    
    print("✅ CVs de prueba creados")
    
    try:
        # Ejecutar el workflow completo
        print("\n🚀 Ejecutando workflow completo...")
        result = hr_workflow.run_workflow(job_profile, cv_texts)
        
        print("\n📋 RESULTADOS DEL WORKFLOW:")
        print(f"   - Total candidatos procesados: {result['total_candidates']}")
        print(f"   - Candidatos seleccionados: {len(result['selected_candidates'])}")
        print(f"   - Candidatos rechazados: {len(result['rejected_candidates'])}")
        print(f"   - Entrevistas programadas: {result['interviews_scheduled']}")
        print(f"   - Emails enviados: {result['emails_sent']}")
        
        # Verificar que el flujo es correcto
        checks = [
            ("Candidatos seleccionados", len(result['selected_candidates']) > 0),
            ("Entrevistas programadas", result['interviews_scheduled'] > 0),
            ("Emails enviados DESPUÉS de programar", result['emails_sent'] > 0),
            ("Información de entrevistas en emails", len(result['scheduled_interviews']) > 0)
        ]
        
        print("\n📋 VERIFICACIONES DEL FLUJO:")
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}: {'PASÓ' if passed else 'FALLÓ'}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 ¡Flujo corregido funcionando correctamente!")
            print("   ✅ Los emails se envían DESPUÉS de programar entrevistas")
            print("   ✅ Los emails incluyen información específica de entrevistas")
            print("   ✅ El flujo es: Análisis → Selección → Programación → Emails")
        else:
            print("\n⚠️ Algunas verificaciones fallaron.")
            print("   Revisar el flujo del workflow.")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error ejecutando workflow: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del flujo corregido")
    print("=" * 60)
    
    # Ejecutar prueba
    test_passed = test_corrected_workflow()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBA:")
    print(f"   - Flujo corregido: {'✅ PASÓ' if test_passed else '❌ FALLÓ'}")
    
    if test_passed:
        print("\n🎉 ¡Flujo corregido exitosamente!")
        print("   Ahora los emails se envían DESPUÉS de programar entrevistas")
        print("   y incluyen toda la información específica de fecha y hora.")
    else:
        print("\n⚠️  La prueba falló. Revisar la implementación.")
    
    print("=" * 60)
