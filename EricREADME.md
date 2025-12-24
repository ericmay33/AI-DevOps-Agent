# Eric – Responsibilities & Development Plan

## Role Summary
Eric leads:

- Practical system implementation
- GitHub integration
- File system parsing
- Patch application
- Automated PR lifecycle

Shawn creates the logic; Eric turns it into working software.

---

# Sprint Plan

## Sprint 1 – Repository Scanner Implementation
### User Story
As the agent, I need to collect repository contents so analysis can be performed.

### Eric Responsibilities
- Build:
  - Directory walker
  - File classification
  - Detection of:
    - Workflow files
    - Dockerfiles
    - Dependency manifests
- Serialize output to Shawn’s schema

### Definition of Done
- Scanner can run against any repo
- Generates structured JSON output

---

## Sprint 2 – GitHub API + CI Log Retrieval
### User Story
As the agent, I need CI logs to determine why jobs failed.

### Eric Responsibilities
- Integrate with GitHub API:
  - Auth setup
  - Fetch CI runs
  - Download logs
- Expose data to Shawn’s analyzer

### Definition of Done
- A script or service can:
  - Download logs
  - Hand them directly to the reasoning engine

---

## Sprint 3 – Patch Application & PR Automation
### User Story
As a developer, I want the AI to apply fixes and open PRs automatically.

### Eric Responsibilities
- Implement:
  - Patch application from Shawn’s structured output
  - Branch creation
  - Commit and push
  - PR opening with relevant details

### Definition of Done
- A fix proposed by the AI results in:
  - Modified files
  - A branch pushed to GitHub
  - A PR created

---

## Sprint 4 – Event/Timeline System
### User Story
As the user, I want to see what the agent is doing in real time.

### Eric Responsibilities
- Emit structured events such as:
  - "Scanning repository"
  - "CI logs retrieved"
  - "Fix proposed"
  - "PR opened"

### Definition of Done
- Frontend can subscribe and display progress in real time

---

## Core Implementation Principle
Eric ensures:

- System is stable and production-safe
- Modules are decoupled
- Adding future infrastructure audits is a small addition, not a rewrite
