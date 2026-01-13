import os
import uuid
import logging
import hashlib
import traceback
from datetime import datetime
from typing import List, Dict
from supabase import Client

from ..models.planning import (
    JobPlan, JobPlanArea, JobPlanItem, 
    JobPlanStatus, JobPlanMode, AreaKey, Strategy, RecommendedAction
)
from .policy_engine import PolicyEngine
from .estimator import Estimator

logger = logging.getLogger(__name__)

class PlannerService:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.policy_engine = PolicyEngine()
        
    def create_plan(self, job_id: str, root_path: str, mode: JobPlanMode = JobPlanMode.STANDARD) -> str:
        """
        Scans the directory, generates a plan, persists it, and returns plan_id.
        """
        print(f"\n[PLANNER] 🚀 Generating Execution Plan for Job {job_id}...", flush=True)
        print(f"[PLANNER] Source Path: {root_path}", flush=True)
        
        try:
            # Fetch project_id and existing evidence
            job_res = self.supabase.table("job_run").select("project_id").eq("job_id", job_id).single().execute()
            project_id = job_res.data.get("project_id")
            
            existing_evidence = {}
            if project_id:
                ev_res = self.supabase.table("evidence").select("file_path, hash").eq("project_id", project_id).execute()
                for ev in ev_res.data:
                    path = ev["file_path"]
                    if path not in existing_evidence:
                        existing_evidence[path] = set()
                    existing_evidence[path].add(ev["hash"])
            
            # 1. Create JobPlan Header
            plan_id = str(uuid.uuid4())
            plan_data = {
                "plan_id": plan_id,
                "job_id": job_id,
                "status": JobPlanStatus.DRAFT,
                "mode": mode,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            self.supabase.table("job_plan").insert(plan_data).execute()
            
            # 2. Create Areas
            areas = self._create_areas(plan_id)
            
            # 3. Inventory & Classify
            items = []
            total_stats = {"total_files": 0, "total_cost": 0.0, "total_time": 0.0}
            
            print(f"[PLANNER] Scanning files in {root_path}...", flush=True)
            for root, dirs, files in os.walk(root_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_path).replace("\\", "/")
                    
                    try:
                        size_bytes = os.path.getsize(full_path)
                    except OSError:
                        size_bytes = 0
                    
                    # Hash Check for Incremental Logic
                    file_hash = self._compute_hash(full_path)
                    is_duplicate = False
                    if rel_path in existing_evidence and file_hash in existing_evidence[rel_path]:
                        is_duplicate = True
                    
                    if is_duplicate:
                        rec_action = RecommendedAction.SKIP
                        reason = "Unchanged (already processed)"
                    else:
                        rec_action, reason = self.policy_engine.evaluate(rel_path, size_bytes)
                        
                    # --- USER OVERRIDE: ALWAYS PROCESS SQL/DTSX ---
                    # Ensure critical files are always selected by default
                    ext_lower = rel_path.split('.')[-1].lower() if '.' in rel_path else ""
                    if ext_lower in ["sql", "dtsx", "dsx"]:
                        rec_action = RecommendedAction.PROCESS
                        reason = "Core Artifact (Always Process)"
                    # ----------------------------------------------
                    
                    # Classification & Strategy
                    area_key, strategy = self._classify_file(rel_path, rec_action)
                    
                    # Estimation
                    est = Estimator.estimate(size_bytes, strategy)
                    
                    # Create Item
                    area_id = areas[area_key]
                    item_id = str(uuid.uuid4())
                    
                    item = {
                        "item_id": item_id,
                        "plan_id": plan_id,
                        "area_id": area_id,
                        "path": rel_path,
                        "size_bytes": size_bytes,
                        "file_type": rel_path.split('.')[-1].upper() if '.' in rel_path else "UNKNOWN",
                        "classifier": {"reason": reason},
                        "strategy": strategy,
                        "recommended_action": rec_action,
                        "enabled": rec_action == RecommendedAction.PROCESS,
                        "file_hash": file_hash,
                        "order_index": 0, 
                        "estimate": est
                    }
                    items.append(item)
                    
                    # Stats
                    if rec_action == RecommendedAction.PROCESS:
                        total_stats["total_files"] += 1
                        total_stats["total_cost"] += est["cost_usd"]
                        total_stats["total_time"] += est["time_seconds"]
            
            print(f"[PLANNER] Found {len(items)} files. Persisting plan items...", flush=True)
            # Batch Insert Items (chunks of 100)
            chunk_size = 100
            for i in range(0, len(items), chunk_size):
                chunk = items[i:i+chunk_size]
                self.supabase.table("job_plan_item").insert(chunk).execute()
                
            # Update Plan Summary
            self.supabase.table("job_plan").update({
                "summary": total_stats,
                "status": JobPlanStatus.READY
            }).eq("plan_id", plan_id).execute()
            
            # Link Plan to Job
            self.supabase.table("job_run").update({
                "plan_id": plan_id,
                "status": "planning_ready" 
            }).eq("job_id", job_id).execute()
            
            print(f"[PLANNER] ✅ Plan {plan_id} completed for Job {job_id}", flush=True)
            return plan_id

        except Exception as e:
            error_msg = f"Planning failed for Job {job_id}: {str(e)}"
            detailed_error = traceback.format_exc()
            print(f"\n[PLANNER] ❌ FAILED to create plan for Job {job_id}: {str(e)}", flush=True)
            print(detailed_error, flush=True)
            
            # --- DEBUG: LOG TO FILE ---
            try: 
                with open("CRASH_LOG_PLANNER.txt", "w", encoding="utf-8") as f:
                    f.write(detailed_error)
            except: pass
            # --------------------------
            
            # Try to log failure to job_run
            try:
                self.supabase.table("job_run").update({
                    "status": "failed",
                    "error_message": error_msg,
                    "error_details": detailed_error
                }).eq("job_id", job_id).execute()
            except:
                pass
            raise e

    def _create_areas(self, plan_id: str) -> Dict[AreaKey, str]:
        """Creates default areas and returns Map<AreaKey, AreaID>"""
        areas_def = [
            {"key": AreaKey.FOUNDATION, "title": "Foundation (SQL & Schema)", "order": 1},
            {"key": AreaKey.PACKAGES, "title": "Orchestration & Packages", "order": 2},
            {"key": AreaKey.DOCS, "title": "Documentation & Diagrams", "order": 3},
            {"key": AreaKey.AUX, "title": "Auxiliary & Scripts", "order": 4}
        ]
        
        area_map = {}
        for a in areas_def:
            area_id = str(uuid.uuid4())
            self.supabase.table("job_plan_area").insert({
                "area_id": area_id,
                "plan_id": plan_id,
                "area_key": a["key"],
                "title": a["title"],
                "order_index": a["order"]
            }).execute()
            area_map[a["key"]] = area_id
            
        return area_map

    def _compute_hash(self, file_path: str) -> str:
        """Calcula el hash SHA256 de un archivo"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return ""

    def _classify_file(self, path: str, rec_action: RecommendedAction) -> tuple[AreaKey, Strategy]:
        """Heuristic classification"""
        if rec_action == RecommendedAction.SKIP:
            return AreaKey.AUX, Strategy.SKIP
            
        lower_path = path.lower()
        ext = lower_path.split('.')[-1] if '.' in lower_path else ""
        
        if ext in ["sql", "ddl"] or "schema" in lower_path or "migration" in lower_path:
            return AreaKey.FOUNDATION, Strategy.PARSER_PLUS_LLM
            
        # 2. Documentation & Diagrams
        if ext in ["md", "json", "txt"] and ("readme" in lower_path or "contract" in lower_path or "docs" in lower_path):
             return AreaKey.DOCS, Strategy.LLM_ONLY

        if ext in ["jpg", "jpeg", "png", "gif", "webp"]:
            return AreaKey.DOCS, Strategy.VLM_EXTRACT

        # 3. Packages
        if ext in ["dtsx", "dsx"]:
            return AreaKey.PACKAGES, Strategy.PARSER_PLUS_LLM # Hybrid Parser v3
            
        if "jobs" in lower_path or "pipelines" in lower_path:
            return AreaKey.PACKAGES, Strategy.LLM_ONLY

        # 3. Aux / Scripts
        if ext in ["py", "sh", "bat", "ps1"]:
            return AreaKey.AUX, Strategy.LLM_ONLY
            
        if ext in ["xml", "config", "yaml", "yml", "env"]:
            return AreaKey.AUX, Strategy.PARSER_ONLY
            
        # Default
        return AreaKey.AUX, Strategy.LLM_ONLY
