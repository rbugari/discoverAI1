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

class TestV5FullLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        cls.logger = FileProcessingLogger(cls.supabase)
        cls.action_runner = ActionRunner(cls.logger)
        cls.auditor = DiscoveryAuditor(cls.supabase)
        cls.refiner = DiscoveryRefiner(cls.auditor, cls.action_runner)
        cls.project_id = "7021ac4b-921d-402f-bc21-1c63701b8180" # SSIS v4 Test Final

    def test_full_loop_execution(self):
        """Verifies that audit and refinement generate valid suggestions"""
        print(f"\n[TEST] Running Full Loop for {self.project_id}...")
        
        result = self.refiner.generate_recommendations(self.project_id)
        
        print("\n--- AUDIT RESULTS ---")
        print(json.dumps(result["audit"]["metrics"], indent=2))
        
        print("\n--- AI SUGGESTIONS ---")
        for s in result["ai_suggestions"]:
            print(f"[*] {s}")
            
        print("\n--- SUGGESTED SOLUTION LAYER PATCH ---")
        print(result["suggested_solution_layer"])
        
        self.assertIn("audit", result)
        self.assertIn("ai_suggestions", result)
        # Check that we got at least some suggestions (either from AI or fallback)
        self.assertGreater(len(result["ai_suggestions"]), 0)

if __name__ == "__main__":
    unittest.main()
