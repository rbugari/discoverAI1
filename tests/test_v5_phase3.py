import sys
import os
import unittest
import json
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.join(os.getcwd(), "apps", "api"))

load_dotenv()

from app.config import settings
from app.services.auditor import DiscoveryAuditor
from app.services.refiner import DiscoveryRefiner
from app.actions import ActionRunner
from app.audit import FileProcessingLogger
from supabase import create_client

class TestV5Phase3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        cls.logger = FileProcessingLogger(cls.supabase)
        cls.action_runner = ActionRunner(cls.logger)
        cls.auditor = DiscoveryAuditor(cls.supabase)
        cls.refiner = DiscoveryRefiner(cls.auditor, cls.action_runner)
        cls.project_id = "7021ac4b-921d-402f-bc21-1c63701b8180" # SSIS v4 Test Final

    def test_complexity_analysis(self):
        """Verifies that complexity analysis returns a valid structure"""
        print(f"\n[TEST] Complexity analysis for {self.project_id}...")
        res = self.auditor.analyze_complexity(self.project_id)
        print(json.dumps(res, indent=2))
        
        self.assertIn("score", res)
        self.assertIn("is_high_complexity", res)

    def test_proactive_refinement(self):
        """Verifies the AI synthesis includes Next Best Action"""
        print(f"\n[TEST] Proactive Refinement (Phase 3) for {self.project_id}...")
        res = self.refiner.generate_recommendations(self.project_id)
        
        print("\n--- PERFORMANCE DATA ---")
        print(f"Complexity Score: {res['complexity']['score']}")
        
        print("\n--- NEXT BEST ACTION ---")
        print(res.get("next_best_action"))
        
        print("\n--- AI SUGGESTIONS ---")
        for s in res['ai_suggestions']:
            print(f"[*] {s}")

        self.assertIn("complexity", res)
        self.assertIn("next_best_action", res)

if __name__ == "__main__":
    unittest.main()
