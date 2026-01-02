import sys
import os
from unittest.mock import MagicMock

# Add apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.auditor import DiscoveryAuditor
from app.services.refiner import DiscoveryRefiner

def test_auditor_fix():
    print("Starting verification of Auditor fix...")
    
    # Mock Supabase
    mock_supabase = MagicMock()
    # Mock some responses if needed, but save_snapshot just inserts
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [{"snapshot_id": "test-snapshot-uuid"}]
    
    # 1. Setup Auditor and Refiner
    auditor = DiscoveryAuditor(mock_supabase)
    runner = MagicMock()
    runner.run_action.return_value.success = True
    runner.run_action.return_value.data = {
        "suggestions": [{"description": "Fix this"}],
        "solution_layer_patch": "...",
        "next_best_action": "Do that"
    }
    
    refiner = DiscoveryRefiner(auditor, runner)
    
    # Mock run_audit to return a valid audit report
    auditor.run_audit = MagicMock(return_value={
        "project_id": "test-project",
        "timestamp": "now",
        "metrics": {"total_assets": 10},
        "gaps": [],
        "recommendations": []
    })
    
    # 2. Simulate main.py fetching latest job_id
    print("Simulating fetching latest job_id...")
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [{"job_id": "84898160-c40d-4f10-92a1-05206263541c"}]
    
    job_res = mock_supabase.table("job_run").select("job_id").eq("project_id", "test-project").order("created_at", desc=True).limit(1).execute()
    latest_job_id = job_res.data[0]["job_id"] if job_res.data else None
    
    # 3. Generate recommendations
    print("Generating recommendations...")
    report = refiner.generate_recommendations("test-project")
    
    # 4. Verify save_snapshot with valid UUID
    print(f"Verifying save_snapshot with UUID: {latest_job_id}...")
    try:
        snapshot_id = auditor.save_snapshot(latest_job_id, report["audit"])
        print(f"✓ Snapshot saved successfully: {snapshot_id}")
    except Exception as e:
        print(f"✗ FAILED: Unexpected error: {e}")
        sys.exit(1)

    # 5. Verify save_snapshot with None (fallback)
    print("Verifying save_snapshot with None...")
    try:
        snapshot_id = auditor.save_snapshot(None, report["audit"])
        print(f"✓ Snapshot saved successfully with None: {snapshot_id}")
    except Exception as e:
        print(f"✗ FAILED: Unexpected error with None: {e}")
        sys.exit(1)

    print("\nSUCCESS: Auditor fix verified.")

if __name__ == "__main__":
    test_auditor_fix()
