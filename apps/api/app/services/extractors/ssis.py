import re
from typing import List, Dict, Any

class SSISParser:
    """
    Parses SSIS .dtsx (XML) files to extract Control Flow structure.
    Does not rely on lxml to avoid dependency issues if not installed, 
    uses Regex/String parsing for robustness on large files.
    """
    
    @staticmethod
    def parse_structure(content: str) -> Dict[str, Any]:
        """
        Returns a detailed JSON structure of the package for v4.0 Deep Dive.
        """
        executables = []
        
        # 1. Extract All Executables with more detail
        # Heuristic: <DTS:Executable ... DTS:ObjectName="Name" ...>
        # We look for ObjectName, Description and Type
        exe_blocks = re.findall(r'<DTS:Executable.*?DTS:ExecutableType="([^"]+)".*?DTS:ObjectName="([^"]+)"(.*?)>', content, re.DOTALL)
        
        for exe_type, exe_name, extra in exe_blocks:
            if "SSIS.Package" in exe_type: continue
            
            comp = {
                "name": exe_name,
                "type": exe_type,
                "is_container": "Sequence" in exe_type or "For" in exe_type
            }
            
            # 2. Heuristic extraction of SQL if it's a SQL Task
            if "ExecuteSQLTask" in exe_type:
                sql_match = re.search(r'SQLStatementSource="([^"]+)"', content) # Simplified, might be in a child node
                if not sql_match:
                    # Look for content between <DirectInput> tags
                    sql_match = re.search(r'<DirectInput>(.*?)</DirectInput>', content, re.DOTALL)
                
                if sql_match:
                    comp["sql_logic"] = sql_match.group(1).strip()[:1000] # Truncate

            # 3. Heuristic for DataFlow components (very simplified)
            if "Pipeline" in exe_type:
                # Look for component names inside the same package block or context
                components = re.findall(r'componentClassID="[^"]+".*?name="([^"]+)"', content)
                comp["internal_components"] = list(set(components))[:20]

            executables.append(comp)
            
        return {
            "summary": f"Found {len(executables)} tasks/containers.",
            "tasks": executables[:40] 
        }
