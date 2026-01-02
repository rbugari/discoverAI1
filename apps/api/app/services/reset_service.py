import logging
from supabase import Client
from .artifact_service import ArtifactService

logger = logging.getLogger(__name__)

class NuclearResetService:
    """
    Handles the structural cleanup of a solution's state.
    Used for 'Reprocess' and 'Delete' operations to ensure no orphan data remains.
    """
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.artifacts = ArtifactService()

    def reset_solution_data(self, solution_id: str):
        """
        Permanently deletes all discovery-related data for a solution.
        """
        print(f"[NUCLEAR RESET] Starting wipe for solution {solution_id}")
        
        try:
            # 1. Dependents (Audit & Evidence) - Must be deleted BEFORE job_run/asset due to FKs
            self.supabase.table("audit_snapshot").delete().eq("project_id", solution_id).execute()
            self.supabase.table("evidence").delete().eq("project_id", solution_id).execute()
            self.supabase.table("reasoning_log").delete().eq("solution_id", solution_id).execute()

            # 2. Main Job Data
            # file_processing_log is deleted via CASCADE from job_run
            self.supabase.table("job_run").delete().eq("project_id", solution_id).execute()
            
            # 3. Deep Dive & Lineage Results
            self.supabase.table("column_lineage").delete().eq("project_id", solution_id).execute()
            self.supabase.table("transformation_ir").delete().eq("project_id", solution_id).execute()
            # package_component is deleted via CASCADE from package
            self.supabase.table("package").delete().eq("project_id", solution_id).execute()
            
            # 4. Core Graph (Edges then Assets)
            self.supabase.table("edge_index").delete().eq("project_id", solution_id).execute()
            self.supabase.table("asset").delete().eq("project_id", solution_id).execute()
            
            # 5. Artifact Sandbox
            self.artifacts.delete_solution_sandbox(solution_id)
            
            print(f"[NUCLEAR RESET] Successfully wiped solution {solution_id}")
            return True
        except Exception as e:
            logger.error(f"Nuclear Reset failed for {solution_id}: {e}")
            print(f"[NUCLEAR RESET] ERROR: {e}")
            return False
