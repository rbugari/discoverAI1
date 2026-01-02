from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class DiscoveryComparator:
    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def compare_snapshots(self, snapshot_a_id: str, snapshot_b_id: str) -> Dict[str, Any]:
        """
        Compares two snapshots (A is baseline, B is new) and returns the delta.
        """
        # 1. Fetch Snapshots
        res_a = self.supabase.table("audit_snapshot").select("*").eq("snapshot_id", snapshot_a_id).single().execute()
        res_b = self.supabase.table("audit_snapshot").select("*").eq("snapshot_id", snapshot_b_id).single().execute()
        
        if not res_a.data or not res_b.data:
            raise ValueError("One or both snapshots not found.")
            
        snap_a = res_a.data
        snap_b = res_b.data
        
        metrics_a = snap_a["metrics"]
        metrics_b = snap_b["metrics"]
        
        # 2. Calculate Deltas
        delta = {
            "coverage_diff": round(metrics_b["coverage_score"] - metrics_a["coverage_score"], 2),
            "confidence_diff": round(metrics_b["avg_confidence"] - metrics_a["avg_confidence"], 2),
            "assets_diff": metrics_b["total_assets"] - metrics_a["total_assets"],
            "relationships_diff": metrics_b["total_relationships"] - metrics_a["total_relationships"],
            "hypothesis_ratio_diff": round(metrics_b["hypothesis_ratio"] - metrics_a["hypothesis_ratio"], 2)
        }
        
        # 3. Analyze Gap Resolution
        gaps_a = snap_a.get("gaps", [])
        gaps_b = snap_b.get("gaps", [])
        
        resolved_count = 0
        b_gap_desc = [g["description"] for g in gaps_b]
        for g in gaps_a:
            if g["description"] not in b_gap_desc:
                resolved_count += 1
                
        # 4. Final Comparison Report
        return {
            "project_id": snap_b["project_id"],
            "baseline_snapshot": snapshot_a_id,
            "new_snapshot": snapshot_b_id,
            "metrics_delta": delta,
            "progress_summary": {
                "resolved_gaps": resolved_count,
                "new_gaps": len(gaps_b) - (len(gaps_a) - resolved_count),
                "trend": "IMPROVED" if delta["coverage_diff"] > 0 or delta["confidence_diff"] > 0 else "STAGNANT"
            }
        }

    def fetch_latest_snapshots(self, project_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retorna los últimos snapshots para facilitar la selección en UI.
        """
        res = self.supabase.table("audit_snapshot")\
            .select("snapshot_id, created_at, metrics")\
            .eq("project_id", project_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return res.data or []
