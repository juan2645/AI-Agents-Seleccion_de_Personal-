from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
from .models import InterviewSchedule, Candidate
import json

class CalendarManager:
    """Gestor de calendario para programar entrevistas"""
    
    def __init__(self, calendar_config: Dict[str, str]):
        self.calendar_config = calendar_config
        self.timezone = pytz.timezone('America/Argentina/Buenos_Aires')  # Ajustar según ubicación
        
        # Horarios disponibles para entrevistas (formato 24h)
        self.available_slots = [
            "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"
        ]
        
        # Días de la semana disponibles (0=Lunes, 6=Domingo)
        self.available_days = [0, 1, 2, 3, 4]  # Lunes a Viernes
        
        # Duración por defecto de entrevistas
        self.default_duration = 60  # minutos
    
    def get_available_slots(self, start_date: datetime, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Obtiene slots disponibles para entrevistas"""
        available_slots = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day in range(days_ahead):
            check_date = current_date + timedelta(days=day)
            
            # Verificar si es un día laboral
            if check_date.weekday() in self.available_days:
                for time_slot in self.available_slots:
                    hour, minute = map(int, time_slot.split(':'))
                    slot_datetime = check_date.replace(hour=hour, minute=minute)
                    
                    # Verificar si el slot está disponible (aquí se integraría con Google Calendar API)
                    if self._is_slot_available(slot_datetime):
                        available_slots.append({
                            "datetime": slot_datetime,
                            "date": slot_datetime.strftime("%Y-%m-%d"),
                            "time": slot_datetime.strftime("%H:%M"),
                            "duration": self.default_duration
                        })
        
        return available_slots
    
    def _is_slot_available(self, slot_datetime: datetime) -> bool:
        """Verifica si un slot está disponible (placeholder para integración con Google Calendar)"""
        # Aquí se integraría con Google Calendar API para verificar disponibilidad real
        # Por ahora, simulamos que todos los slots están disponibles
        return True
    
    def schedule_interview(self, candidate: Candidate, preferred_date: datetime, 
                          interview_type: str = "technical", interviewer: str = None,
                          location: str = "Remoto") -> InterviewSchedule:
        """Programa una entrevista para un candidato"""
        
        # Ajustar la fecha al timezone local
        local_date = preferred_date.astimezone(self.timezone)
        
        # Crear el objeto de programación
        interview = InterviewSchedule(
            candidate_id=candidate.id,
            date=local_date,
            duration_minutes=self.default_duration,
            interview_type=interview_type,
            interviewer=interviewer or "Equipo de RRHH",
            location=location,
            notes=f"Entrevista {interview_type} para {candidate.name}"
        )
        
        # Aquí se integraría con Google Calendar API para crear el evento real
        self._create_calendar_event(interview, candidate)
        
        return interview
    
    def _create_calendar_event(self, interview: InterviewSchedule, candidate: Candidate):
        """Crea un evento en el calendario (placeholder para Google Calendar API)"""
        # Aquí se implementaría la integración con Google Calendar API
        # Por ahora, solo simulamos la creación
        event_data = {
            "summary": f"Entrevista {interview.interview_type} - {candidate.name}",
            "description": f"Candidato: {candidate.name}\nEmail: {candidate.email}\nTipo: {interview.interview_type}",
            "start": {
                "dateTime": interview.date.isoformat(),
                "timeZone": str(self.timezone)
            },
            "end": {
                "dateTime": (interview.date + timedelta(minutes=interview.duration_minutes)).isoformat(),
                "timeZone": str(self.timezone)
            },
            "attendees": [
                {"email": candidate.email},
                {"email": interview.interviewer} if "@" in interview.interviewer else None
            ],
            "location": interview.location
        }
        
        print(f"Evento creado en calendario: {json.dumps(event_data, indent=2)}")
    
    def send_calendar_invitation(self, interview: InterviewSchedule, candidate: Candidate) -> bool:
        """Envía invitación de calendario al candidato"""
        try:
            # Aquí se implementaría el envío de invitación de calendario
            # Por ahora, simulamos el envío
            invitation_data = {
                "to": candidate.email,
                "subject": f"Invitación a entrevista - {interview.interview_type}",
                "body": f"""
                Hola {candidate.name},
                
                Te invitamos a una entrevista {interview.interview_type}.
                
                Fecha: {interview.date.strftime('%d/%m/%Y')}
                Hora: {interview.date.strftime('%H:%M')}
                Duración: {interview.duration_minutes} minutos
                Entrevistador: {interview.interviewer}
                Ubicación: {interview.location}
                
                Por favor confirma tu asistencia.
                """
            }
            
            print(f"Invitación enviada: {json.dumps(invitation_data, indent=2)}")
            return True
            
        except Exception as e:
            print(f"Error enviando invitación: {str(e)}")
            return False
    
    def reschedule_interview(self, interview: InterviewSchedule, new_date: datetime) -> bool:
        """Reprograma una entrevista existente"""
        try:
            old_date = interview.date
            interview.date = new_date.astimezone(self.timezone)
            
            # Aquí se actualizaría el evento en Google Calendar
            print(f"Entrevista reprogramada de {old_date} a {interview.date}")
            return True
            
        except Exception as e:
            print(f"Error reprogramando entrevista: {str(e)}")
            return False
    
    def cancel_interview(self, interview: InterviewSchedule) -> bool:
        """Cancela una entrevista"""
        try:
            # Aquí se cancelaría el evento en Google Calendar
            print(f"Entrevista cancelada: {interview.candidate_id} - {interview.date}")
            return True
            
        except Exception as e:
            print(f"Error cancelando entrevista: {str(e)}")
            return False
