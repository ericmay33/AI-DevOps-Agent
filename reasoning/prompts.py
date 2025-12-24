"""
Prompt templates for LLM-based failure analysis.

These prompts guide the LLM to produce structured, actionable analysis.
"""

from typing import Dict, Any, List
import json


class PromptTemplates:
    """Collection of prompt templates for failure analysis."""

    @staticmethod
    def classification_prompt(
        job_name: str,
        step_name: str,
        log_content: str,
        primary_language: str = "unknown",
        ci_platform: str = "unknown",
        package_manager: str = "unknown"
    ) -> str:
        """Generate prompt for failure classification."""
        return f"""You are analyzing a CI/CD failure log. Classify the failure type.

## Failure Log
Job: {job_name}
Step: {step_name}
Log Content:
```
{log_content[:2000]}  # Truncate long logs
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
}}"""

    @staticmethod
    def root_cause_prompt(
        failure_type: str,
        job_name: str,
        step_name: str,
        error_messages: List[str],
        primary_language: str,
        package_manager: str,
        ci_platform: str,
        affected_artifacts: List[Dict[str, Any]]
    ) -> str:
        """Generate prompt for root cause analysis."""
        artifacts_json = json.dumps(affected_artifacts, indent=2)
        error_text = "\n".join(f"- {msg}" for msg in error_messages[:10])

        return f"""You are analyzing a CI/CD failure to determine the root cause.

## Failure Information
Failure Type: {failure_type}
Job: {job_name}
Step: {step_name}

## Error Messages
{error_text}

## Repository Context
- Primary Language: {primary_language}
- Package Manager: {package_manager}
- CI Platform: {ci_platform}

## Affected Artifacts
{artifacts_json}

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
}}"""

    @staticmethod
    def fix_generation_prompt(
        failure_type: str,
        root_cause: str,
        severity: str,
        affected_files: List[str],
        relevant_artifacts: List[Dict[str, Any]]
    ) -> str:
        """Generate prompt for fix generation."""
        artifacts_json = json.dumps(relevant_artifacts, indent=2)
        files_text = "\n".join(f"- {f}" for f in affected_files)

        return f"""You are proposing a fix for a CI/CD failure.

## Failure Analysis
Failure Type: {failure_type}
Root Cause: {root_cause}
Severity: {severity}

## Affected Files
{files_text}

## Repository Artifacts
{artifacts_json}

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
      "action": "update|add|delete|create|verify|add_secret",
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
}}"""

    @staticmethod
    def evidence_extraction_prompt(log_content: str) -> str:
        """Generate prompt for extracting key evidence from logs."""
        return f"""Extract the most relevant error information from this CI/CD log.

## Log Content
```
{log_content[:3000]}  # Truncate very long logs
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
}}"""

