from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# --- Enums ---

class JobPlanStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"

class JobPlanMode(str, Enum):
    LOW_COST = "low_cost"
    DEEP_SCAN = "deep_scan"
    STANDARD = "standard"

class AreaKey(str, Enum):
    FOUNDATION = "FOUNDATION"
    PACKAGES = "PACKAGES"
    DOCS = "DOCS"
    AUX = "AUX"

class Strategy(str, Enum):
    PARSER_ONLY = "PARSER_ONLY"
    PARSER_PLUS_LLM = "PARSER_PLUS_LLM"
    LLM_ONLY = "LLM_ONLY"
    VLM_EXTRACT = "VLM_EXTRACT"
    SKIP = "SKIP"

class RecommendedAction(str, Enum):
    PROCESS = "PROCESS"
    SKIP = "SKIP"
    REVIEW = "REVIEW"

# --- Models ---

class JobPlanItemBase(BaseModel):
    path: str
    file_hash: Optional[str] = None
    size_bytes: Optional[int] = 0
    file_type: Optional[str] = None
    classifier: Dict[str, Any] = {}
    strategy: Strategy
    recommended_action: RecommendedAction
    enabled: bool = True
    order_index: int = 0
    risk_score: int = 0
    value_score: int = 0
    estimate: Dict[str, Any] = {} # tokens, cost, time
    planning_notes: Optional[str] = None
    status: str = "pending"

class JobPlanItem(JobPlanItemBase):
    item_id: uuid.UUID
    plan_id: uuid.UUID
    area_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class JobPlanAreaBase(BaseModel):
    area_key: AreaKey
    title: str
    order_index: int
    default_enabled: bool = True

class JobPlanArea(JobPlanAreaBase):
    area_id: uuid.UUID
    plan_id: uuid.UUID
    items: List[JobPlanItem] = []
    created_at: datetime

    class Config:
        from_attributes = True

class JobPlanBase(BaseModel):
    job_id: uuid.UUID
    status: JobPlanStatus = JobPlanStatus.DRAFT
    mode: JobPlanMode = JobPlanMode.STANDARD
    summary: Dict[str, Any] = {}
    user_overrides: Dict[str, Any] = {}

class JobPlan(JobPlanBase):
    plan_id: uuid.UUID
    areas: List[JobPlanArea] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- API Request/Response Models ---

class CreatePlanRequest(BaseModel):
    job_id: str
    mode: JobPlanMode = JobPlanMode.STANDARD

class UpdatePlanItemRequest(BaseModel):
    enabled: Optional[bool] = None
    order_index: Optional[int] = None
    area_id: Optional[str] = None

class PlanSummary(BaseModel):
    total_files: int
    total_cost_est: float
    total_time_est: float
    files_by_type: Dict[str, int]
