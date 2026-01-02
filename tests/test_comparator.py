import sys
import os
import unittest
from unittest.mock import MagicMock
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

load_dotenv()

from app.services.comparator import DiscoveryComparator

class TestDiscoveryComparator(unittest.TestCase):
    def setUp(self):
        self.mock_supabase = MagicMock()
        self.comparator = DiscoveryComparator(self.mock_supabase)

    def test_compare_logic(self):
        # Mock Snapshot A (Baseline)
        snap_a = {
            "snapshot_id": "snap-a",
            "project_id": "proj-1",
            "metrics": {
                "coverage_score": 10.0,
                "avg_confidence": 0.5,
                "total_assets": 100,
                "total_relationships": 20,
                "hypothesis_ratio": 50.0
            },
            "gaps": [
                {"description": "Gap 1"},
                {"description": "Gap 2"}
            ]
        }
        
        # Mock Snapshot B (New)
        snap_b = {
            "snapshot_id": "snap-b",
            "project_id": "proj-1",
            "metrics": {
                "coverage_score": 25.0,
                "avg_confidence": 0.8,
                "total_assets": 105,
                "total_relationships": 45,
                "hypothesis_ratio": 10.0
            },
            "gaps": [
                {"description": "Gap 1"},
                {"description": "Gap 3"} # Gap 2 is resolved, Gap 3 is new
            ]
        }

        # Setup mock returns
        self.mock_supabase.table().select().eq().single().execute.side_effect = [
            MagicMock(data=snap_a),
            MagicMock(data=snap_b)
        ]

        report = self.comparator.compare_snapshots("snap-a", "snap-b")
        
        print("\nTest Comparison Report:")
        print(f"Coverage Delta: {report['metrics_delta']['coverage_diff']}%")
        print(f"Resolved Gaps: {report['progress_summary']['resolved_gaps']}")
        print(f"Trend: {report['progress_summary']['trend']}")

        self.assertEqual(report["metrics_delta"]["coverage_diff"], 15.0)
        self.assertEqual(report["progress_summary"]["resolved_gaps"], 1)
        self.assertEqual(report["progress_summary"]["trend"], "IMPROVED")

if __name__ == "__main__":
    unittest.main()
