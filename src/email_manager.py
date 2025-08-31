from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import List, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from .models import Candidate, EmailTemplate, CandidateStatus

class EmailAgent:
    """Gestor de emails para candidatos"""
    
    def __init__(self, openai_api_key: str, smtp_config: Dict[str, str]):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=openai_api_key
        )
        
        self.smtp_config = smtp_config
        
        # Plantillas base de emails
        self.email_templates = {
            "selected": {
                "subject": "¡Felicitaciones! Has sido seleccionado para la siguiente fase",
                "template": """
                Estimado/a {candidate_name},
                
                ¡Felicitaciones! Nos complace informarte que has sido seleccionado/a para continuar en el proceso de selección para el puesto de {job_title}.
                
                Tu perfil ha destacado entre todos los candidatos por {highlight_reasons}.
                
                Próximos pasos:
                - Te contactaremos en los próximos días para coordinar una entrevista
                - La entrevista será {interview_type} y tendrá una duración aproximada de {duration} minutos
                - Te enviaremos un calendario para que selecciones el horario que mejor te convenga
                
                Si tienes alguna pregunta, no dudes en contactarnos.
                
                Saludos cordiales,
                Equipo de Recursos Humanos
                {company_name}
                """
            },
            "rejected": {
                "subject": "Actualización sobre tu aplicación",
                "template": """
                Estimado/a {candidate_name},
                
                Gracias por tu interés en el puesto de {job_title} y por tomarte el tiempo de enviar tu aplicación.
                
                Después de revisar cuidadosamente tu perfil junto con los demás candidatos, lamentamos informarte que en esta oportunidad no hemos podido avanzar con tu candidatura.
                
                Queremos agradecerte por tu interés en formar parte de nuestro equipo y te animamos a que sigas atento/a a nuestras futuras oportunidades.
                
                Te deseamos mucho éxito en tu búsqueda profesional.
                
                Saludos cordiales,
                Equipo de Recursos Humanos
                {company_name}
                """
            },
            "interview_invitation": {
                "subject": "Invitación a entrevista - {job_title}",
                "template": """
                Estimado/a {candidate_name},
                
                Nos complace invitarte a una entrevista para el puesto de {job_title}.
                
                Detalles de la entrevista:
                - Fecha: {interview_date}
                - Hora: {interview_time}
                - Duración: {duration} minutos
                - Tipo: {interview_type}
                - Entrevistador: {interviewer}
                - Ubicación: {location}
                
                {additional_notes}
                
                Por favor confirma tu asistencia respondiendo a este email.
                
                Saludos cordiales,
                Equipo de Recursos Humanos
                {company_name}
                """
            }
        }
    
    def generate_personalized_email(self, candidate: Candidate, template_type: str, 
                                  job_title: str, company_name: str = "Nuestra Empresa",
                                  **kwargs) -> EmailTemplate:
        """Genera un email personalizado usando IA"""
        
        base_template = self.email_templates[template_type]
        
        # Preparar variables para el template
        template_vars = {
            "candidate_name": candidate.name,
            "job_title": job_title,
            "company_name": company_name,
            "highlight_reasons": self._generate_highlight_reasons(candidate),
            **kwargs
        }
        
        # Generar contenido personalizado con IA
        prompt = f"""
        Personaliza el siguiente email para {candidate.name} basándote en su perfil:
        
        Perfil del candidato:
        - Experiencia: {candidate.experience_years} años
        - Habilidades principales: {', '.join(candidate.skills[:5])}
        - Idiomas: {', '.join(candidate.languages)}
        - Puntaje de match: {candidate.match_score}/100
        
        Template base:
        {base_template['template']}
        
        Variables disponibles: {template_vars}
        
        Genera un email más personalizado y específico, manteniendo el tono profesional pero cálido.
        """
        
        response = self.llm.invoke(prompt)
        personalized_body = response.content
        
        return EmailTemplate(
            subject=base_template["subject"].format(**template_vars),
            body=personalized_body,
            template_type=template_type
        )
    
    def _generate_highlight_reasons(self, candidate: Candidate) -> str:
        """Genera razones destacadas para el candidato"""
        reasons = []
        
        if candidate.match_score >= 90:
            reasons.append("tu excelente perfil técnico")
        elif candidate.match_score >= 80:
            reasons.append("tu sólida experiencia")
        elif candidate.match_score >= 70:
            reasons.append("tu buen ajuste al perfil requerido")
        
        if candidate.experience_years >= 5:
            reasons.append("tu amplia experiencia profesional")
        
        if len(candidate.skills) >= 5:
            reasons.append("tu diversidad de habilidades técnicas")
        
        return " y ".join(reasons) if reasons else "tu perfil profesional"
    
    def send_email(self, to_email: str, email_template: EmailTemplate) -> bool:
        """Envía un email usando SMTP"""
        try:
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
            
            return True
            
        except Exception as e:
            print(f"Error enviando email a {to_email}: {str(e)}")
            return False
    
    def send_bulk_emails(self, candidates: List[Candidate], template_type: str,
                        job_title: str, company_name: str = "Nuestra Empresa") -> Dict[str, bool]:
        """Envía emails en lote a múltiples candidatos"""
        results = {}
        
        for candidate in candidates:
            email_template = self.generate_personalized_email(
                candidate, template_type, job_title, company_name
            )
            
            success = self.send_email(candidate.email, email_template)
            results[candidate.email] = success
            
        return results
