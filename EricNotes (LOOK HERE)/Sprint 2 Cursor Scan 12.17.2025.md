# AI DevOps Agent: Autonomous CI/CD Remediation System

## Project Vision

The AI DevOps Agent is a research-grade autonomous system that diagnoses CI/CD failures, generates remediation patches, and opens pull requests with explainable reasoning. Unlike GitHub Copilot or Codex—which assist developers during coding—this agent operates autonomously in production CI/CD environments, analyzing actual runtime failures and proposing fixes without human intervention.

### What Makes This Novel

**The Core Innovation:** Combining static repository analysis with live CI/CD runtime logs creates a unique "sensory system" for the agent:

- **Static Analysis (Sprint 1)** answers: "What does this repository contain? What workflows exist? What dependencies are declared?"
- **Runtime Intelligence (Sprint 2)** answers: "What actually failed? What error messages appeared? Which step crashed?"

Together, these form a complete ground truth that enables the agent to:
1. Understand repository structure (workflows, dependencies, configs)
2. Correlate failures with actual error logs
3. Generate contextually-aware patches
4. Explain reasoning in PR descriptions

This dual-source approach prevents hallucination and enables deterministic remediation—the agent reasons from evidence, not speculation.

### Intended Capabilities

- **Automated Remediation**: Detect CI failures, diagnose root causes, generate patches
- **PR Automation**: Create branches, commit fixes, open PRs with detailed explanations
- **Observability**: Real-time event stream showing agent reasoning steps
- **Future Expansion**: Infrastructure drift detection, policy compliance scanning

---

## System Architecture (Current State)

The system is modular and pipeline-oriented. Each module produces structured output that feeds into the next stage.

### Data Flow

GitHub Repository URL
↓
[github_bridge/client.py] → Authenticate (PAT)
↓
[github_bridge/clone.py] → Clone to temp directory
↓
[scanner/scanner.py] → Three-phase repository scan
├─ Phase 1: Discovery (file inventory)
├─ Phase 2: Classification (artifact categorization)
└─ Phase 3: Extraction (content parsing)
↓
[github_bridge/workflows.py] → Discover workflow runs
↓
[github_bridge/logs.py] → Extract failure logs (if failures exist)
↓
[github_bridge/context_builder.py] → Merge into AgentContext
↓
agent_context.json (single source of truth)

---

### Module Breakdown

#### `scanner/` — Repository Intelligence Engine

**Purpose:** Build a comprehensive knowledge model of repository structure and contents.

**Components:**
- `discovery.py`: Phase 1 — Filesystem traversal, respects `.gitignore`, handles symlinks
- `classifiers.py`: Phase 2 — Artifact type detection (workflows, Dockerfiles, manifests, configs)
- `extraction.py`: Phase 3 — Content parsing (YAML, JSON, structured data extraction)
- `scanner.py`: Main orchestrator — Coordinates three-phase pipeline

**Output:** Structured JSON containing:
- Artifact inventory (type, path, metadata, content)
- Relationship graph (workflow → Dockerfile → dependencies)
- Repository summary (primary language, CI platform, containerization status)

**Key Features:**
- Respects `.gitignore` and default ignore patterns (`.git`, `__pycache__`, `node_modules`, etc.)
- Filters failed reads (empty content with errors)
- Minified output (excludes IDs, timestamps, empty tags)
- Size limits (1MB files = metadata only)

#### `github_bridge/` — GitHub API & CI/CD Intelligence

**Purpose:** Connect static analysis to live GitHub runtime context.

**Components:**
- `client.py`: GitHub API authentication and repository metadata fetching
- `clone.py`: Secure repository cloning to temporary directories
- `workflows.py`: Workflow run discovery (`WorkflowDiscoverer`)
- `logs.py`: Failure log extraction (`LogMiner`) — extracts error lines from failed jobs
- `context_builder.py`: Merges scanner output + CI context into `AgentContext`
- `bridge.py`: Main orchestrator — executes full pipeline end-to-end

**Output:** `AgentContext` Pydantic model containing:
- Repository metadata (`full_name`, `default_branch`)
- Static analysis results (from scanner)
- CI context (`platform`, `recent_runs`, `failure_logs`)

**Key Design Decisions:**
- Temporary clone directories (cleaned up automatically)
- Error extraction from logs (searches for Error/Exception patterns, limits to last 100 lines)
- Graceful degradation (warnings if workflows/logs unavailable, continues execution)

---

## Sprint Breakdown

### Sprint 1: Repository Intelligence (Completed)

**Goal:** Build a comprehensive scanner that understands repository structure.

**What It Does:**
- Performs three-phase hierarchical traversal:
  1. **Discovery**: Walk filesystem, build inventory
  2. **Classification**: Categorize files into artifact types
  3. **Extraction**: Parse content, extract structured metadata

**Problems Solved:**
- **Knowledge Gap**: Agent needs to understand what files exist, what they contain
- **Relationship Mapping**: Discovers connections (workflow → Dockerfile → dependencies)
- **Structured Query**: Provides LLM with queryable repository knowledge model

**Schema & Outputs:**
{
  "repository": {
    "id": "...",
    "name": "...",
    "scanned_at": "...",
    "scan_version": "1.0.0"
  },
  "artifacts": [
    {
      "type": "workflow",
      "subtype": "github_actions",
      "path": ".github/workflows/ci.yml",
      "metadata": { "platform": "github_actions", "jobs": [...] },
      "content": { "raw": "...", "structured": {...} }
    }
  ],
  "relationships": { "artifact_id": [{"type": "depends_on", "to": "..."}] },
  "summary": {
    "primary_language": "python",
    "ci_platform": "github_actions",
    "containerization": true
  }
}**Status:** ✅ Complete — Production-ready scanner with artifact classification, relationship detection, and optimized output.

---

### Sprint 2: GitHub Bridge & CI/CD Log Intelligence (Completed)

**Goal:** Connect static repository knowledge to live CI/CD runtime failures.

**What It Does:**
- Authenticates with GitHub API (PAT-based, extensible to OAuth)
- Clones repositories to temporary directories
- Discovers workflow runs (recent runs, latest failures)
- Extracts failure logs from failed jobs
- Merges everything into `agent_context.json`

**Problems Solved:**
- **Runtime Evidence**: Static analysis alone cannot explain why CI failed
- **Error Extraction**: Raw logs are massive; extracts relevant error lines
- **Context Unification**: Single JSON file contains both static and runtime data

**Authentication Strategy:**
- Current: GitHub Personal Access Token (PAT) via environment variable or `.env`
- Future: OAuth App with user-scoped repository access (Sprint 4)

**Repo Cloning Strategy:**
- Uses `tempfile.mkdtemp()` for secure temporary directories
- Supports public and private repos (via token injection)
- Automatic cleanup in `finally` block

**Workflow Discovery:**
- Fetches recent workflow runs (configurable limit, default 10)
- Identifies latest failure (`get_latest_failure()`)
- Populates `WorkflowRun` models (minified: `run_id`, `name`, `conclusion` only)

**CI/CD Failure Log Extraction:**
- Downloads logs via GitHub API (`/actions/jobs/{job_id}/logs`)
- Processes plain text logs (not ZIP files)
- Extracts error-relevant lines:
  - Searches for patterns: `Error`, `Exception`, `FAILED`, `Traceback`
  - Includes context (5 lines before/after error)
  - Limits to last 100 lines if no error patterns found
- Creates `FailureLog` objects with `job_name`, `step_name`, `log_content`

**How Runtime Errors Are Captured:**
# Example FailureLog structure
{
  "job_name": "test",
  "step_name": "Run pytest",
  "log_content": "Error: ModuleNotFoundError: No module named 'pytest'\n..."
}**Status:** ✅ Complete — Full pipeline from GitHub URL to `agent_context.json` with CI log mining.

---

### Sprints 1–2 Together: The Agent's Sensory System

**Sprint 1** provides the "anatomy" — what the repository contains.  
**Sprint 2** provides the "symptoms" — what actually failed at runtime.

Together, they enable the agent to:
- Correlate failures with repository structure
- Understand dependencies between artifacts
- Generate fixes that respect existing patterns
- Explain reasoning with evidence

**Example:** If a workflow fails with "ModuleNotFoundError: pytest", the agent can:
1. Check `requirements.txt` (from Sprint 1) — is pytest declared?
2. Check workflow YAML (from Sprint 1) — is it installed correctly?
3. Check failure log (from Sprint 2) — what exact error occurred?
4. Generate fix: Add pytest to requirements.txt or fix installation step

---

## Key Engineering Decisions

### Why Python

- **Rapid Development**: Fast iteration for research-grade system
- **Ecosystem**: Rich libraries for GitHub API, YAML/JSON parsing, file system operations
- **LLM Integration**: Native support for OpenAI/Anthropic APIs
- **Future-Proof**: Easy to add FastAPI backend, async operations

### Why PyGithub / GitHub API

- **PyGithub**: Python-native wrapper, stable, well-maintained
- **Direct API Calls**: For log downloads (PyGithub doesn't expose log endpoints cleanly)
- **Extensibility**: Architecture supports swapping auth methods (PAT → OAuth) without refactoring

### Why Logs Are More Valuable Than YAML Alone

**The Critical Insight:** Workflow YAML files describe *intent*, but logs describe *reality*.

- **YAML tells you:** "This step runs `pytest`"
- **Logs tell you:** "pytest failed because module X is missing version Y"

Logs contain:
- Actual error messages (not just exit codes)
- Environment-specific failures (version mismatches, missing dependencies)
- Step-by-step execution traces
- Context that YAML cannot capture

**Example:** A workflow YAML might declare `python-version: '3.9'`, but logs reveal the runner actually used Python 3.10, causing a dependency conflict. The agent needs logs to diagnose this.

### Why Context Is Bundled Into `agent_context.json`

**Single Source of Truth:** The LLM receives one complete context file, preventing:
- Hallucination from incomplete data
- Inconsistencies between static and runtime data
- Token waste from redundant information

**Versioned & Inspectable:** Each `agent_context.json` is:
- Reproducible (same repo URL = same context, modulo CI runs)
- Debuggable (can inspect what agent saw)
- Testable (can replay reasoning on historical contexts)

**Optimized for LLM Consumption:**
- Minified fields (removed IDs, timestamps, empty tags)
- Filtered noise (skipped failed reads, ignored directories)
- Structured for easy parsing (Pydantic models → JSON)

---

## Example Output

**High-Level Structure of `agent_context.json`:**

{
  "repo": {
    "full_name": "owner/repo",
    "default_branch": "main"
  },
  "static_analysis": {
    "repository": { "name": "...", "scanned_at": "..." },
    "artifacts": [
      {
        "type": "workflow",
        "path": ".github/workflows/ci.yml",
        "metadata": { "platform": "github_actions", "jobs": [...] },
        "content": { "raw": "name: CI\non: [push]\n..." }
      },
      {
        "type": "dependency_manifest",
        "path": "requirements.txt",
        "metadata": { "package_manager": "pip", "dependencies": {...} }
      }
    ],
    "summary": {
      "primary_language": "python",
      "ci_platform": "github_actions",
      "containerization": false
    }
  },
  "ci_context": {
    "platform": "github_actions",
    "recent_runs": [
      {
        "run_id": 123456789,
        "name": "CI Build",
        "conclusion": "failure"
      }
    ],
    "failure_logs": [
      {
        "job_name": "test",
        "step_name": "Install dependencies",
        "log_content": "ERROR: Could not find a version that satisfies the requirement pytest==7.0.0\n..."
      }
    ]
  }
}**What the Agent Sees:**
- Repository structure (workflows, dependencies, configs)
- Recent CI runs (which failed, which succeeded)
- Actual error messages from failed jobs
- Relationships between artifacts

**What the Agent Can Do:**
- Correlate failure logs with repository artifacts
- Identify root cause (dependency version mismatch, missing step, etc.)
- Generate fix (update requirements.txt, add installation step, etc.)

---

## What Comes Next

### Sprint 3: LLM Reasoning + Patch Generation + PR Automation

**Goal:** Transform `agent_context.json` into actionable patches and pull requests.

**Components:**
- **Reasoning Engine**: LLM-based failure classification and root cause analysis
- **Patch Generator**: Deterministic file modifications (update requirements.txt, fix workflow YAML, etc.)
- **PR Automation**: Branch creation, commit, push, PR opening with explanations

**Deliverables:**
- Structured patch output (file path → old content → new content)
- PR descriptions with reasoning chain
- Confidence scoring for fixes
- Guardrails (no destructive changes, requires approval for sensitive files)

**Status:** 🚧 In Design — Architecture defined, implementation pending.

---

### Sprint 4: Frontend Visualization + OAuth + Live Events

**Goal:** Human-facing interface for agent observability and control.

**Components:**
- **Frontend**: Real-time agent event stream, repository selection, PR review UI
- **OAuth Integration**: GitHub OAuth App for user-scoped repository access
- **Event System**: Structured events ("Scanning repository...", "Fix proposed", "PR opened")

**Deliverables:**
- Web interface showing agent actions in real time
- OAuth flow for repository access
- Event API for frontend consumption
- PR review interface

**Status:** 📋 Planned — Architecture extensible, Sprint 2 supports GitHub OAuth swap.

---