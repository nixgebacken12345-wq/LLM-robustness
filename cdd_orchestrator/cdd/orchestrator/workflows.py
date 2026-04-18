from datetime import timedelta
import asyncio
from typing import List
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import schemas for type safety
# Note: In production, these would be imported from your actual package structure
with workflow.unsafe.imports_passed_through():
    from cdd.llm.schemas import AnalysisReport, ConsensusPlan, ExecutionTask
    from cdd.config import settings

@workflow.defn
class CDDOrchestratorWorkflow:
    """
    Main Orchestrator for Project CDD.
    Coordinates the multi-phase LLM development lifecycle.
    """

    @workflow.run
    async def run(self, requirements: str, project_path: str) -> str:
        # 1. Configuration & Policies
        standard_retry = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_attempts=settings.RETRY_MAX_ATTEMPTS,
            non_retryable_error_types=["ValueError"]
        )

        # 2. Phase 0: Genesis (Scan environment)
        # This activity would be defined in phase0_genesis.py
        workflow.logger.info(f"Starting Phase 0 for project at {project_path}")
        context_data = await workflow.execute_activity(
            "phase0_scan_repository",
            args=[project_path],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=standard_retry
        )

        # 3. Phase 1: Diverge (Parallel Analysis)
        workflow.logger.info("Starting Phase 1: Parallel LLM Analysis")
        analysis_tasks = []
        for i in range(settings.PHASE1_PARALLELISM):
            # We pass unique seeds or slightly varied prompts to ensure diversity
            analysis_tasks.append(
                workflow.execute_activity(
                    "phase1_analyze_requirements",
                    args=[{"context": context_data, "requirements": requirements, "agent_id": i}],
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=standard_retry
                )
            )
        
        # Execute all analysis calls in parallel
        reports: List[AnalysisReport] = await asyncio.gather(*analysis_tasks)

        # 4. Phase 2: Converge (Arbiter / Consensus)
        workflow.logger.info("Starting Phase 2: Generating Consensus Plan")
        plan: ConsensusPlan = await workflow.execute_activity(
            "phase2_generate_consensus",
            args=[reports],
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=standard_retry
        )

        # 5. Phase 3: Execute (DAG Traversal)
        # For simplicity in this unit, we execute the DAG sequentially.
        # In a more complex version, we would use a task-completion map to run 
        # independent nodes in parallel.
        workflow.logger.info(f"Executing DAG with {len(plan.dag)} tasks")
        for task in plan.dag:
            await workflow.execute_activity(
                "phase3_execute_task",
                args=[task],
                start_to_close_timeout=timedelta(minutes=30),
                retry_policy=standard_retry
            )

        # 6. Phase 4: Audit
        workflow.logger.info("Starting Phase 4: Final Audit")
        audit_result = await workflow.execute_activity(
            "phase4_perform_audit",
            args=[plan.consensus_summary],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=standard_retry
        )

        return f"Workflow Complete. Audit Status: {audit_result}"