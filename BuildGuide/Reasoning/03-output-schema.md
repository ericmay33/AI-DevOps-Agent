# 03: Output Schema

## What This Does

This document defines the structured output format that the reasoning engine produces. This output is used by Sprint 3 (Patch Generation) to create fixes and PRs.

---

## Main Output: FailureAnalysis

The reasoning engine produces a `FailureAnalysis` object with the following structure:

```python
{
    "failure_type": str,           # Primary failure category
    "subtype": Optional[str],      # More specific failure type
    "root_cause": str,             # Detailed explanation of why it failed
    "fix_summary": str,            # Brief description of the fix
    "severity": str,               # Low|Medium|High|Critical
    "confidence": float,           # 0.0-1.0 confidence score
    "affected_files": List[str],   # Files that need modification
    "evidence": List[str],         # Log lines that support the analysis
    "fix_steps": List[FixStep],    # Detailed fix instructions
    "contributing_factors": List[str],  # Additional factors
    "alternative_fixes": List[AlternativeFix]  # Other possible fixes
}
```

---

## Field Descriptions

### failure_type (required)

**Type:** `str`

**Description:** Primary failure category from the classification system.

**Possible values:**
- `dependency_version_mismatch`
- `dependency_missing`
- `missing_environment_variable`
- `test_assertion_failure`
- `compilation_error`
- `permission_error`
- `network_timeout`
- `runtime_exception`
- `workflow_syntax_error`
- `unknown_error`

**Example:**
```json
"failure_type": "dependency_version_mismatch"
```

### subtype (optional)

**Type:** `Optional[str]`

**Description:** More specific failure type within the main category.

**Example:**
```json
"subtype": "version_not_available"
```

### root_cause (required)

**Type:** `str`

**Description:** Detailed explanation of why the failure occurred. Should be 1-3 sentences explaining the underlying cause.

**Example:**
```json
"root_cause": "Package pytest==7.0.0 is not available for Python 3.12. The specified version constraint is too strict and incompatible with the Python version used in CI."
```

### fix_summary (required)

**Type:** `str`

**Description:** Brief, actionable description of how to fix the issue. Should be 1-2 sentences.

**Example:**
```json
"fix_summary": "Update requirements.txt to use flexible version constraint for pytest (>=7.0.0 instead of ==7.0.0) to allow compatible versions for Python 3.12"
```

### severity (required)

**Type:** `str` (enum)

**Description:** Severity level indicating impact and urgency.

**Possible values:**
- `Low` - Minor issue, doesn't block development
- `Medium` - Moderate issue, may cause problems
- `High` - Significant issue, blocks important functionality
- `Critical` - Critical issue, blocks all functionality

**Example:**
```json
"severity": "Medium"
```

### confidence (required)

**Type:** `float` (0.0-1.0)

**Description:** Confidence score indicating how certain the analysis is.

**Interpretation:**
- `0.9-1.0`: Very high confidence, strong evidence
- `0.7-0.9`: High confidence, good evidence
- `0.5-0.7`: Medium confidence, some evidence
- `0.0-0.5`: Low confidence, weak evidence

**Example:**
```json
"confidence": 0.92
```

### affected_files (required)

**Type:** `List[str]`

**Description:** List of file paths (relative to repository root) that need to be modified to fix the issue.

**Example:**
```json
"affected_files": ["requirements.txt", ".github/workflows/ci.yml"]
```

### evidence (required)

**Type:** `List[str]`

**Description:** Specific log lines or error messages that support the analysis. Should include the most relevant lines.

**Example:**
```json
"evidence": [
  "ERROR: Could not find a version that satisfies the requirement pytest==7.0.0",
  "ERROR: No matching distribution found for pytest==7.0.0"
]
```

### fix_steps (required)

**Type:** `List[FixStep]`

**Description:** Detailed step-by-step instructions for fixing the issue.

**FixStep structure:**
```python
{
    "action": str,        # "update" | "add" | "delete" | "create" | "verify"
    "file": str,          # File path (relative to repo root)
    "change": str,        # Description of the change
    "line": Optional[int], # Line number (if applicable)
    "description": Optional[str]  # Additional details
}
```

**Example:**
```json
"fix_steps": [
  {
    "action": "update",
    "file": "requirements.txt",
    "change": "Change 'pytest==7.0.0' to 'pytest>=7.0.0'",
    "line": 15,
    "description": "Update version constraint to allow compatible versions"
  }
]
```

### contributing_factors (optional)

**Type:** `List[str]`

**Description:** Additional factors that contributed to the failure but aren't the primary cause.

**Example:**
```json
"contributing_factors": [
  "Python version mismatch (3.12 vs expected 3.9)",
  "Pinned version constraint (==7.0.0) instead of flexible (>=7.0.0)"
]
```

### alternative_fixes (optional)

**Type:** `List[AlternativeFix]`

**Description:** Other possible fixes with pros and cons.

**AlternativeFix structure:**
```python
{
    "description": str,   # Description of the alternative approach
    "pros": List[str],    # Advantages
    "cons": List[str]     # Disadvantages
}
```

**Example:**
```json
"alternative_fixes": [
  {
    "description": "Pin to specific compatible version (pytest==7.4.0)",
    "pros": ["More deterministic", "Explicit version"],
    "cons": ["May break again if Python version changes", "Requires research"]
  }
]
```

---

## Complete Example

```json
{
  "failure_type": "dependency_version_mismatch",
  "subtype": "version_not_available",
  "root_cause": "Package pytest==7.0.0 is not available for Python 3.12. The specified version constraint is too strict and incompatible with the Python version used in CI.",
  "fix_summary": "Update requirements.txt to use flexible version constraint for pytest (>=7.0.0 instead of ==7.0.0) to allow compatible versions for Python 3.12",
  "severity": "Medium",
  "confidence": 0.92,
  "affected_files": ["requirements.txt"],
  "evidence": [
    "ERROR: Could not find a version that satisfies the requirement pytest==7.0.0",
    "ERROR: No matching distribution found for pytest==7.0.0"
  ],
  "fix_steps": [
    {
      "action": "update",
      "file": "requirements.txt",
      "change": "Change 'pytest==7.0.0' to 'pytest>=7.0.0'",
      "line": 15,
      "description": "Update version constraint to allow compatible versions"
    }
  ],
  "contributing_factors": [
    "Python version mismatch (3.12 vs expected 3.9)",
    "Pinned version constraint (==7.0.0) instead of flexible (>=7.0.0)"
  ],
  "alternative_fixes": [
    {
      "description": "Pin to specific compatible version (pytest==7.4.0)",
      "pros": ["More deterministic", "Explicit version"],
      "cons": ["May break again if Python version changes", "Requires research"]
    }
  ]
}
```

---

## Multiple Failures

If multiple failures are analyzed, the output is a list:

```json
{
  "analyses": [
    {
      "failure_type": "dependency_version_mismatch",
      ...
    },
    {
      "failure_type": "missing_environment_variable",
      ...
    }
  ],
  "summary": {
    "total_failures": 2,
    "critical_count": 0,
    "high_count": 1,
    "medium_count": 1,
    "low_count": 0
  }
}
```

---

## Validation

The output schema should be validated using Pydantic models:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class FixAction(str, Enum):
    UPDATE = "update"
    ADD = "add"
    DELETE = "delete"
    CREATE = "create"
    VERIFY = "verify"

class FixStep(BaseModel):
    action: FixAction
    file: str
    change: str
    line: Optional[int] = None
    description: Optional[str] = None

class AlternativeFix(BaseModel):
    description: str
    pros: List[str]
    cons: List[str]

class FailureAnalysis(BaseModel):
    failure_type: str
    subtype: Optional[str] = None
    root_cause: str = Field(..., min_length=10)
    fix_summary: str = Field(..., min_length=10)
    severity: Severity
    confidence: float = Field(..., ge=0.0, le=1.0)
    affected_files: List[str]
    evidence: List[str]
    fix_steps: List[FixStep]
    contributing_factors: Optional[List[str]] = None
    alternative_fixes: Optional[List[AlternativeFix]] = None
```

---

## Integration with Sprint 3

This output schema is designed to be consumed by Sprint 3 (Patch Generation):

1. **fix_steps** → Direct instructions for file modifications
2. **affected_files** → Files to modify
3. **fix_summary** → PR description content
4. **root_cause** → PR explanation
5. **confidence** → Whether to auto-apply or require review

---

## Extensibility

The schema can be extended for future needs:

- Add `metadata` field for custom data
- Add `tags` for categorization
- Add `related_issues` for linking to GitHub issues
- Add `estimated_time` for fix complexity

