#!/usr/bin/env python3
"""
Main entry point for the AI DevOps Agent bridge.

Orchestrates repository scanning, CI/CD discovery, and log mining
to produce agent-ready context.
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

from github_bridge import (
    run_bridge,
    BridgeError,
    MissingTokenError,
    RepositoryNotFoundError,
    CloneError,
)
from github_bridge.context_builder import ContextBuilder


def print_summary(context):
    """Print a summary of the gathered context.
    
    Args:
        context: AgentContext model
    """
    print("\n" + "="*60)
    print("BRIDGE EXECUTION SUMMARY")
    print("="*60)
    
    # Repository info
    print(f"\nRepository: {context.repo.full_name}")
    print(f"Default Branch: {context.repo.default_branch}")
    
    # Static analysis summary
    static_analysis = context.static_analysis
    artifact_count = len(static_analysis.get('artifacts', []))
    print(f"\nStatic Analysis:")
    print(f"  Artifacts Found: {artifact_count}")
    
    if 'summary' in static_analysis:
        summary = static_analysis['summary']
        print(f"  Primary Language: {summary.get('primary_language', 'unknown')}")
        print(f"  Project Type: {summary.get('project_type', 'unknown')}")
        print(f"  CI Platform: {summary.get('ci_platform', 'none')}")
        print(f"  Containerized: {summary.get('containerization', False)}")
    
    # CI Context summary
    ci_context = context.ci_context
    run_count = len(ci_context.recent_runs)
    print(f"\nCI/CD Context:")
    print(f"  Platform: {ci_context.platform or 'none'}")
    print(f"  Workflow Runs Found: {run_count}")
    
    if ci_context.recent_runs:
        print(f"  Recent Runs:")
        for run in ci_context.recent_runs[:5]:
            status_icon = "❌" if run.conclusion == "failure" else "✅" if run.conclusion == "success" else "⏳"
            print(f"    {status_icon} {run.name} ({run.conclusion})")
    
    if ci_context.failure_logs:
        print(f"  Failure Logs: {len(ci_context.failure_logs)} job(s)")
        for log in ci_context.failure_logs:
            print(f"    - {log.job_name}" + (f" ({log.step_name})" if log.step_name else ""))
    else:
        print(f"  Failure Logs: None")
    
    print("\n" + "="*60)


def main():
    # Load environment variables from .env file
    load_dotenv()


    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI DevOps Agent Bridge - Scan repository and gather CI/CD context",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Basic usage (uses GITHUB_TOKEN from .env)
            python main.py --repo https://github.com/owner/repo
            
            # Specify output file
            python main.py --repo owner/repo --output my_context.json
            
            # Use owner/repo format
            python main.py --repo octocat/Hello-World

            # Override token from command line
            python main.py --repo owner/repo --token ghp_xxx
        """
    )
    
    parser.add_argument(
        '--repo',
        type=str,
        required=True,
        help='Repository URL (HTTPS, SSH, or owner/repo format)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='agent_context.json',
        help='Output file path (default: agent_context.json)'
    )
    
    parser.add_argument(
        '--token',
        type=str,
        default=None,
        help='GitHub Personal Access Token (default: uses GITHUB_TOKEN env var)'
    )
    
    args = parser.parse_args()
    
    # Validate output path
    output_path = Path(args.output)
    if output_path.exists() and not output_path.is_file():
        print(f"Error: Output path exists but is not a file: {args.output}")
        sys.exit(1)
    
    print(f"Starting bridge execution for: {args.repo}")
    print(f"Output will be saved to: {args.output}")
    
    try:
        # Run the bridge pipeline
        context = run_bridge(args.repo, token=args.token)
        
        # Print summary
        print_summary(context)
        
        # Save to file
        ContextBuilder.save_to_file(context, args.output)
        
        print(f"\n✅ Bridge execution completed successfully!")
        sys.exit(0)
        
    except MissingTokenError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("\nPlease either:")
        print("  1. Create a .env file with: GITHUB_TOKEN=ghp_xxx")
        print("  2. Set environment variable: export GITHUB_TOKEN=ghp_xxx")
        print("  3. Pass token via command line: --token ghp_xxx")
        sys.exit(1)
        
    except RepositoryNotFoundError as e:
        print(f"\n❌ Repository Not Found: {e}")
        print("\nPlease check:")
        print("  1. The repository URL is correct")
        print("  2. The repository exists and is accessible")
        print("  3. Your token has access to the repository")
        sys.exit(1)
        
    except CloneError as e:
        print(f"\n❌ Clone Error: {e}")
        print("\nPlease check:")
        print("  1. Git is installed and available")
        print("  2. You have network access to GitHub")
        print("  3. The repository URL is correct")
        sys.exit(1)
        
    except BridgeError as e:
        print(f"\n❌ Bridge Error: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Bridge execution interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
