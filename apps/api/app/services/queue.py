from supabase import create_client, Client
from ..config import settings
import datetime

class SQLJobQueue:
    def __init__(self):
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        # Use Service Role Key for worker operations if available to bypass RLS
        if settings.SUPABASE_SERVICE_ROLE_KEY:
            self.admin_supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        else:
            self.admin_supabase = self.supabase

    def enqueue_job(self, job_id: str):
        """Add a job to the queue."""
        data = {
            "job_id": job_id,
            "status": "pending",
            "attempts": 0,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat()
        }
        res = self.admin_supabase.table("job_queue").insert(data).execute()
        return res.data

    def fetch_next_job(self):
        """Fetch the next pending job. Simple FIFO."""
        # 1. Get oldest pending job
        res = self.admin_supabase.table("job_queue")\
            .select("*")\
            .eq("status", "pending")\
            .order("created_at")\
            .limit(1)\
            .execute()
        
        if not res.data:
            return None
        
        job_queue_item = res.data[0]
        
        # 2. Mark as processing (Optimistic locking via status check)
        # We try to update only if status is still pending
        update_res = self.admin_supabase.table("job_queue")\
            .update({
                "status": "processing",
                "updated_at": datetime.datetime.utcnow().isoformat()
            })\
            .eq("id", job_queue_item["id"])\
            .eq("status", "pending")\
            .execute()
            
        if not update_res.data:
            # Race condition lost, try again recursively or return None
            return None
            
        return update_res.data[0]

    def complete_job(self, queue_id: str):
        """Mark job as completed in queue."""
        self.admin_supabase.table("job_queue")\
            .update({
                "status": "completed",
                "updated_at": datetime.datetime.utcnow().isoformat()
            })\
            .eq("id", queue_id)\
            .execute()

    def fail_job(self, queue_id: str, error_message: str):
        """Mark job as failed in queue."""
        self.admin_supabase.table("job_queue")\
            .update({
                "status": "failed",
                "last_error": error_message,
                "updated_at": datetime.datetime.utcnow().isoformat()
            })\
            .eq("id", queue_id)\
            .execute()
