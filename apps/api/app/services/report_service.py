import logging
import datetime
from typing import Dict, Any
from supabase import Client
# Nota: fpdf2 o reportlab deberían estar en requirements.txt
# Para este MVP usaremos una estructura de datos que luego el endpoint convertirá o servirá.

from fpdf import FPDF
import io

from .artifact_service import ArtifactService

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.artifacts = ArtifactService()

    async def get_solution_summary(self, solution_id: str) -> Dict[str, Any]:
        """Fetches a structured summary for the report"""
        # 1. Solution Info
        sol_res = self.supabase.table("solutions").select("*").eq("id", solution_id).single().execute()
        solution = sol_res.data
        if not solution:
             raise Exception(f"Solution {solution_id} not found")

        # 2. Asset count by type
        assets_res = self.supabase.table("asset").select("asset_id, asset_type, name_display").eq("project_id", solution_id).execute()
        assets = assets_res.data or []
        
        asset_types = {}
        for a in assets:
            at = a.get("asset_type", "Unknown")
            asset_types[at] = asset_types.get(at, 0) + 1
        
        # 3. Last job run
        job_res = self.supabase.table("job_run").select("*").eq("project_id", solution_id).order("created_at", desc=True).limit(1).execute()
        last_job = job_res.data[0] if job_res.data else None

        # 4. Audit statistics
        audit_res = self.supabase.table("file_processing_log")\
            .select("model_used, total_tokens, cost_estimate_usd")\
            .eq("job_id", last_job["job_id"] if last_job else "")\
            .execute()
        
        total_cost = sum([float(x.get("cost_estimate_usd") or 0) for x in audit_res.data])
        total_tokens = sum([int(x.get("total_tokens") or 0) for x in audit_res.data])

        # 5. Relationships (Edges)
        edges_res = self.supabase.table("edge_index").select("edge_type").eq("project_id", solution_id).execute()
        edges = edges_res.data or []
        edge_types = {}
        for e in edges:
            et = e.get("edge_type", "DEPENDS_ON")
            edge_types[et] = edge_types.get(et, 0) + 1

        # 6. Packages
        pkg_res = self.supabase.table("package").select("name, type").eq("project_id", solution_id).execute()
        packages = pkg_res.data or []

        return {
            "solution_name": solution.get("name", "Unknown"),
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": solution.get("status", "N/A"),
            "asset_count": len(assets),
            "asset_types": asset_types,
            "top_assets": assets[:15],  # List first 15 as sample
            "edge_count": len(edges),
            "edge_types": edge_types,
            "packages": packages,
            "last_job": {
                "status": last_job["status"] if last_job else "N/A",
                "cost_usd": total_cost,
                "tokens": total_tokens
            },
            "report_title": f"Nexus Discovery AI - Technical Architecture Report"
        }

    def generate_pdf_buffer(self, data: Dict[str, Any]):
        """Generates the PDF binary using fpdf2 with a professional design"""
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, 'Nexus Discovery AI | Confidential Technical Report', 0, 0, 'R')
                self.ln(15)

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(150, 150, 150)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # --- COVER SECTION ---
        pdf.set_fill_color(30, 41, 59) # Dark blue / Slate
        pdf.rect(0, 0, 210, 40, 'F')
        
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 20)
        pdf.cell(0, 20, data['report_title'], ln=True, align='L')
        
        pdf.set_font("Helvetica", '', 12)
        pdf.cell(0, 10, f"Solution: {data['solution_name']}", ln=True, align='L')
        pdf.ln(20)
        
        pdf.set_text_color(0, 0, 0)
        
        # --- EXECUTIVE SUMMARY ---
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 10, "1. Executive Summary", ln=True)
        pdf.set_draw_color(226, 232, 240)
        pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        
        summary_info = [
            ("Infrastructure Status", data['status']),
            ("Total Assets Discovered", str(data['asset_count'])),
            ("Total Dependencies Mapped", str(data['edge_count'])),
            ("Packages Identified", str(len(data['packages']))),
            ("Report Generated On", data['generated_at'])
        ]
        
        for label, val in summary_info:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(50, 8, f"{label}:", 0)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, val, 0, 1)
        
        pdf.ln(10)
        
        # --- ASSET INVENTORY ---
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 10, "2. Asset Inventory Analysis", ln=True)
        pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 6, "The following distribution represents the diversity of technical assets identified within the provided source code and metadata.")
        pdf.ln(3)
        
        # table header
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(80, 8, "Asset Type", 1, 0, 'C', True)
        pdf.cell(40, 8, "Count", 1, 1, 'C', True)
        
        pdf.set_font("Arial", '', 10)
        for atype, count in data['asset_types'].items():
            pdf.cell(80, 8, atype, 1, 0, 'L')
            pdf.cell(40, 8, str(count), 1, 1, 'C')
        
        pdf.ln(10)
        
        # --- DEPENDENCY MAP ---
        if data['edge_types']:
            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(0, 10, "3. Dependency & Flow Analysis", ln=True)
            pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, "Analysis of the relationships between assets reveals the internal data flow and service dependencies.")
            pdf.ln(3)
            
            pdf.set_fill_color(241, 245, 249)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(80, 8, "Relationship Type", 1, 0, 'C', True)
            pdf.cell(40, 8, "Count", 1, 1, 'C', True)
            
            pdf.set_font("Arial", '', 10)
            for etype, count in data['edge_types'].items():
                pdf.cell(80, 8, etype, 1, 0, 'L')
                pdf.cell(40, 8, str(count), 1, 1, 'C')
            
            pdf.ln(10)

        # --- PACKAGES ---
        if data['packages']:
            pdf.set_font("Arial", 'B', 14)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(0, 10, "4. Discovered Packages (SSIS/DataStage)", ln=True)
            pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 10)
            for pkg in data['packages'][:20]: # Show top 20
                pdf.cell(0, 7, f"- {pkg['name']} ({pkg['type']})", ln=True)
            
            pdf.ln(10)

        # --- COST METRICS ---
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(0, 10, "5. Analysis Performance & Cost", ln=True)
        pdf.line(pdf.get_x(), pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(0, 0, 0)
        last_job = data.get('last_job', {})
        metrics = [
            ("Execution Status", last_job.get('status', 'N/A')),
            ("Estimated AI Cost", f"${last_job.get('cost_usd', 0):.4f} USD"),
            ("Total Tokens Processed", f"{last_job.get('total_tokens', data.get('last_job', {}).get('tokens', 0))}")
        ]
        
        for label, val in metrics:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(50, 8, f"{label}:", 0)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, val, 0, 1)

        # Output to bytes
        return bytes(pdf.output())

    def generate_markdown_summary(self, data: Dict[str, Any]) -> str:
        """Generates a professional Markdown summary of the discovery."""
        md = f"# Architecture Discovery Report: {data['solution_name']}\n\n"
        md += f"*Generated on: {data['generated_at']}*\n\n"
        
        md += "## Executive Summary\n"
        md += f"- **Status**: {data['status']}\n"
        md += f"- **Total Assets**: {data['asset_count']}\n"
        md += f"- **Total Dependencies**: {data['edge_count']}\n"
        md += f"- **Packages Identified**: {len(data['packages'])}\n\n"
        
        md += "## Asset Inventory\n"
        md += "| Asset Type | Count |\n| --- | --- |\n"
        for atype, count in data['asset_types'].items():
            md += f"| {atype} | {count} |\n"
        md += "\n"
        
        if data['edge_types']:
            md += "## Dependency Analysis\n"
            md += "| Relationship Type | Count |\n| --- | --- |\n"
            for etype, count in data['edge_types'].items():
                md += f"| {etype} | {count} |\n"
            md += "\n"
        
        md += "## Performance & Intelligence Metrics\n"
        last_job = data.get('last_job', {})
        md += f"- **Tokens Processed**: {last_job.get('tokens', 0)}\n"
        md += f"- **Estimated Cost**: ${last_job.get('cost_usd', 0):.4f} USD\n"
        
        return md

    async def generate_and_save_latest_artifacts(self, solution_id: str):
        """
        Creates both PDF and MD reports for the latest state of the solution
        and saves them to the Artifact Sandbox.
        """
        try:
            print(f"[REPORTS] Generating automated artifacts for solution {solution_id}")
            data = await self.get_solution_summary(solution_id)
            
            # 1. PDF
            pdf_bytes = self.generate_pdf_buffer(data)
            self.artifacts.save_artifact(solution_id, "architecture_report.pdf", pdf_bytes)
            
            # 2. Markdown
            md_content = self.generate_markdown_summary(data)
            self.artifacts.save_artifact(solution_id, "architecture_report.md", md_content)
            
            print(f"[REPORTS] Successfully saved artifacts for {solution_id}")
        except Exception as e:
            logger.error(f"Failed to generate automated artifacts: {e}")
            print(f"[REPORTS] ERROR: {e}")
