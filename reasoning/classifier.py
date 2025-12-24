"""
Failure classification using pattern matching and heuristics.

This provides fast, deterministic classification before LLM analysis.
"""

import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """Result of failure classification."""
    failure_type: str
    subtype: Optional[str] = None
    confidence: float = 0.0
    evidence: List[str] = None

    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []


class FailureClassifier:
    """Classifies CI/CD failures using pattern matching."""

    # Pattern definitions for each failure type
    PATTERNS: Dict[str, List[Tuple[str, float]]] = {
        'dependency_version_mismatch': [
            (r'Could not find a version that satisfies', 0.95),
            (r'No matching distribution found', 0.90),
            (r'version.*not found', 0.85),
            (r'incompatible.*version', 0.80),
        ],
        'dependency_missing': [
            (r'PackageNotFoundError', 0.95),
            (r'ModuleNotFoundError', 0.90),
            (r'package.*not found', 0.85),
            (r'Cannot find module', 0.80),
        ],
        'dependency_conflict': [
            (r'Resolving dependencies.*failed', 0.90),
            (r'Dependency conflict', 0.85),
            (r'incompatible.*dependencies', 0.80),
        ],
        'missing_environment_variable': [
            (r'is not set', 0.95),
            (r'Environment variable.*required', 0.90),
            (r'Missing.*environment variable', 0.85),
            (r'env.*not set', 0.80),
        ],
        'invalid_configuration': [
            (r'ConfigurationError', 0.90),
            (r'Invalid configuration', 0.85),
            (r'Config.*error', 0.80),
        ],
        'test_assertion_failure': [
            (r'AssertionError', 0.95),
            (r'Test failed', 0.85),
            (r'FAILED.*test', 0.80),
        ],
        'test_timeout': [
            (r'Test.*timeout', 0.95),
            (r'TimeoutError.*test', 0.90),
            (r'Test.*exceeded.*time', 0.85),
        ],
        'compilation_error': [
            (r'CompilationError', 0.95),
            (r'error: failed to compile', 0.90),
            (r'Build failed', 0.85),
        ],
        'syntax_error': [
            (r'SyntaxError', 0.95),
            (r'syntax error', 0.90),
            (r'invalid syntax', 0.85),
        ],
        'permission_error': [
            (r'PermissionError', 0.95),
            (r'Permission denied', 0.90),
            (r'EACCES', 0.85),
            (r'Access denied', 0.80),
        ],
        'network_timeout': [
            (r'TimeoutError', 0.90),
            (r'Connection.*timeout', 0.85),
            (r'Request.*timeout', 0.80),
        ],
        'connection_failed': [
            (r'ConnectionError', 0.95),
            (r'Failed to connect', 0.90),
            (r'Connection refused', 0.85),
        ],
        'runtime_exception': [
            (r'RuntimeError', 0.90),
            (r'Unhandled exception', 0.85),
        ],
        'import_error': [
            (r'ImportError', 0.95),
            (r'cannot import', 0.90),
        ],
        'workflow_syntax_error': [
            (r'Workflow.*syntax error', 0.90),
            (r'Invalid workflow', 0.85),
        ],
    }

    def __init__(self):
        """Initialize the classifier."""
        # Compile patterns for efficiency
        self.compiled_patterns: Dict[str, List[Tuple[re.Pattern, float]]] = {}
        for failure_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[failure_type] = [
                (re.compile(pattern, re.IGNORECASE), confidence)
                for pattern, confidence in patterns
            ]

    def classify(self, log_content: str) -> Optional[ClassificationResult]:
        """
        Classify a failure log.

        Args:
            log_content: The failure log text

        Returns:
            ClassificationResult or None if no match found
        """
        if not log_content:
            return None

        best_match: Optional[Tuple[str, float, List[str]]] = None

        # Try each failure type
        for failure_type, patterns in self.compiled_patterns.items():
            for pattern, base_confidence in patterns:
                matches = pattern.findall(log_content)
                if matches:
                    # Extract matching lines as evidence
                    lines = log_content.split('\n')
                    evidence_lines = [
                        line for line in lines
                        if pattern.search(line)
                    ][:3]  # Limit to 3 evidence lines

                    # Use the highest confidence match for this type
                    if best_match is None or base_confidence > best_match[1]:
                        best_match = (failure_type, base_confidence, evidence_lines)

        if best_match is None:
            return None

        failure_type, confidence, evidence = best_match

        # Determine subtype if applicable
        subtype = self._determine_subtype(failure_type, log_content)

        return ClassificationResult(
            failure_type=failure_type,
            subtype=subtype,
            confidence=confidence,
            evidence=evidence
        )

    def _determine_subtype(self, failure_type: str, log_content: str) -> Optional[str]:
        """Determine a more specific subtype."""
        if failure_type == 'dependency_version_mismatch':
            if 'version that satisfies' in log_content.lower():
                return 'version_not_available'
            elif 'incompatible' in log_content.lower():
                return 'version_incompatible'
        elif failure_type == 'dependency_missing':
            if 'PackageNotFoundError' in log_content:
                return 'package_not_found'
            elif 'ModuleNotFoundError' in log_content:
                return 'module_not_found'
        elif failure_type == 'missing_environment_variable':
            if 'not set' in log_content.lower():
                return 'variable_not_set'
            elif 'required' in log_content.lower():
                return 'variable_required'
        elif failure_type == 'test_assertion_failure':
            if 'AssertionError' in log_content:
                return 'assertion_failed'
        elif failure_type == 'permission_error':
            if 'Permission denied' in log_content:
                return 'access_denied'
            elif 'EACCES' in log_content:
                return 'permission_denied'

        return None


def get_default_classifier() -> FailureClassifier:
    """Get a default classifier instance."""
    return FailureClassifier()

