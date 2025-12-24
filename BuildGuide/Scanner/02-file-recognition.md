# 02: File Recognition & Classification

## What This Does

After files are discovered, they need to be classified into specific types (workflow, dockerfile, dependency, etc.) and have their metadata extracted. This document explains what types are recognized and how classification works.

---

## Recognized Artifact Types

The system recognizes 6 main artifact types, each with specific patterns and extracted metadata.

### 1. CI/CD Workflows

**What they are**: Files that define continuous integration/continuous deployment pipelines

**Patterns recognized**:
- `.github/workflows/*.yml`, `.github/workflows/*.yaml` (GitHub Actions)
- `.gitlab-ci.yml`, `.gitlab-ci.yaml` (GitLab CI)
- `.circleci/config.yml` (CircleCI)
- `Jenkinsfile`, `.jenkinsfile` (Jenkins)
- `azure-pipelines.yml` (Azure DevOps)
- `.travis.yml` (Travis CI)

**Metadata extracted**:
- Platform (GitHub Actions, GitLab CI, etc.)
- Workflow name/ID
- Trigger events (when workflow runs: push, PR, schedule, manual)
- Jobs and their steps
- Environment variables used
- Secrets referenced
- Docker images used
- Dependencies between jobs

**Example**:
```yaml
# .github/workflows/test.yml
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm test
```

**Extracted metadata**:
```json
{
  "platform": "github_actions",
  "workflow_name": "Run Tests",
  "triggers": {"push": {}, "pull_request": {}},
  "jobs": [{
    "job_id": "test",
    "runs_on": "ubuntu-latest",
    "steps": [...]
  }]
}
```

---

### 2. Docker Artifacts

**What they are**: Files that define container images and services

**Patterns recognized**:
- `Dockerfile`, `Dockerfile.*` (e.g., `Dockerfile.prod`)
- `*.dockerfile`
- `docker-compose.yml`, `docker-compose.yaml`
- `*.dockerignore`

**Metadata extracted**:
- Base image (e.g., `node:18`, `python:3.9`)
- Exposed ports
- Environment variables
- Volume mounts
- Build arguments
- Multi-stage build stages (if applicable)
- Services (for docker-compose)

**Example**:
```dockerfile
FROM node:18
WORKDIR /app
COPY package.json .
RUN npm install
EXPOSE 3000
CMD ["npm", "start"]
```

**Extracted metadata**:
```json
{
  "base_image": "node",
  "base_image_tag": "18",
  "exposed_ports": ["3000"],
  "stages": [{
    "base_image": "node:18",
    "commands": ["WORKDIR /app", "COPY package.json .", ...]
  }]
}
```

---

### 3. Dependency Manifests

**What they are**: Files that list project dependencies and package information

**Patterns recognized**:
- `package.json` (Node.js/npm)
- `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` (Python)
- `pom.xml`, `build.gradle`, `build.gradle.kts` (Java)
- `Cargo.toml`, `Cargo.lock` (Rust)
- `go.mod`, `go.sum` (Go)
- `Gemfile`, `Gemfile.lock` (Ruby)
- `composer.json`, `composer.lock` (PHP)
- `pubspec.yaml` (Dart/Flutter)
- `*.csproj`, `*.sln` (C#/.NET)

**Metadata extracted**:
- Package manager type (npm, pip, maven, etc.)
- Direct dependencies with versions
- Lock file presence/status
- Scripts/commands defined
- Build toolchain requirements
- Language version

**Example**:
```json
// package.json
{
  "name": "my-app",
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "4.17.21"
  },
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  }
}
```

**Extracted metadata**:
```json
{
  "package_manager": "npm",
  "dependencies": {
    "direct": [
      {"name": "express", "version": "^4.18.0", "type": "runtime"},
      {"name": "lodash", "version": "4.17.21", "type": "runtime"}
    ]
  },
  "scripts": {
    "start": "node index.js",
    "test": "jest"
  }
}
```

---

### 4. Configuration Files

**What they are**: Files that configure tools, environments, or project settings

**Patterns recognized**:
- `.env*`, `*.env` (Environment variables)
- `config/*.yml`, `config/*.yaml`, `config/*.json` (Config files)
- `*.config.js`, `*.config.ts` (JavaScript/TypeScript configs)
- `Makefile`, `makefile` (Build automation)
- `.nvmrc`, `.node-version` (Node version)
- `.python-version`, `.ruby-version` (Language versions)

**Metadata extracted**:
- Configuration type (env_file, makefile, version_file, etc.)
- Configuration keys (for structured formats)
- Environment variable references
- Tool version specifications

**Example**:
```makefile
# Makefile
install:
	npm install

test:
	npm test
```

**Extracted metadata**:
```json
{
  "subtype": "makefile"
}
```

---

### 5. Infrastructure as Code (IaC)

**What they are**: Files that define cloud infrastructure and deployment configurations

**Patterns recognized**:
- `*.tf`, `*.tfvars` (Terraform)
- `*.tf.json` (Terraform JSON)
- `serverless.yml`, `serverless.yaml` (Serverless Framework)
- `*.yaml`, `*.yml` in `k8s/`, `kubernetes/`, `manifests/` (Kubernetes)
- `*.bicep` (Azure Bicep)
- `*.cf`, `*.cfn` (CloudFormation)

**Metadata extracted**:
- IaC type (terraform, kubernetes, serverless, etc.)
- Resource types (for Terraform)
- Provider information
- Variable definitions
- Output values
- Module dependencies

**Example**:
```hcl
# main.tf
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
}
```

**Extracted metadata**:
```json
{
  "iac_type": "terraform"
}
```

---

### 6. Source Code

**What they are**: Programming language source files

**Patterns recognized**:
- Language-specific extensions: `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.rb`, `.php`, `.cpp`, `.c`, `.cs`, `.dart`

**Metadata extracted**:
- Programming language
- File extension

**Note**: Source code files are detected but not fully loaded (metadata only) to avoid storing too much data.

---

## Classification Priority

When a file matches multiple patterns, the system uses this priority order:

1. **CI/CD Workflows** (highest priority)
2. **Dependency Manifests**
3. **Docker Artifacts**
4. **Infrastructure as Code**
5. **Configuration Files**
6. **Source Code** (lowest priority)

**Why this order?**
- Workflows are most important for CI failure analysis
- Dependencies are critical for understanding build requirements
- Docker files are important for containerized deployments
- Source code is least important (too many files, metadata only)

**Example**:
- A file `Dockerfile.python` matches both Docker pattern and source code pattern
- It's classified as **Docker Artifact** (priority 3) because Docker has higher priority than Source Code (priority 6)

---

## How Classification Works

1. **File is discovered** in Phase 1 with initial type guess
2. **Classifiers try in priority order**:
   - Each classifier checks if it can handle the file
   - First matching classifier wins
3. **Metadata extraction**:
   - Classifier reads file content
   - Parses structured formats (YAML, JSON, etc.)
   - Extracts type-specific metadata
4. **Artifact created**:
   - Type, subtype, path, name
   - Extracted metadata
   - File content (if small enough)

---

## Implementation Files

- `scanner/classifiers.py` - All classifier implementations
- `scanner/discovery.py` - Initial type identification

---

## Next Steps

After classification, artifacts are structured into a knowledge model → [03-knowledge-model.md](03-knowledge-model.md)

