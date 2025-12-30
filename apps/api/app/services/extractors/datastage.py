import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class DataStageParser:
    """
    Structural parser for IBM DataStage .dsx files.
    Uses a line-based state machine to extract Jobs, Stages, Links, and Annotations.
    """

    @staticmethod
    def parse_structure(content: str) -> Dict[str, Any]:
        """
        Parses the .dsx content and returns a structured representation.
        """
        jobs = []
        current_job = None
        current_stage = None
        current_link = None
        
        lines = content.splitlines()
        
        for line in lines:
            line = line.strip()
            if not line: continue

            # --- JOB level ---
            if line.startswith("BEGIN DSJOB"):
                current_job = {"name": "", "stages": [], "annotations": [], "parameters": {}}
                name_match = re.search(r'Identifier "([^"]+)"', line)
                if name_match: current_job["name"] = name_match.group(1)
                jobs.append(current_job)
                continue
            
            if line == "END DSJOB":
                current_job = None
                continue

            if not current_job: continue

            # --- STAGE level ---
            if line.startswith("BEGIN DSSTAGE"):
                current_stage = {"name": "", "type": "", "links": [], "properties": {}}
                name_match = re.search(r'Identifier "([^"]+)"', line)
                if name_match: current_stage["name"] = name_match.group(1)
                current_job["stages"].append(current_stage)
                continue

            if line == "END DSSTAGE":
                current_stage = None
                continue

            # --- LINK level ---
            if line.startswith("BEGIN DSLINK"):
                current_link = {"name": "", "partner": "", "properties": {}}
                name_match = re.search(r'Identifier "([^"]+)"', line)
                if name_match: current_link["name"] = name_match.group(1)
                if current_stage: current_stage["links"].append(current_link)
                continue

            if line == "END DSLINK":
                current_link = None
                continue

            # --- PROPERTY EXTRACTION (Key "Value") ---
            prop_match = re.match(r'(\w+)\s+"(.*)"', line)
            if prop_match:
                key, value = prop_match.groups()
                
                if current_link:
                    current_link["properties"][key] = value
                    if key == "Partner": current_link["partner"] = value
                elif current_stage:
                    current_stage["properties"][key] = value
                    if key == "StageType": current_stage["type"] = value
                elif current_job:
                    if key == "Identifier" and not current_job["name"]:
                         current_job["name"] = value

        return {
            "summary": f"Found {len(jobs)} jobs in file.",
            "jobs": jobs[:10] # Limit to avoid context explosion
        }
