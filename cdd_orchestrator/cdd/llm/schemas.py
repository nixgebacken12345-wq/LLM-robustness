import enum
from typing import List, Literal
from pydantic import BaseModel, Field

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProposedChange(BaseModel):
    file_path: str = Field(..., description="Target file for modification")
    change_type: Literal["create", "modify", "delete"] = Field(...)
    description: str = Field(..., description="Summary of what is being changed")
    impact_analysis: str = Field(..., description="How this affects other modules")

class AnalysisReport(BaseModel):
    """Output of Phase 1: Diverge"""
    thought_chain: str = Field(..., description="Step-by-step reasoning")
    risks: List[str] = Field(default_factory=list)
    risk_score: RiskLevel
    suggested_changes: List[ProposedChange]

class ExecutionTask(BaseModel):
    task_id: str = Field(..., description="Unique ID for DAG node")
    depends_on: List[str] = Field(default_factory=list, description="IDs of prerequisite tasks")
    action_type: str = Field(..., description="e.g., 'TDD_LOOP', 'REFACTOR', 'DOC_GEN'")
    target_files: List[str]
    instructions: str = Field(..., description="Detailed instructions for the executor agent")

class ConsensusPlan(BaseModel):
    """Output of Phase 2: Converge"""
    consensus_summary: str
    architectural_decisions: List[str]
    dag: List[ExecutionTask]
    total_token_estimate: int