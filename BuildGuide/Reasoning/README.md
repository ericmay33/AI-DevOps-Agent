# Sprint 2: Failure Analysis Reasoning - Build Guide

## Overview

This guide documents the complete design and implementation of Sprint 2: Failure Analysis Reasoning. The system analyzes CI/CD failure logs, classifies failure types, determines root causes, and generates structured remediation plans.

---

## Quick Start

1. **Failure Classification** → [01-failure-classification.md](01-failure-classification.md)
2. **Reasoning Workflow** → [02-reasoning-workflow.md](02-reasoning-workflow.md)
3. **Output Schema** → [03-output-schema.md](03-output-schema.md)
4. **Prompt Templates** → [04-prompt-templates.md](04-prompt-templates.md)

---

## Document Structure

### 01-failure-classification.md
**What it covers:**
- All failure categories the system recognizes
- How failures are classified
- Examples of each failure type
- Classification confidence scoring

**Key concepts:**
- Failure types (dependency, configuration, test, build, etc.)
- Pattern matching in logs
- Classification heuristics
- Confidence levels

### 02-reasoning-workflow.md
**What it covers:**
- Multi-step reasoning process
- How the LLM analyzes failures
- Correlation with repository artifacts
- Root cause determination

**Key concepts:**
- Step-by-step analysis
- Context correlation
- Evidence gathering
- Root cause analysis

### 03-output-schema.md
**What it covers:**
- Structured output format
- Analysis result schema
- Severity levels
- Confidence scoring
- Affected files identification

**Key concepts:**
- JSON schema
- Data models
- Output validation
- Result structure

### 04-prompt-templates.md
**What it covers:**
- All prompt templates used
- Prompt structure and variables
- Multi-step prompt logic
- Examples and use cases

**Key concepts:**
- Prompt engineering
- Template variables
- LLM instructions
- Structured output prompts

---

## Implementation Status

✅ **Complete:**
- Section 1: Failure Classification (implemented)
- Section 2: Reasoning Workflow (implemented)
- Section 3: Output Schema (implemented)
- Section 4: Prompt Templates (implemented)

---

## Code Location

All implementation code is in the `reasoning/` directory:

- `reasoning/models.py` - Data models for analysis results
- `reasoning/classifier.py` - Failure classification logic
- `reasoning/prompts.py` - Prompt templates
- `reasoning/engine.py` - Main reasoning engine
- `reasoning/__init__.py` - Public API

---

## Usage Example

```python
from reasoning import ReasoningEngine
from github_bridge import run_bridge

# Get agent context (from Sprint 2 bridge)
context = run_bridge('owner/repo')

# Analyze failures
engine = ReasoningEngine()
analysis = engine.analyze(context)

# Access results
print(f"Failure Type: {analysis.failure_type}")
print(f"Root Cause: {analysis.root_cause}")
print(f"Severity: {analysis.severity}")
print(f"Fix Summary: {analysis.fix_summary}")
```

---

## Input: agent_context.json

The reasoning engine takes `agent_context.json` as input, which contains:

- **Repository metadata**: Name, branch, etc.
- **Static analysis**: Repository structure, artifacts, workflows
- **CI context**: Workflow runs, failure logs

**Key input fields:**
- `ci_context.failure_logs`: List of failure logs with job names, step names, and log content
- `static_analysis.artifacts`: Repository artifacts (workflows, dependencies, configs)
- `static_analysis.summary`: Repository summary (language, platform, etc.)

---

## Output: Failure Analysis

The reasoning engine produces structured analysis:

```json
{
  "failure_type": "dependency_version_mismatch",
  "root_cause": "Package pytest==7.0.0 is not available for Python 3.12",
  "fix_summary": "Update requirements.txt to use pytest>=7.0.0 or compatible version",
  "severity": "Medium",
  "confidence": 0.92,
  "affected_files": ["requirements.txt"],
  "evidence": ["Error log line 42: 'Could not find a version...'"]
}
```

---

## Integration Points

**From Sprint 1:**
- Uses repository knowledge model for context
- Queries artifacts to correlate failures

**To Sprint 3:**
- Provides structured analysis for patch generation
- Identifies affected files for modification
- Supplies fix summaries for PR descriptions

---

## Design Philosophy

**Evidence-Based Reasoning:**
- All conclusions must be backed by log evidence
- Correlates failures with repository artifacts
- Avoids hallucination through structured prompts

**Deterministic Classification:**
- Failure types are well-defined categories
- Classification uses both heuristics and LLM reasoning
- Confidence scores indicate certainty

**Actionable Output:**
- Every analysis includes fix suggestions
- Affected files are explicitly identified
- Severity helps prioritize fixes

