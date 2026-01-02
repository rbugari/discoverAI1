import sys
import os
import unittest
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

load_dotenv()

from app.config import settings
from app.services.auditor import DiscoveryAuditor
from supabase import create_client

class TestDiscoveryAuditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        cls.auditor = DiscoveryAuditor(cls.supabase)
        # Real IDs from the DB
        cls.test_projects = [
            "7021ac4b-921d-402f-bc21-1c63701b8180", # SSIS v4 Test Final
            "72404860-eaaa-4967-82dd-39bd99aec634", # ss1
            "8ceed462-24f4-4e21-8b61-e01944515d90"  # ds 1
        ]

    def test_audit_real_data(self):
        """Tests the auditor against one of the real repositories"""
        project_id = self.test_projects[0]
        report = self.auditor.run_audit(project_id)
        
        print(f"\nAudit Report for {project_id}:")
        print(f"- Coverage Score: {report['metrics']['coverage_score']}%")
        print(f"- Avg Confidence: {report['metrics']['avg_confidence']}")
        print(f"- Gaps Found: {len(report['gaps'])}")
        
        self.assertEqual(report["project_id"], project_id)
        self.assertIn("metrics", report)
        self.assertGreaterEqual(report["metrics"]["coverage_score"], 0)

    def test_audit_multiple_repos(self):
        """Quick check for all 3 repos"""
        for pid in self.test_projects:
            report = self.auditor.run_audit(pid)
            self.assertIsNotNone(report)
            print(f"Project {pid} - Coverage: {report['metrics']['coverage_score']}%")

if __name__ == "__main__":
    unittest.main()
