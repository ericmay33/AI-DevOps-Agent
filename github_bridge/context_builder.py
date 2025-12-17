"""
Context builder for merging scanner output with CI context.

Validates and assembles all data sources into the AgentContext model.
"""

import json
from pathlib import Path
from typing import Dict, Any

from .models import AgentContext, GitHubRepo, CIContext


class ContextBuilder:
    """Builds and validates AgentContext from disparate data sources."""
    
    @staticmethod
    def build_context(
        repo: GitHubRepo,
        knowledge_model: Dict[str, Any],
        ci_context: CIContext
    ) -> AgentContext:
        """Build AgentContext from repository info, scanner output, and CI context.
        
        Args:
            repo: GitHubRepo model with repository metadata
            knowledge_model: Dictionary output from RepositoryScanner.scan()
            ci_context: CIContext model with workflow runs and failure logs
            
        Returns:
            Fully populated AgentContext object
            
        Raises:
            ValueError: If inputs are invalid or cannot be merged
        """
        # Validate inputs
        if not isinstance(repo, GitHubRepo):
            raise ValueError(f"repo must be a GitHubRepo instance, got {type(repo)}")
        
        if not isinstance(knowledge_model, dict):
            raise ValueError(f"knowledge_model must be a dict, got {type(knowledge_model)}")
        
        if not isinstance(ci_context, CIContext):
            raise ValueError(f"ci_context must be a CIContext instance, got {type(ci_context)}")
        
        # Ensure knowledge_model is assigned to static_analysis
        # The scanner output is already in the correct format
        static_analysis = knowledge_model
        
        # Build and return AgentContext
        agent_context = AgentContext(
            repo=repo,
            static_analysis=static_analysis,
            ci_context=ci_context
        )
        
        return agent_context
    
    @staticmethod
    def save_to_file(context: AgentContext, filepath: str) -> None:
        """Save AgentContext to a JSON file.
        
        Args:
            context: AgentContext model to save
            filepath: Path to output JSON file
            
        Raises:
            IOError: If file cannot be written
        """
        if not isinstance(context, AgentContext):
            raise ValueError(f"context must be an AgentContext instance, got {type(context)}")
        
        # Convert Pydantic model to dict
        context_dict = context.model_dump(mode='json')
        
        # Ensure directory exists
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON with indentation
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(context_dict, f, indent=2, ensure_ascii=False)
        
        print(f"Agent context saved to: {filepath}")

