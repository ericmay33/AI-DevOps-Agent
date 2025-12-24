"""
Data models for failure analysis results.

Uses Pydantic for validation and JSON serialization.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for failures."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class FixAction(str, Enum):
    """Types of fix actions."""
    UPDATE = "update"
    ADD = "add"
    DELETE = "delete"
    CREATE = "create"
    VERIFY = "verify"
    ADD_SECRET = "add_secret"  # For GitHub secrets


class FixStep(BaseModel):
    """A single step in fixing a failure."""
    action: FixAction = Field(..., description="Type of action to take")
    file: str = Field(..., description="File path (relative to repo root)")
    change: str = Field(..., description="Description of the change")
    line: Optional[int] = Field(None, description="Line number (if applicable)")
    description: Optional[str] = Field(None, description="Additional details")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "update",
                "file": "requirements.txt",
                "change": "Change 'pytest==7.0.0' to 'pytest>=7.0.0'",
                "line": 15,
                "description": "Update version constraint"
            }
        }


class AlternativeFix(BaseModel):
    """An alternative approach to fixing the failure."""
    description: str = Field(..., description="Description of the alternative approach")
    pros: List[str] = Field(default_factory=list, description="Advantages")
    cons: List[str] = Field(default_factory=list, description="Disadvantages")

    class Config:
        json_schema_extra = {
            "example": {
                "description": "Pin to specific compatible version",
                "pros": ["More deterministic", "Explicit version"],
                "cons": ["May break again if Python version changes"]
            }
        }


class FailureAnalysis(BaseModel):
    """Complete analysis of a CI/CD failure."""
    failure_type: str = Field(..., description="Primary failure category")
    subtype: Optional[str] = Field(None, description="More specific failure type")
    root_cause: str = Field(..., min_length=10, description="Detailed explanation of why it failed")
    fix_summary: str = Field(..., min_length=10, description="Brief description of the fix")
    severity: Severity = Field(..., description="Severity level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)")
    affected_files: List[str] = Field(default_factory=list, description="Files that need modification")
    evidence: List[str] = Field(default_factory=list, description="Log lines that support the analysis")
    fix_steps: List[FixStep] = Field(default_factory=list, description="Detailed fix instructions")
    contributing_factors: Optional[List[str]] = Field(None, description="Additional contributing factors")
    alternative_fixes: Optional[List[AlternativeFix]] = Field(None, description="Other possible fixes")

    class Config:
        json_schema_extra = {
            "example": {
                "failure_type": "dependency_version_mismatch",
                "subtype": "version_not_available",
                "root_cause": "Package pytest==7.0.0 is not available for Python 3.12",
                "fix_summary": "Update requirements.txt to use flexible version constraint",
                "severity": "Medium",
                "confidence": 0.92,
                "affected_files": ["requirements.txt"],
                "evidence": ["ERROR: Could not find a version..."],
                "fix_steps": [
                    {
                        "action": "update",
                        "file": "requirements.txt",
                        "change": "Change 'pytest==7.0.0' to 'pytest>=7.0.0'",
                        "line": 15
                    }
                ]
            }
        }


class FailureRelationship(BaseModel):
    """Relationship between multiple failures."""
    failure_1: int = Field(..., description="Index of first failure in analyses list")
    failure_2: int = Field(..., description="Index of second failure in analyses list")
    relationship: str = Field(..., description="Type: caused_by, related_to, or independent")


class MultiFailureAnalysis(BaseModel):
    """Analysis of multiple failures."""
    analyses: List[FailureAnalysis] = Field(..., description="Individual failure analyses")
    relationships: Optional[List[FailureRelationship]] = Field(None, description="Relationships between failures")
    fix_priority: Optional[List[int]] = Field(None, description="Indices in order to fix")
    overall_severity: Severity = Field(..., description="Overall severity across all failures")

    class Config:
        json_schema_extra = {
            "example": {
                "analyses": [],
                "relationships": [],
                "fix_priority": [0, 1],
                "overall_severity": "High"
            }
        }

