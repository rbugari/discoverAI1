from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Locator(BaseModel):
    file: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    xpath: Optional[str] = None
    byte_start: Optional[int] = None
    byte_end: Optional[int] = None

class Evidence(BaseModel):
    evidence_id: str
    kind: str = Field(..., description="code|xml|log|config|regex_match")
    locator: Locator
    snippet: str
    hash: Optional[str] = None

class ExtractedNode(BaseModel):
    node_id: str
    node_type: str = Field(..., description="table|view|file|api|process|package|task|script")
    name: str
    system: str = Field(..., description="sqlserver|files|api|unknown")
    attributes: Dict[str, Any] = Field(default_factory=dict)

class ExtractedEdge(BaseModel):
    edge_id: str
    edge_type: str = Field(..., description="READS_FROM|WRITES_TO|DEPENDS_ON|CALLS_API|CONTAINS")
    from_node_id: str
    to_node_id: str
    confidence: float
    rationale: str
    evidence_refs: List[str] = Field(default_factory=list)
    is_hypothesis: bool = False

class ExtractionResult(BaseModel):
    meta: Dict[str, Any]
    nodes: List[ExtractedNode]
    edges: List[ExtractedEdge]
    evidences: List[Evidence]
    assumptions: List[str] = Field(default_factory=list)
