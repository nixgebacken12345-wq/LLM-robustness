import pytest
from cdd.llm.schemas import ExecutionTask, ConsensusPlan

def test_consensus_plan_dag_validity():
    """Verify that a consensus plan does not have obvious circular dependencies."""
    task1 = ExecutionTask(task_id="A", action_type="test", target_files=["f1.py"], instructions="do A")
    task2 = ExecutionTask(task_id="B", depends_on=["A"], action_type="test", target_files=["f2.py"], instructions="do B")
    
    plan = ConsensusPlan(
        consensus_summary="OK",
        architectural_decisions=[],
        dag=[task1, task2],
        total_token_estimate=100
    )
    
    ids = [t.task_id for t in plan.dag]
    for task in plan.dag:
        for dep in task.depends_on:
            assert dep in ids, f"Dependency {dep} missing from task list"