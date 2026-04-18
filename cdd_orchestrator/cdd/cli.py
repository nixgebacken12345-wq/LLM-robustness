import asyncio
import typer
from pathlib import Path
from typing import Optional
from temporalio.client import Client
from cdd.config import settings
from cdd.state.db import init_db
from cdd.orchestrator.workflows import CDDOrchestratorWorkflow

app = typer.Typer(help="CDD Orchestrator CLI - Human-in-the-loop LLM Development.")

async def _run_workflow(requirements: str, project_path: str):
    """Internal helper to connect to Temporal and start the workflow."""
    try:
        client = await Client.connect(settings.TEMPORAL_ENDPOINT)
        
        # Start a workflow
        handle = await client.start_workflow(
            CDDOrchestratorWorkflow.run,
            args=[requirements, project_path],
            id=f"cdd-run-{int(asyncio.get_event_loop().time())}",
            task_queue="cdd-task-queue",
        )
        
        typer.secho(f"🚀 Workflow started successfully!", fg=typer.colors.GREEN)
        typer.secho(f"Workflow ID: {handle.id}", fg=typer.colors.CYAN)
        typer.echo(f"Run ID: {handle.result_run_id}")
        
    except Exception as e:
        typer.secho(f"❌ Failed to connect to Temporal: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

@app.command()
def init():
    """
    Initialize the local CDD environment.
    Creates the schema registry and required local directories.
    """
    typer.echo("Initializing CDD environment...")
    try:
        # Create user-facing directories
        Path(".cdd/context").mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite tables
        init_db()
        
        typer.secho("✅ Environment initialized. Registry created at cdd_state.db", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"❌ Initialization failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def run(
    requirements: str = typer.Argument(..., help="The feature or fix requirements as a string."),
    path: Path = typer.Option(
        Path("."), 
        "--path", "-p", 
        help="Target project directory path."
    )
):
    """
    Start a new CDD Orchestration cycle.
    """
    if not path.exists() or not path.is_dir():
        typer.secho(f"❌ Error: Path {path} is not a valid directory.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    abs_path = str(path.resolve())
    typer.echo(f"Target Project: {abs_path}")
    
    # Run the async temporal client
    asyncio.run(_run_workflow(requirements, abs_path))

@app.command()
def status(workflow_id: str):
    """
    Check the status of a specific CDD workflow execution.
    """
    async def _check():
        try:
            client = await Client.connect(settings.TEMPORAL_ENDPOINT)
            handle = client.get_workflow_handle(workflow_id)
            desc = await handle.describe()
            typer.echo(f"Status: {desc.status.name}")
        except Exception as e:
            typer.secho(f"❌ Could not retrieve status: {e}", fg=typer.colors.RED)

    asyncio.run(_check())

if __name__ == "__main__":
    app()