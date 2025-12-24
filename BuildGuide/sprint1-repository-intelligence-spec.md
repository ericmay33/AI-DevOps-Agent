# Sprint 1: Repository Intelligence Design Specification

## Overview
This specification defines how the system scans, represents, and queries repository knowledge. It serves as the foundation for CI failure analysis and future infrastructure policy scanning.

---

## 1. Repository Scanning Strategy

### 1.1 Scanning Approach
The scanner performs a **hierarchical traversal** of the repository filesystem:

1. **Initial Discovery Phase**
   - Walk the entire repository tree (respecting `.gitignore` patterns)
   - Build a file inventory with paths and basic metadata
   - Identify file types by extension, location, and content patterns

2. **Classification Phase**
   - Categorize files into recognized artifact types
   - Extract relevant metadata for each artifact
   - Build relationships between artifacts (e.g., workflow → Dockerfile → dependency file)

3. **Content Extraction Phase**
   - Read and parse file contents for recognized types
   - Extract structured data where applicable (e.g., YAML/JSON parsing)
   - Store raw content for LLM analysis

### 1.2 Scanning Rules
- **Respect `.gitignore`**: Files ignored by git are excluded from scanning
- **Size Limits**: Files > 1MB are indexed but not fully loaded (metadata only)
- **Binary Files**: Detected binary files are skipped (except Docker images, which are handled separately)
- **Symlinks**: Followed with depth limit of 3 to prevent cycles
- **Hidden Files**: Included if they match recognized patterns (e.g., `.github/workflows/*.yml`)

---

## 2. File Recognition & Classification

### 2.1 Recognized Artifact Types

#### CI/CD Workflows
- **Patterns**: 
  - `.github/workflows/*.yml`, `.github/workflows/*.yaml`
  - `.gitlab-ci.yml`, `.gitlab-ci.yaml`
  - `.circleci/config.yml`
  - `.jenkinsfile`, `Jenkinsfile`
  - `azure-pipelines.yml`
  - `.travis.yml`
- **Metadata Extracted**:
  - Workflow name/ID
  - Trigger events (push, PR, schedule, etc.)
  - Job names and steps
  - Dependencies between jobs
  - Environment variables referenced
  - Docker images used
  - Service dependencies

#### Docker Artifacts
- **Patterns**:
  - `Dockerfile`, `Dockerfile.*`, `*.dockerfile`
  - `docker-compose.yml`, `docker-compose.yaml`
  - `*.dockerignore`
- **Metadata Extracted**:
  - Base image
  - Exposed ports
  - Environment variables
  - Volume mounts
  - Build arguments
  - Multi-stage build stages
  - Dependencies on other Dockerfiles

#### Dependency Manifests
- **Patterns**:
  - `package.json` (Node.js)
  - `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` (Python)
  - `pom.xml`, `build.gradle`, `build.gradle.kts` (Java)
  - `Cargo.toml`, `Cargo.lock` (Rust)
  - `go.mod`, `go.sum` (Go)
  - `Gemfile`, `Gemfile.lock` (Ruby)
  - `composer.json`, `composer.lock` (PHP)
  - `pubspec.yaml` (Dart/Flutter)
  - `*.csproj`, `*.sln` (C#)
- **Metadata Extracted**:
  - Package manager type
  - Direct dependencies with versions
  - Lock file presence/status
  - Scripts/commands defined
  - Build toolchain requirements

#### Configuration Files
- **Patterns**:
  - `.env*`, `*.env`
  - `config/*.yml`, `config/*.yaml`, `config/*.json`
  - `*.config.js`, `*.config.ts`
  - `Makefile`, `makefile`
  - `.nvmrc`, `.node-version`
  - `.python-version`, `.ruby-version`
- **Metadata Extracted**:
  - Configuration keys (for structured formats)
  - Environment variable references
  - Tool version specifications

#### Infrastructure as Code
- **Patterns**:
  - `*.tf`, `*.tfvars` (Terraform)
  - `*.tf.json` (Terraform JSON)
  - `serverless.yml`, `serverless.yaml` (Serverless Framework)
  - `*.yaml`, `*.yml` in `k8s/`, `kubernetes/`, `manifests/` (Kubernetes)
  - `*.bicep` (Azure Bicep)
  - `*.cf`, `*.cfn` (CloudFormation)
- **Metadata Extracted**:
  - Resource types
  - Provider information
  - Variable definitions
  - Output values
  - Module dependencies

#### Source Code Structure
- **Patterns**:
  - Language-specific patterns (e.g., `src/**/*.py`, `lib/**/*.rb`)
  - Entry points: `main.py`, `index.js`, `main.go`, etc.
- **Metadata Extracted**:
  - Primary programming language(s)
  - Project structure pattern (monorepo, microservices, etc.)
  - Entry point files
  - Test file locations

### 2.2 Classification Priority
When a file matches multiple patterns, classification follows this priority:
1. CI/CD Workflows (highest priority for CI analysis)
2. Dependency Manifests
3. Docker Artifacts
4. Infrastructure as Code
5. Configuration Files
6. Source Code

---

## 3. Repository Knowledge Model Data Structure

### 3.1 Core Schema

```json
{
  "repository": {
    "id": "string (repo identifier)",
    "name": "string",
    "url": "string",
    "default_branch": "string",
    "scanned_at": "ISO8601 timestamp",
    "scan_version": "string (semver)"
  },
  "artifacts": [
    {
      "id": "string (unique artifact ID)",
      "type": "workflow|dockerfile|dependency_manifest|config|iac|source",
      "subtype": "string (e.g., 'github_actions', 'dockerfile', 'package_json')",
      "path": "string (relative path from repo root)",
      "name": "string (artifact name)",
      "metadata": {
        // Type-specific metadata (see sections below)
      },
      "content": {
        "raw": "string (full file content, if < 1MB)",
        "structured": {} // Parsed structure for structured formats
      },
      "relationships": {
        "depends_on": ["artifact_id"],
        "used_by": ["artifact_id"],
        "references": ["artifact_id"]
      },
      "tags": ["string"], // AI-generated tags
      "summary": "string", // AI-generated summary
      "extracted_at": "ISO8601 timestamp"
    }
  ],
  "relationships": {
    "workflow_to_docker": [
      {"workflow_id": "string", "dockerfile_id": "string"}
    ],
    "workflow_to_dependencies": [
      {"workflow_id": "string", "manifest_id": "string"}
    ],
    "docker_to_dependencies": [
      {"dockerfile_id": "string", "manifest_id": "string"}
    ]
  },
  "summary": {
    "primary_language": "string",
    "project_type": "string (e.g., 'web_app', 'library', 'monorepo')",
    "ci_platform": "string (e.g., 'github_actions', 'gitlab_ci')",
    "containerization": "boolean",
    "dependency_managers": ["string"],
    "infrastructure_tools": ["string"]
  }
}
```

### 3.2 Artifact-Specific Metadata Schemas

#### Workflow Artifact Metadata
```json
{
  "platform": "github_actions|gitlab_ci|circleci|jenkins|azure_devops|travis",
  "workflow_name": "string",
  "workflow_id": "string",
  "triggers": {
    "push": {"branches": ["string"], "paths": ["string"]},
    "pull_request": {"branches": ["string"], "paths": ["string"]},
    "schedule": ["cron_expression"],
    "workflow_dispatch": "boolean",
    "manual": "boolean"
  },
  "jobs": [
    {
      "job_id": "string",
      "name": "string",
      "runs_on": "string|array",
      "steps": [
        {
          "step_id": "string",
          "name": "string",
          "type": "run|action|checkout|setup",
          "command": "string",
          "uses": "string",
          "env": {}
        }
      ],
      "needs": ["job_id"],
      "docker_image": "string",
      "services": []
    }
  ],
  "env_vars": ["string"],
  "secrets": ["string"],
  "matrix_strategies": []
}
```

#### Dockerfile Artifact Metadata
```json
{
  "base_image": "string",
  "base_image_tag": "string",
  "exposed_ports": ["number"],
  "env_vars": ["string"],
  "volume_mounts": ["string"],
  "build_args": ["string"],
  "stages": [
    {
      "stage_name": "string",
      "base_image": "string",
      "commands": ["string"]
    }
  ],
  "entrypoint": "string",
  "cmd": "string",
  "workdir": "string"
}
```

#### Dependency Manifest Metadata
```json
{
  "package_manager": "npm|pip|maven|gradle|cargo|go|gem|composer|pub|nuget",
  "lock_file_present": "boolean",
  "lock_file_path": "string",
  "dependencies": {
    "direct": [
      {
        "name": "string",
        "version": "string",
        "type": "runtime|dev|peer|optional"
      }
    ],
    "indirect": [] // If lock file is parsed
  },
  "scripts": {
    "script_name": "command_string"
  },
  "build_tools": ["string"],
  "language_version": "string"
}
```

### 3.3 Storage Strategy
- **Primary Format**: JSON (for portability and LLM consumption)
- **Indexing**: Maintain separate indexes for:
  - Artifacts by type
  - Artifacts by path pattern
  - Relationships graph
- **Versioning**: Each scan produces a new versioned snapshot
- **Persistence**: Can be stored as:
  - JSON file
  - Database (SQLite for local, PostgreSQL for production)
  - Vector store (for semantic search, future enhancement)

---

## 4. AI Summarization & Tagging

### 4.1 Summarization Strategy

For each artifact, the LLM generates:

1. **Summary** (1-2 sentences):
   - What the artifact does
   - Its role in the repository
   - Key characteristics

2. **Tags** (3-10 tags):
   - Functional tags: `ci-workflow`, `build-step`, `test-runner`
   - Technology tags: `python`, `docker`, `nodejs`
   - Purpose tags: `deployment`, `testing`, `linting`
   - Risk tags: `security-sensitive`, `production-critical`

### 4.2 Prompt Template for Summarization

```
You are analyzing a repository artifact. Generate a concise summary and relevant tags.

Artifact Type: {type}
Path: {path}
Content Preview:
{content_preview}

Metadata:
{metadata}

Generate:
1. A 1-2 sentence summary describing what this artifact does and its role
2. 3-10 tags that categorize this artifact (functional, technology, purpose, risk)

Output format (JSON):
{
  "summary": "string",
  "tags": ["string"]
}
```

### 4.3 Repository-Level Summary

The LLM also generates a high-level repository summary:

```
Analyze this repository structure and generate a comprehensive summary.

Repository Artifacts:
{artifact_summaries}

Relationships:
{relationship_graph}

Generate a summary covering:
1. Project type and primary purpose
2. Technology stack
3. CI/CD approach
4. Architecture patterns
5. Key dependencies and tools

Output format (JSON):
{
  "project_type": "string",
  "primary_language": "string",
  "tech_stack": ["string"],
  "ci_approach": "string",
  "architecture": "string",
  "key_characteristics": ["string"]
}
```

---

## 5. LLM Query Interface

### 5.1 Query Types

The system supports three query patterns:

#### 5.1.1 Direct Artifact Queries
**Purpose**: Retrieve specific artifacts or artifact types

**Query Format**:
```json
{
  "type": "artifact_query",
  "filters": {
    "artifact_type": "workflow|dockerfile|dependency_manifest|all",
    "path_pattern": "string (glob pattern)",
    "tags": ["string"],
    "metadata": {
      "key": "value"
    }
  },
  "include_content": "boolean",
  "include_relationships": "boolean"
}
```

**Response Format**:
```json
{
  "artifacts": [
    {
      "id": "string",
      "type": "string",
      "path": "string",
      "summary": "string",
      "tags": ["string"],
      "metadata": {},
      "content": {} // if include_content=true
    }
  ],
  "relationships": {} // if include_relationships=true
}
```

#### 5.1.2 Semantic Queries
**Purpose**: Find artifacts by meaning/intent (uses embeddings/vector search)

**Query Format**:
```json
{
  "type": "semantic_query",
  "query": "string (natural language)",
  "limit": "number",
  "threshold": "number (similarity threshold)"
}
```

**Response Format**: Same as artifact query response

#### 5.1.3 Analysis Queries
**Purpose**: Ask questions about the repository structure

**Query Format**:
```json
{
  "type": "analysis_query",
  "question": "string",
  "context": {
    "artifact_ids": ["string"], // Optional: focus on specific artifacts
    "relationship_depth": "number"
  }
}
```

**Response Format**:
```json
{
  "answer": "string",
  "supporting_artifacts": ["artifact_id"],
  "confidence": "number (0-1)"
}
```

### 5.2 Query Interface Implementation

The query interface is implemented as a **prompt-based system** that:

1. **Receives query** in structured format
2. **Retrieves relevant artifacts** from knowledge model
3. **Constructs context** for LLM
4. **Sends prompt** to LLM with:
   - Query intent
   - Relevant artifact summaries
   - Relationship context
   - Metadata filters
5. **Returns structured response**

### 5.3 Example Queries

#### Example 1: Find all CI workflows
```json
{
  "type": "artifact_query",
  "filters": {
    "artifact_type": "workflow"
  },
  "include_content": true,
  "include_relationships": true
}
```

#### Example 2: Find Dockerfiles used by workflows
```json
{
  "type": "analysis_query",
  "question": "Which Dockerfiles are referenced in CI workflows?",
  "context": {
    "relationship_depth": 2
  }
}
```

#### Example 3: Semantic search for test-related artifacts
```json
{
  "type": "semantic_query",
  "query": "artifacts related to running tests",
  "limit": 10
}
```

---

## 6. Future-Proofing for Infrastructure Policy Scans

### 6.1 Extensibility Principles

The repository knowledge model is designed to support future infrastructure policy scanning without architectural changes:

1. **Type System is Extensible**
   - New artifact types can be added without changing core schema
   - Metadata schemas are additive (new fields don't break existing queries)

2. **Relationship Graph is Generic**
   - Relationships are not hardcoded to specific types
   - New relationship types can be added dynamically

3. **Query Interface is Abstract**
   - Query types are not limited to CI/CD use cases
   - Analysis queries can handle any domain question

### 6.2 Infrastructure Policy Scan Integration Points

When infrastructure policy scanning is added:

1. **New Artifact Types**:
   - `terraform_module`
   - `kubernetes_manifest`
   - `cloudformation_template`
   - Already defined in section 2.1!

2. **New Metadata Fields**:
   - Policy compliance status
   - Security scan results
   - Drift detection data
   - Can be added to existing metadata schemas

3. **New Query Types**:
   - `policy_query`: Check compliance against policies
   - `drift_query`: Detect infrastructure drift
   - Can be added to query interface without breaking existing queries

4. **New Relationships**:
   - `terraform_module → kubernetes_manifest`
   - `policy → artifact` (compliance relationships)
   - Uses existing relationship graph structure

### 6.3 Backward Compatibility Guarantee

- All new fields in metadata schemas are optional
- Existing queries continue to work with new artifact types
- New query types are additive, not replacements
- Core schema versioning ensures compatibility

---

## 7. Implementation Notes for Eric

### 7.1 Scanner Output Format
The scanner must produce JSON matching the schema in section 3.1. The output file should be named `repo_knowledge.json` and placed in a `knowledge/` directory.

### 7.2 Required Scanner Capabilities
1. File system traversal with `.gitignore` support
2. File type detection and classification
3. YAML/JSON parsing for structured files
4. Metadata extraction per artifact type
5. Relationship detection (e.g., workflow references to Dockerfiles)
6. JSON serialization of knowledge model

### 7.3 Integration Points
- Scanner output → Knowledge Model storage
- Knowledge Model → LLM query interface
- Knowledge Model → Failure analysis (Sprint 2)
- Knowledge Model → Patch generation (Sprint 3)

---

## 8. Definition of Done Checklist

- [x] Specification document created
- [ ] Scanner strategy defined ✓
- [ ] File recognition rules defined ✓
- [ ] Repo knowledge model schema defined ✓
- [ ] Metadata schemas defined ✓
- [ ] AI summarization approach defined ✓
- [ ] LLM query interface designed ✓
- [ ] Future-proofing strategy documented ✓
- [ ] Implementation notes for Eric provided ✓

---

## Appendix A: Example Knowledge Model Output

See `examples/repo_knowledge_example.json` (to be created by Eric during implementation).

---

## Appendix B: Query Interface API Specification

The query interface can be exposed as:
- REST API endpoint: `POST /api/v1/query`
- Python function: `query_repo_knowledge(query: dict) -> dict`
- CLI command: `devops-agent query <query_json>`

---

**Document Version**: 1.0  
**Last Updated**: Sprint 1  
**Author**: Shawn  
**Status**: Specification Complete

