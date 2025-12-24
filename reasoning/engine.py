"""
Main reasoning engine for CI/CD failure analysis.

Orchestrates the multi-step reasoning process:
1. Parse & Extract
2. Classify
3. Correlate
4. Analyze Root Cause
5. Generate Fix
"""

import json
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .models import (
    FailureAnalysis,
    FixStep,
    AlternativeFix,
    Severity,
    FixAction,
    MultiFailureAnalysis,
)
from .classifier import FailureClassifier, get_default_classifier
from .prompts import PromptTemplates

# Import types for type hints only (avoid circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from github_bridge.models import AgentContext, FailureLog
else:
    # For runtime, try to import but handle gracefully
    try:
        from github_bridge.models import AgentContext, FailureLog
    except ImportError:
        # Define minimal types for testing
        from typing import Any, Optional, List, Dict
        from pydantic import BaseModel, Field
        
        class FailureLog(BaseModel):
            job_name: str
            step_name: Optional[str] = None
            log_content: str
        
        class GitHubRepo(BaseModel):
            full_name: str
            default_branch: str = "main"
        
        class CIContext(BaseModel):
            platform: Optional[str] = None
            recent_runs: List[Any] = []
            failure_logs: Optional[List[FailureLog]] = None
            data: Dict[str, Any] = {}
        
        class AgentContext(BaseModel):
            repo: GitHubRepo
            static_analysis: Dict[str, Any] = {}
            ci_context: CIContext = CIContext()


@dataclass
class ExtractedError:
    """Extracted error information from a log."""
    error_messages: List[str]
    exit_code: Optional[int]
    key_lines: List[str]
    context: Dict[str, Any]


class ReasoningEngine:
    """Main reasoning engine for failure analysis."""

    def __init__(self, classifier: Optional[FailureClassifier] = None, use_llm: bool = False):
        """
        Initialize the reasoning engine.

        Args:
            classifier: Optional custom classifier (defaults to standard)
            use_llm: Whether to use LLM for analysis (default: False, uses heuristics)
        """
        self.classifier = classifier or get_default_classifier()
        self.use_llm = use_llm
        self.prompts = PromptTemplates()

    def analyze(self, context: AgentContext) -> FailureAnalysis:
        """
        Analyze failures from agent context.

        Args:
            context: AgentContext from github_bridge

        Returns:
            FailureAnalysis result
        """
        if not context.ci_context.failure_logs:
            # No failures to analyze
            return self._create_no_failure_analysis()

        # For now, analyze the first failure
        # TODO: Support multiple failures
        failure_log = context.ci_context.failure_logs[0]
        return self.analyze_failure(failure_log, context)

    def analyze_failure(
        self,
        failure_log: FailureLog,
        context: AgentContext
    ) -> FailureAnalysis:
        """
        Analyze a single failure.

        Args:
            failure_log: The failure log to analyze
            context: Full agent context

        Returns:
            FailureAnalysis result
        """
        # Step 1: Parse & Extract
        extracted = self._extract_errors(failure_log.log_content)

        # Step 2: Classify
        classification = self.classifier.classify(failure_log.log_content)
        if not classification:
            classification = self._classify_unknown(failure_log.log_content)

        # Step 3: Correlate
        affected_artifacts = self._correlate_with_artifacts(
            classification.failure_type,
            extracted,
            context
        )

        # Step 4 & 5: Root Cause & Fix (using heuristics for now)
        if self.use_llm:
            # TODO: Implement LLM-based analysis
            analysis = self._analyze_with_llm(
                classification, extracted, affected_artifacts, context, failure_log
            )
        else:
            analysis = self._analyze_with_heuristics(
                classification, extracted, affected_artifacts, context, failure_log
            )

        return analysis

    def _extract_errors(self, log_content: str) -> ExtractedError:
        """Extract key error information from log."""
        lines = log_content.split('\n')
        error_messages = []
        key_lines = []
        exit_code = None

        # Find error patterns
        error_patterns = [
            r'ERROR:',
            r'Error:',
            r'FAILED',
            r'Exception:',
            r'Traceback',
        ]

        for line in lines:
            # Check for error patterns
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in error_patterns):
                error_messages.append(line.strip())
                key_lines.append(line.strip())

            # Find exit codes
            exit_match = re.search(r'exit code (\d+)', line, re.IGNORECASE)
            if exit_match:
                exit_code = int(exit_match.group(1))

        # Limit to most relevant
        error_messages = error_messages[:10]
        key_lines = key_lines[:10]

        # Extract context
        context = {
            'files_mentioned': self._extract_file_paths(log_content),
            'packages_mentioned': self._extract_package_names(log_content),
        }

        return ExtractedError(
            error_messages=error_messages,
            exit_code=exit_code,
            key_lines=key_lines,
            context=context
        )

    def _extract_file_paths(self, log_content: str) -> List[str]:
        """Extract file paths mentioned in log."""
        # Simple pattern matching
        patterns = [
            r'File "([^"]+)"',
            r'([/\w\-\.]+\.(py|js|ts|yml|yaml|json|txt|md))',
        ]
        files = []
        for pattern in patterns:
            matches = re.findall(pattern, log_content)
            for match in matches:
                if isinstance(match, tuple):
                    files.append(match[0])
                else:
                    files.append(match)
        return list(set(files))[:10]  # Deduplicate and limit

    def _extract_package_names(self, log_content: str) -> List[str]:
        """Extract package names mentioned in log."""
        # Look for common package error patterns
        patterns = [
            r'Could not find.*requirement (\w+)',
            r'PackageNotFoundError.*(\w+)',
            r'ModuleNotFoundError.*(\w+)',
        ]
        packages = []
        for pattern in patterns:
            matches = re.findall(pattern, log_content, re.IGNORECASE)
            packages.extend(matches)
        return list(set(packages))[:10]

    def _classify_unknown(self, log_content: str):
        """Create unknown classification."""
        from .classifier import ClassificationResult
        return ClassificationResult(
            failure_type='unknown_error',
            confidence=0.3,
            evidence=[log_content[:200]]
        )

    def _correlate_with_artifacts(
        self,
        failure_type: str,
        extracted: ExtractedError,
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """Correlate failure with repository artifacts."""
        artifacts = context.static_analysis.get('artifacts', [])
        affected = []

        # Based on failure type, find relevant artifacts
        if 'dependency' in failure_type:
            # Find dependency manifests
            for artifact in artifacts:
                if artifact.get('type') == 'dependency_manifest':
                    affected.append(artifact)
        elif 'environment' in failure_type or 'config' in failure_type:
            # Find config files and workflows
            for artifact in artifacts:
                if artifact.get('type') in ['config', 'workflow']:
                    affected.append(artifact)
        elif 'test' in failure_type:
            # Find test-related artifacts
            for artifact in artifacts:
                if 'test' in artifact.get('path', '').lower():
                    affected.append(artifact)

        # Also check if any files mentioned in log match artifacts
        for file_path in extracted.context.get('files_mentioned', []):
            for artifact in artifacts:
                if file_path in artifact.get('path', ''):
                    if artifact not in affected:
                        affected.append(artifact)

        return affected

    def _analyze_with_heuristics(
        self,
        classification,
        extracted: ExtractedError,
        affected_artifacts: List[Dict[str, Any]],
        context: AgentContext,
        failure_log: FailureLog
    ) -> FailureAnalysis:
        """Analyze failure using heuristics (no LLM)."""
        # Generate root cause based on failure type
        root_cause = self._generate_root_cause_heuristic(
            classification.failure_type,
            extracted,
            context
        )

        # Generate fix summary
        fix_summary = self._generate_fix_summary_heuristic(
            classification.failure_type,
            root_cause,
            affected_artifacts
        )

        # Determine severity
        severity = self._determine_severity(classification.failure_type)

        # Generate fix steps
        fix_steps = self._generate_fix_steps_heuristic(
            classification.failure_type,
            affected_artifacts,
            extracted
        )

        # Get affected files
        affected_files = [a.get('path', '') for a in affected_artifacts if a.get('path')]

        return FailureAnalysis(
            failure_type=classification.failure_type,
            subtype=classification.subtype,
            root_cause=root_cause,
            fix_summary=fix_summary,
            severity=severity,
            confidence=classification.confidence * 0.8,  # Lower confidence for heuristic
            affected_files=affected_files,
            evidence=classification.evidence or extracted.key_lines[:5],
            fix_steps=fix_steps,
            contributing_factors=self._identify_contributing_factors(classification, context)
        )

    def _generate_root_cause_heuristic(
        self,
        failure_type: str,
        extracted: ExtractedError,
        context: AgentContext
    ) -> str:
        """Generate root cause using heuristics."""
        static_summary = context.static_analysis.get('summary', {})
        language = static_summary.get('primary_language', 'unknown')

        if failure_type == 'dependency_version_mismatch':
            return f"A required package version is not available or incompatible with the current environment (likely {language} version mismatch)."
        elif failure_type == 'dependency_missing':
            return f"A required package is not installed or not found in the package registry."
        elif failure_type == 'missing_environment_variable':
            return "A required environment variable is not set in the CI/CD environment."
        elif failure_type == 'test_assertion_failure':
            return "A test assertion failed, indicating the code behavior doesn't match expectations."
        elif failure_type == 'compilation_error':
            return f"Code compilation failed, likely due to syntax errors or type mismatches in {language}."
        elif failure_type == 'permission_error':
            return "File or directory permissions are insufficient for the required operation."
        else:
            return f"Failure occurred due to {failure_type.replace('_', ' ')}."

    def _generate_fix_summary_heuristic(
        self,
        failure_type: str,
        root_cause: str,
        affected_artifacts: List[Dict[str, Any]]
    ) -> str:
        """Generate fix summary using heuristics."""
        if affected_artifacts:
            file_path = affected_artifacts[0].get('path', 'file')
        else:
            file_path = 'configuration'

        if failure_type == 'dependency_version_mismatch':
            return f"Update {file_path} to use a compatible package version or adjust version constraints."
        elif failure_type == 'dependency_missing':
            return f"Add the missing package to {file_path} or install it in the CI environment."
        elif failure_type == 'missing_environment_variable':
            return f"Add the required environment variable to GitHub secrets and reference it in the workflow."
        elif failure_type == 'test_assertion_failure':
            return "Fix the test assertion or update the code to match expected behavior."
        else:
            return f"Address the {failure_type.replace('_', ' ')} issue in {file_path}."

    def _determine_severity(self, failure_type: str) -> Severity:
        """Determine severity based on failure type."""
        critical_types = ['compilation_error', 'workflow_syntax_error']
        high_types = ['dependency_missing', 'permission_error', 'runtime_exception']
        medium_types = ['dependency_version_mismatch', 'test_assertion_failure', 'missing_environment_variable']

        if failure_type in critical_types:
            return Severity.CRITICAL
        elif failure_type in high_types:
            return Severity.HIGH
        elif failure_type in medium_types:
            return Severity.MEDIUM
        else:
            return Severity.LOW

    def _generate_fix_steps_heuristic(
        self,
        failure_type: str,
        affected_artifacts: List[Dict[str, Any]],
        extracted: ExtractedError
    ) -> List[FixStep]:
        """Generate fix steps using heuristics."""
        steps = []

        if not affected_artifacts:
            return steps

        artifact = affected_artifacts[0]
        file_path = artifact.get('path', '')

        if failure_type == 'dependency_version_mismatch':
            # Try to extract package name from error
            packages = extracted.context.get('packages_mentioned', [])
            if packages:
                package = packages[0]
                steps.append(FixStep(
                    action=FixAction.UPDATE,
                    file=file_path,
                    change=f"Update {package} version constraint to be more flexible (e.g., >= instead of ==)",
                    description="Allow compatible versions"
                ))
        elif failure_type == 'missing_environment_variable':
            # Extract variable name from error
            var_name = self._extract_env_var_name(extracted.error_messages)
            if var_name:
                steps.append(FixStep(
                    action=FixAction.ADD_SECRET,
                    file="GitHub Secrets",
                    change=f"Add {var_name} to repository secrets",
                    description="Required environment variable"
                ))
                steps.append(FixStep(
                    action=FixAction.UPDATE,
                    file=file_path,
                    change=f"Reference {var_name} using ${{{{ secrets.{var_name} }}}}",
                    description="Use the secret in workflow"
                ))

        return steps

    def _extract_env_var_name(self, error_messages: List[str]) -> Optional[str]:
        """Extract environment variable name from error messages."""
        for msg in error_messages:
            # Look for patterns like "MISSING_API_KEY is not set"
            match = re.search(r'([A-Z_]+)\s+is not set', msg, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _identify_contributing_factors(
        self,
        classification,
        context: AgentContext
    ) -> List[str]:
        """Identify contributing factors."""
        factors = []
        static_summary = context.static_analysis.get('summary', {})

        if 'dependency' in classification.failure_type:
            language = static_summary.get('primary_language', 'unknown')
            factors.append(f"Language version: {language}")

        return factors

    def _analyze_with_llm(
        self,
        classification,
        extracted: ExtractedError,
        affected_artifacts: List[Dict[str, Any]],
        context: AgentContext,
        failure_log: FailureLog
    ) -> FailureAnalysis:
        """Analyze failure using LLM (TODO: implement)."""
        # For now, fall back to heuristics
        # TODO: Implement LLM integration
        return self._analyze_with_heuristics(
            classification, extracted, affected_artifacts, context, failure_log
        )

    def _create_no_failure_analysis(self) -> FailureAnalysis:
        """Create analysis when no failures exist."""
        return FailureAnalysis(
            failure_type='no_failures',
            root_cause="No CI/CD failures detected in the repository.",
            fix_summary="No action needed.",
            severity=Severity.LOW,
            confidence=1.0,
            affected_files=[],
            evidence=[],
            fix_steps=[]
        )

