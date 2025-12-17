import os
import sys
from dotenv import load_dotenv
from github_bridge.client import GitHubClient
from github_bridge.workflows import WorkflowDiscoverer
from github_bridge.logs import LogMiner

load_dotenv()

# 1. Setup
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ Error: GITHUB_TOKEN not found.")
    sys.exit(1)

# Use a repo known to have GitHub Actions (Your own, or a public one)
# Ideally, point this to a repo of yours that has a FAILED run recently.
TEST_REPO_URL = "https://github.com/ericmay33/GitHub-Actions-Test" 

print(f"Investigating GitHub Actions: {TEST_REPO_URL}\n")

try:
    # 2. Connect
    client = GitHubClient(token)
    repo_model = client.get_repo(TEST_REPO_URL)
    full_repo_name = f"{repo_model.owner}/{repo_model.name}"
    
    # 3. Discover Workflows
    print("\nFetching Recent Runs...")
    discoverer = WorkflowDiscoverer(client)
    recent_runs = discoverer.get_recent_runs(full_repo_name, limit=5)
    
    if not recent_runs:
        print("(No recent runs found.)")
    
    for run in recent_runs:
        if run.conclusion == "success":
            icon = "✅"
        else: 
            icon = "❌"
        print(f"{icon} [{run.run_id}] {run.name} ({run.status}): {run.conclusion}")

    # 4. Mine Logs (Find a failure)
    print("\n⛏️ Mining for failure evidence...")
    failed_run = discoverer.get_latest_failure(full_repo_name)
    
    if failed_run:
        print(f"   found failure in run: {failed_run.run_id} ({failed_run.name})")
        
        miner = LogMiner(client)
        print("   Downloading and parsing logs (this extracts 'Error' lines)...")
        logs = miner.get_failure_logs(full_repo_name, failed_run.run_id)
        
        if logs:
            for log in logs:
                print(f"\n   📜 Job: {log.job_name}")
                print(f"   --- LOG SNIPPET ---")
                print(log.log_content[:500] + "..." if len(log.log_content) > 500 else log.log_content)
                print(f"   -------------------")
        else:
            print("   (Run failed, but no specific log snippets matched our extraction rules.)")
            
    else:
        print("No failed runs found!.")
        print("To fully test, push a broken commit to your repo.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()