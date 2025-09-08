#!/usr/bin/env python3
"""
Script de prueba para la Fase 2 del refactor
Verifica que la integración del calendario en hr_workflow.py funciona correctamente
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir el directorio src al path
sys.path.append('src')

from src.models import JobProfile, Candidate
from src.hr_workflow import HRWorkflowAgent, ProcessingState
from src.calendar_manager import CalendarAgent

def test_calendar_integration():
    """Prueba la integración del calendario en el workflow"""
    
    print("🧪 Probando integración de calendario - Fase 2 del refactor")
    print("=" * 60)
    
    # Verificar que la API key esté configurada
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY no está configurada en el archivo .env")
        return False
    
    print("✅ API key de OpenAI configurada")
    
    # Configuración de calendario de prueba
    calendar_config = {
        "calendar_id": "test_calendar",
        "credentials_file": "test_credentials.json"
    }
    
    # Configuración SMTP de prueba
    smtp_config = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "email_user": "",
        "email_password": ""
    }
    
    print("✅ Configuraciones de prueba creadas")
    
    # Probar CalendarAgent independiente
    try:
        print("\n📅 Probando CalendarAgent independiente...")
        calendar_agent = CalendarAgent(calendar_config)
        
        # Probar obtención de slots disponibles
        from datetime import datetime, timedelta
        start_date = datetime.now() + timedelta(days=1)
        available_slots = calendar_agent.get_available_slots(start_date, 3)
        
        print(f"✅ CalendarAgent creado exitosamente")
        print(f"   - Slots disponibles encontrados: {len(available_slots)}")
        
        if available_slots:
            print(f"   - Primer slot: {available_slots[0]['date']} a las {available_slots[0]['time']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando CalendarAgent: {str(e)}")
        return False

def test_workflow_with_calendar():
    """Prueba el workflow completo con calendario integrado"""
    
    print("\n🔄 Probando workflow completo con calendario...")
    
    try:
        # Configuración de calendario
        calendar_config = {
            "calendar_id": "test_calendar",
            "credentials_file": "test_credentials.json"
        }
        
        # Configuración SMTP
        smtp_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email_user": "",
            "email_password": ""
        }
        
        # Crear workflow con calendario
        workflow = HRWorkflowAgent(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            smtp_config=smtp_config,
            calendar_config=calendar_config
        )
        
        print("✅ HRWorkflowAgent creado con calendario integrado")
        
        # Verificar que el calendar_agent esté configurado
        if workflow.calendar_agent:
            print("✅ CalendarAgent integrado correctamente")
        else:
            print("❌ CalendarAgent no se integró correctamente")
            return False
        
        # Probar programación de entrevistas
        print("\n📅 Probando programación de entrevistas...")
        
        # Crear candidatos de prueba
        test_candidates = [
            Candidate(
                id="test_001",
                name="María González",
                email="maria.gonzalez@email.com",
                phone="+54 11 1234-5678",
                cv_text="CV de prueba",
                experience_years=3,
                skills=["Python", "FastAPI"],
                languages=["Español", "Inglés"],
                education=["Ingeniería en Sistemas"],
                match_score=85.0,
                notes="Candidato de prueba"
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
                notes="Candidato de prueba 2"
            )
        ]
        
        # Programar entrevistas
        scheduled_interviews = workflow.schedule_interviews(
            test_candidates,
            interview_type="technical",
            days_ahead=5
        )
        
        print(f"✅ Programación de entrevistas completada")
        print(f"   - Entrevistas programadas: {len(scheduled_interviews)}")
        
        for i, interview_data in enumerate(scheduled_interviews, 1):
            candidate = interview_data["candidate"]
            slot = interview_data["slot"]
            print(f"   {i}. {candidate.name}: {slot['date']} a las {slot['time']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba del workflow: {str(e)}")
        return False

def test_processing_state():
    """Prueba el ProcessingState actualizado"""
    
    print("\n📊 Probando ProcessingState actualizado...")
    
    try:
        processing_state = ProcessingState()
        
        # Verificar atributos
        assert hasattr(processing_state, 'emails_sent')
        assert hasattr(processing_state, 'interviews_scheduled')
        assert hasattr(processing_state, 'candidates_processed')
        assert hasattr(processing_state, 'scheduled_interviews')
        
        print("✅ ProcessingState tiene todos los atributos requeridos")
        
        # Probar inicialización
        assert processing_state.emails_sent == 0
        assert processing_state.interviews_scheduled == 0
        assert processing_state.candidates_processed == 0
        assert processing_state.scheduled_interviews == []
        
        print("✅ ProcessingState se inicializa correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando ProcessingState: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de la Fase 2 del refactor")
    print("=" * 60)
    
    # Ejecutar pruebas
    test1_passed = test_calendar_integration()
    test2_passed = test_workflow_with_calendar()
    test3_passed = test_processing_state()
    
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE PRUEBAS:")
    print(f"   - Integración de CalendarAgent: {'✅ PASÓ' if test1_passed else '❌ FALLÓ'}")
    print(f"   - Workflow con calendario: {'✅ PASÓ' if test2_passed else '❌ FALLÓ'}")
    print(f"   - ProcessingState actualizado: {'✅ PASÓ' if test3_passed else '❌ FALLÓ'}")
    
    if test1_passed and test2_passed and test3_passed:
        print("\n🎉 ¡Fase 2 del refactor completada exitosamente!")
        print("   El calendario está integrado y funcionando en el workflow principal.")
        print("   Las entrevistas se pueden programar automáticamente.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisar la implementación.")
    
    print("=" * 60)
