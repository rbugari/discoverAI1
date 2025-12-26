from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Package(BaseModel):
    package_id: uuid.UUID
    project_id: uuid.UUID
    asset_id: Optional[uuid.UUID] = None
    name: str
    type: Optional[str] = None # SSIS, DataStage, Python
    source_system: Optional[str] = None
    target_system: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    business_intent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PackageComponent(BaseModel):
    component_id: uuid.UUID
    package_id: uuid.UUID
    parent_component_id: Optional[uuid.UUID] = None
    name: str
    type: str
    logic_raw: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    source_mapping: List[Dict[str, Any]] = Field(default_factory=list)
    target_mapping: List[Dict[str, Any]] = Field(default_factory=list)
    order_index: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class TransformationIR(BaseModel):
    ir_id: uuid.UUID
    project_id: uuid.UUID
    source_component_id: Optional[uuid.UUID] = None
    operation: str # READ, WRITE, SELECT, FILTER, JOIN, AGGREGATE, LOOKUP, DERIVE, SCD
    logic_summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime

    class Config:
        from_attributes = True

class ColumnLineage(BaseModel):
    lineage_id: uuid.UUID
    project_id: uuid.UUID
    package_id: Optional[uuid.UUID] = None
    ir_id: Optional[uuid.UUID] = None
    source_asset_id: Optional[uuid.UUID] = None
    source_column: Optional[str] = None
    target_asset_id: Optional[uuid.UUID] = None
    target_column: Optional[str] = None
    transformation_rule: Optional[str] = None
    confidence: float = 1.0
    created_at: datetime

    class Config:
        from_attributes = True

# --- Results for Pipeline ---

class DeepDiveResult(BaseModel):
    package: Package
    components: List[PackageComponent]
    transformations: List[TransformationIR]
    lineage: List[ColumnLineage]
