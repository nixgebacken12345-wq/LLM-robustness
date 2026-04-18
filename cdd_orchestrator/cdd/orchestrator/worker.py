import asyncio
import signal
from temporalio.client import Client
from temporalio.worker import Worker

# Configuration and Workflow imports
from cdd.config import settings
from cdd.orchestrator.workflows import CDDOrchestratorWorkflow

# Activity imports
# Note: These must be imported so they can be registered
from cdd.orchestrator.activities.llm_tasks import (
    phase1_analyze_requirements,
    phase2_generate_consensus
)

# Placeholder imports for upcoming activity units
# In a full system, these are implemented in their respective phaseN_*.py files
async def phase0_scan_repository(project_path: str) -> str:
    from cdd.parsers.repo_mapper import RepoMapper
    mapper = RepoMapper(project_path)
    mapper.scan()
    return f"Scan complete for {project_path}"

async def phase3_execute_task(task: any) -> str:
    # Logic for Docker sandbox execution
    return f"Task {task.task_id} executed"

async def phase4_perform_audit(summary: str) -> str:
    # Logic for final verification
    return "Audit passed"

async def main():
    # 1. Connect to Temporal Server
    try:
        client = await Client.connect(settings.TEMPORAL_ENDPOINT)
    except Exception as e:
        print(f"CRITICAL: Could not connect to Temporal at {settings.TEMPORAL_ENDPOINT}: {e}")
        return

    # 2. Define Activities
    # Every activity function used in the workflow MUST be registered here.
    activities = [
        phase0_scan_repository,
        phase1_analyze_requirements,
        phase2_generate_consensus,
        phase3_execute_task,
        phase4_perform_audit,
    ]

    # 3. Initialize Worker
    # task_queue must match the name used in the CLI/Workflow starter
    worker = Worker(
        client,
        task_queue="cdd-task-queue",
        workflows=[CDDOrchestratorWorkflow],
        activities=activities,
    )

    print(f"👷 CDD Worker started on queue 'cdd-task-queue'...")
    print(f"Connected to Temporal: {settings.TEMPORAL_ENDPOINT}")

    # 4. Graceful Shutdown Handling
    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        # Run the worker until the stop event is set
        await worker.run()
    except Exception as e:
        print(f"Worker crashed: {e}")
    finally:
        print("Worker shutting down...")

if __name__ == "__main__":
    asyncio.run(main())