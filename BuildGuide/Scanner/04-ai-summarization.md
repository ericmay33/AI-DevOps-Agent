# 04: AI Summarization & Tagging

## What This Does

After artifacts are classified and stored, they get summarized and tagged to make them easier to understand and search. This adds human-readable descriptions and categorization tags to each artifact.

---

## Overview

**For each artifact**, the system generates:
1. **Summary** (1-2 sentences): What the artifact does and its role
2. **Tags** (3-10 tags): Categories for filtering and searching

**For the repository**, the system generates:
- A high-level summary covering project type, tech stack, CI/CD approach, etc.

---

## Artifact Summarization

### Summary Format

Each artifact gets a 1-2 sentence summary describing:
- What the artifact does
- Its role in the repository
- Key characteristics

**Examples**:

**Workflow**:
> "GitHub Actions workflow that runs tests on push and pull requests. Uses Node.js 18 and runs linting, unit tests, and integration tests."

**Dockerfile**:
> "Multi-stage Dockerfile for Python application. Builds from Python 3.9 base image, installs dependencies from requirements.txt, and exposes port 8000."

**Dependency Manifest**:
> "Node.js package.json defining project dependencies. Includes Express for web server, Jest for testing, and ESLint for code quality."

### Tag Categories

Tags are organized into 4 categories:

1. **Functional tags**: What the artifact does
   - `ci-workflow`, `build-step`, `test-runner`, `deployment`, `linting`

2. **Technology tags**: What technologies it uses
   - `python`, `docker`, `nodejs`, `github-actions`, `terraform`

3. **Purpose tags**: Why it exists
   - `testing`, `deployment`, `build`, `configuration`, `infrastructure`

4. **Risk tags**: Important characteristics
   - `security-sensitive`, `production-critical`, `external-dependency`

**Example tags for a workflow**:
```json
{
  "tags": [
    "ci-workflow",        // Functional
    "github-actions",     // Technology
    "testing",            // Purpose
    "production-critical" // Risk
  ]
}
```

---

## Repository-Level Summary

The repository gets a high-level summary covering:

1. **Project type**: What kind of project (web app, library, monorepo, etc.)
2. **Technology stack**: Main technologies used
3. **CI/CD approach**: How CI/CD is set up
4. **Architecture patterns**: Project structure patterns
5. **Key dependencies and tools**: Important external dependencies

**Example repository summary**:
```json
{
  "project_type": "web_application",
  "primary_language": "python",
  "tech_stack": ["python", "flask", "docker", "postgresql"],
  "ci_approach": "GitHub Actions with multi-job workflows",
  "architecture": "monolithic",
  "key_characteristics": [
    "REST API",
    "Containerized deployment",
    "Database-backed",
    "Automated testing"
  ]
}
```

---

## How It Works

### Current Implementation (Heuristic-Based)

The system currently uses **rule-based heuristics** to generate summaries and tags. This works offline without requiring LLM API keys.

**Heuristic approach**:
1. **Analyze artifact type and metadata**:
   - Workflow: Extract job names, triggers, steps
   - Dockerfile: Extract base image, ports, stages
   - Dependencies: Extract package manager, key dependencies
2. **Generate summary**:
   - Combine type, metadata, and path information
   - Create descriptive sentence
3. **Generate tags**:
   - Extract from type, subtype, metadata
   - Add functional, technology, purpose tags
   - Infer risk tags from context

**Example heuristic summary**:
```python
# For a GitHub Actions workflow
if artifact.type == "workflow" and artifact.subtype == "github_actions":
    jobs = artifact.metadata.get("jobs", [])
    triggers = artifact.metadata.get("triggers", {})
    
    summary = f"GitHub Actions workflow"
    if triggers.get("push"):
        summary += " triggered on push"
    if jobs:
        job_names = [j.get("name") for j in jobs]
        summary += f" running {', '.join(job_names)}"
    
    tags = ["ci-workflow", "github-actions"]
    if "test" in str(jobs).lower():
        tags.append("testing")
```

### Future: LLM-Based Summarization

The system is designed to support LLM-based summarization when enabled:

**LLM prompt template** (from spec):
```
You are analyzing a repository artifact. Generate a concise summary and relevant tags.

Artifact Type: {type}
Path: {path}
Content Preview: {content_preview}
Metadata: {metadata}

Generate:
1. A 1-2 sentence summary describing what this artifact does and its role
2. 3-10 tags that categorize this artifact (functional, technology, purpose, risk)

Output format (JSON):
{
  "summary": "string",
  "tags": ["string"]
}
```

**When LLM is enabled**:
- Artifact content and metadata are sent to LLM
- LLM generates more nuanced summaries
- Better tag generation based on semantic understanding

---

## Configuration

Summarization is **opt-in** (disabled by default):

```python
from scanner import RepositoryScanner, get_default_summarization_config

# Enable summarization
summ_config = get_default_summarization_config()
summ_config.enabled = True

scanner = RepositoryScanner(summarization=summ_config)
knowledge = scanner.scan('/path/to/repo')
```

**Configuration options**:
- `enabled`: Turn summarization on/off (default: False)
- `provider`: "heuristic" or "openai" (default: "heuristic")
- `max_preview_chars`: Max characters to send to LLM (default: 2000)
- `max_tags`: Maximum tags per artifact (default: 10)

---

## Output in Knowledge Model

Summaries and tags are added to artifacts:

```json
{
  "artifacts": [
    {
      "id": "wf1",
      "type": "workflow",
      "path": ".github/workflows/ci.yml",
      "summary": "GitHub Actions workflow that runs tests...",  // ← Added
      "tags": ["ci-workflow", "testing", "github-actions"],     // ← Added
      "metadata": {...},
      "content": {...}
    }
  ],
  "summary": {  // ← Repository-level summary enhanced
    "primary_language": "python",
    "project_type": "web_application",
    "tech_stack": ["python", "flask", "docker"],
    ...
  }
}
```

---

## Use Cases

1. **Query Interface**: Tags enable semantic search
2. **CI Failure Analysis**: Summaries help understand artifact purpose
3. **Documentation**: Auto-generated descriptions of repository components
4. **Onboarding**: New team members can quickly understand the codebase

---

## Implementation Files

- `scanner/summarization.py` - Summarization engine
- `scanner/scanner.py` - Integration with scanner

---

## Next Steps

After summarization, the knowledge model can be queried → [05-query-interface.md](05-query-interface.md)

