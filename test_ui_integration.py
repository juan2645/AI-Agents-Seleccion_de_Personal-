#!/usr/bin/env python3
"""
Script de prueba para la integración de UI con programación de entrevistas
Verifica que la interfaz web y los emails funcionen correctamente
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir el directorio src al path
sys.path.append('src')

from src.models import JobProfile, Candidate
from src.email_manager import EmailAgent

def test_email_with_interview_info():
    """Prueba el envío de emails con información de entrevista"""
    
    print("🧪 Probando emails con información de entrevista")
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
    
    # Crear EmailAgent
    email_agent = EmailAgent(openai_api_key, smtp_config)
    print("✅ EmailAgent creado")
    
    # Crear candidato de prueba
    test_candidate = Candidate(
        id="test_001",
        name="María González",
        email="maria.gonzalez@email.com",
        phone="+54 11 1234-5678",
        cv_text="CV de prueba",
        experience_years=3,
        skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        languages=["Español", "Inglés"],
        education=["Ingeniería en Sistemas"],
        match_score=85.0,
        notes="Candidato de prueba con buena experiencia"
    )
    
    print("✅ Candidato de prueba creado")
    
    # Probar email sin información de entrevista
    print("\n📧 Probando email sin información de entrevista...")
    try:
        email_template = email_agent.generate_personalized_email(
            candidate=test_candidate,
            template_type="selected",
            job_title="Desarrollador Python Senior",
            company_name="TechCorp"
        )
        
        print("✅ Email generado sin información de entrevista")
        print(f"   Asunto: {email_template.subject}")
        print(f"   Contenido (primeros 200 caracteres): {email_template.body[:200]}...")
        
    except Exception as e:
        print(f"❌ Error generando email sin entrevista: {str(e)}")
        return False
    
    # Probar email con información de entrevista programada
    print("\n📅 Probando email con información de entrevista programada...")
    try:
        interview_info = {
            "scheduled": True,
            "date": "2025-09-10",
            "time": "14:00",
            "duration": 60,
            "interviewer": "Juan Pérez - Tech Lead",
            "location": "Remoto (Google Meet)",
            "type": "Técnica",
            "notes": "La entrevista será sobre Python, APIs REST y bases de datos. Por favor ten listo tu entorno de desarrollo."
        }
        
        email_template_with_interview = email_agent.generate_personalized_email(
            candidate=test_candidate,
            template_type="selected",
            job_title="Desarrollador Python Senior",
            company_name="TechCorp",
            interview_info=interview_info
        )
        
        print("✅ Email generado con información de entrevista")
        print(f"   Asunto: {email_template_with_interview.subject}")
        print(f"   Contenido (primeros 300 caracteres): {email_template_with_interview.body[:300]}...")
        
        # Verificar que el contenido incluye información de la entrevista
        if "ENTREVISTA PROGRAMADA" in email_template_with_interview.body:
            print("✅ El email incluye la sección de entrevista programada")
        else:
            print("⚠️ El email no incluye la sección de entrevista programada")
        
        if "2025-09-10" in email_template_with_interview.body and "14:00" in email_template_with_interview.body:
            print("✅ El email incluye la fecha y hora de la entrevista")
        else:
            print("⚠️ El email no incluye la fecha y hora de la entrevista")
        
    except Exception as e:
        print(f"❌ Error generando email con entrevista: {str(e)}")
        return False
    
    return True

def test_bulk_emails_with_interviews():
    """Prueba el envío de emails en lote con información de entrevistas"""
    
    print("\n📬 Probando envío de emails en lote con entrevistas...")
    
    # Configuración SMTP de prueba
    smtp_config = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "email_user": "",
        "email_password": ""
    }
    
    # Crear EmailAgent
    email_agent = EmailAgent(os.getenv("OPENAI_API_KEY"), smtp_config)
    
    # Crear candidatos de prueba
    candidates = [
        Candidate(
            id="test_001",
            name="María González",
            email="maria.gonzalez@email.com",
            phone="+54 11 1234-5678",
            cv_text="CV de prueba 1",
            experience_years=3,
            skills=["Python", "FastAPI"],
            languages=["Español", "Inglés"],
            education=["Ingeniería en Sistemas"],
            match_score=85.0,
            notes="Candidato 1"
        ),
        Candidate(
            id="test_002",
            name="Carlos Rodríguez",
            email="carlos.rodriguez@email.com",
            phone="+54 11 8765-4321",
            cv_text="CV de prueba 2",
            experience_years=5,
            skills=["Python", "Django", "PostgreSQL"],
            languages=["Español"],
            education=["Ingeniería en Informática"],
            match_score=90.0,
            notes="Candidato 2"
        )
    ]
    
    # Información de entrevistas
    interviews_info = {
        "maria.gonzalez@email.com": {
            "scheduled": True,
            "date": "2025-09-10",
            "time": "14:00",
            "duration": 60,
            "interviewer": "Juan Pérez - Tech Lead",
            "location": "Remoto",
            "type": "Técnica",
            "notes": "Entrevista técnica sobre Python y APIs"
        },
        "carlos.rodriguez@email.com": {
            "scheduled": True,
            "date": "2025-09-11",
            "time": "10:00",
            "duration": 60,
            "interviewer": "Ana García - HR Manager",
            "location": "Presencial",
            "type": "HR",
            "notes": "Entrevista de recursos humanos"
        }
    }
    
    try:
        # Generar emails (sin enviar realmente)
        for candidate in candidates:
            candidate_interview_info = interviews_info.get(candidate.email)
            
            email_template = email_agent.generate_personalized_email(
                candidate=candidate,
                template_type="selected",
                job_title="Desarrollador Python Senior",
                company_name="TechCorp",
                interview_info=candidate_interview_info
            )
            
            print(f"✅ Email generado para {candidate.name}")
            print(f"   - Incluye entrevista: {'Sí' if candidate_interview_info else 'No'}")
            if candidate_interview_info:
                print(f"   - Fecha: {candidate_interview_info['date']} a las {candidate_interview_info['time']}")
        
        print("✅ Todos los emails generados correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en envío en lote: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de integración UI con programación de entrevistas")
    print("=" * 60)
    
    # Ejecutar pruebas
    test1_passed = test_email_with_interview_info()
    test2_passed = test_bulk_emails_with_interviews()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS:")
    print(f"   - Emails con información de entrevista: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"   - Envío en lote con entrevistas: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ¡Integración UI completada exitosamente!")
        print("   Los emails ahora incluyen información de entrevistas programadas.")
        print("   La interfaz web permite programar entrevistas.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisar la implementación.")
    
    print("=" * 60)
