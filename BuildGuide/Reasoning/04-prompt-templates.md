# 04: Prompt Templates

## What This Does

This document contains all prompt templates used by the reasoning engine. These prompts guide the LLM to produce structured, actionable analysis.

---

## Prompt Design Principles

1. **Structured Output**: Always request JSON responses
2. **Evidence-Based**: Reference specific log lines and artifacts
3. **Actionable**: Focus on what can be fixed, not just diagnosis
4. **Context-Rich**: Include repository context for better reasoning
5. **Deterministic**: Use clear instructions to reduce variability

---

## Template 1: Failure Classification

**Purpose:** Classify a failure log into a known category

**When used:** Step 2 of reasoning workflow

**Template:**
```
You are analyzing a CI/CD failure log. Classify the failure type.

## Failure Log
Job: {job_name}
Step: {step_name}
Log Content:
```
{log_content}
```

## Repository Context
- Primary Language: {primary_language}
- CI Platform: {ci_platform}
- Package Manager: {package_manager}

## Available Failure Types
1. dependency_version_mismatch - Required package version doesn't exist or is incompatible
2. dependency_missing - Package not found in registry
3. dependency_conflict - Multiple packages require incompatible versions
4. missing_environment_variable - Required environment variable not set
5. invalid_configuration - Configuration file has errors
6. test_assertion_failure - Test assertion failed
7. test_timeout - Test exceeded time limit
8. compilation_error - Code doesn't compile
9. syntax_error - Syntax error in source code
10. permission_error - File or directory permission denied
11. network_timeout - Network request timed out
12. runtime_exception - Unhandled exception during execution
13. workflow_syntax_error - Workflow YAML has syntax errors
14. unknown_error - Cannot classify into known categories

## Instructions
1. Analyze the log content for error patterns
2. Identify the most specific failure type
3. Assess your confidence (0.0-1.0)
4. Provide reasoning for your classification

## Response Format
Respond with valid JSON only:
{{
  "failure_type": "one of the types above",
  "subtype": "optional more specific type",
  "confidence": 0.0-1.0,
  "reasoning": "explanation of why this classification",
  "key_evidence": ["log line 1", "log line 2"]
}}
```

**Variables:**
- `{job_name}` - Name of the failed job
- `{step_name}` - Name of the failed step (if available)
- `{log_content}` - The actual failure log text
- `{primary_language}` - Repository primary language
- `{ci_platform}` - CI platform (github_actions, etc.)
- `{package_manager}` - Package manager (pip, npm, etc.)

---

## Template 2: Root Cause Analysis

**Purpose:** Determine why the failure occurred

**When used:** Step 4 of reasoning workflow

**Template:**
```
You are analyzing a CI/CD failure to determine the root cause.

## Failure Information
Failure Type: {failure_type}
Job: {job_name}
Step: {step_name}

## Error Messages
{error_messages}

## Repository Context
- Primary Language: {primary_language}
- Package Manager: {package_manager}
- CI Platform: {ci_platform}

## Affected Artifacts
{affected_artifacts_json}

## Instructions
1. Analyze why this specific failure occurred
2. Consider what changed or is missing
3. Identify contributing factors
4. Assess severity (Low/Medium/High/Critical)
5. Provide step-by-step reasoning

## Response Format
Respond with valid JSON only:
{{
  "root_cause": "detailed 1-3 sentence explanation of why this failed",
  "contributing_factors": ["factor1", "factor2"],
  "severity": "Low|Medium|High|Critical",
  "reasoning": "step-by-step analysis of how you determined the root cause"
}}
```

**Variables:**
- `{failure_type}` - Classified failure type
- `{job_name}` - Name of the failed job
- `{step_name}` - Name of the failed step
- `{error_messages}` - Extracted error messages
- `{primary_language}` - Repository primary language
- `{package_manager}` - Package manager
- `{ci_platform}` - CI platform
- `{affected_artifacts_json}` - JSON array of affected artifacts

---

## Template 3: Fix Generation

**Purpose:** Generate actionable fix steps

**When used:** Step 5 of reasoning workflow

**Template:**
```
You are proposing a fix for a CI/CD failure.

## Failure Analysis
Failure Type: {failure_type}
Root Cause: {root_cause}
Severity: {severity}

## Affected Files
{affected_files}

## Repository Artifacts
{relevant_artifacts_json}

## Instructions
1. Propose a minimal, safe fix that addresses the root cause
2. Identify specific files and changes needed
3. Provide step-by-step fix instructions
4. Consider best practices for the technology stack
5. Assess confidence in the fix (0.0-1.0)
6. Suggest alternative approaches if applicable

## Response Format
Respond with valid JSON only:
{{
  "fix_summary": "brief 1-2 sentence description of the fix",
  "fix_steps": [
    {{
      "action": "update|add|delete|create|verify",
      "file": "path/to/file",
      "change": "description of the change",
      "line": 42,
      "description": "additional details"
    }}
  ],
  "affected_files": ["file1", "file2"],
  "confidence": 0.0-1.0,
  "alternative_fixes": [
    {{
      "description": "alternative approach",
      "pros": ["advantage1", "advantage2"],
      "cons": ["disadvantage1", "disadvantage2"]
    }}
  ]
}}
```

**Variables:**
- `{failure_type}` - Classified failure type
- `{root_cause}` - Determined root cause
- `{severity}` - Severity level
- `{affected_files}` - List of affected file paths
- `{relevant_artifacts_json}` - JSON of relevant repository artifacts

---

## Template 4: Multi-Failure Analysis

**Purpose:** Analyze multiple failures together

**When used:** When multiple failure logs exist

**Template:**
```
You are analyzing multiple CI/CD failures. Some may be related.

## Failures
{failures_json}

## Repository Context
- Primary Language: {primary_language}
- CI Platform: {ci_platform}

## Instructions
1. Analyze each failure individually
2. Determine if failures are related (cascading failures)
3. Identify the primary failure that caused others
4. Prioritize fixes (which to fix first)
5. Assess overall impact

## Response Format
Respond with valid JSON only:
{{
  "analyses": [
    {{
      "failure_type": "...",
      "root_cause": "...",
      "fix_summary": "...",
      "severity": "...",
      "confidence": 0.0-1.0,
      "affected_files": ["..."],
      "evidence": ["..."],
      "fix_steps": [...]
    }}
  ],
  "relationships": [
    {{
      "failure_1": "index in analyses",
      "failure_2": "index in analyses",
      "relationship": "caused_by|related_to|independent"
    }}
  ],
  "fix_priority": [0, 1, 2],  // Indices in order to fix
  "overall_severity": "Low|Medium|High|Critical"
}}
```

**Variables:**
- `{failures_json}` - JSON array of failure logs
- `{primary_language}` - Repository primary language
- `{ci_platform}` - CI platform

---

## Template 5: Evidence Extraction

**Purpose:** Extract key evidence from long logs

**When used:** Step 1 of reasoning workflow (pre-processing)

**Template:**
```
Extract the most relevant error information from this CI/CD log.

## Log Content
```
{log_content}
```

## Instructions
1. Identify error messages (lines starting with ERROR, FAILED, etc.)
2. Extract stack traces
3. Find exit codes
4. Identify key context (file paths, line numbers, package names)
5. Filter out noise (timestamps, ANSI codes, verbose output)

## Response Format
Respond with valid JSON only:
{{
  "error_messages": ["error1", "error2"],
  "exit_code": 1,
  "key_lines": ["line1", "line2"],
  "stack_trace": "full stack trace if present",
  "context": {{
    "files_mentioned": ["file1", "file2"],
    "line_numbers": [42, 100],
    "packages_mentioned": ["package1"]
  }}
}}
```

**Variables:**
- `{log_content}` - Full log content

---

## Prompt Variable Substitution

All templates use variable substitution. Example implementation:

```python
def format_prompt(template: str, **kwargs) -> str:
    """Format prompt template with variables."""
    return template.format(**kwargs)
```

**Example:**
```python
prompt = format_prompt(
    CLASSIFICATION_PROMPT,
    job_name="test",
    step_name="Run tests",
    log_content=log_content,
    primary_language="python",
    ci_platform="github_actions",
    package_manager="pip"
)
```

---

## LLM Configuration

**Recommended settings:**
- **Model**: GPT-4 or Claude 3 (for structured output)
- **Temperature**: 0.0-0.2 (for deterministic output)
- **Max Tokens**: 2000-4000 (depending on template)
- **Response Format**: JSON mode (if supported)

**Example:**
```python
response = llm.complete(
    prompt=formatted_prompt,
    temperature=0.1,
    max_tokens=2000,
    response_format={"type": "json_object"}
)
```

---

## Error Handling

**If LLM fails to produce valid JSON:**
1. Retry with more explicit JSON instructions
2. Use JSON schema validation
3. Fall back to heuristic-based analysis
4. Flag as low confidence

**If LLM produces low confidence:**
1. Request more detailed reasoning
2. Provide additional context
3. Use alternative prompt phrasing
4. Consider manual review

---

## Prompt Versioning

Prompts should be versioned for:
- Tracking changes
- A/B testing improvements
- Rollback if needed

**Example:**
```python
PROMPT_VERSION = "2.1.0"
```

Store prompt versions in code comments or configuration.

