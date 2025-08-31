import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import json
from .models import Candidate, JobProfile, RecruitmentReport, ProcessingState

class ReportAgent:
    """Generador de reportes de reclutamiento"""
    
    def __init__(self):
        self.report_templates = {
            "summary": self._generate_summary_report,
            "detailed": self._generate_detailed_report,
            "excel": self._generate_excel_report
        }
    
    def generate_report(self, candidates: List[Candidate], job_profile: JobProfile,
                       processing_state: ProcessingState, report_type: str = "summary") -> RecruitmentReport:
        """Genera un reporte de reclutamiento"""
        
        # Calcular estadísticas
        total_candidates = len(candidates)
        selected_candidates = len([c for c in candidates if c.status.value in ["selected", "interview_scheduled"]])
        rejected_candidates = len([c for c in candidates if c.status.value == "rejected"])
        average_score = sum(c.match_score for c in candidates) / total_candidates if total_candidates > 0 else 0
        
        # Obtener top candidatos
        top_candidates = sorted(candidates, key=lambda x: x.match_score, reverse=True)[:5]
        
        # Crear reporte
        report = RecruitmentReport(
            job_profile=job_profile,
            total_candidates=total_candidates,
            selected_candidates=selected_candidates,
            rejected_candidates=rejected_candidates,
            average_match_score=average_score,
            top_candidates=top_candidates,
            processing_time=processing_state.candidates_processed
        )
        
        return report
    
    def _generate_summary_report(self, report: RecruitmentReport) -> str:
        """Genera un reporte resumido en texto"""
        
        summary = f"""
        ========================================
        REPORTE DE RECLUTAMIENTO
        ========================================
        
        Perfil del Puesto: {report.job_profile.title}
        Fecha de Generación: {report.generated_at.strftime('%d/%m/%Y %H:%M')}
        
        ESTADÍSTICAS GENERALES:
        - Total de Candidatos: {report.total_candidates}
        - Candidatos Seleccionados: {report.selected_candidates}
        - Candidatos Rechazados: {report.rejected_candidates}
        - Puntaje Promedio: {report.average_match_score:.1f}/100
        
        TOP 5 CANDIDATOS:
        """
        
        for i, candidate in enumerate(report.top_candidates, 1):
            summary += f"""
        {i}. {candidate.name}
           - Email: {candidate.email}
           - Puntaje: {candidate.match_score:.1f}/100
           - Experiencia: {candidate.experience_years} años
           - Habilidades: {', '.join(candidate.skills[:3])}
           - Estado: {candidate.status.value}
            """
        
        summary += f"""
        
        PERFIL DEL PUESTO:
        - Título: {report.job_profile.title}
        - Experiencia Requerida: {report.job_profile.experience_years} años
        - Habilidades: {', '.join(report.job_profile.skills)}
        - Idiomas: {', '.join(report.job_profile.languages)}
        - Ubicación: {report.job_profile.location}
        
        ========================================
        """
        
        return summary
    
    def _generate_detailed_report(self, report: RecruitmentReport) -> Dict[str, Any]:
        """Genera un reporte detallado en formato JSON"""
        
        detailed_report = {
            "metadata": {
                "job_title": report.job_profile.title,
                "generated_at": report.generated_at.isoformat(),
                "total_candidates": report.total_candidates,
                "processing_time": report.processing_time
            },
            "statistics": {
                "selected_count": report.selected_candidates,
                "rejected_count": report.rejected_candidates,
                "pending_count": report.total_candidates - report.selected_candidates - report.rejected_candidates,
                "average_score": round(report.average_match_score, 2),
                "score_distribution": self._calculate_score_distribution(report.top_candidates)
            },
            "job_profile": {
                "title": report.job_profile.title,
                "requirements": report.job_profile.requirements,
                "skills": report.job_profile.skills,
                "experience_years": report.job_profile.experience_years,
                "languages": report.job_profile.languages,
                "location": report.job_profile.location,
                "description": report.job_profile.description
            },
            "top_candidates": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "match_score": c.match_score,
                    "experience_years": c.experience_years,
                    "skills": c.skills,
                    "languages": c.languages,
                    "education": c.education,
                    "status": c.status.value,
                    "notes": c.notes
                }
                for c in report.top_candidates
            ],
            "recommendations": self._generate_recommendations(report)
        }
        
        return detailed_report
    
    def _generate_excel_report(self, report: RecruitmentReport, filename: str = None) -> str:
        """Genera un reporte en formato Excel"""
        
        if filename is None:
            # Crear carpeta de reportes si no existe
            import os
            os.makedirs("reports", exist_ok=True)
            filename = f"reports/reporte_reclutamiento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Crear DataFrame con todos los candidatos
        candidates_data = []
        for candidate in report.top_candidates:
            candidates_data.append({
                "ID": candidate.id,
                "Nombre": candidate.name,
                "Email": candidate.email,
                "Teléfono": candidate.phone or "",
                "Puntaje": candidate.match_score,
                "Años Experiencia": candidate.experience_years,
                "Habilidades": ", ".join(candidate.skills),
                "Idiomas": ", ".join(candidate.languages),
                "Educación": ", ".join(candidate.education),
                "Estado": candidate.status.value,
                "Notas": candidate.notes or ""
            })
        
        df_candidates = pd.DataFrame(candidates_data)
        
        # Crear DataFrame con estadísticas
        stats_data = {
            "Métrica": [
                "Total Candidatos",
                "Candidatos Seleccionados", 
                "Candidatos Rechazados",
                "Puntaje Promedio",
                "Perfil del Puesto",
                "Experiencia Requerida",
                "Ubicación"
            ],
            "Valor": [
                report.total_candidates,
                report.selected_candidates,
                report.rejected_candidates,
                f"{report.average_match_score:.1f}/100",
                report.job_profile.title,
                f"{report.job_profile.experience_years} años",
                report.job_profile.location
            ]
        }
        
        df_stats = pd.DataFrame(stats_data)
        
        # Crear archivo Excel
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            df_candidates.to_excel(writer, sheet_name='Candidatos', index=False)
            df_stats.to_excel(writer, sheet_name='Estadísticas', index=False)
            
            # Obtener el workbook y worksheet para formateo
            workbook = writer.book
            worksheet_candidates = writer.sheets['Candidatos']
            worksheet_stats = writer.sheets['Estadísticas']
            
            # Formatear columnas
            for i, col in enumerate(df_candidates.columns):
                max_length = max(
                    df_candidates[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet_candidates.set_column(i, i, max_length + 2)
            
            for i, col in enumerate(df_stats.columns):
                max_length = max(
                    df_stats[col].astype(str).apply(len).max(),
                    len(col)
                )
                worksheet_stats.set_column(i, i, max_length + 2)
        
        return filename
    
    def _calculate_score_distribution(self, candidates: List[Candidate]) -> Dict[str, int]:
        """Calcula la distribución de puntajes"""
        distribution = {
            "90-100": 0,
            "80-89": 0,
            "70-79": 0,
            "60-69": 0,
            "0-59": 0
        }
        
        for candidate in candidates:
            score = candidate.match_score
            if score >= 90:
                distribution["90-100"] += 1
            elif score >= 80:
                distribution["80-89"] += 1
            elif score >= 70:
                distribution["70-79"] += 1
            elif score >= 60:
                distribution["60-69"] += 1
            else:
                distribution["0-59"] += 1
        
        return distribution
    
    def _generate_recommendations(self, report: RecruitmentReport) -> List[str]:
        """Genera recomendaciones basadas en los resultados"""
        recommendations = []
        
        if report.selected_candidates == 0:
            recommendations.append("No se encontraron candidatos que cumplan los criterios mínimos. Considerar revisar los requisitos del puesto.")
        
        if report.average_match_score < 60:
            recommendations.append("El puntaje promedio es bajo. Considerar ajustar los criterios de evaluación o ampliar la búsqueda.")
        
        if report.selected_candidates > 10:
            recommendations.append("Hay muchos candidatos seleccionados. Considerar aumentar los criterios de filtrado para la siguiente fase.")
        
        if report.total_candidates < 5:
            recommendations.append("Pocos candidatos en la base. Considerar ampliar las fuentes de reclutamiento.")
        
        return recommendations
