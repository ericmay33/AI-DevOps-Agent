"""
Data models for the GitHub bridge module.

Uses Pydantic for easy JSON serialization to LLM context.
"""

from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field


class GitHubRepo(BaseModel):
    """Represents a GitHub repository."""
    full_name: str = Field(..., description="Repository full name with owner")
    default_branch: str = Field(default="main", description="Default branch name")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "full_name": "octocat/Hello-World",
                "default_branch": "main"
            }
        }


class WorkflowRun(BaseModel):
    """Represents a GitHub Actions workflow run."""
    run_id: int = Field(..., description="Unique workflow run ID")
    name: str = Field(..., description="Workflow run name (e.g., 'CI Build')")
    conclusion: str = Field(..., description="Run conclusion (e.g., 'success', 'failure', 'cancelled')")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "run_id": 123456789,
                "name": "CI Build",
                "conclusion": "failure"
            }
        }


class FailureLog(BaseModel):
    """Represents a failure log from a CI/CD job."""
    job_name: str = Field(..., description="Name of the job that failed")
    step_name: Optional[str] = Field(default=None, description="Name of the step that failed (if available)")
    log_content: str = Field(..., description="The actual error log text")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "job_name": "test",
                "step_name": "Run tests",
                "log_content": "Error: Test failed\nAssertionError: expected True but got False"
            }
        }


class CIContext(BaseModel):
    """CI/CD workflow run data and failure logs.
    
    Contains workflow runs and extracted failure logs for agent analysis.
    """
    platform: Optional[str] = Field(default=None, description="CI platform (e.g., 'github_actions')")
    recent_runs: List[WorkflowRun] = Field(default_factory=list, description="Recent workflow runs")
    failure_logs: Optional[List[FailureLog]] = Field(default=None, description="Extracted failure logs from failed runs")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional CI context data")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "platform": "github_actions",
                "recent_runs": [],
                "failure_logs": [],
                "data": {}
            }
        }


class AgentContext(BaseModel):
    """Master context object for the DevOps Agent.
    
    Combines repository metadata, static analysis results, and CI context.
    """
    repo: GitHubRepo = Field(..., description="GitHub repository information")
    static_analysis: Dict[str, Any] = Field(default_factory=dict, description="Static analysis results from Sprint 1 scanner")
    ci_context: CIContext = Field(default_factory=CIContext, description="CI/CD runtime context")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "repo": {
                    "full_name": "octocat/Hello-World",
                    "default_branch": "main"
                },
                "static_analysis": {},
                "ci_context": {
                    "platform": None,
                    "data": {}
                }
            }
        }

