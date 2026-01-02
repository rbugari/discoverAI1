import asyncio
import os
import sys
import shutil
from unittest.mock import MagicMock

# Set up path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.artifact_service import ArtifactService
from app.services.reset_service import NuclearResetService
from app.services.report_service import ReportService

async def verify_enterprise_hub():
    print("--- Enterprise Hub Verification (Phase 6.3) ---")
    
    solution_id = "f63-test-solution-id"
    
    # 1. Test ArtifactService
    print("[TEST] Testing ArtifactService...")
    artifacts = ArtifactService()
    test_content = b"This is a test PDF content."
    rel_path = artifacts.save_artifact(solution_id, "test_report.pdf", test_content)
    
    sol_dir = artifacts.get_solution_dir(solution_id)
    if os.path.exists(os.path.join(sol_dir, "reports", "test_report.pdf")):
        print(f"[SUCCESS] Artifact saved to: {rel_path}")
    else:
        print("[FAIL] Artifact not found in sandbox.")
        return

    # 2. Test ReportService Integration (Mocked)
    print("[TEST] Testing ReportService automated save...")
    supabase = MagicMock()
    # Mock solution summary
    report_service = ReportService(supabase)
    report_service.get_solution_summary = MagicMock(return_value=asyncio.Future())
    report_service.get_solution_summary.return_value.set_result({
        "solution_name": "Test Solution",
        "generated_at": "2025-12-31",
        "status": "READY",
        "asset_count": 10,
        "asset_types": {"table": 5},
        "edge_count": 5,
        "edge_types": {"DEPENDS_ON": 5},
        "packages": [],
        "last_job": {"tokens": 100, "cost_usd": 0.01}
    })
    
    await report_service.generate_and_save_latest_artifacts(solution_id)
    
    if os.path.exists(os.path.join(sol_dir, "reports", "architecture_report.pdf")) and \
       os.path.exists(os.path.join(sol_dir, "reports", "architecture_report.md")):
        print("[SUCCESS] Automated PDF and MD reports generated and saved to sandbox.")
    else:
        print("[FAIL] Automated reports missing.")

    # 3. Test Nuclear Reset
    print("[TEST] Testing NuclearResetService...")
    reset_service = NuclearResetService(supabase)
    
    # Mock Supabase table deletes
    supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    
    reset_service.reset_solution_data(solution_id)
    
    if not os.path.exists(sol_dir):
        print("[SUCCESS] Nuclear Reset successfully purged the physical sandbox.")
    else:
        print("[FAIL] Sandbox still exists after Nuclear Reset.")

if __name__ == "__main__":
    asyncio.run(verify_enterprise_hub())
