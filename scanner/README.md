# Repository Scanner Module

This module implements Section 1.1: Scanning Approach - the three-phase repository scanning system.

## Overview

The scanner performs hierarchical traversal of repositories to build a comprehensive knowledge model:

1. **Phase 1: Initial Discovery** - Walk repository tree, build file inventory
2. **Phase 2: Classification** - Categorize files into artifact types, extract metadata
3. **Phase 3: Content Extraction** - Read and parse file contents

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
python scan_repo.py <repo_path> [output_file]
```

Example:
```bash
python scan_repo.py /path/to/repo knowledge/repo_knowledge.json
```

### Python API

```python
from scanner import RepositoryScanner

scanner = RepositoryScanner()
knowledge = scanner.scan('/path/to/repository')

# knowledge is a dict matching the repository knowledge model schema
print(f"Found {len(knowledge['artifacts'])} artifacts")
```

## Module Structure

- `models.py` - Data models (FileInfo, Artifact, ArtifactCollection, etc.)
- `discovery.py` - Phase 1: Initial discovery and file inventory
- `gitignore.py` - Gitignore pattern matching
- `classifiers.py` - Phase 2: Artifact classifiers (Workflow, Dockerfile, etc.)
- `relationships.py` - Relationship building between artifacts
- `extraction.py` - Phase 3: Content extraction and parsing
- `scanner.py` - Main orchestrator (RepositoryScanner class)

## Supported Artifact Types

- **Workflows**: GitHub Actions, GitLab CI, CircleCI, Jenkins, Azure DevOps, Travis
- **Dockerfiles**: Dockerfile, docker-compose.yml
- **Dependency Manifests**: package.json, requirements.txt, go.mod, Cargo.toml, etc.
- **Configuration Files**: .env, Makefile, version files
- **Infrastructure as Code**: Terraform, Kubernetes, Serverless Framework
- **Source Code**: Detected but not fully loaded (metadata only)

## Output Format

The scanner produces a JSON structure matching the repository knowledge model schema:

```json
{
  "repository": {
    "id": "...",
    "name": "...",
    "scanned_at": "...",
    "scan_version": "1.0.0"
  },
  "artifacts": [...],
  "relationships": {...},
  "summary": {
    "primary_language": "...",
    "project_type": "...",
    "ci_platform": "...",
    "containerization": true,
    "dependency_managers": [...]
  }
}
```

## Features

- ✅ Respects `.gitignore` patterns
- ✅ Handles symlinks with cycle prevention
- ✅ Binary file detection
- ✅ Size limits (1MB) for large files
- ✅ Relationship detection (workflow → dockerfile, etc.)
- ✅ Structured parsing (YAML, JSON, Dockerfile)
- ✅ Error handling and graceful degradation

## Next Steps

This implementation is ready for Eric to integrate with:
- GitHub API integration (Sprint 2)
- LLM summarization and tagging
- Query interface for repository knowledge

