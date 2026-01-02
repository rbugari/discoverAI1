import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from ..config import settings
from ..services.config_manager import ConfigManager

router = APIRouter(prefix="/admin", tags=["admin"])

def get_supabase():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# --- Model Config (Existing) ---

@router.get("/model-config")
async def get_model_config():
    """Returns available and active model configurations."""
    # Note: path adjustment since this is now in routers/
    config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
    manager = ConfigManager(config_dir)
    return manager.list_available_configs()

class ActivateConfigRequest(BaseModel):
    provider_path: str
    routing_path: str

@router.post("/model-config/activate")
async def activate_model_config(req: ActivateConfigRequest):
    """Activates a specific model configuration."""
    config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
    manager = ConfigManager(config_dir)
    try:
        manager.activate_config(req.provider_path, req.routing_path)
        return {"status": "success", "message": f"Activated {req.routing_path}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Prompt Management (v4.0) ---

class PromptLayerBase(BaseModel):
    layer_type: str # BASE, DOMAIN, ORG, SOLUTION
    name: str
    content: str
    is_active: bool = True
    project_id: Optional[str] = None

@router.get("/prompts/layers")
async def list_prompt_layers(supabase: Client = Depends(get_supabase)):
    res = supabase.table("prompt_layer").select("*").order("name").execute()
    return res.data

@router.post("/prompts/layers")
async def upsert_prompt_layer(layer: PromptLayerBase, supabase: Client = Depends(get_supabase)):
    res = supabase.table("prompt_layer").upsert(layer.model_dump(), on_conflict="name").execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to save prompt layer")
    return res.data[0]

@router.get("/prompts/config")
async def get_action_prompt_config(supabase: Client = Depends(get_supabase)):
    res = supabase.table("action_prompt_config").select("*").execute()
    return res.data

class ActionPromptMapping(BaseModel):
    action_name: str
    base_layer_id: Optional[str] = None
    domain_layer_id: Optional[str] = None
    org_layer_id: Optional[str] = None

@router.patch("/prompts/config")
async def update_action_prompt_mapping(mapping: ActionPromptMapping, supabase: Client = Depends(get_supabase)):
    res = supabase.table("action_prompt_config").upsert(mapping.model_dump(), on_conflict="action_name").execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to update mapping")
    return res.data[0]

# --- Solution-Specific Prompt Config ---

@router.get("/prompts/solutions/{project_id}/config")
async def get_project_action_prompt_config(project_id: str, supabase: Client = Depends(get_supabase)):
    res = supabase.table("project_action_config").select("*").eq("project_id", project_id).execute()
    return res.data

class ProjectActionPromptMapping(BaseModel):
    project_id: str
    action_name: str
    solution_layer_id: str

@router.patch("/prompts/solutions/config")
async def update_project_action_prompt_mapping(mapping: ProjectActionPromptMapping, supabase: Client = Depends(get_supabase)):
    res = supabase.table("project_action_config").upsert(mapping.model_dump(), on_conflict="project_id, action_name").execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to update project mapping")
    return res.data[0]

# --- Model Config YAML Editor ---

@router.get("/model-config/file")
async def get_config_file(path: str):
    """Reads the raw text of a configuration file."""
    config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
    manager = ConfigManager(config_dir)
    try:
        content = manager.read_config_file(path)
        return {"content": content, "path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class SaveConfigRequest(BaseModel):
    path: str
    content: str

@router.post("/model-config/file")
async def save_config_file(req: SaveConfigRequest):
    """Saves raw text to a configuration file."""
    config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
    manager = ConfigManager(config_dir)
    try:
        manager.write_config_file(req.path, req.content)
        return {"status": "success", "message": f"Saved {req.path}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cleanup")
async def admin_cleanup_database():
    """Nuclear option from main.py"""
    # Logic already in main.py, keeping it simple here for now or migrating it later
    # For now, I'll refer the user to the existing endpoint if they want to move it.
    pass
