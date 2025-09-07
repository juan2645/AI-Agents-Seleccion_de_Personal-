from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import List, Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
import time
from .models import Candidate, EmailTemplate, CandidateStatus

class EmailAgent:
    """
    Agente para gestión de emails en el proceso de selección de personal.
    
    Funcionalidades principales:
    - Generación de emails personalizados usando IA
    - Envío individual y masivo de emails
    - Plantillas predefinidas para diferentes tipos de comunicación
    - Integración con servidores SMTP
    
    Nota: Requiere configuración SMTP válida para funcionar correctamente.
    """
    
    def __init__(self, openai_api_key: str, smtp_config: Dict[str, str]):
        """
        Inicializa el agente de emails.
        
        Args:
            openai_api_key: Clave API de OpenAI para generación de contenido
            smtp_config: Configuración SMTP con keys: email_user, email_password, smtp_server, smtp_port
        """
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=openai_api_key
        )
        
        self.smtp_config = self._validate_smtp_config(smtp_config)
        self.logger = logging.getLogger(__name__)
        
        # Cargar plantillas de email
        self.email_templates = self._load_email_templates()
    
    def _validate_smtp_config(self, smtp_config: Dict[str, str]) -> Dict[str, str]:
        """
        Valida la configuración SMTP.
        
        Args:
            smtp_config: Configuración SMTP a validar
            
        Returns:
            Dict[str, str]: Configuración SMTP validada
            
        Raises:
            ValueError: Si la configuración es inválida
        """
        required_keys = ['email_user', 'email_password', 'smtp_server', 'smtp_port']
        
        for key in required_keys:
            if key not in smtp_config:
                raise ValueError(f"Configuración SMTP incompleta: falta '{key}'")
        
        # Validar que el puerto sea un número
        try:
            smtp_config['smtp_port'] = int(smtp_config['smtp_port'])
        except ValueError:
            raise ValueError("El puerto SMTP debe ser un número")
        
        return smtp_config
    
    def _load_email_templates(self) -> Dict[str, Dict[str, str]]:
        """
        Carga las plantillas de email predefinidas.
        
        Returns:
            Dict[str, Dict[str, str]]: Plantillas organizadas por tipo
        """
        return {
            "selected": {
                "subject": "¡Felicitaciones! Has sido seleccionado para la siguiente fase",
                "template": """Estimado/a {candidate_name},

¡Felicitaciones! Has sido seleccionado/a para continuar en el proceso de selección para el puesto de {job_title}.

Tu perfil ha destacado por {highlight_reasons}.

Próximos pasos:
- Te contactaremos para coordinar una entrevista
- La entrevista será {interview_type} ({duration} minutos)
- Te enviaremos un calendario para seleccionar horario

Si tienes preguntas, no dudes en contactarnos.

Saludos cordiales,
Equipo de RRHH - {company_name}"""
            },
            "rejected": {
                "subject": "Actualización sobre tu aplicación",
                "template": """Estimado/a {candidate_name},

Gracias por tu interés en el puesto de {job_title}.

Después de revisar tu perfil, lamentamos informarte que en esta oportunidad no hemos podido avanzar con tu candidatura.

Te agradecemos tu interés y te animamos a seguir atento/a a nuestras futuras oportunidades.

Te deseamos mucho éxito en tu búsqueda profesional.

Saludos cordiales,
Equipo de RRHH - {company_name}"""
            },
            "interview_invitation": {
                "subject": "Invitación a entrevista - {job_title}",
                "template": """Estimado/a {candidate_name},

Te invitamos a una entrevista para el puesto de {job_title}.

Detalles:
- Fecha: {interview_date}
- Hora: {interview_time}
- Duración: {duration} minutos
- Tipo: {interview_type}
- Entrevistador: {interviewer}
- Ubicación: {location}

{additional_notes}

Por favor confirma tu asistencia respondiendo a este email.

Saludos cordiales,
Equipo de RRHH - {company_name}"""
            }
        }
    
    def generate_personalized_email(self, candidate: Candidate, template_type: str, 
                                  job_title: str, company_name: str = "Nuestra Empresa",
                                  use_ai_personalization: bool = True, **kwargs) -> EmailTemplate:
        """
        Genera un email personalizado para un candidato.
        
        Args:
            candidate: Objeto Candidate con información del candidato
            template_type: Tipo de plantilla ('selected', 'rejected', 'interview_invitation')
            job_title: Título del puesto de trabajo
            company_name: Nombre de la empresa
            use_ai_personalization: Si usar IA para personalizar el contenido
            **kwargs: Variables adicionales para la plantilla
            
        Returns:
            EmailTemplate: Plantilla de email personalizada
        """
        if template_type not in self.email_templates:
            raise ValueError(f"Tipo de plantilla no válido: {template_type}")
        
        base_template = self.email_templates[template_type]
        
        # Preparar variables para el template
        template_vars = {
            "candidate_name": candidate.name,
            "job_title": job_title,
            "company_name": company_name,
            "highlight_reasons": self._generate_highlight_reasons(candidate),
            **kwargs
        }
        
        if use_ai_personalization:
            # Generar contenido personalizado con IA
            personalized_body = self._generate_ai_content(candidate, base_template['template'], template_vars)
        else:
            # Usar plantilla base con variables
            personalized_body = base_template['template'].format(**template_vars)
        
        return EmailTemplate(
            subject=base_template["subject"].format(**template_vars),
            body=personalized_body,
            template_type=template_type
        )
    
    def _generate_ai_content(self, candidate: Candidate, base_template: str, template_vars: Dict[str, Any]) -> str:
        """
        Genera contenido personalizado usando IA.
        
        Args:
            candidate: Información del candidato
            base_template: Plantilla base
            template_vars: Variables para la plantilla
            
        Returns:
            str: Contenido personalizado
        """
        try:
            prompt = f"""
            Personaliza el siguiente email para {candidate.name} basándote en su perfil:
            
            Perfil del candidato:
            - Experiencia: {candidate.experience_years} años
            - Habilidades principales: {', '.join(candidate.skills[:5]) if candidate.skills else 'No especificadas'}
            - Idiomas: {', '.join(candidate.languages) if candidate.languages else 'No especificados'}
            - Puntaje de match: {candidate.match_score}/100
            
            Template base:
            {base_template}
            
            Genera un email más personalizado y específico, manteniendo el tono profesional pero cálido.
            """
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error generando contenido con IA: {str(e)}")
            # Fallback a plantilla base
            return base_template.format(**template_vars)
    
    def _generate_highlight_reasons(self, candidate: Candidate) -> str:
        """
        Genera razones destacadas para el candidato basadas en su perfil.
        
        Args:
            candidate: Información del candidato
            
        Returns:
            str: Razones destacadas formateadas
        """
        reasons = []
        
        # Razones basadas en puntaje de match
        if candidate.match_score >= 90:
            reasons.append("tu excelente perfil técnico")
        elif candidate.match_score >= 80:
            reasons.append("tu sólida experiencia")
        elif candidate.match_score >= 70:
            reasons.append("tu buen ajuste al perfil requerido")
        
        # Razones basadas en experiencia
        if candidate.experience_years >= 5:
            reasons.append("tu amplia experiencia profesional")
        elif candidate.experience_years >= 2:
            reasons.append("tu experiencia relevante")
        
        # Razones basadas en habilidades
        if candidate.skills and len(candidate.skills) >= 5:
            reasons.append("tu diversidad de habilidades técnicas")
        elif candidate.skills and len(candidate.skills) >= 3:
            reasons.append("tus habilidades especializadas")
        
        # Razones basadas en idiomas
        if candidate.languages and len(candidate.languages) > 1:
            reasons.append("tu dominio de múltiples idiomas")
        
        return " y ".join(reasons) if reasons else "tu perfil profesional"
    
    def send_email(self, to_email: str, email_template: EmailTemplate) -> bool:
        """
        Envía un email usando SMTP.
        
        Args:
            to_email: Dirección de email del destinatario
            email_template: Plantilla de email a enviar
            
        Returns:
            bool: True si el email se envió correctamente, False en caso contrario
        """
        try:
            # Validar email del destinatario
            if not self._is_valid_email(to_email):
                self.logger.error(f"Email inválido: {to_email}")
                return False
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['email_user']
            msg['To'] = to_email
            msg['Subject'] = email_template.subject
            
            msg.attach(MIMEText(email_template.body, 'plain', 'utf-8'))
            
            # Conectar al servidor SMTP
            server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            server.starttls()
            server.login(self.smtp_config['email_user'], self.smtp_config['email_password'])
            
            # Enviar email
            text = msg.as_string()
            server.sendmail(self.smtp_config['email_user'], to_email, text)
            server.quit()
            
            self.logger.info(f"Email enviado exitosamente a {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"Error de autenticación SMTP: {str(e)}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            self.logger.error(f"Destinatario rechazado {to_email}: {str(e)}")
            return False
        except smtplib.SMTPServerDisconnected as e:
            self.logger.error(f"Servidor SMTP desconectado: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error enviando email a {to_email}: {str(e)}")
            return False
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Valida formato básico de email.
        
        Args:
            email: Email a validar
            
        Returns:
            bool: True si el formato es válido
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def send_bulk_emails(self, candidates: List[Candidate], template_type: str,
                        job_title: str, company_name: str = "Nuestra Empresa",
                        delay_between_emails: float = 1.0, max_retries: int = 3) -> Dict[str, Any]:
        """
        Envía emails en lote a múltiples candidatos con control de rate limiting.
        
        Args:
            candidates: Lista de candidatos
            template_type: Tipo de plantilla a usar
            job_title: Título del puesto
            company_name: Nombre de la empresa
            delay_between_emails: Delay en segundos entre emails (para evitar spam)
            max_retries: Número máximo de reintentos por email
            
        Returns:
            Dict[str, Any]: Resultados detallados del envío
        """
        results = {
            'successful': [],
            'failed': [],
            'total_sent': 0,
            'total_failed': 0
        }
        
        self.logger.info(f"Iniciando envío masivo de {len(candidates)} emails")
        
        for i, candidate in enumerate(candidates):
            try:
                # Generar email personalizado
                email_template = self.generate_personalized_email(
                    candidate, template_type, job_title, company_name
                )
                
                # Intentar envío con reintentos
                success = self._send_with_retries(candidate.email, email_template, max_retries)
                
                if success:
                    results['successful'].append({
                        'email': candidate.email,
                        'name': candidate.name,
                        'template_type': template_type
                    })
                    results['total_sent'] += 1
                else:
                    results['failed'].append({
                        'email': candidate.email,
                        'name': candidate.name,
                        'error': 'Failed after retries'
                    })
                    results['total_failed'] += 1
                
                # Delay entre emails para evitar rate limiting
                if i < len(candidates) - 1:  # No delay después del último email
                    time.sleep(delay_between_emails)
                    
            except Exception as e:
                self.logger.error(f"Error procesando candidato {candidate.name}: {str(e)}")
                results['failed'].append({
                    'email': candidate.email,
                    'name': candidate.name,
                    'error': str(e)
                })
                results['total_failed'] += 1
        
        self.logger.info(f"Envió masivo completado: {results['total_sent']} exitosos, {results['total_failed']} fallidos")
        return results
    
    def _send_with_retries(self, to_email: str, email_template: EmailTemplate, max_retries: int) -> bool:
        """
        Envía email con reintentos en caso de fallo.
        
        Args:
            to_email: Email del destinatario
            email_template: Plantilla de email
            max_retries: Número máximo de reintentos
            
        Returns:
            bool: True si se envió exitosamente
        """
        for attempt in range(max_retries):
            try:
                if self.send_email(to_email, email_template):
                    return True
            except Exception as e:
                self.logger.warning(f"Intento {attempt + 1} fallido para {to_email}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponencial
        
        return False
    
    def get_email_templates(self) -> List[str]:
        """
        Obtiene la lista de tipos de plantillas disponibles.
        
        Returns:
            List[str]: Lista de tipos de plantillas
        """
        return list(self.email_templates.keys())
    
    def test_smtp_connection(self) -> bool:
        """
        Prueba la conexión SMTP con la configuración actual.
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            server.starttls()
            server.login(self.smtp_config['email_user'], self.smtp_config['email_password'])
            server.quit()
            self.logger.info("Conexión SMTP exitosa")
            return True
        except Exception as e:
            self.logger.error(f"Error en conexión SMTP: {str(e)}")
            return False
    
    def get_smtp_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de la configuración SMTP.
        
        Returns:
            Dict[str, Any]: Estado de la configuración SMTP
        """
        return {
            'server': self.smtp_config['smtp_server'],
            'port': self.smtp_config['smtp_port'],
            'user': self.smtp_config['email_user'],
            'connection_test': self.test_smtp_connection()
        }
