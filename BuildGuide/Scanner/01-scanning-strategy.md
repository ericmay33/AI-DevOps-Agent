# 01: Repository Scanning Strategy

## What This Does

The scanner walks through a repository, finds all files, classifies them, and extracts their content. This happens in three phases that build on each other.

---

## The Three Phases

### Phase 1: Initial Discovery
**Goal**: Find all files in the repository

**What happens:**
1. Walk through every directory in the repository
2. For each file found:
   - Check if it should be ignored (gitignore rules)
   - Detect if it's a binary file
   - Guess what type it might be (workflow, dockerfile, etc.)
   - Record basic info: path, size, modification time

**Output**: A list of all files with basic metadata

### Phase 2: Classification
**Goal**: Categorize files into specific types and extract metadata

**What happens:**
1. For each file from Phase 1:
   - Try different classifiers (workflow, dockerfile, dependency, etc.)
   - First classifier that matches wins (priority order)
   - Extract type-specific metadata:
     - Workflows: jobs, steps, triggers
     - Dockerfiles: base image, ports, stages
     - Dependencies: package manager, dependency list
2. Build relationships between artifacts:
   - Which workflows use which dockerfiles
   - Which workflows depend on which dependency files

**Output**: Classified artifacts with rich metadata and relationships

### Phase 3: Content Extraction
**Goal**: Read and parse file contents

**What happens:**
1. For each classified artifact:
   - Check file size (skip if too large)
   - Read file content
   - Parse structured formats (YAML, JSON, Dockerfile)
   - Store both raw content and parsed structure

**Output**: Artifacts with full content ready for analysis

---

## Scanning Rules

These rules control what gets scanned and how:

### 1. Gitignore Respect
**Rule**: Files listed in `.gitignore` are skipped

**Why**: Don't scan files that git ignores (build artifacts, dependencies, etc.)

**How it works**:
- Loads patterns from `.gitignore` and `.git/info/exclude`
- Matches file paths against patterns
- Skips matching files

**Example**: If `.gitignore` contains `node_modules/`, that entire directory is skipped

### 2. Size Limits
**Rule**: Files larger than 1MB are indexed but content is not loaded

**Why**: Large files (logs, data files) would consume too much memory

**How it works**:
- Files over 1MB: Only metadata stored (path, size, type)
- Files under 1MB: Full content loaded
- Configurable threshold (default: 1MB)

**Example**: A 5MB log file is detected and classified, but its content isn't stored

### 3. Binary File Detection
**Rule**: Binary files are skipped (except special cases)

**Why**: Binary files (images, executables) aren't useful for CI analysis

**How it works**:
- Detects binary by:
  1. File extension (.exe, .jpg, .png, etc.)
  2. Content analysis (checks for null bytes, non-UTF-8 content)
- Skips binary files automatically
- Configurable: can disable binary skipping

**Example**: `.jpg` images are detected and skipped

### 4. Symlink Handling
**Rule**: Follow symlinks up to depth 3, prevent cycles

**Why**: Symlinks can point to files outside repo or create infinite loops

**How it works**:
- Tracks visited symlink targets
- Stops following if depth exceeds 3
- Skips broken symlinks gracefully

**Example**: A symlink pointing to `/usr/bin/python` is followed, but cycles are prevented

### 5. Hidden File Inclusion
**Rule**: Include hidden files (starting with `.`) only if they match important patterns

**Why**: Some hidden files are important (`.github/workflows/`), others aren't (`.DS_Store`)

**How it works**:
- Always includes: `.github/**/*`, `.gitlab-ci.yml`, `.env*`, `.dockerignore`, etc.
- Always excludes: `.git/objects/**`, `node_modules/**`, etc.
- Other hidden files: Excluded unless they match patterns

**Example**: `.github/workflows/test.yml` is included, but `.DS_Store` is excluded

---

## Configuration

All rules are configurable via `ScanningRules`:

```python
from scanner import create_custom_rules

# Custom rules: 2MB limit, don't skip binary files
rules = create_custom_rules(
    max_file_size=2 * 1024 * 1024,  # 2MB
    skip_binary_files=False,
    max_symlink_depth=5
)
```

---

## How It Works (Technical Details)

### File System Traversal
- Recursive directory walk
- Respects `.gitignore` patterns
- Handles symlinks with cycle detection
- Skips files based on rules

### Binary Detection
1. Check file extension against known binary extensions
2. Read first 512 bytes
3. Check for null bytes (indicates binary)
4. Try UTF-8 decoding (fails for binary)

### Initial Type Identification
Files are quickly categorized by:
1. **Path patterns** (highest priority):
   - `.github/workflows/*.yml` → workflow
   - `Dockerfile` → dockerfile
   - `package.json` → dependency manifest
2. **File extension** (fallback):
   - `.py` → source code
   - `.yml` → YAML file
3. **Content sniffing** (last resort):
   - Read first few bytes
   - Check for file signatures

---

## Example Flow

```
Repository: /my-project
  ├── .github/workflows/ci.yml  → Phase 1: Found, type: workflow
  ├── Dockerfile                 → Phase 1: Found, type: dockerfile
  ├── package.json               → Phase 1: Found, type: dependency
  └── node_modules/              → Phase 1: Skipped (gitignore)

Phase 2:
  ├── ci.yml → Classified as GitHub Actions workflow
  │           Extracted: jobs, steps, triggers
  ├── Dockerfile → Classified as Dockerfile
  │               Extracted: base image, ports, stages
  └── package.json → Classified as npm manifest
                     Extracted: dependencies, scripts

Phase 3:
  ├── ci.yml → Content loaded, YAML parsed
  ├── Dockerfile → Content loaded, parsed into stages
  └── package.json → Content loaded, JSON parsed
```

---

## Implementation Files

- `scanner/discovery.py` - Phase 1 implementation
- `scanner/rules.py` - Scanning rules and configuration
- `scanner/gitignore.py` - Gitignore pattern matching

---

## Next Steps

After scanning, files are classified → [02-file-recognition.md](02-file-recognition.md)

