#!/usr/bin/env python3
"""
Main script to run the repository scanner.
Usage: python scan_repo.py <repo_path_or_url> [output_file]

Examples:
  # Local path
  python scan_repo.py /path/to/repo knowledge/repo_knowledge.json
  
  # GitHub URL (will clone to temp directory)
  python scan_repo.py https://github.com/user/repo knowledge/repo_knowledge.json
"""

import sys
import json
import re
import tempfile
import shutil
import subprocess
from pathlib import Path

from scanner import RepositoryScanner


def is_url(path: str) -> bool:
    """Check if the input is a URL."""
    url_patterns = [
        r'^https?://',
        r'^git@',
        r'^git://',
        r'^ssh://'
    ]
    return any(re.match(pattern, path) for pattern in url_patterns)


def clone_repo(url: str, temp_dir: Path) -> Path:
    """Clone a repository to a temporary directory."""
    print(f"Cloning repository from: {url}")
    try:
        subprocess.run(
            ['git', 'clone', '--depth', '1', url, str(temp_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Repository cloned successfully to: {temp_dir}")
        return temp_dir
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository: {e.stderr}")
        raise
    except FileNotFoundError:
        print("Error: 'git' command not found. Please install Git to clone repositories.")
        raise


def main():
    if len(sys.argv) < 2:
        print("Usage: python scan_repo.py <repo_path_or_url> [output_file]")
        print("\nExamples:")
        print("  # Local path")
        print("  python scan_repo.py /path/to/repo")
        print("  # GitHub URL (will clone automatically)")
        print("  python scan_repo.py https://github.com/user/repo")
        sys.exit(1)
    
    repo_input = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Handle URL vs local path
    temp_clone_dir = None
    repo_path = repo_input
    
    if is_url(repo_input):
        # Clone to temporary directory
        temp_clone_dir = Path(tempfile.mkdtemp(prefix='repo_scan_'))
        try:
            repo_path = clone_repo(repo_input, temp_clone_dir)
        except Exception as e:
            print(f"Failed to clone repository: {e}")
            sys.exit(1)
    else:
        # Validate local repo path
        if not Path(repo_path).exists():
            print(f"Error: Repository path does not exist: {repo_path}")
            sys.exit(1)
        
        if not Path(repo_path).is_dir():
            print(f"Error: Path is not a directory: {repo_path}")
            sys.exit(1)
    
    print(f"Scanning repository: {repo_path}")
    print("Phase 1: Initial Discovery...")
    
    # Create scanner and scan (convert Path to string if needed)
    scanner = RepositoryScanner()
    knowledge = scanner.scan(str(repo_path))
    
    print(f"Phase 2: Classification...")
    print(f"Phase 3: Content Extraction...")
    print(f"\nScan complete!")
    print(f"Found {len(knowledge['artifacts'])} artifacts")
    
    # Output results
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(knowledge, f, indent=2)
        print(f"Results saved to: {output_file}")
    else:
        # Print summary
        print("\nRepository Summary:")
        summary = knowledge['summary']
        print(f"  Primary Language: {summary['primary_language']}")
        print(f"  Project Type: {summary['project_type']}")
        print(f"  CI Platform: {summary['ci_platform']}")
        print(f"  Containerized: {summary['containerization']}")
        print(f"  Dependency Managers: {', '.join(summary['dependency_managers'])}")
        
        print("\nArtifact Breakdown:")
        type_counts = {}
        for artifact in knowledge['artifacts']:
            artifact_type = artifact['type']
            type_counts[artifact_type] = type_counts.get(artifact_type, 0) + 1
        
        for artifact_type, count in sorted(type_counts.items()):
            print(f"  {artifact_type}: {count}")
    
    # Clean up temporary clone if we cloned from URL
    if temp_clone_dir and temp_clone_dir.exists():
        print(f"\nCleaning up temporary clone: {temp_clone_dir}")
        shutil.rmtree(temp_clone_dir)


if __name__ == '__main__':
    main()

