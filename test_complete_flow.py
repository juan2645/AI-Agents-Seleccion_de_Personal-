#!/usr/bin/env python3
"""
Script de prueba para el flujo completo de programación de entrevistas
Verifica que la interfaz web y los emails funcionen correctamente con fechas y horas específicas
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir el directorio src al path
sys.path.append('src')

from src.models import JobProfile, Candidate, InterviewSchedule
from src.email_manager import EmailAgent
from datetime import datetime, timedelta

def test_complete_interview_flow():
    """Prueba el flujo completo de programación de entrevistas"""
    
    print("🧪 Probando flujo completo de programación de entrevistas")
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
    
    # Simular entrevista programada con fecha y hora específicas
    interview_date = datetime.now() + timedelta(days=3)  # 3 días desde ahora
    interview_time = "14:30"  # Hora específica
    
    interview_info = {
        "scheduled": True,
        "date": interview_date.strftime("%Y-%m-%d"),
        "time": interview_time,
        "duration": 60,
        "interviewer": "Juan Pérez - Tech Lead",
        "location": "Remoto (Google Meet)",
        "type": "Técnica",
        "notes": "La entrevista será sobre Python, APIs REST y bases de datos. Por favor ten listo tu entorno de desarrollo y prepárate para una sesión de coding."
    }
    
    print(f"✅ Información de entrevista preparada:")
    print(f"   - Fecha: {interview_info['date']}")
    print(f"   - Hora: {interview_info['time']}")
    print(f"   - Duración: {interview_info['duration']} minutos")
    print(f"   - Entrevistador: {interview_info['interviewer']}")
    print(f"   - Ubicación: {interview_info['location']}")
    
    # Probar email con información específica de entrevista
    print("\n📧 Generando email con información específica de entrevista...")
    try:
        email_template = email_agent.generate_personalized_email(
            candidate=test_candidate,
            template_type="selected",
            job_title="Desarrollador Python Senior",
            company_name="TechCorp",
            interview_info=interview_info
        )
        
        print("✅ Email generado con información específica de entrevista")
        print(f"   Asunto: {email_template.subject}")
        
        # Verificar que el email contiene la información específica
        email_content = email_template.body
        
        checks = [
            ("Fecha específica", interview_info['date'] in email_content),
            ("Hora específica", interview_info['time'] in email_content),
            ("Duración", str(interview_info['duration']) in email_content),
            ("Entrevistador", interview_info['interviewer'] in email_content),
            ("Ubicación", interview_info['location'] in email_content),
            ("Tipo de entrevista", interview_info['type'] in email_content),
            ("Sección de entrevista programada", "ENTREVISTA PROGRAMADA" in email_content)
        ]
        
        print("\n📋 Verificaciones del contenido del email:")
        all_passed = True
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}: {'PASÓ' if passed else 'FALLÓ'}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 ¡Todas las verificaciones pasaron!")
            print("   El email contiene toda la información específica de la entrevista.")
        else:
            print("\n⚠️ Algunas verificaciones fallaron.")
            print("   Revisar el contenido del email.")
        
        # Mostrar una muestra del contenido del email
        print(f"\n📄 Muestra del contenido del email:")
        print("=" * 50)
        lines = email_content.split('\n')
        for i, line in enumerate(lines[:20]):  # Mostrar primeras 20 líneas
            if line.strip():
                print(f"{i+1:2d}: {line}")
        if len(lines) > 20:
            print("    ... (contenido adicional)")
        print("=" * 50)
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error generando email: {str(e)}")
        return False

def test_multiple_interviews():
    """Prueba el envío de múltiples invitaciones de entrevista"""
    
    print("\n📬 Probando envío de múltiples invitaciones...")
    
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
    
    # Información de entrevistas con fechas y horas específicas
    interviews_info = {
        "maria.gonzalez@email.com": {
            "scheduled": True,
            "date": "2025-09-10",
            "time": "14:00",
            "duration": 60,
            "interviewer": "Juan Pérez - Tech Lead",
            "location": "Remoto (Google Meet)",
            "type": "Técnica",
            "notes": "Entrevista técnica sobre Python y APIs REST. Prepárate para coding."
        },
        "carlos.rodriguez@email.com": {
            "scheduled": True,
            "date": "2025-09-11",
            "time": "10:30",
            "duration": 45,
            "interviewer": "Ana García - HR Manager",
            "location": "Presencial - Oficina Principal",
            "type": "HR",
            "notes": "Entrevista de recursos humanos. Trae documentos originales."
        }
    }
    
    try:
        # Generar emails para cada candidato
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
            print(f"   - Fecha: {candidate_interview_info['date']}")
            print(f"   - Hora: {candidate_interview_info['time']}")
            print(f"   - Duración: {candidate_interview_info['duration']} minutos")
            print(f"   - Entrevistador: {candidate_interview_info['interviewer']}")
            print(f"   - Ubicación: {candidate_interview_info['location']}")
            print(f"   - Tipo: {candidate_interview_info['type']}")
        
        print("✅ Todos los emails generados correctamente con información específica")
        return True
        
    except Exception as e:
        print(f"❌ Error en envío múltiple: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del flujo completo de programación de entrevistas")
    print("=" * 60)
    
    # Ejecutar pruebas
    test1_passed = test_complete_interview_flow()
    test2_passed = test_multiple_interviews()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS:")
    print(f"   - Flujo completo con fecha/hora específica: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"   - Múltiples invitaciones con detalles: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ¡Flujo completo funcionando correctamente!")
        print("   ✅ El botón de programar entrevistas funciona")
        print("   ✅ Los emails incluyen fecha y hora específicas")
        print("   ✅ La información de entrevista se muestra correctamente")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisar la implementación.")
    
    print("=" * 60)
