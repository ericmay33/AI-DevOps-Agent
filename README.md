# DevOps Autonomous CI Remediation Agent

## Overview
This project is an AI-powered DevOps agent that analyzes a repository, detects CI/CD pipeline failures, determines the root cause, proposes or applies fixes, and automatically opens pull requests.

The system is built now with:

- 🔍 Repository analysis  
- 🧠 CI failure diagnosis  
- 🛠️ Auto-generated patches  
- 🔁 PR automation with explanations  

We are **not yet implementing infrastructure consistency scans**, but the system architecture is intentionally designed so that such features can plug in later without major rewrites.

---

## System Architecture\

Repository
↓
Scanner / Analyzer
↓
Knowledge Model (LLM + structured storage)
↓
Failure Analysis (root cause)
↓
Proposed Fix / Patch Generator
↓
GitHub API → Branch → Commit → PR

### Components

#### Repo Analysis Engine
- Walks repo tree
- Identifies:
  - Workflows
  - Dockerfiles
  - Dependency files
  - Key config files
- Produces a structured data model the agent can query

#### CI Log Ingestion
- Interfaces with GitHub API
- Fetches logs from failed runs

#### Reasoning Engine
- Classifies failure type  
- Generates a structured remediation plan

#### Patch Generator
- Applies file edits
- Writes or updates config files accordingly

#### PR Automation
Creates a full pull request including:
- Summary of failure
- Reasoning behind fix
- Changes made
- Confidence estimates

---

## Technology Stack

### Backend
- Python (FastAPI or similar)
- GitHub REST or GraphQL API
- Repo FS parsing
- Docker

### Agent / AI
- LLM-based reasoning
- Deterministic guardrail prompts
- Optional embeddings for persistent repo context

### Frontend
A minimal interface showing:
- Live agent actions (e.g. “Analyzing CI logs…”)
- Repo scan results
- Proposed patches
- PR history

---

## Future Expansion
Later we will add **infrastructure consistency and drift checks**, and the architecture has been built to make this possible without:

- Changing the repo knowledge model
- Rewriting patch application logic
- Replacing the CI analysis workflow

---

## Project Status
- Requirements defined  
- Architecture designed  
- Development beginning  
