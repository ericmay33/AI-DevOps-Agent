"""
Log mining module for extracting failure logs from GitHub Actions runs.

Extracts and processes job logs to identify errors and failures.
"""

import re
import requests
from typing import List
from github.GithubException import GithubException

from .client import GitHubClient, GitHubClientError
from .models import FailureLog


class LogMiningError(GitHubClientError):
    """Raised when log mining fails."""
    pass


class LogMiner:
    """Extracts and processes failure logs from GitHub Actions workflow runs."""
    
    # Maximum lines to extract from large logs
    MAX_LOG_LINES = 100
    
    # Patterns to identify error lines
    ERROR_PATTERNS = [
        r'Error:',
        r'ERROR',
        r'Exception:',
        r'FAILED',
        r'FAILURE',
        r'Traceback',
        r'AssertionError',
        r'fatal:',
        r'error:',
    ]
    
    def __init__(self, client: GitHubClient):
        """Initialize the log miner.
        
        Args:
            client: Authenticated GitHubClient instance
        """
        self.client = client
    
    def _extract_error_lines(self, log_content: str) -> str:
        """Extract error-relevant lines from log content.
        
        Args:
            log_content: Full log content as string
            
        Returns:
            Extracted error lines or last N lines if log is too large
        """
        lines = log_content.split('\n')
        
        # If log is small enough, return it all
        if len(lines) <= self.MAX_LOG_LINES:
            return log_content
        
        # Try to find error lines first
        error_lines = []
        for line in lines:
            for pattern in self.ERROR_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    error_lines.append(line)
                    break
        
        # If we found error lines, return them (with some context)
        if error_lines:
            # Get indices of error lines
            error_indices = [i for i, line in enumerate(lines) if line in error_lines]
            
            # Collect error lines with context (5 lines before and after)
            result_lines = []
            seen_indices = set()
            
            for idx in error_indices:
                start = max(0, idx - 5)
                end = min(len(lines), idx + 6)
                
                for i in range(start, end):
                    if i not in seen_indices:
                        result_lines.append(lines[i])
                        seen_indices.add(i)
            
            # Limit to MAX_LOG_LINES
            if len(result_lines) > self.MAX_LOG_LINES:
                result_lines = result_lines[-self.MAX_LOG_LINES:]
            
            return '\n'.join(result_lines)
        
        # If no error patterns found, return last N lines
        return '\n'.join(lines[-self.MAX_LOG_LINES:])
    
    def get_failure_logs(self, repo_name: str, run_id: int) -> List[FailureLog]:
        """Fetch and extract failure logs from a workflow run.
        
        Args:
            repo_name: Repository name in format 'owner/repo' or full URL
            run_id: Workflow run ID
            
        Returns:
            List of FailureLog objects containing job names and error text
            
        Raises:
            LogMiningError: If logs cannot be fetched or processed
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
            
            # Get the specific workflow run directly by ID
            target_run = github_repo.get_workflow_run(run_id)
            
            # Get jobs for this run
            jobs = target_run.jobs()
            
            failure_logs = []
            
            for job in jobs:
                # Only process failed jobs
                if job.conclusion == 'failure':
                    try:
                        # Download logs using GitHub API directly
                        log_url = f"https://api.github.com/repos/{full_name}/actions/jobs/{job.id}/logs"
                        
                        headers = {
                            "Authorization": f"token {self.client.token}",
                            "Accept": "application/vnd.github.v3+json"
                        }
                        
                        # GitHub API returns a 302 redirect to the actual log URL
                        # The redirect expires after 1 minute
                        response = requests.get(log_url, headers=headers, timeout=30, allow_redirects=True)
                        
                        if response.status_code == 200:
                            # Individual job logs are returned as plain text
                            log_content = response.text
                            
                            if log_content:
                                # Extract error-relevant lines
                                extracted_log = self._extract_error_lines(log_content)
                                
                                # Get step information if available
                                step_name = None
                                try:
                                    # Try to get steps from the job
                                    if hasattr(job, 'steps') and job.steps:
                                        # Find the first failed step
                                        for step in job.steps:
                                            if hasattr(step, 'conclusion') and step.conclusion == 'failure':
                                                step_name = step.name if hasattr(step, 'name') else None
                                                break
                                except Exception:
                                    # Steps might not be available, continue without step name
                                    pass
                                
                                failure_log = FailureLog(
                                    job_name=job.name,
                                    step_name=step_name,
                                    log_content=extracted_log
                                )
                                failure_logs.append(failure_log)
                            else:
                                # Empty log content
                                failure_log = FailureLog(
                                    job_name=job.name,
                                    step_name=None,
                                    log_content="Log content was empty"
                                )
                                failure_logs.append(failure_log)
                        else:
                            # If we can't download logs, create a placeholder
                            failure_log = FailureLog(
                                job_name=job.name,
                                step_name=None,
                                log_content=f"Failed to download logs: HTTP {response.status_code}"
                            )
                            failure_logs.append(failure_log)
                            
                    except requests.RequestException as e:
                        # Network/request errors
                        failure_log = FailureLog(
                            job_name=job.name,
                            step_name=None,
                            log_content=f"Failed to download logs: {e}"
                        )
                        failure_logs.append(failure_log)
                    except Exception as e:
                        # Log the error but continue processing other jobs
                        print(f"Warning: Failed to process job {job.name}: {e}")
                        continue
            
            return failure_logs
            
        except GithubException as e:
            raise LogMiningError(f"GitHub API error fetching logs: {e}")
        except LogMiningError:
            raise
        except Exception as e:
            raise LogMiningError(f"Unexpected error mining logs: {e}")