"""
Sistema de Automatización de Selección de Personal
==================================================

Este módulo implementa una API REST para automatizar el proceso de reclutamiento
usando inteligencia artificial. Permite subir CVs, analizarlos y generar reportes
de candidatos seleccionados y rechazados.

Funcionalidades principales:
- Procesamiento de CVs en múltiples formatos (.docx, .pdf, .txt)
- Análisis automático de candidatos usando IA
- Generación de reportes en diferentes formatos
- Envío automático de emails (opcional)
- Programación de entrevistas (opcional)

Autor: Sistema de IA para Recursos Humanos
Versión: 1.0.0
"""

import os
import json
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Importar modelos y agentes del sistema
from src.models import JobProfile, Candidate
from src.hr_workflow import HRWorkflowAgent
from src.cv_reader import CVReaderAgent

# =============================================================================
# CONFIGURACIÓN DEL SISTEMA
# =============================================================================

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Configuración de OpenAI (requerida para el funcionamiento del sistema)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configuración SMTP para envío de emails (opcional)
SMTP_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),  # Servidor SMTP
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),            # Puerto SMTP
    "email_user": os.getenv("EMAIL_USER", ""),                  # Usuario de email
    "email_password": os.getenv("EMAIL_PASSWORD", "")           # Contraseña de aplicación
}

# Configuración de Google Calendar para programar entrevistas (opcional)
CALENDAR_CONFIG = {
    "calendar_id": os.getenv("CALENDAR_ID", ""),                # ID del calendario
    "credentials_file": os.getenv("GOOGLE_CREDENTIALS_FILE", "") # Archivo de credenciales
}

# =============================================================================
# INICIALIZACIÓN DEL WORKFLOW
# =============================================================================

# Variable global para almacenar la instancia del workflow de HR
hr_workflow = None

def initialize_workflow():
    """
    Inicializa el workflow de HR con las configuraciones necesarias.
    
    Esta función:
    1. Verifica que la API key de OpenAI esté configurada
    2. Crea una instancia del HRWorkflowAgent
    3. Maneja errores de inicialización
    
    Returns:
        None: La instancia se almacena en la variable global hr_workflow
    """
    global hr_workflow
    
    # Verificar que la API key de OpenAI esté configurada
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY no está configurada")
        print("💡 Crea un archivo .env con: OPENAI_API_KEY=tu_clave_aqui")
        hr_workflow = None
        return
    
    try:
        # Crear instancia del workflow con todas las configuraciones
        hr_workflow = HRWorkflowAgent(OPENAI_API_KEY, SMTP_CONFIG, CALENDAR_CONFIG)
        print("✅ Workflow de HR inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando workflow: {str(e)}")
        hr_workflow = None

# =============================================================================
# CICLO DE VIDA DE LA APLICACIÓN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación FastAPI.
    
    Esta función se ejecuta:
    - Al iniciar la aplicación: inicializa el workflow
    - Al cerrar la aplicación: limpia recursos (si es necesario)
    
    Args:
        app: Instancia de la aplicación FastAPI
    """
    # Inicialización al arrancar la aplicación
    try:
        initialize_workflow()
    except Exception as e:
        print(f"❌ Error inicializando workflow: {str(e)}")
    
    yield  # La aplicación está ejecutándose
    
    # Limpieza al cerrar la aplicación (si es necesario)
    # Por ahora no hay limpieza específica

# =============================================================================
# CONFIGURACIÓN DE FASTAPI
# =============================================================================

# Crear instancia de la aplicación FastAPI
app = FastAPI(
    title="Sistema de Automatización de Selección de Personal",
    description="API para automatizar el proceso de reclutamiento usando IA",
    version="1.0.0",
    lifespan=lifespan  # Usar el manejador de ciclo de vida
)

# Montar archivos estáticos para servir la interfaz web
app.mount("/static", StaticFiles(directory="static"), name="static")

# =============================================================================
# ENDPOINTS DE ARCHIVOS ESTÁTICOS
# =============================================================================

@app.get("/styles.css")
async def get_styles():
    """
    Sirve el archivo CSS de la interfaz web.
    
    Returns:
        FileResponse: Archivo CSS con los estilos de la aplicación
    """
    return FileResponse("static/styles.css")

@app.get("/script.js")
async def get_script():
    """
    Sirve el archivo JavaScript de la interfaz web.
    
    Returns:
        FileResponse: Archivo JS con la lógica del frontend
    """
    return FileResponse("static/script.js")

# =============================================================================
# ENDPOINTS PRINCIPALES DE LA API
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Endpoint raíz - Sirve la interfaz web principal.
    
    Este endpoint devuelve la página HTML principal donde los usuarios
    pueden subir CVs y configurar el proceso de reclutamiento.
    
    Returns:
        HTMLResponse: Página HTML de la interfaz web
    """
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api")
async def api_root():
    """
    Endpoint de información de la API.
    
    Proporciona información básica sobre el sistema y su estado.
    
    Returns:
        dict: Información de la API (nombre, versión, estado)
    """
    return {
        "message": "Sistema de Automatización de Selección de Personal",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """
    Verificación de salud del sistema.
    
    Este endpoint permite verificar el estado de las configuraciones
    del sistema (OpenAI, SMTP, Calendar).
    
    Returns:
        dict: Estado de salud y configuraciones del sistema
    """
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY),
        "smtp_configured": bool(SMTP_CONFIG["email_user"]),
        "calendar_configured": bool(CALENDAR_CONFIG["calendar_id"])
    }

# =============================================================================
# ENDPOINT PRINCIPAL DE PROCESAMIENTO
# =============================================================================

@app.post("/process-recruitment-with-files")
async def process_recruitment_with_files(
    files: List[UploadFile] = File(...),
    job_profile: str = None
):
    """
    Procesa un reclutamiento completo usando archivos CV subidos.
    
    Este es el endpoint principal del sistema. Permite:
    1. Subir múltiples archivos CV en diferentes formatos (.docx, .pdf, .txt)
    2. Configurar un perfil de trabajo personalizado
    3. Analizar automáticamente los CVs usando IA
    4. Generar reportes de candidatos seleccionados y rechazados
    5. Enviar emails automáticamente (si está configurado)
    6. Programar entrevistas (si está configurado)
    
    Args:
        files (List[UploadFile]): Lista de archivos CV subidos
        job_profile (str, optional): Perfil del puesto en formato JSON string.
                                   Si no se proporciona, usa un perfil por defecto.
    
    Returns:
        dict: Resultado del procesamiento con:
            - success: bool - Indica si el procesamiento fue exitoso
            - message: str - Mensaje descriptivo
            - data: dict - Datos detallados del procesamiento:
                - total_candidates: int - Total de candidatos procesados
                - selected_candidates: list - Lista de candidatos seleccionados
                - rejected_candidates: list - Lista de candidatos rechazados
                - emails_sent: int - Número de emails enviados
                - interviews_scheduled: int - Número de entrevistas programadas
                - processing_time: int - Tiempo de procesamiento
    
    Raises:
        HTTPException: 500 si el workflow no está inicializado
        HTTPException: 400 si no se pudieron procesar los archivos
        HTTPException: 500 si ocurre un error durante el procesamiento
    """
    if not hr_workflow:
        raise HTTPException(
            status_code=500, 
            detail="Workflow no inicializado. Verifica que OPENAI_API_KEY esté configurada correctamente."
        )
    
    try:
        # =====================================================================
        # 1. CONFIGURAR PERFIL DEL TRABAJO
        # =====================================================================
        
        if job_profile:
            # Usar perfil personalizado proporcionado por el usuario
            job_data = json.loads(job_profile)
            job_profile_obj = JobProfile(**job_data)
        else:
            # Usar perfil por defecto si no se proporciona uno personalizado
            job_profile_obj = JobProfile(
                title="Desarrollador Python Senior",
                requirements=[
                    "Experiencia mínima de 2 años en desarrollo Python",
                    "Conocimientos sólidos en APIs REST",
                    "Conocimientos de bases de datos SQL y NoSQL",
                    "Experiencia con Docker y CI/CD"
                ],
                skills=["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "Git", "AWS"],
                experience_years=5,
                languages=["Español", "Inglés"],
                location="Remoto",
                salary_range="$3000 - $5000 USD",
                description="Buscamos un desarrollador Python senior para unirse a nuestro equipo de desarrollo."
            )
        
        # =====================================================================
        # 2. PROCESAR ARCHIVOS CV SUBIDOS
        # =====================================================================
        
        cv_texts = []  # Lista para almacenar los textos extraídos de los CVs
        cv_reader = CVReaderAgent()  # Agente para leer diferentes formatos de archivo
        
        for file in files:
            # Verificar que el archivo tenga una extensión soportada
            if file.filename.endswith(('.docx', '.pdf', '.txt')):
                content = await file.read()  # Leer contenido del archivo
                
                if file.filename.endswith('.txt'):
                    # Archivo de texto simple - decodificar directamente
                    cv_texts.append(content.decode('utf-8'))
                    
                elif file.filename.endswith('.docx'):
                    # Archivo Word - requiere procesamiento especial
                    import tempfile
                    
                    # Crear archivo temporal para procesar el documento Word
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
                        temp_file.write(content)
                        temp_file_path = temp_file.name
                    
                    try:
                        # Usar CVReaderAgent para extraer texto del documento Word
                        text = cv_reader.read_word_document(temp_file_path)
                        cv_texts.append(text)
                    finally:
                        # Limpiar archivo temporal
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                            
                else:
                    # Para archivos PDF - usar decode con manejo de errores
                    cv_texts.append(content.decode('utf-8', errors='ignore'))
        
        # Verificar que se pudieron procesar al menos algunos archivos
        if not cv_texts:
            raise HTTPException(status_code=400, detail="No se pudieron procesar los archivos")
        
        # =====================================================================
        # 3. EJECUTAR WORKFLOW DE ANÁLISIS
        # =====================================================================
        
        # Ejecutar el workflow completo de análisis de candidatos
        # Esto incluye: extracción de datos, scoring, selección, envío de emails, etc.
        result = hr_workflow.run_workflow(job_profile_obj, cv_texts)
        
        # =====================================================================
        # 4. PREPARAR RESPUESTA PARA EL CLIENTE
        # =====================================================================
        
        return {
            "success": True,
            "message": "Proceso de reclutamiento completado",
            "data": {
                "total_candidates": len(result["candidates"]),
                "selected_candidates": [
                    {
                        "name": c.name,
                        "email": c.email,
                        "phone": c.phone,
                        "match_score": c.match_score,
                        "skills": c.skills,
                        "languages": c.languages,
                        "experience_years": c.experience_years,
                        "notes": c.notes
                    }
                    for c in result["selected_candidates"]
                ],
                "rejected_candidates": [
                    {
                        "name": c.name,
                        "email": c.email,
                        "phone": c.phone,
                        "match_score": c.match_score,
                        "skills": c.skills,
                        "languages": c.languages,
                        "experience_years": c.experience_years,
                        "notes": c.notes
                    }
                    for c in result["rejected_candidates"]
                ],
                "emails_sent": result["processing_state"].emails_sent,
                "interviews_scheduled": result["processing_state"].interviews_scheduled,
                "processing_time": result["processing_state"].candidates_processed
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento: {str(e)}")

# =============================================================================
# ENDPOINT DE DESCARGA DE REPORTES
# =============================================================================

@app.get("/download-report/{report_type}")
async def download_report(report_type: str):
    """
    Descarga un reporte generado por el sistema.
    
    Permite descargar reportes en diferentes formatos:
    - summary: Reporte resumido en formato texto
    - detailed: Reporte detallado en formato JSON
    - excel: Reporte en formato Excel
    
    Args:
        report_type (str): Tipo de reporte a descargar.
                          Valores válidos: "summary", "detailed", "excel"
    
    Returns:
        FileResponse: Archivo del reporte solicitado
    
    Raises:
        HTTPException: 404 si el reporte no existe o no se encuentra
    """
    filename = None
    
    # Determinar el archivo según el tipo de reporte solicitado
    if report_type == "summary":
        filename = "reports/reporte_resumen.txt"
    elif report_type == "detailed":
        filename = "reports/reporte_detallado.json"
    elif report_type == "excel":
        # Buscar el archivo Excel más reciente
        import glob
        excel_files = glob.glob("reports/reporte_reclutamiento_*.xlsx")
        if excel_files:
            filename = max(excel_files, key=os.path.getctime)
    
    # Verificar que el archivo existe
    if not filename or not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    return FileResponse(filename, filename=filename)

# =============================================================================
# ENDPOINT PARA ENVÍO DE INVITACIONES DE ENTREVISTAS
# =============================================================================

@app.post("/send-interview-invitations")
async def send_interview_invitations(request: dict):
    """
    Envía invitaciones de entrevistas a candidatos programados.
    
    Este endpoint recibe la información de entrevistas programadas y envía
    emails personalizados con los detalles específicos de cada entrevista.
    
    Args:
        request (dict): Datos de la solicitud que incluyen:
            - job_title: Título del puesto
            - scheduled_interviews: Lista de entrevistas programadas
    
    Returns:
        dict: Resultado del envío con:
            - success: bool - Indica si el envío fue exitoso
            - message: str - Mensaje descriptivo
            - emails_sent: int - Número de emails enviados
            - details: dict - Detalles del envío
    """
    if not hr_workflow:
        raise HTTPException(
            status_code=500, 
            detail="Workflow no inicializado. Verifica que OPENAI_API_KEY esté configurada correctamente."
        )
    
    try:
        # Extraer datos de la solicitud
        job_title = request.get("job_title", "Puesto de Trabajo")
        scheduled_interviews_data = request.get("scheduled_interviews", [])
        
        if not scheduled_interviews_data:
            raise HTTPException(status_code=400, detail="No hay entrevistas programadas para enviar")
        
        print(f"📧 Procesando envío de invitaciones para {len(scheduled_interviews_data)} entrevistas")
        
        # Convertir datos a objetos del sistema
        from src.models import Candidate, InterviewSchedule
        from datetime import datetime
        
        scheduled_interviews = []
        
        for item in scheduled_interviews_data:
            # Crear objeto Candidate
            candidate_data = item["candidate"]
            candidate = Candidate(
                id=candidate_data["id"],
                name=candidate_data["name"],
                email=candidate_data["email"],
                phone=candidate_data.get("phone"),
                cv_text=candidate_data["cv_text"],
                experience_years=candidate_data["experience_years"],
                skills=candidate_data["skills"],
                languages=candidate_data["languages"],
                education=candidate_data["education"],
                match_score=candidate_data["match_score"],
                notes=candidate_data.get("notes")
            )
            
            # Crear objeto InterviewSchedule
            interview_data = item["interview"]
            interview = InterviewSchedule(
                candidate_id=candidate.id,
                date=datetime.fromisoformat(interview_data["datetime"].replace('Z', '+00:00')),
                duration_minutes=interview_data["duration"],
                interview_type=interview_data["type"],
                interviewer=interview_data["interviewer"],
                location=interview_data["location"],
                notes=interview_data.get("notes")
            )
            
            scheduled_interviews.append({
                "candidate": candidate,
                "interview": interview
            })
        
        # Enviar invitaciones usando el workflow
        email_results = hr_workflow.send_interview_invitations(scheduled_interviews, job_title)
        
        # Preparar respuesta
        emails_sent = sum(email_results.values())
        
        return {
            "success": True,
            "message": f"Invitaciones de entrevista enviadas exitosamente",
            "emails_sent": emails_sent,
            "details": {
                "total_interviews": len(scheduled_interviews),
                "emails_successful": emails_sent,
                "emails_failed": len(scheduled_interviews) - emails_sent,
                "email_results": email_results
            }
        }
        
    except Exception as e:
        print(f"❌ Error enviando invitaciones: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error enviando invitaciones: {str(e)}")

# =============================================================================
# PUNTO DE ENTRADA DE LA APLICACIÓN
# =============================================================================

if __name__ == "__main__":
    """
    Punto de entrada principal de la aplicación.
    
    Inicia el servidor FastAPI en el puerto 8000.
    """
    print("🌐 Iniciando servidor API...")
    uvicorn.run(app, host="0.0.0.0", port=8000)