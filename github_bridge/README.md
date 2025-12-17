# github_bridge

## Purpose

The `github_bridge` module connects static repository intelligence (Sprint 1 Scanner) to live GitHub runtime context (CI/CD executions, logs, commits).

It acts as the real-world ingestion layer for the DevOps Agent.

## 🔌 Why This Exists

**Sprint 1 answers:**
> "What does this repository look like?"

**Sprint 2 answers:**
> "What actually happened when this repository ran in CI?"

The DevOps Agent cannot reason correctly without both.

### This module:

- Pulls repositories from GitHub
- Executes the scanner on real code
- Fetches failed CI/CD runs + logs
- Bundles everything into agent-ready context

**This is the bridge between GitHub and the agent brain.**

## 🧠 Conceptual Flow

```
GitHub Repo URL
      ↓
Authenticate (PAT)
      ↓
Clone Repository
      ↓
Run Repository Scanner (Sprint 1)
      ↓
Fetch CI/CD Workflow Runs
      ↓
Extract Failed Job Logs
      ↓
Bundle Everything → agent_context.json
```

> **Note:** This module does NOT perform AI reasoning  
> **Note:** This module does NOT modify repositories

It prepares ground truth + runtime evidence so Sprint 3 can act safely.

## 🔐 Authentication Model

### Current (Sprint 2):

GitHub Personal Access Token (PAT)

Stored via environment variable:

```
export GITHUB_TOKEN=ghp_xxx
```

### Future (Sprint 4+):

- GitHub OAuth App
- User-scoped repo access via frontend

This module is written so auth can be swapped without refactoring logic.

## 🧩 Core Components

### `client.py`

**Responsible for:**

- Initializing authenticated GitHub API access
- Resolving repo metadata from URL
- Listing workflows, runs, jobs

**Uses:**
- PyGithub (Python-native, stable, fast iteration)

### `clone.py`

**Responsible for:**

- Cloning repos securely to temp directories
- Supporting:
  - Public repos
  - Private repos (via PAT)
- Cleaning up after execution

**Example:**

```
/tmp/agent-scans/{repo_name}_{uuid}/
```

**This ensures:**

- Scanner runs on real file trees
- No mutation of user environments

### `logs.py`

**Responsible for:**

- Identifying CI platform (GitHub Actions first)
- Fetching:
  - Recent workflow runs
  - Failed runs
  - Failed jobs
  - Downloading raw logs
- Extracting:
  - Error messages
  - Exit codes
  - Step names

**This is the most important Sprint 2 contribution.**

> Logs are where the truth lives.

### `context_builder.py`

**Responsible for:**

- Executing the full pipeline:
  - Clone repo
  - Run scanner
  - Fetch CI logs
  - Normalize data
- Emitting a single artifact: `agent_context.json`

**This file becomes:**

- The sole input to Sprint 3 agent reasoning
- Versioned, inspectable, reproducible

## 📦 Output: agent_context.json

This module produces a single structured context bundle:

```json
{
  "repository": {...},
  "repository_knowledge": {...},  // Scanner output
  "ci_context": {
    "platform": "github_actions",
    "last_failed_run": {
      "run_id": "...",
      "commit": "...",
      "workflow": "...",
      "jobs": [
        {
          "job_name": "...",
          "logs": "raw log text"
        }
      ]
    }
  }
}
```

This structure is intentionally verbose so the LLM:

- Does NOT hallucinate
- Can trace errors to files
- Can generate safe patches

## 🧠 Design Philosophy

### Why This Is Not "Just Another GitHub Bot"

- We do **not** blindly fix things
- We do **not** act without evidence
- We separate scanning, context, reasoning, execution

**This separation:**

- Enables safety
- Enables explainability
- Enables enterprise trust

## 🔮 How This Feeds Future Sprints

### Sprint 3 — The Agent

- Reads `agent_context.json`
- Plans fixes based on actual failure logs
- Generates patch plans
- Opens PRs

### Sprint 4 — Frontend

**Displays:**

- Scan progress
- CI failures
- Agent reasoning steps
- PR creation events

## ✅ Sprint 2 Definition of Done

- ✅ Repo URL → clone → scan works
- ✅ CI logs fetched for failed workflows
- ✅ Context bundle generated
- ✅ No AI logic inside this module
- ✅ Clean handoff to Sprint 3

## 🧠 Mental Model (Important)

- **Sprint 1:** What exists
- **Sprint 2:** What failed
- **Sprint 3:** What to do
- **Sprint 4:** Watch it happen