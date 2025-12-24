# 02: Reasoning Workflow

## What This Does

The reasoning workflow is a multi-step process that takes failure logs and repository context, then produces a structured analysis with root cause and fix suggestions. This is the "brain" of the agent.

---

## Overview

The reasoning workflow consists of 5 steps:

1. **Parse & Extract** - Extract key information from failure logs
2. **Classify** - Determine failure type
3. **Correlate** - Match failures with repository artifacts
4. **Analyze Root Cause** - Determine why the failure occurred
5. **Generate Fix** - Propose remediation steps

---

## Step 1: Parse & Extract

**Goal:** Extract structured information from raw failure logs

**What happens:**
- Parse log content line by line
- Identify error messages, stack traces, exit codes
- Extract relevant context (job name, step name, timestamps)
- Filter noise (timestamps, ANSI codes, verbose output)

**Input:**
```json
{
  "job_name": "test",
  "step_name": "Run tests",
  "log_content": "2025-12-17T06:23:27.6442268Z ERROR: Could not find a version..."
}
```

**Output:**
```json
{
  "error_messages": [
    "ERROR: Could not find a version that satisfies the requirement pytest==7.0.0"
  ],
  "exit_code": 1,
  "key_lines": [
    "ERROR: Could not find a version...",
    "No matching distribution found..."
  ],
  "context": {
    "job": "test",
    "step": "Run tests"
  }
}
```

---

## Step 2: Classify

**Goal:** Categorize the failure into a known type

**What happens:**
- Use pattern matching (heuristics)
- If uncertain, use LLM classification
- Assign confidence score
- Identify subtype if applicable

**Input:** Extracted error information from Step 1

**Output:**
```json
{
  "failure_type": "dependency_version_mismatch",
  "subtype": "version_not_available",
  "confidence": 0.92,
  "evidence": ["ERROR: Could not find a version..."]
}
```

**See:** [01-failure-classification.md](01-failure-classification.md) for details

---

## Step 3: Correlate

**Goal:** Match the failure with relevant repository artifacts

**What happens:**
- Query repository knowledge model for related artifacts
- Find dependency files, config files, workflow files
- Identify which files are likely affected
- Extract relevant metadata (versions, paths, etc.)

**Input:** 
- Failure classification from Step 2
- Repository static analysis (from Sprint 1)

**Process:**
```python
# Example: Dependency failure
if failure_type == "dependency_version_mismatch":
    # Find dependency manifests
    dependency_files = query_artifacts({
        "type": "dependency_manifest"
    })
    
    # Find workflows that use dependencies
    workflows = query_artifacts({
        "type": "workflow"
    })
    
    # Correlate error message with specific package
    package_name = extract_package_name(error_message)
    affected_files = find_files_containing_package(dependency_files, package_name)
```

**Output:**
```json
{
  "affected_artifacts": [
    {
      "type": "dependency_manifest",
      "path": "requirements.txt",
      "metadata": {
        "package_manager": "pip",
        "dependencies": {"pytest": "==7.0.0"}
      }
    }
  ],
  "related_artifacts": [
    {
      "type": "workflow",
      "path": ".github/workflows/ci.yml",
      "metadata": {
        "jobs": [{"name": "test", "steps": [...]}]
      }
    }
  ]
}
```

---

## Step 4: Analyze Root Cause

**Goal:** Determine why the failure occurred

**What happens:**
- Combine failure classification, error messages, and repository context
- Use LLM to reason about root cause
- Identify contributing factors
- Assess severity

**LLM Prompt Structure:**
```
You are analyzing a CI/CD failure. Determine the root cause.

Failure Type: {failure_type}
Error Messages: {error_messages}
Repository Context:
- Language: {language}
- Package Manager: {package_manager}
- Affected Files: {affected_files}

Analyze why this failure occurred. Consider:
1. What specific condition caused the failure?
2. What changed or is missing?
3. Why did this happen now?

Respond with JSON:
{
  "root_cause": "Detailed explanation of why this failed",
  "contributing_factors": ["factor1", "factor2"],
  "severity": "Low|Medium|High|Critical",
  "reasoning": "Step-by-step analysis"
}
```

**Output:**
```json
{
  "root_cause": "Package pytest==7.0.0 is not available for Python 3.12. The specified version constraint is too strict and incompatible with the Python version used in CI.",
  "contributing_factors": [
    "Python version mismatch (3.12 vs expected 3.9)",
    "Pinned version constraint (==7.0.0) instead of flexible (>=7.0.0)"
  ],
  "severity": "Medium",
  "reasoning": "The error message indicates pytest==7.0.0 cannot be found. Checking Python version compatibility reveals 3.12 is being used, but pytest 7.0.0 may not have wheels for 3.12. The == constraint prevents using compatible versions."
}
```

---

## Step 5: Generate Fix

**Goal:** Propose actionable remediation steps

**What happens:**
- Based on root cause, generate fix suggestions
- Identify specific files to modify
- Propose exact changes
- Calculate confidence in fix

**LLM Prompt Structure:**
```
Based on this failure analysis, propose a fix.

Root Cause: {root_cause}
Failure Type: {failure_type}
Affected Files: {affected_files}

Propose a fix that:
1. Addresses the root cause
2. Is minimal and safe
3. Follows best practices

Respond with JSON:
{
  "fix_summary": "Brief description of the fix",
  "fix_steps": [
    {"action": "update", "file": "requirements.txt", "change": "pytest==7.0.0 → pytest>=7.0.0"},
    {"action": "verify", "description": "Check Python version compatibility"}
  ],
  "affected_files": ["requirements.txt"],
  "confidence": 0.85,
  "alternative_fixes": [
    {"description": "Alternative approach", "pros": [...], "cons": [...]}
  ]
}
```

**Output:**
```json
{
  "fix_summary": "Update requirements.txt to use flexible version constraint for pytest (>=7.0.0 instead of ==7.0.0) to allow compatible versions for Python 3.12",
  "fix_steps": [
    {
      "action": "update",
      "file": "requirements.txt",
      "change": "Change 'pytest==7.0.0' to 'pytest>=7.0.0'",
      "line": 15
    }
  ],
  "affected_files": ["requirements.txt"],
  "confidence": 0.90,
  "alternative_fixes": [
    {
      "description": "Pin to specific compatible version",
      "pros": ["More deterministic"],
      "cons": ["May break again if Python version changes"]
    }
  ]
}
```

---

## Complete Workflow Example

**Input:** `agent_context.json` with failure log

**Step 1 - Parse:**
```
Error: MISSING_API_KEY is not set
```

**Step 2 - Classify:**
```
Type: missing_environment_variable
Confidence: 0.90
```

**Step 3 - Correlate:**
```
Affected: .github/workflows/deploy.yml
Related: .env.example (shows expected variables)
```

**Step 4 - Root Cause:**
```
Root Cause: The workflow step requires MISSING_API_KEY environment variable, but it's not set in the workflow secrets or environment configuration.
```

**Step 5 - Fix:**
```
Fix: Add MISSING_API_KEY to GitHub repository secrets and reference it in the workflow.
```

**Final Output:**
```json
{
  "failure_type": "missing_environment_variable",
  "root_cause": "The workflow step requires MISSING_API_KEY environment variable, but it's not set in the workflow secrets or environment configuration.",
  "fix_summary": "Add MISSING_API_KEY to GitHub repository secrets and reference it in the workflow using ${{ secrets.MISSING_API_KEY }}",
  "severity": "High",
  "confidence": 0.90,
  "affected_files": [".github/workflows/deploy.yml"],
  "fix_steps": [
    {
      "action": "add_secret",
      "description": "Add MISSING_API_KEY to GitHub repository secrets"
    },
    {
      "action": "update",
      "file": ".github/workflows/deploy.yml",
      "change": "Add env: MISSING_API_KEY: ${{ secrets.MISSING_API_KEY }}"
    }
  ]
}
```

---

## Error Handling

**If classification fails:**
- Fall back to "unknown_error" type
- Still attempt root cause analysis
- Lower confidence score

**If correlation finds nothing:**
- Proceed with available information
- Note missing context in output
- Lower confidence score

**If LLM reasoning fails:**
- Use heuristic-based fallback
- Provide basic fix suggestion
- Flag as low confidence

---

## Performance Considerations

**Caching:**
- Cache classification results for similar errors
- Cache artifact queries
- Reuse LLM responses when possible

**Parallelization:**
- Process multiple failure logs in parallel
- Batch LLM requests when possible

**Token Optimization:**
- Truncate long logs (keep error sections)
- Summarize repository context
- Use structured prompts for efficiency

