# Sprint 1: Repository Intelligence - Build Guide

## Overview

This guide documents the complete design and implementation of Sprint 1: Repository Intelligence. The system scans repositories, classifies files, builds a knowledge model, and provides query capabilities for CI failure analysis.

**Who is this for?**
- New team members understanding the system
- Developers implementing or extending features
- Anyone needing to understand how repository scanning works

---

## Quick Start

1. **How Scanning Works** → [01-scanning-strategy.md](01-scanning-strategy.md)
2. **What Files Are Recognized** → [02-file-recognition.md](02-file-recognition.md)
3. **How Data Is Structured** → [03-knowledge-model.md](03-knowledge-model.md)
4. **How AI Summarization Works** → [04-ai-summarization.md](04-ai-summarization.md)
5. **How to Query the Knowledge** → [05-query-interface.md](05-query-interface.md)

---

## Document Structure

### 01-scanning-strategy.md
**What it covers:**
- How the scanner walks through repositories
- Three-phase scanning process (Discovery → Classification → Extraction)
- Rules that govern file processing (gitignore, size limits, binary detection, etc.)

**Key concepts:**
- File system traversal
- Gitignore pattern matching
- Binary file detection
- Symlink handling
- Size limits and content loading

### 02-file-recognition.md
**What it covers:**
- All file types the system recognizes
- How files are classified into artifact types
- What metadata is extracted from each type
- Classification priority when files match multiple patterns

**Key concepts:**
- Artifact types (workflows, dockerfiles, dependencies, etc.)
- Pattern matching
- Metadata extraction
- Classification priority

### 03-knowledge-model.md
**What it covers:**
- The JSON structure that represents repository knowledge
- How artifacts are stored
- Relationship mapping between artifacts
- Repository-level summaries

**Key concepts:**
- Knowledge model schema
- Artifact structure
- Relationship graphs
- Data storage format

### 04-ai-summarization.md
**What it covers:**
- How artifacts get summarized
- Tag generation for artifacts
- Repository-level summary generation
- Integration with LLM (when enabled)

**Key concepts:**
- Artifact summarization
- Tag categorization
- Repository analysis
- LLM integration points

### 05-query-interface.md
**What it covers:**
- How to query the knowledge model
- Three types of queries (direct, semantic, analysis)
- Query examples and use cases
- Response formats

**Key concepts:**
- Query types
- Filtering and searching
- Question answering
- Query results

---

## Implementation Status

✅ **Complete:**
- Section 1: Scanning Strategy (implemented)
- Section 2: File Recognition (implemented)
- Section 3: Knowledge Model (implemented)
- Section 4: AI Summarization (implemented with heuristics)
- Section 5: Query Interface (implemented)

---

## Code Location

All implementation code is in the `scanner/` directory:

- `scanner/discovery.py` - Phase 1: File discovery
- `scanner/classifiers.py` - Phase 2: File classification
- `scanner/extraction.py` - Phase 3: Content extraction
- `scanner/rules.py` - Scanning rules and configuration
- `scanner/models.py` - Data models
- `scanner/relationships.py` - Relationship building
- `scanner/summarization.py` - AI summarization
- `scanner/query.py` - Query interface
- `scanner/scanner.py` - Main orchestrator

---

## Usage Example

```python
from scanner import RepositoryScanner, QueryEngine

# Scan a repository
scanner = RepositoryScanner()
knowledge = scanner.scan('/path/to/repo')

# Query the knowledge
query_engine = QueryEngine(knowledge)
result = query_engine.query({
    "type": "artifact_query",
    "filters": {"artifact_type": "workflow"}
})
```
