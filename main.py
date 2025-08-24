import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import uvicorn

from src.models import JobProfile, Candidate
from src.hr_workflow import HRWorkflow
from src.cv_reader import CVReader

# Cargar variables de entorno
load_dotenv()

# Configuración
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SMTP_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "email_user": os.getenv("EMAIL_USER", ""),
    "email_password": os.getenv("EMAIL_PASSWORD", "")
}
CALENDAR_CONFIG = {
    "calendar_id": os.getenv("CALENDAR_ID", ""),
    "credentials_file": os.getenv("GOOGLE_CREDENTIALS_FILE", "")
}

# Inicializar FastAPI
app = FastAPI(
    title="Sistema de Automatización de Selección de Personal",
    description="API para automatizar el proceso de reclutamiento usando IA",
    version="1.0.0"
)

# Inicializar workflow
hr_workflow = None

def initialize_workflow():
    """Inicializa el workflow de HR"""
    global hr_workflow
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no está configurada")
    
    hr_workflow = HRWorkflow(OPENAI_API_KEY, SMTP_CONFIG, CALENDAR_CONFIG)
    print("✅ Workflow de HR inicializado correctamente")

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    try:
        initialize_workflow()
    except Exception as e:
        print(f"❌ Error inicializando workflow: {str(e)}")

# Datos de ejemplo
EXAMPLE_JOB_PROFILE = JobProfile(
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

EXAMPLE_CVS = [
    """
    JUAN PÉREZ
    Email: juan.perez@email.com
    Teléfono: +54 11 1234-5678
    
    EXPERIENCIA PROFESIONAL:
    - Desarrollador Python Senior en TechCorp (2020-2024)
      * Desarrollo de APIs REST con FastAPI
      * Implementación de microservicios
      * Liderazgo técnico de equipo de 5 desarrolladores
    
    - Desarrollador Python en StartupXYZ (2018-2020)
      * Desarrollo backend con Django
      * Integración con bases de datos PostgreSQL
    
    HABILIDADES TÉCNICAS:
    - Python, Django, FastAPI, PostgreSQL, Docker, Git, AWS
    - Microservicios, APIs REST, CI/CD
    
    EDUCACIÓN:
    - Ingeniería en Sistemas, Universidad de Buenos Aires (2018)
    
    IDIOMAS:
    - Español (Nativo)
    - Inglés (Avanzado)
    """,
    
    """
    MARÍA GONZÁLEZ
    Email: maria.gonzalez@email.com
    Teléfono: +54 11 9876-5432
    
    EXPERIENCIA PROFESIONAL:
    - Desarrolladora Full Stack en DigitalSolutions (2021-2024)
      * Desarrollo frontend con React y backend con Python
      * Implementación de APIs REST
      * Experiencia con bases de datos MongoDB
    
    - Desarrolladora Junior en WebDev (2019-2021)
      * Desarrollo web con Python y JavaScript
      * Mantenimiento de aplicaciones existentes
    
    HABILIDADES TÉCNICAS:
    - Python, JavaScript, React, Node.js, MongoDB, Git
    - HTML, CSS, APIs REST
    
    EDUCACIÓN:
    - Licenciatura en Informática, Universidad Nacional (2019)
    
    IDIOMAS:
    - Español (Nativo)
    - Inglés (Intermedio)
    """,
    
    """
    CARLOS RODRÍGUEZ
    Email: carlos.rodriguez@email.com
    Teléfono: +54 11 5555-1234
    
    EXPERIENCIA PROFESIONAL:
    - Desarrollador Python en DataTech (2022-2024)
      * Análisis de datos con Python y pandas
      * Desarrollo de scripts de automatización
      * Experiencia básica con APIs
    
    - Analista de Datos en AnalyticsCorp (2020-2022)
      * Procesamiento de datos con Python
      * Creación de reportes y dashboards
    
    HABILIDADES TÉCNICAS:
    - Python, pandas, numpy, matplotlib, SQL
    - Jupyter Notebooks, Excel
    
    EDUCACIÓN:
    - Licenciatura en Estadística, Universidad de Córdoba (2020)
    
    IDIOMAS:
    - Español (Nativo)
    - Inglés (Básico)
    """
]

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema de Automatización de Selección de Personal",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Verificación de salud del sistema"""
    return {
        "status": "healthy",
        "openai_configured": bool(OPENAI_API_KEY),
        "smtp_configured": bool(SMTP_CONFIG["email_user"]),
        "calendar_configured": bool(CALENDAR_CONFIG["calendar_id"])
    }

@app.post("/process-recruitment")
async def process_recruitment(
    job_profile: JobProfile = None,
    cv_texts: List[str] = None
):
    """
    Procesa un proceso de reclutamiento completo
    
    Args:
        job_profile: Perfil del puesto de trabajo
        cv_texts: Lista de CVs en texto plano
    
    Returns:
        Resultado del procesamiento
    """
    if not hr_workflow:
        raise HTTPException(status_code=500, detail="Workflow no inicializado")
    
    # Usar datos de ejemplo si no se proporcionan
    if job_profile is None:
        job_profile = EXAMPLE_JOB_PROFILE
    
    if cv_texts is None:
        cv_texts = EXAMPLE_CVS
    
    try:
        # Ejecutar workflow
        result = hr_workflow.run_workflow(job_profile, cv_texts)
        
        return {
            "success": True,
            "message": "Proceso de reclutamiento completado",
            "data": {
                "total_candidates": len(result["candidates"]),
                "selected_candidates": len(result["selected_candidates"]),
                "rejected_candidates": len(result["rejected_candidates"]),
                "emails_sent": result["processing_state"].emails_sent,
                "interviews_scheduled": result["processing_state"].interviews_scheduled,
                "processing_time": result["processing_state"].candidates_processed
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento: {str(e)}")

@app.post("/upload-cvs")
async def upload_cvs(file: UploadFile = File(...)):
    """
    Sube un archivo con CVs para procesar
    
    Args:
        file: Archivo de texto con CVs (uno por línea)
    
    Returns:
        Lista de CVs extraídos
    """
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .txt")
    
    try:
        content = await file.read()
        cv_texts = content.decode('utf-8').split('\n\n')
        cv_texts = [cv.strip() for cv in cv_texts if cv.strip()]
        
        return {
            "success": True,
            "cvs_extracted": len(cv_texts),
            "cv_texts": cv_texts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")

@app.post("/process-cvs-from-folder")
async def process_cvs_from_folder():
    """
    Procesa CVs desde la carpeta 'curriculums/'
    
    Returns:
        Información de los CVs encontrados
    """
    try:
        cv_reader = CVReader()
        cvs = cv_reader.read_all_cvs()
        
        return {
            "success": True,
            "cvs_found": len(cvs),
            "cv_files": [cv['file_name'] for cv in cvs],
            "cv_details": [
                {
                    "file_name": cv['file_name'],
                    "file_size": cv['file_size'],
                    "text_length": len(cv['text'])
                }
                for cv in cvs
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando CVs: {str(e)}")

@app.post("/process-recruitment-from-folder")
async def process_recruitment_from_folder(
    job_profile: JobProfile = None
):
    """
    Procesa un reclutamiento completo usando CVs desde la carpeta 'curriculums/'
    
    Args:
        job_profile: Perfil del puesto de trabajo
    
    Returns:
        Resultado del procesamiento
    """
    if not hr_workflow:
        raise HTTPException(status_code=500, detail="Workflow no inicializado")
    
    # Usar perfil de ejemplo si no se proporciona
    if job_profile is None:
        job_profile = EXAMPLE_JOB_PROFILE
    
    try:
        # Leer CVs desde la carpeta
        cv_reader = CVReader()
        cv_texts = cv_reader.get_cv_texts()
        
        if not cv_texts:
            raise HTTPException(status_code=404, detail="No se encontraron CVs en la carpeta 'curriculums/'")
        
        # Ejecutar workflow
        result = hr_workflow.run_workflow(job_profile, cv_texts)
        
        return {
            "success": True,
            "message": "Proceso de reclutamiento completado",
            "data": {
                "total_candidates": len(result["candidates"]),
                "selected_candidates": len(result["selected_candidates"]),
                "rejected_candidates": len(result["rejected_candidates"]),
                "emails_sent": result["processing_state"].emails_sent,
                "interviews_scheduled": result["processing_state"].interviews_scheduled,
                "processing_time": result["processing_state"].candidates_processed
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el procesamiento: {str(e)}")

@app.get("/download-report/{report_type}")
async def download_report(report_type: str):
    """
    Descarga un reporte generado
    
    Args:
        report_type: Tipo de reporte (summary, detailed, excel)
    
    Returns:
        Archivo del reporte
    """
    filename = None
    
    if report_type == "summary":
        filename = "reportes/reporte_resumen.txt"
    elif report_type == "detailed":
        filename = "reportes/reporte_detallado.json"
    elif report_type == "excel":
        # Buscar el archivo Excel más reciente
        import glob
        excel_files = glob.glob("reportes/reporte_reclutamiento_*.xlsx")
        if excel_files:
            filename = max(excel_files, key=os.path.getctime)
    
    if not filename or not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    return FileResponse(filename, filename=filename)

@app.get("/example-data")
async def get_example_data():
    """Obtiene datos de ejemplo para testing"""
    return {
        "job_profile": EXAMPLE_JOB_PROFILE.dict(),
        "cv_count": len(EXAMPLE_CVS),
        "cv_preview": [cv[:200] + "..." for cv in EXAMPLE_CVS]
    }

def run_example():
    """Ejecuta un ejemplo del sistema"""
    print("🚀 Ejecutando ejemplo del sistema de selección de personal...")
    
    try:
        # Inicializar workflow
        initialize_workflow()
        
        # Ejecutar proceso de reclutamiento
        result = hr_workflow.run_workflow(EXAMPLE_JOB_PROFILE, EXAMPLE_CVS)
        
        print("\n" + "="*60)
        print("📊 RESULTADOS DEL EJEMPLO:")
        print("="*60)
        
        print(f"👥 Total de candidatos procesados: {len(result['candidates'])}")
        print(f"✅ Candidatos seleccionados: {len(result['selected_candidates'])}")
        print(f"❌ Candidatos rechazados: {len(result['rejected_candidates'])}")
        
        if result['selected_candidates']:
            print("\n🏆 TOP CANDIDATOS SELECCIONADOS:")
            for i, candidate in enumerate(result['selected_candidates'], 1):
                print(f"{i}. {candidate.name} - {candidate.match_score}/100")
                print(f"   Email: {candidate.email}")
                print(f"   Habilidades: {', '.join(candidate.skills[:3])}")
        
        print(f"\n📧 Emails enviados: {result['processing_state'].emails_sent}")
        print(f"📅 Entrevistas programadas: {result['processing_state'].interviews_scheduled}")
        
        print("\n✅ Ejemplo completado exitosamente!")
        print("📁 Los reportes se han guardado en:")
        print("   - reportes/reporte_resumen.txt")
        print("   - reportes/reporte_detallado.json")
        print("   - reportes/reporte_reclutamiento_*.xlsx")
        
    except Exception as e:
        print(f"❌ Error ejecutando ejemplo: {str(e)}")

def run_example_with_folder_cvs():
    """Ejecuta un ejemplo usando CVs desde la carpeta"""
    print("🚀 Ejecutando ejemplo con CVs desde la carpeta...")
    
    try:
        # Inicializar workflow
        initialize_workflow()
        
        # Leer CVs desde la carpeta
        cv_reader = CVReader()
        cv_texts = cv_reader.get_cv_texts()
        
        if not cv_texts:
            print("❌ No se encontraron CVs en la carpeta 'curriculums/'")
            print("💡 Ejecuta 'python create_sample_cvs.py' para crear CVs de ejemplo")
            return
        
        print(f"📄 CVs encontrados: {len(cv_texts)}")
        
        # Ejecutar proceso de reclutamiento
        result = hr_workflow.run_workflow(EXAMPLE_JOB_PROFILE, cv_texts)
        
        print("\n" + "="*60)
        print("📊 RESULTADOS DEL EJEMPLO CON CVs DE CARPETA:")
        print("="*60)
        
        print(f"👥 Total de candidatos procesados: {len(result['candidates'])}")
        print(f"✅ Candidatos seleccionados: {len(result['selected_candidates'])}")
        print(f"❌ Candidatos rechazados: {len(result['rejected_candidates'])}")
        
        if result['selected_candidates']:
            print("\n🏆 TOP CANDIDATOS SELECCIONADOS:")
            for i, candidate in enumerate(result['selected_candidates'], 1):
                print(f"{i}. {candidate.name} - {candidate.match_score}/100")
                print(f"   Email: {candidate.email}")
                print(f"   Habilidades: {', '.join(candidate.skills[:3])}")
        
        print(f"\n📧 Emails enviados: {result['processing_state'].emails_sent}")
        print(f"📅 Entrevistas programadas: {result['processing_state'].interviews_scheduled}")
        
        print("\n✅ Ejemplo con CVs de carpeta completado exitosamente!")
        print("📁 Los reportes se han guardado en:")
        print("   - reportes/reporte_resumen.txt")
        print("   - reportes/reporte_detallado.json")
        print("   - reportes/reporte_reclutamiento_*.xlsx")
        
    except Exception as e:
        print(f"❌ Error ejecutando ejemplo: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "example":
            # Ejecutar ejemplo con CVs hardcodeados
            run_example()
        elif sys.argv[1] == "example-folder":
            # Ejecutar ejemplo con CVs desde la carpeta
            run_example_with_folder_cvs()
        else:
            print("❌ Opción no válida")
            print("💡 Opciones disponibles:")
            print("   - python main.py (inicia el servidor API)")
            print("   - python main.py example (ejemplo con CVs hardcodeados)")
            print("   - python main.py example-folder (ejemplo con CVs de la carpeta)")
    else:
        # Ejecutar servidor API
        print("🌐 Iniciando servidor API...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
