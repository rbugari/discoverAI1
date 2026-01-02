import os
import shutil
import logging
from typing import List, Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)

class ArtifactService:
    """
    Manages the 'Solution Artifact Sandbox'.
    Each solution has a persistent directory for its generated reports and exports.
    """
    
    def __init__(self, base_dir: str = None):
        # Default artifacts directory inside storage
        self.base_dir = base_dir or os.path.join(settings.UPLOAD_DIR, "..", "artifacts", "solutions")
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            print(f"[ARTIFACTS] Created base directory: {self.base_dir}")

    def get_solution_dir(self, solution_id: str) -> str:
        """Returns and ensures the existence of a solution's sandbox directory."""
        path = os.path.join(self.base_dir, solution_id)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    def save_artifact(self, solution_id: str, filename: str, content: bytes, category: str = "reports") -> str:
        """
        Saves a binary or text artifact to the solution's sandbox.
        Returns the relative path for metadata storage.
        """
        sol_dir = self.get_solution_dir(solution_id)
        category_dir = os.path.join(sol_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        
        target_path = os.path.join(category_dir, filename)
        
        mode = "wb" if isinstance(content, bytes) else "w"
        encoding = None if isinstance(content, bytes) else "utf-8"
        
        with open(target_path, mode, encoding=encoding) as f:
            f.write(content)
            
        print(f"[ARTIFACTS] Saved {filename} to {target_path}")
        # Return relative path from base_dir for storage flexibility
        return os.path.join(solution_id, category, filename)

    def list_artifacts(self, solution_id: str) -> List[Dict[str, Any]]:
        """Lists all artifacts in a solution's sandbox."""
        sol_dir = os.path.join(self.base_dir, solution_id)
        if not os.path.exists(sol_dir):
            return []
            
        artifacts = []
        for root, _, files in os.walk(sol_dir):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, self.base_dir)
                artifacts.append({
                    "name": f,
                    "path": rel_path,
                    "size": os.path.getsize(full_path),
                    "created_at": os.path.getctime(full_path),
                    "category": os.path.basename(root)
                })
        return artifacts

    def delete_solution_sandbox(self, solution_id: str):
        """Wipes the entire sandbox for a solution (Nuclear reset)."""
        sol_dir = os.path.join(self.base_dir, solution_id)
        if os.path.exists(sol_dir):
            shutil.rmtree(sol_dir)
            print(f"[ARTIFACTS] Purged sandbox for solution {solution_id}")
