import csv
import json
import io
from typing import List, Dict, Any, Optional
from supabase import Client

class GovernanceExportService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def _to_csv(self, rows: List[Dict[str, Any]], fieldnames: List[str]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Filter row to only include desired fields
            filtered_row = {k: row.get(k, "") for k in fieldnames}
            writer.writerow(filtered_row)
        return output.getvalue()

    def export_for_purview(self, project_id: str) -> str:
        """
        Generates a CSV string compatible with Microsoft Purview bulk upload.
        """
        # Fetch assets
        assets = self.supabase.table("asset").select("*").eq("project_id", project_id).execute().data
        
        fieldnames = ["Qualified Name", "Display Name", "Description", "Asset Type"]
        rows = []
        for asset in assets:
            rows.append({
                "Qualified Name": asset.get("canonical_name") or asset.get("name_display"),
                "Display Name": asset.get("name_display"),
                "Description": f"Extracted from DiscoverAI. System: {asset.get('system')}",
                "Asset Type": asset.get("asset_type")
            })
            
        return self._to_csv(rows, fieldnames)

    def export_for_unity_catalog(self, project_id: str) -> str:
        """
        Generates a CSV representing lineage and assets for Unity Catalog manual import.
        """
        # Fetch lineage
        lineage = self.supabase.table("column_lineage")\
            .select("*, source_asset:source_asset_id(name_display), target_asset:target_asset_id(name_display)")\
            .eq("project_id", project_id).execute().data
        
        fieldnames = ["Source Table", "Source Column", "Target Table", "Target Column", "Transformation"]
        rows = []
        for lin in lineage:
            rows.append({
                "Source Table": lin.get("source_asset", {}).get("name_display") if lin.get("source_asset") else "Unknown",
                "Source Column": lin.get("source_column"),
                "Target Table": lin.get("target_asset", {}).get("name_display") if lin.get("target_asset") else "Unknown",
                "Target Column": lin.get("target_column"),
                "Transformation": lin.get("logic")
            })
            
        return self._to_csv(rows, fieldnames)

    def export_for_dbt(self, project_id: str) -> str:
        """
        Generates a dbt sources.yml fragment based on extracted assets.
        """
        assets = self.supabase.table("asset").select("*").eq("project_id", project_id).execute().data
        
        # Group by system (or use a default source name)
        sources = {}
        for asset in assets:
            if asset.get("asset_type") != "table":
                continue
            
            system = asset.get("system") or "external_source"
            if system not in sources:
                sources[system] = []
            
            sources[system].append({
                "name": asset.get("name_display"),
                "description": f"Imported from DiscoverAI. Canonical: {asset.get('canonical_name')}"
            })
            
        if not sources:
            return "version: 2\nsources: []"
            
        output = ["version: 2", "sources:"]
        for sys_name, tables in sources.items():
            output.append(f"  - name: {sys_name}")
            output.append("    tables:")
            for table in tables:
                output.append(f"      - name: {table['name']}")
                output.append(f"        description: \"{table['description']}\"")
                
        return "\n".join(output)

    def export_raw_json(self, project_id: str) -> str:
        """
        Returns a full technical export of the project metadata in JSON format.
        """
        data = {
            "assets": self.supabase.table("asset").select("*").eq("project_id", project_id).execute().data,
            "edges": self.supabase.table("edge_index").select("*").eq("project_id", project_id).execute().data,
            "packages": self.supabase.table("package").select("*").eq("project_id", project_id).execute().data,
            "lineage": self.supabase.table("column_lineage").select("*").eq("project_id", project_id).execute().data
        }
        return json.dumps(data, indent=2, default=str)
