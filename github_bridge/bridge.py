"""
Main bridge orchestrator for Sprint 2.

Connects repository scanning, GitHub API access, and CI/CD context gathering
into a single pipeline that produces agent-ready context.
"""

import shutil
from typing import Optional

from scanner import RepositoryScanner
from .client import GitHubClient, GitHubClientError, MissingTokenError, RepositoryNotFoundError
from .clone import clone_repo, CloneError
from .workflows import WorkflowDiscoverer, WorkflowDiscoveryError
from .logs import LogMiner, LogMiningError
from .context_builder import ContextBuilder
from .models import AgentContext, CIContext, GitHubRepo


class BridgeError(Exception):
    """Base exception for bridge operations."""
    pass


def run_bridge(repo_url: str, token: Optional[str] = None) -> AgentContext:
    """
    Run the complete bridge pipeline: clone, scan, discover CI, and mine logs.
    
    This is the main orchestrator that:
    1. Authenticates with GitHub
    2. Fetches repository metadata
    3. Clones the repository to a temporary directory
    4. Runs the repository scanner
    5. Discovers workflow runs
    6. Mines failure logs if any exist
    7. Assembles everything into AgentContext
    8. Cleans up temporary files
    
    Args:
        repo_url: GitHub repository URL (HTTPS, SSH, or owner/repo format)
        token: Optional GitHub token (if None, uses GITHUB_TOKEN env var)
        
    Returns:
        AgentContext model containing all gathered information
        
    Raises:
        BridgeError: If any step in the pipeline fails
        MissingTokenError: If GitHub token is not available
        RepositoryNotFoundError: If repository cannot be accessed
        CloneError: If repository cloning fails
    """
    temp_clone_path: Optional[str] = None
    
    try:
        # Step 1: Initialize GitHub Client
        try:
            client = GitHubClient(token=token)
        except MissingTokenError as e:
            raise BridgeError(f"Authentication failed: {e}")
        
        # Step 2: Fetch Repository Info
        try:
            repo_info = client.get_repo(repo_url)
        except (ValueError, RepositoryNotFoundError) as e:
            raise BridgeError(f"Failed to fetch repository info: {e}")
        
        # Step 3: Clone Repository
        try:
            temp_clone_path = clone_repo(repo_url, token=client.token)
        except CloneError as e:
            raise BridgeError(f"Failed to clone repository: {e}")
        
        # Step 4: Run Repository Scanner
        try:
            scanner = RepositoryScanner()
            static_analysis = scanner.scan(temp_clone_path)
        except Exception as e:
            raise BridgeError(f"Repository scanning failed: {e}")
        
        # Step 5: CI Discovery
        workflow_discoverer = WorkflowDiscoverer(client)
        recent_runs = []
        latest_failure = None
        failure_logs = None
        
        try:
            # Get recent workflow runs
            recent_runs = workflow_discoverer.get_recent_runs(repo_info.full_name, limit=10)
            
            # Get latest failure if any
            latest_failure = workflow_discoverer.get_latest_failure(repo_info.full_name)
        except WorkflowDiscoveryError as e:
            # Log warning but don't fail - repo might not have workflows
            print(f"Warning: Could not fetch workflow runs: {e}")
        
        # Step 6: Log Mining (if there's a failure)
        if latest_failure:
            try:
                log_miner = LogMiner(client)
                failure_logs = log_miner.get_failure_logs(
                    repo_info.full_name,
                    latest_failure.run_id
                )
            except LogMiningError as e:
                # Log warning but don't fail - continue without logs
                print(f"Warning: Could not fetch failure logs: {e}")
                failure_logs = []
        
        # Step 7: Build CI Context
        ci_context = CIContext(
            platform="github_actions",
            recent_runs=recent_runs,
            failure_logs=failure_logs,
            data={
                "latest_failure_run_id": latest_failure.run_id if latest_failure else None,
                "total_runs_fetched": len(recent_runs)
            }
        )
        
        # Step 8: Assemble Agent Context using ContextBuilder
        try:
            context_builder = ContextBuilder()
            agent_context = context_builder.build_context(
                repo=repo_info,
                knowledge_model=static_analysis,
                ci_context=ci_context
            )
        except ValueError as e:
            raise BridgeError(f"Failed to build agent context: {e}")
        
        return agent_context
        
    except BridgeError:
        raise
    except Exception as e:
        raise BridgeError(f"Unexpected error in bridge pipeline: {e}")
    
    finally:
        # Step 9: Cleanup - Always remove temp directory
        if temp_clone_path:
            try:
                shutil.rmtree(temp_clone_path, ignore_errors=True)
            except Exception as e:
                # Log but don't fail on cleanup errors
                print(f"Warning: Failed to clean up temporary directory {temp_clone_path}: {e}")

