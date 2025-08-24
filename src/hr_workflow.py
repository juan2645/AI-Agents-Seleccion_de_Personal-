from langgraph.graph import StateGraph, END
from typing import Dict, List, Any, TypedDict
import time
from datetime import datetime
from .models import (
    Candidate, JobProfile, ProcessingState, CandidateStatus, 
    InterviewSchedule, RecruitmentReport
)
from .cv_analyzer import CVAnalyzer
from .email_manager import EmailManager
from .calendar_manager import CalendarManager
from .report_generator import ReportGenerator

class WorkflowState(TypedDict):
    """Estado del workflow de reclutamiento"""
    job_profile: JobProfile
    cv_texts: List[str]
    candidates: List[Candidate]
    selected_candidates: List[Candidate]
    rejected_candidates: List[Candidate]
    interviews_scheduled: List[InterviewSchedule]
    emails_sent: Dict[str, bool]
    processing_state: ProcessingState
    report: RecruitmentReport
    human_approval_required: bool
    errors: List[str]

class HRWorkflow:
    """Workflow principal de reclutamiento usando LangGraph"""
    
    def __init__(self, openai_api_key: str, smtp_config: Dict[str, str], 
                 calendar_config: Dict[str, str]):
        
        # Inicializar componentes
        self.cv_analyzer = CVAnalyzer(openai_api_key)
        self.email_manager = EmailManager(openai_api_key, smtp_config)
        self.calendar_manager = CalendarManager(calendar_config)
        self.report_generator = ReportGenerator()
        
        # Crear el grafo de workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Crea el grafo de workflow usando LangGraph"""
        
        workflow = StateGraph(WorkflowState)
        
        # Agregar nodos
        workflow.add_node("analyze_cvs", self._analyze_cvs_node)
        workflow.add_node("rank_candidates", self._rank_candidates_node)
        workflow.add_node("human_review", self._human_review_node)
        workflow.add_node("send_emails", self._send_emails_node)
        workflow.add_node("schedule_interviews", self._schedule_interviews_node)
        workflow.add_node("generate_report", self._generate_report_node)
        
        # Definir el flujo
        workflow.set_entry_point("analyze_cvs")
        
        workflow.add_edge("analyze_cvs", "rank_candidates")
        workflow.add_edge("rank_candidates", "human_review")
        workflow.add_edge("human_review", "send_emails")
        workflow.add_edge("send_emails", "schedule_interviews")
        workflow.add_edge("schedule_interviews", "generate_report")
        workflow.add_edge("generate_report", END)
        
        # Agregar condicionales para human review
        workflow.add_conditional_edges(
            "human_review",
            self._should_require_human_approval,
            {
                "approve": "send_emails",
                "review": "human_review"
            }
        )
        
        return workflow.compile()
    
    def _analyze_cvs_node(self, state: WorkflowState) -> WorkflowState:
        """Nodo para analizar CVs"""
        print("🔍 Analizando CVs...")
        
        candidates = []
        processing_state = state.get("processing_state", ProcessingState(
            current_step="analyze_cvs",
            total_steps=5,
            candidates_processed=0,
            emails_sent=0,
            interviews_scheduled=0
        ))
        
        for i, cv_text in enumerate(state["cv_texts"]):
            try:
                candidate = self.cv_analyzer.analyze_cv(cv_text, state["job_profile"])
                candidates.append(candidate)
                processing_state.candidates_processed += 1
                print(f"  ✓ CV {i+1} analizado: {candidate.name} - {candidate.match_score}/100")
            except Exception as e:
                print(f"  ✗ Error analizando CV {i+1}: {str(e)}")
                state["errors"].append(f"Error en CV {i+1}: {str(e)}")
        
        processing_state.current_step = "rank_candidates"
        state["candidates"] = candidates
        state["processing_state"] = processing_state
        
        return state
    
    def _rank_candidates_node(self, state: WorkflowState) -> WorkflowState:
        """Nodo para rankear candidatos"""
        print("📊 Rankeando candidatos...")
        
        candidates = state["candidates"]
        
        # Filtrar candidatos por puntaje mínimo
        min_score = 70.0
        qualified_candidates = self.cv_analyzer.filter_candidates(candidates, min_score)
        
        # Rankear candidatos
        ranked_candidates = self.cv_analyzer.rank_candidates(qualified_candidates, top_n=10)
        
        # Separar candidatos seleccionados y rechazados
        selected = []
        rejected = []
        
        for candidate in candidates:
            if candidate.match_score >= min_score and candidate in ranked_candidates[:5]:
                candidate.status = CandidateStatus.SELECTED
                selected.append(candidate)
            else:
                candidate.status = CandidateStatus.REJECTED
                rejected.append(candidate)
        
        state["selected_candidates"] = selected
        state["rejected_candidates"] = rejected
        state["processing_state"].current_step = "human_review"
        
        print(f"  ✓ {len(selected)} candidatos seleccionados")
        print(f"  ✓ {len(rejected)} candidatos rechazados")
        
        return state
    
    def _human_review_node(self, state: WorkflowState) -> WorkflowState:
        """Nodo para revisión humana (human in the loop)"""
        print("👤 Revisión humana requerida...")
        
        # Simular revisión humana
        # En un caso real, aquí se mostraría una interfaz para que el reclutador revise
        selected_candidates = state["selected_candidates"]
        
        print("\n" + "="*50)
        print("CANDIDATOS SELECCIONADOS PARA REVISIÓN:")
        print("="*50)
        
        for i, candidate in enumerate(selected_candidates, 1):
            print(f"\n{i}. {candidate.name}")
            print(f"   Email: {candidate.email}")
            print(f"   Puntaje: {candidate.match_score}/100")
            print(f"   Experiencia: {candidate.experience_years} años")
            print(f"   Habilidades: {', '.join(candidate.skills[:3])}")
            print(f"   Notas: {candidate.notes}")
        
        print("\n" + "="*50)
        print("¿Desea proceder con el envío de emails? (s/n): s")
        print("="*50)
        
        # Por ahora, asumimos que se aprueba automáticamente
        state["human_approval_required"] = False
        state["processing_state"].current_step = "send_emails"
        
        return state
    
    def _should_require_human_approval(self, state: WorkflowState) -> str:
        """Determina si se requiere aprobación humana"""
        if state.get("human_approval_required", False):
            return "review"
        return "approve"
    
    def _send_emails_node(self, state: WorkflowState) -> WorkflowState:
        """Nodo para enviar emails"""
        print("📧 Enviando emails...")
        
        emails_sent = {}
        
        # Enviar emails de rechazo
        if state["rejected_candidates"]:
            print("  Enviando emails de rechazo...")
            rejection_results = self.email_manager.send_bulk_emails(
                state["rejected_candidates"],
                "rejected",
                state["job_profile"].title
            )
            emails_sent.update(rejection_results)
        
        # Enviar emails de selección
        if state["selected_candidates"]:
            print("  Enviando emails de selección...")
            selection_results = self.email_manager.send_bulk_emails(
                state["selected_candidates"],
                "selected",
                state["job_profile"].title
            )
            emails_sent.update(selection_results)
        
        state["emails_sent"] = emails_sent
        state["processing_state"].emails_sent = len([s for s in emails_sent.values() if s])
        state["processing_state"].current_step = "schedule_interviews"
        
        print(f"  ✓ {state['processing_state'].emails_sent} emails enviados")
        
        return state
    
    def _schedule_interviews_node(self, state: WorkflowState) -> WorkflowState:
        """Nodo para programar entrevistas"""
        print("📅 Programando entrevistas...")
        
        interviews_scheduled = []
        
        for candidate in state["selected_candidates"]:
            try:
                # Obtener slots disponibles
                start_date = datetime.now()
                available_slots = self.calendar_manager.get_available_slots(start_date, days_ahead=7)
                
                if available_slots:
                    # Seleccionar el primer slot disponible
                    slot = available_slots[0]
                    interview = self.calendar_manager.schedule_interview(
                        candidate=candidate,
                        preferred_date=slot["datetime"],
                        interview_type="technical"
                    )
                    
                    interviews_scheduled.append(interview)
                    candidate.status = CandidateStatus.INTERVIEW_SCHEDULED
                    
                    # Enviar invitación de calendario
                    self.calendar_manager.send_calendar_invitation(interview, candidate)
                    
                    print(f"  ✓ Entrevista programada para {candidate.name}: {slot['date']} {slot['time']}")
                else:
                    print(f"  ⚠ No hay slots disponibles para {candidate.name}")
                    
            except Exception as e:
                print(f"  ✗ Error programando entrevista para {candidate.name}: {str(e)}")
                state["errors"].append(f"Error programando entrevista para {candidate.name}: {str(e)}")
        
        state["interviews_scheduled"] = interviews_scheduled
        state["processing_state"].interviews_scheduled = len(interviews_scheduled)
        state["processing_state"].current_step = "generate_report"
        
        print(f"  ✓ {len(interviews_scheduled)} entrevistas programadas")
        
        return state
    
    def _generate_report_node(self, state: WorkflowState) -> WorkflowState:
        """Nodo para generar reporte final"""
        print("📋 Generando reporte final...")
        
        all_candidates = state["candidates"]
        job_profile = state["job_profile"]
        processing_state = state["processing_state"]
        
        # Generar reporte
        report = self.report_generator.generate_report(
            candidates=all_candidates,
            job_profile=job_profile,
            processing_state=processing_state
        )
        
        # Generar reporte en diferentes formatos
        summary_report = self.report_generator._generate_summary_report(report)
        detailed_report = self.report_generator._generate_detailed_report(report)
        excel_filename = self.report_generator._generate_excel_report(report)
        
        state["report"] = report
        state["processing_state"].current_step = "completed"
        
        # Crear carpeta de reportes si no existe
        import os
        os.makedirs("reportes", exist_ok=True)
        
        # Guardar reportes
        with open("reportes/reporte_resumen.txt", "w", encoding="utf-8") as f:
            f.write(summary_report)
        
        with open("reportes/reporte_detallado.json", "w", encoding="utf-8") as f:
            import json
            json.dump(detailed_report, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Reporte generado: {excel_filename}")
        print(f"  ✓ Reporte resumen: reportes/reporte_resumen.txt")
        print(f"  ✓ Reporte detallado: reportes/reporte_detallado.json")
        
        return state
    
    def run_workflow(self, job_profile: JobProfile, cv_texts: List[str]) -> Dict[str, Any]:
        """Ejecuta el workflow completo de reclutamiento"""
        
        print("🚀 Iniciando workflow de reclutamiento...")
        print(f"📋 Perfil: {job_profile.title}")
        print(f"📄 CVs a procesar: {len(cv_texts)}")
        print("="*60)
        
        start_time = time.time()
        
        # Estado inicial
        initial_state = WorkflowState(
            job_profile=job_profile,
            cv_texts=cv_texts,
            candidates=[],
            selected_candidates=[],
            rejected_candidates=[],
            interviews_scheduled=[],
            emails_sent={},
            processing_state=ProcessingState(
                current_step="start",
                total_steps=5,
                candidates_processed=0,
                emails_sent=0,
                interviews_scheduled=0
            ),
            report=None,
            human_approval_required=False,
            errors=[]
        )
        
        # Ejecutar workflow
        try:
            final_state = self.workflow.invoke(initial_state)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print("\n" + "="*60)
            print("✅ WORKFLOW COMPLETADO")
            print("="*60)
            print(f"⏱️  Tiempo total: {processing_time:.2f} segundos")
            print(f"👥 Candidatos procesados: {len(final_state['candidates'])}")
            print(f"✅ Candidatos seleccionados: {len(final_state['selected_candidates'])}")
            print(f"❌ Candidatos rechazados: {len(final_state['rejected_candidates'])}")
            print(f"📧 Emails enviados: {final_state['processing_state'].emails_sent}")
            print(f"📅 Entrevistas programadas: {final_state['processing_state'].interviews_scheduled}")
            
            if final_state["errors"]:
                print(f"⚠️  Errores: {len(final_state['errors'])}")
                for error in final_state["errors"]:
                    print(f"   - {error}")
            
            return final_state
            
        except Exception as e:
            print(f"❌ Error en workflow: {str(e)}")
            raise
