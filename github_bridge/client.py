"""
GitHub API client for authenticated repository access.

Handles authentication, URL parsing, and repository metadata retrieval.
"""

import os
import re
from typing import Tuple, Optional
from github import Github
from github.GithubException import GithubException, UnknownObjectException

from .models import GitHubRepo


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""
    pass


class MissingTokenError(GitHubClientError):
    """Raised when GITHUB_TOKEN is not found in environment."""
    pass


class RepositoryNotFoundError(GitHubClientError):
    """Raised when a repository cannot be found."""
    pass


class GitHubClient:
    """Authenticated GitHub API client."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub client.
        
        Args:
            token: GitHub Personal Access Token. If None, loads from GITHUB_TOKEN env var.
            
        Raises:
            MissingTokenError: If token is not provided and GITHUB_TOKEN is not set.
        """
        if token is None:
            token = os.getenv("GITHUB_TOKEN")
        
        if not token:
            raise MissingTokenError(
                "GITHUB_TOKEN environment variable is required. "
                "Set it with: export GITHUB_TOKEN=ghp_xxx"
            )
        
        self.client = Github(token)
        self.token = token
    

    @staticmethod
    def parse_repo_url(url: str) -> Tuple[str, str]:
        """Parse a GitHub repository URL into owner and repository name.
        
        Supports formats:
        - https://github.com/owner/repo
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        - owner/repo
        
        Args:
            url: Repository URL or owner/repo string
            
        Returns:
            Tuple of (owner, repo_name)
            
        Raises:
            ValueError: If URL format is invalid
        """
        """Parse a GitHub repository URL into owner and repository name."""

        def strip_git_suffix(name: str) -> str:
            return name[:-4] if name.endswith(".git") else name

        # owner/repo
        if "/" in url and "github.com" not in url and "@" not in url:
            parts = url.split("/")
            if len(parts) == 2:
                return parts[0], strip_git_suffix(parts[1])

        # SSH: git@github.com:owner/repo.git
        ssh_pattern = r"git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+)"
        ssh_match = re.match(ssh_pattern, url)
        if ssh_match:
            return ssh_match.group("owner"), strip_git_suffix(ssh_match.group("repo"))

        # HTTPS
        https_pattern = r"https?://(?:www\.)?github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$"
        https_match = re.match(https_pattern, url)
        if https_match:
            return https_match.group("owner"), strip_git_suffix(https_match.group("repo"))

        raise ValueError(f"Invalid GitHub repository URL format: {url}")
    

    def get_repo(self, url: str) -> GitHubRepo:
        """Fetch repository metadata from GitHub.
        
        Args:
            url: Repository URL or owner/repo string
            
        Returns:
            GitHubRepo model with repository information
            
        Raises:
            ValueError: If URL format is invalid
            RepositoryNotFoundError: If repository does not exist or is not accessible
            GitHubClientError: For other GitHub API errors
        """
        try:
            owner, repo_name = self.parse_repo_url(url)
        except ValueError as e:
            raise ValueError(f"Failed to parse repository URL: {e}")
        
        try:
            github_repo = self.client.get_repo(f"{owner}/{repo_name}")
            
            return GitHubRepo(
                full_name=f"{owner}/{repo_name}",
                default_branch=github_repo.default_branch
            )
        except UnknownObjectException:
            raise RepositoryNotFoundError(
                f"Repository '{owner}/{repo_name}' not found. "
                "Check that the repository exists and your token has access."
            )
        except GithubException as e:
            raise GitHubClientError(f"GitHub API error: {e}")
        except Exception as e:
            raise GitHubClientError(f"Unexpected error fetching repository: {e}")

