from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response, StreamingResponse
from supabase import Client
from ..services.governance_service import GovernanceExportService
from .admin import get_supabase
import io

router = APIRouter(prefix="/admin/governance", tags=["governance"])

@router.get("/export/{project_id}/purview")
def export_purview(project_id: str, supabase: Client = Depends(get_supabase)):
    service = GovernanceExportService(supabase)
    csv_content = service.export_for_purview(project_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=purview_export_{project_id[:8]}.csv"}
    )

@router.get("/export/{project_id}/unity-catalog")
def export_unity_catalog(project_id: str, supabase: Client = Depends(get_supabase)):
    service = GovernanceExportService(supabase)
    csv_content = service.export_for_unity_catalog(project_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=unity_catalog_export_{project_id[:8]}.csv"}
    )

@router.get("/export/{project_id}/dbt")
def export_dbt(project_id: str, supabase: Client = Depends(get_supabase)):
    service = GovernanceExportService(supabase)
    yml_content = service.export_for_dbt(project_id)
    return Response(
        content=yml_content,
        media_type="text/yaml",
        headers={"Content-Disposition": f"attachment; filename=dbt_sources_{project_id[:8]}.yml"}
    )

@router.get("/export/{project_id}/raw")
def export_raw(project_id: str, supabase: Client = Depends(get_supabase)):
    service = GovernanceExportService(supabase)
    json_content = service.export_raw_json(project_id)
    return Response(
        content=json_content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=discoverai_export_{project_id[:8]}.json"}
    )
