"""
GitHub bridge module for connecting static analysis to live GitHub context.
"""

from .models import (
    GitHubRepo,
    CIContext,
    AgentContext,
    WorkflowRun,
    FailureLog,
)
from .client import GitHubClient, GitHubClientError, MissingTokenError, RepositoryNotFoundError
from .clone import clone_repo, CloneError
from .workflows import WorkflowDiscoverer, WorkflowDiscoveryError
from .logs import LogMiner, LogMiningError
from .context_builder import ContextBuilder
from .bridge import run_bridge, BridgeError

__all__ = [
    # Models
    "GitHubRepo",
    "CIContext",
    "AgentContext",
    "WorkflowRun",
    "FailureLog",
    # Client
    "GitHubClient",
    "GitHubClientError",
    "MissingTokenError",
    "RepositoryNotFoundError",
    # Clone
    "clone_repo",
    "CloneError",
    # Workflows
    "WorkflowDiscoverer",
    "WorkflowDiscoveryError",
    # Logs
    "LogMiner",
    "LogMiningError",
    # Context Builder
    "ContextBuilder",
    # Bridge
    "run_bridge",
    "BridgeError",
]

