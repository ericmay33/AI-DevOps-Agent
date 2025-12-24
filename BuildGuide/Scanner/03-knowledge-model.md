# 03: Repository Knowledge Model

## What This Is

The knowledge model is the structured representation of everything the scanner found in a repository. It's a JSON document that contains all artifacts, their relationships, and repository-level summaries.

**Think of it as**: A complete "map" of the repository that the AI agent can query to understand the codebase.

---

## Overall Structure

The knowledge model is a JSON object with 4 main sections:

```json
{
  "repository": { ... },      // Info about the repo itself
  "artifacts": [ ... ],       // All files found, classified
  "relationships": { ... },   // How artifacts connect
  "summary": { ... }          // High-level overview
}
```

---

## 1. Repository Section

Basic information about the repository and scan:

```json
{
  "repository": {
    "id": "1aff736ce245cbcf",           // Unique ID for this repo
    "name": "my-project",                // Repository name
    "url": "https://github.com/user/repo", // GitHub URL (if known)
    "default_branch": "main",            // Default branch
    "scanned_at": "2025-11-30T00:44:13", // When scan happened
    "scan_version": "1.0.0"              // Scanner version
  }
}
```

**Purpose**: Identifies which repository was scanned and when.

---

## 2. Artifacts Section

A list of every file found, with detailed information:

```json
{
  "artifacts": [
    {
      "id": "859889471cb8",              // Unique artifact ID
      "type": "workflow",                 // Artifact type
      "subtype": "github_actions",       // Specific platform/tool
      "path": ".github/workflows/ci.yml", // File path
      "name": "CI Workflow",              // Artifact name
      
      "metadata": {                       // Type-specific metadata
        "platform": "github_actions",
        "workflow_name": "CI Workflow",
        "triggers": { ... },
        "jobs": [ ... ]
      },
      
      "content": {                        // File content
        "raw": "...",                     // Full file content
        "structured": { ... }             // Parsed structure (YAML/JSON)
      },
      
      "relationships": {                  // Connections to other artifacts
        "depends_on": ["artifact_id"],
        "used_by": ["artifact_id"],
        "references": ["artifact_id"]
      },
      
      "tags": ["ci", "testing"],         // AI-generated tags
      "summary": "GitHub Actions workflow...", // AI-generated summary
      "extracted_at": "2025-11-30T00:44:13"
    },
    // ... more artifacts
  ]
}
```

### Artifact Types

Each artifact has a `type` field indicating what it is:

- `workflow` - CI/CD workflow files
- `dockerfile` - Docker files
- `dependency_manifest` - Package/dependency files
- `config` - Configuration files
- `iac` - Infrastructure as Code
- `source` - Source code files
- `generic` - Everything else

### Metadata Examples

**Workflow metadata**:
```json
{
  "platform": "github_actions",
  "workflow_name": "CI",
  "triggers": {
    "push": {"branches": ["main"]},
    "pull_request": {}
  },
  "jobs": [
    {
      "job_id": "test",
      "runs_on": "ubuntu-latest",
      "steps": [
        {"name": "Checkout", "uses": "actions/checkout@v3"},
        {"name": "Run tests", "run": "npm test"}
      ]
    }
  ],
  "env_vars": ["NODE_ENV"],
  "secrets": ["GITHUB_TOKEN"]
}
```

**Dockerfile metadata**:
```json
{
  "base_image": "node",
  "base_image_tag": "18",
  "exposed_ports": ["3000"],
  "env_vars": ["NODE_ENV"],
  "volume_mounts": ["/app/data"],
  "build_args": ["BUILD_VERSION"],
  "stages": [
    {
      "base_image": "node:18",
      "commands": ["WORKDIR /app", "COPY package.json .", ...]
    }
  ]
}
```

**Dependency manifest metadata**:
```json
{
  "package_manager": "npm",
  "dependencies": {
    "direct": [
      {"name": "express", "version": "^4.18.0", "type": "runtime"},
      {"name": "jest", "version": "27.0.0", "type": "dev"}
    ]
  },
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  }
}
```

### Content Field

The `content` field contains:
- `raw`: Full file content (if file is small enough, < 1MB)
- `structured`: Parsed structure for YAML/JSON files
- For large files: `metadata_only: true` (content not loaded)

---

## 3. Relationships Section

Shows how artifacts connect to each other:

```json
{
  "relationships": {
    "workflow_id_1": [
      {"type": "uses", "to": "dockerfile_id_1"},
      {"type": "depends_on", "to": "package_json_id"}
    ],
    "dockerfile_id_1": [
      {"type": "uses", "to": "package_json_id"}
    ]
  }
}
```

**Relationship types**:
- `uses` - Artifact uses another artifact
- `depends_on` - Artifact depends on another artifact
- `references` - Artifact references another artifact

**Example relationships**:
- Workflow → Dockerfile (workflow uses a Docker image)
- Workflow → Dependency manifest (workflow installs dependencies)
- Dockerfile → Dependency manifest (Dockerfile copies dependency files)

---

## 4. Summary Section

High-level overview of the repository:

```json
{
  "summary": {
    "primary_language": "python",           // Main programming language
    "project_type": "application",          // Type of project
    "ci_platform": "github_actions",       // CI platform detected
    "containerization": true,              // Has Dockerfiles?
    "dependency_managers": ["pip", "npm"], // Package managers found
    "infrastructure_tools": ["terraform"]  // IaC tools found
  }
}
```

**Purpose**: Quick understanding of what kind of project this is without reading all artifacts.

---

## Complete Example

```json
{
  "repository": {
    "id": "abc123",
    "name": "my-api",
    "url": "https://github.com/user/my-api",
    "default_branch": "main",
    "scanned_at": "2025-11-30T00:44:13",
    "scan_version": "1.0.0"
  },
  "artifacts": [
    {
      "id": "wf1",
      "type": "workflow",
      "subtype": "github_actions",
      "path": ".github/workflows/ci.yml",
      "name": "CI",
      "metadata": {
        "platform": "github_actions",
        "jobs": [...]
      },
      "content": {
        "raw": "name: CI\non: [push]\n...",
        "structured": {...}
      },
      "relationships": {
        "depends_on": ["df1", "pkg1"]
      },
      "tags": ["ci", "testing"],
      "summary": "GitHub Actions workflow for CI"
    },
    {
      "id": "df1",
      "type": "dockerfile",
      "subtype": "dockerfile",
      "path": "Dockerfile",
      "name": "Dockerfile",
      "metadata": {
        "base_image": "python",
        "base_image_tag": "3.9"
      },
      "content": {
        "raw": "FROM python:3.9\n...",
        "structured": null
      },
      "relationships": {
        "uses": ["pkg1"]
      },
      "tags": ["docker", "container"],
      "summary": "Python 3.9 Docker image"
    },
    {
      "id": "pkg1",
      "type": "dependency_manifest",
      "subtype": "pip",
      "path": "requirements.txt",
      "name": "requirements.txt",
      "metadata": {
        "package_manager": "pip",
        "dependencies": {
          "direct": [
            {"name": "flask", "version": "2.0.0"}
          ]
        }
      },
      "content": {
        "raw": "flask==2.0.0\n...",
        "structured": null
      },
      "relationships": {},
      "tags": ["python", "dependencies"],
      "summary": "Python dependencies"
    }
  ],
  "relationships": {
    "wf1": [
      {"type": "uses", "to": "df1"},
      {"type": "depends_on", "to": "pkg1"}
    ],
    "df1": [
      {"type": "uses", "to": "pkg1"}
    ]
  },
  "summary": {
    "primary_language": "python",
    "project_type": "application",
    "ci_platform": "github_actions",
    "containerization": true,
    "dependency_managers": ["pip"],
    "infrastructure_tools": []
  }
}
```

---

## Storage Format

- **Primary format**: JSON (portable, LLM-friendly, human-readable)
- **File location**: Can be saved to `knowledge/repo_knowledge.json`
- **Versioning**: Each scan produces a new versioned snapshot
- **Size**: Typically 100KB - 10MB depending on repository size

---

## How It's Used

1. **CI Failure Analysis** (Sprint 2): Query workflows and dependencies to understand failures
2. **Patch Generation** (Sprint 3): Use artifact metadata to generate fixes
3. **Query Interface** (Section 5): Search and analyze repository structure

---

## Implementation Files

- `scanner/models.py` - Data model definitions
- `scanner/scanner.py` - Knowledge model builder
- `scanner/relationships.py` - Relationship building

---

## Next Steps

After the knowledge model is built, it can be summarized → [04-ai-summarization.md](04-ai-summarization.md)

