from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from supabase import create_client, Client
from ..config import settings
from ..services.report_service import ReportService
from ..services.catalog import CatalogService

router = APIRouter(prefix="/solutions", tags=["solutions"])

def get_supabase():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@router.get("")
async def list_solutions(supabase: Client = Depends(get_supabase)):
    """Returns a list of all projects/solutions."""
    res = supabase.table("solutions").select("id, name").execute()
    return res.data

@router.get("/{solution_id}/report/pdf")
async def get_solution_report_pdf(solution_id: str, supabase: Client = Depends(get_supabase)):
    report_service = ReportService(supabase)
    try:
        data = await report_service.get_solution_summary(solution_id)
        buffer = report_service.generate_pdf_buffer(data)
        
        # En una versión real usaríamos StreamingResponse con media_type="application/pdf"
        from fastapi.responses import Response
        return Response(content=buffer, media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=report_{solution_id}.pdf"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{solution_id}/integrations/status")
async def get_integrations_status(solution_id: str, supabase: Client = Depends(get_supabase)):
    # Placeholder para el GovernanceService
    return {
        "dbt": {"status": "not_configured"},
        "unity_catalog": {"status": "not_configured"},
        "purview": {"status": "not_configured"}
    }
