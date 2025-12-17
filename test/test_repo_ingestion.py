import os
from dotenv import load_dotenv
from github_bridge.client import GitHubClient
from github_bridge.clone import clone_repo

load_dotenv()

# 1. Setup
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ Error: GITHUB_TOKEN not found in environment.")
    exit(1)

repo_url = "https://github.com/ericmay33/AI-DevOps-Agent"

print(f"🔄 Testing Bridge for: {repo_url}\n")

# 2. Test Client & Auth
try:
    client = GitHubClient(token)
    repo_model = client.get_repo(repo_url)
    print(f"✅ Auth Success! Connected to: {repo_model.full_name} (Default Branch: {repo_model.default_branch})\n")
except Exception as e:
    print(f"❌ Client Failed: {e}")
    exit(1)

# 3. Test Cloning
try:
    print("⬇️  Attempting clone (this may take a few seconds)...")
    local_path = clone_repo(repo_url)
    print(f"✅ Clone Success! Repository materialized at: {local_path}")
    
    # Verify file existence
    if os.path.exists(os.path.join(local_path, "README.md")):
        print("✅ (Confirmed README.md exists on disk)\n")
    else:
        print("❌ (Warning: Clone finished but README.md not found?)\n")
        
except Exception as e:
    print(f"❌ Clone Failed: {e}")
    exit(1)

print("FINISHED: Phase 1 Complete. The Bridge is stable.")