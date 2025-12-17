"""
Git repository cloning functionality.

Handles secure cloning to temporary directories for analysis.
"""

import os
import subprocess
import tempfile
from typing import Optional
from pathlib import Path


class CloneError(Exception):
    """Raised when git clone operation fails."""
    pass


def clone_repo(repo_url: str, token: Optional[str] = None) -> str:
    """Clone a GitHub repository to a temporary directory.
    
    Creates a secure temporary directory and clones the repository there.
    Supports both public and private repositories (with token).
    
    Args:
        repo_url: Repository URL (HTTPS or SSH format)
        token: Optional GitHub Personal Access Token for private repos.
               If None, uses GITHUB_TOKEN from environment if needed.
    
    Returns:
        Absolute path to the cloned repository directory
        
    Raises:
        CloneError: If the clone operation fails (bad URL, permissions, etc.)
    """
    # Create a secure temporary directory
    # The OS will handle cleanup, but we return the path for the caller to use
    temp_dir = tempfile.mkdtemp(prefix="agent-scans_")
    
    try:
        # Prepare the clone URL
        # If token is provided and URL is HTTPS, inject token for authentication
        clone_url = repo_url
        if token and repo_url.startswith("https://"):
            # Inject token into HTTPS URL: https://token@github.com/owner/repo
            if "://" in repo_url:
                # Extract the part after https://
                url_parts = repo_url.split("://", 1)
                clone_url = f"{url_parts[0]}://{token}@{url_parts[1]}"
        elif not token and repo_url.startswith("https://"):
            # Try to use GITHUB_TOKEN from environment if available
            env_token = os.getenv("GITHUB_TOKEN")
            if env_token:
                url_parts = repo_url.split("://", 1)
                clone_url = f"{url_parts[0]}://{env_token}@{url_parts[1]}"
        
        # Run git clone
        # Capture both stdout and stderr for error reporting
        result = subprocess.run(
            ["git", "clone", clone_url, temp_dir],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown git clone error"
            raise CloneError(
                f"Failed to clone repository '{repo_url}': {error_msg}"
            )
        
        # Verify the directory exists and has content
        if not os.path.exists(temp_dir) or not os.listdir(temp_dir):
            raise CloneError(
                f"Clone appeared to succeed but directory is empty or missing: {temp_dir}"
            )
        
        # Return absolute path
        return os.path.abspath(temp_dir)
        
    except subprocess.TimeoutExpired:
        # Clean up on timeout
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        raise CloneError(f"Git clone timed out after 5 minutes for '{repo_url}'")
    except CloneError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Clean up on unexpected errors
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        raise CloneError(f"Unexpected error during clone: {e}")

