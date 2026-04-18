
### Instructions for the X: Drive:
1. Open your terminal in `X:\Redteam\git\LLM-robustness`.
2. Run: `notepad README.md`
3. Paste the content below and save.

---

# PROJECT-CDD: Industrial LLM Redteaming Orchestrator

**Status:** Infrastructure Initialized (Core-8 Units Deployed)  
**Target:** Robustness testing against encoding artifacts (Homoglyphs, Zero-Width characters, AST-level injections).

## 🏗 Repository Architecture
The system is built on an **Industrial 5-Phase Lifecycle** managed by Temporal.io.

| Component | Path | Status | Purpose |
| :--- | :--- | :--- | :--- |
| **Config** | `cdd/config.py` | ✅ Deployed | Pydantic-Settings & Env Validation |
| **State** | `cdd/state/db.py` | ✅ Deployed | SQLite Registry & ACID Compliance |
| **Contracts** | `cdd/llm/schemas.py` | ✅ Deployed | Pydantic Models for LLM Consensus |
| **Client** | `cdd/llm/client.py` | ✅ Deployed | Instructor-patched LiteLLM Service |
| **Workflows** | `cdd/orchestrator/workflows.py` | ✅ Deployed | Deterministic State Machine |
| **Activities** | `cdd/orchestrator/activities/llm_tasks.py` | ✅ Deployed | LLM Analysis & Arbiter Logic |
| **Parser** | `cdd/parsers/repo_mapper.py` | ✅ Deployed | Tree-Sitter AST Mapping |
| **Interface** | `cdd/cli.py` | ✅ Deployed | Typer CLI for System Control |



## 🚀 Operations Manual

### 1. Infrastructure Boot
Ensure the Temporal Cluster is active via Docker:
```bash
docker-compose -f docker-compose.temporal.yml up -d
```

### 2. The Engine Room (Worker)
The Worker must be running to execute activities. Open a dedicated terminal:
```bash
call venv\Scripts\activate
python -m cdd.orchestrator.worker
```

### 3. Command Line Interface
```bash
# Initialize Registry
python -m cdd.cli init

# Trigger Orchestration
python -m cdd.cli run "Analyze for hidden encoding artifacts" --path .
```

## 🛠 Engineering Backlog (Pending Implementation)

### High Priority: Phase 3 (Execution Sandbox)
- [ ] **`cdd/sandbox/docker_manager.py`**: Safe execution of LLM-generated code in isolated containers.
- [ ] **`cdd/sandbox/templates/`**: Multi-version Python Dockerfiles.

### Reliability & Redteaming
- [ ] **Saga Implementation**: `saga_tasks.py` for automated Git rollbacks on audit failure.
- [ ] **Artifact Detectors**: Regex and byte-level scanners for detecting homoglyphs in `AnalysisReport`.
- [ ] **HITL Gates**: Manual approval steps for high-risk architectural changes.

## ⚠️ Critical Constraints
- **Absolute Imports**: Always run from project root using `python -m`.
- **Determinism**: Workflows must not use non-deterministic functions (e.g., `datetime.now()`).
- **Encoding Integrity**: Edits to test cases must be saved in **UTF-8 (No BOM)** to preserve redteam artifacts.

