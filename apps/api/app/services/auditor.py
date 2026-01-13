from supabase import Client
from typing import Dict, List, Any, Optional
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class DiscoveryAuditor:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def run_audit(self, project_id: str) -> Dict[str, Any]:
        """
        Runs a full accuracy and coverage audit for a project.
        """
        logger.info(f"[AUDITOR] Running audit for project {project_id}")
        
        # 1. Fetch Data
        assets = self.supabase.table("asset").select("*").eq("project_id", project_id).execute().data or []
        edges = self.supabase.table("edge_index").select("*").eq("project_id", project_id).execute().data or []
        col_lineage = self.supabase.table("column_lineage").select("*").eq("project_id", project_id).execute().data or []
        packages = self.supabase.table("package").select("*").eq("project_id", project_id).execute().data or []
        
        if not assets and not packages:
            return {
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "total_assets": 0,
                    "total_relationships": 0,
                    "coverage_score": 0.0,
                    "avg_confidence": 0.0,
                    "hypothesis_ratio": 0.0
                },
                "gaps": [],
                "recommendations": ["No data found for this project. Start an analysis run."]
            }

        # 2. Calculate Metrics
        total_assets = len(assets)
        total_edges = len(edges) + len(col_lineage)
        
        # Confidence & Hypotheses
        all_conf = [e.get("confidence", 1.0) for e in edges] + [l.get("confidence", 1.0) for l in col_lineage]
        avg_conf = sum(all_conf) / len(all_conf) if all_conf else 1.0
        
        hypothesis_count = len([e for e in edges if e.get("is_hypothesis")])
        hypothesis_ratio = (hypothesis_count / len(edges)) * 100 if edges else 0.0
        
        # Coverage Estimation
        functional_types = ["TABLE", "VIEW", "PIPELINE", "SCRIPT", "PACKAGE", "STORED_PROCEDURE"]
        functional_assets = [a for a in assets if a.get("asset_type", "").upper() in functional_types]
        connected_assets = set()
        for e in edges:
            connected_assets.add(e["from_asset_id"])
            connected_assets.add(e["to_asset_id"])
        
        # Add column lineage connections
        for l in col_lineage:
            if l.get("source_asset_id"): connected_assets.add(l["source_asset_id"])
            if l.get("target_asset_id"): connected_assets.add(l["target_asset_id"])
            
        documented_count = len([a for a in functional_assets if a["asset_id"] in connected_assets])
        
        # If we have packages but no assets connected yet, check if package components exist
        if not documented_count and packages:
            # Check for package enrichment
            documented_count = len(packages) # Basic fallback if packages exist
            
        raw_score = (documented_count / len(functional_assets)) * 100 if functional_assets else 0.0
        coverage_score = min(raw_score, 100.0)
        
        if not functional_assets and packages: coverage_score = 100.0 # If only packages exist
        
        # 3. Identify Gaps
        gaps = []
        # Find orphan functional assets
        orphans = [a for a in functional_assets if a["asset_id"] not in connected_assets]
        for orphan in orphans[:10]: # Limit gaps to top 10
            gaps.append({
                "type": "ORPHAN_ASSET",
                "asset_name": orphan["name_display"],
                "asset_type": orphan["asset_type"],
                "severity": "MEDIUM",
                "description": f"Asset '{orphan['name_display']}' has no detected relationships."
            })
            
        # Find low confidence clusters
        low_conf_edges = [e for e in edges if e.get("confidence", 1.0) < 0.5]
        if low_conf_edges:
            gaps.append({
                "type": "LOW_CONFIDENCE_CLUSTER",
                "count": len(low_conf_edges),
                "severity": "HIGH",
                "description": f"Found {len(low_conf_edges)} relationships with confidence below 50%."
            })

        # 4. Generate Recommendations
        recommendations = []
        if coverage_score < 80:
            recommendations.append("Add more context to the Solution Layer for the 'Unknown' asset types.")
        
        if avg_conf < 0.7:
            recommendations.append("Consider upgrading to a High-IQ model (GPT-4o / Grok-1) to resolve ambiguities.")
            
        if orphans:
            recommendations.append(f"Define naming conventions in the Org Layer to help resolve {len(orphans)} orphan assets.")

        return {
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_assets": total_assets,
                "total_relationships": total_edges,
                "coverage_score": round(coverage_score, 2),
                "avg_confidence": round(avg_conf, 2),
                "hypothesis_ratio": round(hypothesis_ratio, 2)
            },
            "gaps": gaps,
            "recommendations": recommendations
        }

    def save_snapshot(self, job_id: str, report: Dict[str, Any]) -> str:
        """
        Persists an audit report to the audit_snapshot table.
        """
        try:
            snapshot_data = {
                "project_id": report["project_id"],
                "job_id": job_id,
                "metrics": report["metrics"],
                "gaps": report["gaps"],
                "recommendations": report["recommendations"],
                "created_at": "now()"
            }
            res = self.supabase.table("audit_snapshot").insert(snapshot_data).execute()
            if res.data:
                snapshot_id = res.data[0]["snapshot_id"]
                logger.info(f"[AUDITOR] Snapshot {snapshot_id} saved for job {job_id}")
                return snapshot_id
        except Exception as e:
            logger.error(f"[AUDITOR] Failed to save snapshot for job {job_id}: {e}")
            # Non-blocking error for the pipeline
        return None

    def analyze_complexity(self, project_id: str) -> Dict[str, Any]:
        """
        Calculates a complexity score for the project based on number of assets,
        deep nest levels (if available), and relationship density.
        """
        try:
            # Basic stats
            assets = self.supabase.table("asset").select("asset_id, asset_type").eq("project_id", project_id).execute().data or []
            edges = self.supabase.table("edge_index").select("edge_id").eq("project_id", project_id).execute().data or []
            
            total_assets = len(assets)
            total_edges = len(edges)
            
            density = total_edges / total_assets if total_assets > 0 else 0
            
            # Identify "Hot Spots" (Complexity nodes)
            # e.g., Packages with many components
            packages = self.supabase.table("package").select("package_id").eq("project_id", project_id).execute().data or []
            
            score = 0
            if total_assets > 500: score += 30
            if total_assets > 1000: score += 20
            if density > 5: score += 20
            if len(packages) > 50: score += 30
            
            return {
                "score": min(score, 100),
                "density": round(density, 2),
                "is_high_complexity": score > 60,
                "recommendation": "Use High-IQ models (GPT-4o / Claude 3.5) for better lineage resolution." if score > 60 else "Groq models are sufficient for this architecture."
            }
        except Exception as e:
            logger.error(f"[AUDITOR] Complexity analysis failed: {e}")
            return {"score": 0, "is_high_complexity": False}
