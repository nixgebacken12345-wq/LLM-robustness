from typing import List, Dict
from temporalio import activity
from cdd.llm.client import LLMService
from cdd.llm.schemas import AnalysisReport, ConsensusPlan

@activity.defn
async def phase1_analyze_requirements(input_data: Dict[str, str]) -> AnalysisReport:
    """Temporal Activity for Phase 1 (Diverge)."""
    prompt = f"Analyze requirements and codebase: {input_data['context']}"
    
    try:
        return await LLMService.call_structured(
            prompt=prompt,
            response_model=AnalysisReport,
            system_message="Analyze code for technical debt and feasibility."
        )
    except Exception as e:
        raise RuntimeError(f"Phase 1 Analysis Failed: {str(e)}")

@activity.defn
async def phase2_generate_consensus(reports: List[AnalysisReport]) -> ConsensusPlan:
    """Temporal Activity for Phase 2 (Converge)."""
    report_text = "\n---\n".join([r.model_dump_json() for r in reports])
    prompt = f"Consolidate reports into a master execution plan:\n{report_text}"
    
    try:
        return await LLMService.call_structured(
            prompt=prompt,
            response_model=ConsensusPlan,
            system_message="Act as the Arbiter. Resolve conflicts and output a DAG."
        )
    except Exception as e:
        raise RuntimeError(f"Phase 2 Consensus Failed: {str(e)}")