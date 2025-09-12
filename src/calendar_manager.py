from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
from .models import InterviewSchedule, Candidate
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class CalendarAgent:
    """Gestor de calendario para programar entrevistas con Google Calendar API"""
    
    # Scopes necesarios para Google Calendar
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, calendar_config: Dict[str, str] = None):
        self.calendar_config = calendar_config or {}
        self.timezone = pytz.timezone('America/Argentina/Buenos_Aires')
        
        # Horarios disponibles para entrevistas (formato 24h)
        self.available_slots = [
            "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"
        ]
        
        # Días de la semana disponibles (0=Lunes, 6=Domingo)
        self.available_days = [0, 1, 2, 3, 4]  # Lunes a Viernes
        
        # Duración por defecto de entrevistas
        self.default_duration = 60  # minutos
        
        # Inicializar Google Calendar API
        self.service = self._initialize_calendar_service()
        self.calendar_id = self.calendar_config.get('calendar_id')
    
    def _initialize_calendar_service(self):
        """Inicializa el servicio de Google Calendar usando Service Account"""
        try:
            credentials_file = self.calendar_config.get('credentials_file', 'credentials.json')
            
            if not os.path.exists(credentials_file):
                print(f"❌ Archivo {credentials_file} no encontrado")
                return None
            
            # Usar Service Account para autenticación
            from google.oauth2 import service_account
            
            creds = service_account.Credentials.from_service_account_file(
                credentials_file, 
                scopes=self.SCOPES
            )
            
            # Construir el servicio
            service = build('calendar', 'v3', credentials=creds)
            print("✅ Google Calendar API inicializada correctamente con Service Account")
            return service
            
        except Exception as e:
            print(f"❌ Error inicializando Google Calendar API: {str(e)}")
            return None
    
    def get_available_slots(self, start_date: datetime, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Obtiene slots disponibles para entrevistas consultando Google Calendar"""
        available_slots = []
        current_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if not self.service:
            print("❌ Servicio de Google Calendar no disponible")
            return available_slots
        
        # Intentar con el Calendar ID específico primero, luego con 'primary' como fallback
        calendar_ids_to_try = [self.calendar_id, 'primary'] if self.calendar_id else ['primary']
        
        for calendar_id in calendar_ids_to_try:
            if not calendar_id:
                continue
                
            try:
                
                # Obtener eventos existentes en el rango de fechas
                end_date = current_date + timedelta(days=days_ahead)
                events_result = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=current_date.isoformat() + 'Z',
                    timeMax=end_date.isoformat() + 'Z',
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                # Crear un set de horarios ocupados para verificación rápida
                busy_times = set()
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    if 'T' in start:  # Es un datetime, no solo fecha
                        event_start = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        busy_times.add(event_start.strftime('%Y-%m-%d %H:%M'))
                
                # Generar slots disponibles
                for day in range(days_ahead):
                    check_date = current_date + timedelta(days=day)
                    
                    # Verificar si es un día laboral
                    if check_date.weekday() in self.available_days:
                        for time_slot in self.available_slots:
                            hour, minute = map(int, time_slot.split(':'))
                            slot_datetime = check_date.replace(hour=hour, minute=minute)
                            
                            # Verificar si el slot está disponible
                            if self._is_slot_available(slot_datetime, busy_times):
                                available_slots.append({
                                    "datetime": slot_datetime,
                                    "date": slot_datetime.strftime("%Y-%m-%d"),
                                    "time": slot_datetime.strftime("%H:%M"),
                                    "duration": self.default_duration
                                })
                
                print(f"✅ Encontrados {len(available_slots)} slots disponibles en {calendar_id}")
                # Actualizar el calendar_id que funcionó
                self.calendar_id = calendar_id
                return available_slots
                
            except HttpError as error:
                print(f"❌ Error consultando calendario {calendar_id}: {error}")
                continue
        
        print("❌ No se pudo acceder a ningún calendario")
        return available_slots
    
    def _is_slot_available(self, slot_datetime: datetime, busy_times: set = None) -> bool:
        """Verifica si un slot está disponible consultando Google Calendar"""
        if busy_times is None:
            return True
        
        slot_key = slot_datetime.strftime('%Y-%m-%d %H:%M')
        return slot_key not in busy_times
    
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
        """Crea un evento real en Google Calendar"""
        if not self.service or not self.calendar_id:
            print("❌ Servicio de Google Calendar no disponible")
            return None
        
        try:
            # Preparar datos del evento
            event_data = {
                "summary": f"Entrevista {interview.interview_type} - {candidate.name}",
                "description": f"Candidato: {candidate.name}\nEmail: {candidate.email}\nTipo: {interview.interview_type}\nNotas: {interview.notes}",
                "start": {
                    "dateTime": interview.date.isoformat(),
                    "timeZone": str(self.timezone)
                },
                "end": {
                    "dateTime": (interview.date + timedelta(minutes=interview.duration_minutes)).isoformat(),
                    "timeZone": str(self.timezone)
                },
                "attendees": [
                    {"email": candidate.email}
                ],
                "location": interview.location,
                "reminders": {
                    "useDefault": False,
                    "overrides": [
                        {"method": "email", "minutes": 24 * 60},  # 1 día antes
                        {"method": "popup", "minutes": 30}        # 30 minutos antes
                    ]
                }
            }
            
            # Agregar entrevistador si tiene email
            if "@" in interview.interviewer:
                event_data["attendees"].append({"email": interview.interviewer})
            
            # Crear el evento en Google Calendar
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_data,
                sendUpdates='all'  # Enviar notificaciones a todos los asistentes
            ).execute()
            
            print(f"✅ Evento creado en Google Calendar: {event.get('htmlLink')}")
            return event
            
        except HttpError as error:
            print(f"❌ Error creando evento en Google Calendar: {error}")
            return None
    
    def send_calendar_invitation(self, interview: InterviewSchedule, candidate: Candidate) -> bool:
        """Envía invitación de calendario al candidato (ya incluida en la creación del evento)"""
        try:
            # Las invitaciones se envían automáticamente cuando se crea el evento con sendUpdates='all'
            # Aquí solo registramos la información para logging
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
                
                La invitación de calendario se ha enviado automáticamente.
                """
            }
            
            print(f"✅ Invitación de calendario enviada automáticamente a {candidate.email}")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando invitación: {str(e)}")
            return False
    
    def reschedule_interview(self, interview: InterviewSchedule, new_date: datetime, event_id: str = None) -> bool:
        """Reprograma una entrevista existente en Google Calendar"""
        if not self.service or not self.calendar_id:
            print("❌ Servicio de Google Calendar no disponible")
            return False
        
        try:
            if not event_id:
                print("❌ Se requiere event_id para reprogramar")
                return False
            
            old_date = interview.date
            interview.date = new_date.astimezone(self.timezone)
            
            # Actualizar el evento en Google Calendar
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Actualizar fechas
            event['start']['dateTime'] = interview.date.isoformat()
            event['end']['dateTime'] = (interview.date + timedelta(minutes=interview.duration_minutes)).isoformat()
            
            # Guardar cambios
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            print(f"✅ Entrevista reprogramada de {old_date} a {interview.date}")
            return True
            
        except HttpError as error:
            print(f"❌ Error reprogramando entrevista: {error}")
            return False
    
    def cancel_interview(self, interview: InterviewSchedule, event_id: str = None) -> bool:
        """Cancela una entrevista en Google Calendar"""
        if not self.service or not self.calendar_id:
            print("❌ Servicio de Google Calendar no disponible")
            return False
        
        try:
            if not event_id:
                print("❌ Se requiere event_id para cancelar")
                return False
            
            # Cancelar el evento en Google Calendar
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            print(f"✅ Entrevista cancelada: {interview.candidate_id} - {interview.date}")
            return True
            
        except HttpError as error:
            print(f"❌ Error cancelando entrevista: {error}")
            return False
