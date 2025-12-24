"""
Workflow discovery module for GitHub Actions.

Discovers and retrieves workflow run information from GitHub repositories.
"""

from typing import List, Optional
from github.GithubException import GithubException

from .client import GitHubClient, GitHubClientError
from .models import WorkflowRun


class WorkflowDiscoveryError(GitHubClientError):
    """Raised when workflow discovery fails."""
    pass


class WorkflowDiscoverer:
    """Discovers and retrieves GitHub Actions workflow runs."""
    
    def __init__(self, client: GitHubClient):
        """Initialize the workflow discoverer.
        
        Args:
            client: Authenticated GitHubClient instance
        """
        self.client = client
    
    def get_recent_runs(self, repo_name: str, limit: int = 5) -> List[WorkflowRun]:
        """Fetch recent workflow runs for a repository.
        
        Args:
            repo_name: Repository name in format 'owner/repo' or full URL
            limit: Maximum number of runs to return (default: 5)
            
        Returns:
            List of WorkflowRun models
            
        Raises:
            WorkflowDiscoveryError: If workflow runs cannot be fetched
        """
        try:
            # Parse repo name if it's a URL
            if "/" in repo_name and "github.com" not in repo_name and "@" not in repo_name:
                # Already in owner/repo format
                full_name = repo_name
            else:
                # Parse URL to get owner/repo
                owner, repo = self.client.parse_repo_url(repo_name)
                full_name = f"{owner}/{repo}"
            
            # Get the repository object
            github_repo = self.client.client.get_repo(full_name)
            
            # Get workflow runs
            runs = github_repo.get_workflow_runs()[:limit]
            
            workflow_runs = []
            for run in runs:
                try:
                    workflow_run = WorkflowRun(
                        run_id=run.id,
                        name=run.name or "Unknown Workflow",
                        conclusion=run.conclusion or "unknown"
                    )
                    workflow_runs.append(workflow_run)
                except Exception as e:
                    # Skip runs that fail to parse, but log the error
                    continue
            
            return workflow_runs
            
        except GithubException as e:
            raise WorkflowDiscoveryError(f"GitHub API error fetching workflow runs: {e}")
        except Exception as e:
            raise WorkflowDiscoveryError(f"Unexpected error fetching workflow runs: {e}")
    
    def get_latest_failure(self, repo_name: str) -> Optional[WorkflowRun]:
        """Get the most recent failed workflow run.
        
        Args:
            repo_name: Repository name in format 'owner/repo' or full URL
            
        Returns:
            WorkflowRun model for the latest failure, or None if no failures found
            
        Raises:
            WorkflowDiscoveryError: If workflow runs cannot be fetched
        """
        try:
            # Get recent runs (check more than 5 to find a failure)
            runs = self.get_recent_runs(repo_name, limit=20)
            
            # Find the first run with conclusion == 'failure'
            for run in runs:
                if run.conclusion == 'failure':
                    return run
            
            return None
            
        except WorkflowDiscoveryError:
            raise
        except Exception as e:
            raise WorkflowDiscoveryError(f"Unexpected error finding latest failure: {e}")

