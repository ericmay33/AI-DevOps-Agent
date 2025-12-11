"""
Main repository scanner orchestrator.
Implements the complete three-phase scanning approach.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

from .discovery import initial_discovery
from .classifiers import get_classifiers
from .relationships import RelationshipBuilder
from .extraction import content_extraction_phase
from .models import (
    FileInventory,
    ArtifactCollection,
    Artifact,
    ArtifactType,
    RelationshipGraph
)


class RepositoryScanner:
    """
    Main scanner that orchestrates the three-phase scanning approach.
    """
    
    def __init__(self):
        self.classifiers = get_classifiers()
        # Sort classifiers by priority
        self.classifiers.sort(key=lambda c: c.get_priority())
        self.relationship_builder = RelationshipBuilder()
    
    def scan(self, repo_root: str) -> Dict[str, Any]:
        """
        Scan a repository and return the knowledge model.
        
        Args:
            repo_root: Root directory of the repository to scan
            
        Returns:
            Dictionary matching the repository knowledge model schema
        """
        # Phase 1: Initial Discovery
        inventory = initial_discovery(repo_root)
        
        # Phase 2: Classification
        artifacts, relationships = self._classification_phase(inventory)
        
        # Phase 3: Content Extraction
        enriched_artifacts = content_extraction_phase(artifacts)
        
        # Build final knowledge model
        knowledge = self._build_knowledge_model(
            repo_root, enriched_artifacts, relationships
        )
        
        return knowledge
    
    def _classification_phase(
        self, inventory: FileInventory
    ) -> Tuple[ArtifactCollection, RelationshipGraph]:
        """
        Perform classification phase: categorize files and build relationships.
        
        Args:
            inventory: File inventory from discovery phase
            
        Returns:
            Tuple of (ArtifactCollection, RelationshipGraph)
        """
        artifacts = ArtifactCollection()
        
        for file_info in inventory.files:
            # Skip binary files (except special cases)
            if file_info.is_binary and not self._is_special_binary(file_info):
                continue
            
            # Skip files over size limit (metadata only)
            if file_info.size > 1 * 1024 * 1024:  # 1MB
                artifact = self._create_metadata_only_artifact(file_info)
                artifacts.add(artifact)
                continue
            
            # Try each classifier in priority order
            artifact = None
            for classifier in self.classifiers:
                if classifier.can_handle(file_info):
                    artifact = classifier.classify(file_info)
                    break
            
            # If no classifier matched, create generic artifact
            if artifact is None:
                artifact = self._create_generic_artifact(file_info)
            
            artifacts.add(artifact)
        
        # Build relationships
        relationships = self.relationship_builder.build(artifacts)
        
        return artifacts, relationships
    
    def _is_special_binary(self, file_info) -> bool:
        """Check if binary file should be processed (e.g., Docker images)."""
        # For now, skip all binary files
        # Can be extended for special cases
        return False
    
    def _create_metadata_only_artifact(self, file_info) -> Artifact:
        """Create an artifact for large files (metadata only)."""
        return Artifact(
            id=self._generate_artifact_id(file_info.relative_path),
            type=ArtifactType.GENERIC,
            subtype=file_info.initial_type,
            path=file_info.relative_path,
            name=Path(file_info.relative_path).name,
            metadata={
                'size': file_info.size,
                'size_exceeded_limit': True
            },
            content={
                'raw': None,
                'metadata_only': True
            },
            is_metadata_only=True
        )
    
    def _create_generic_artifact(self, file_info) -> Artifact:
        """Create a generic artifact for unclassified files."""
        return Artifact(
            id=self._generate_artifact_id(file_info.relative_path),
            type=ArtifactType.GENERIC,
            subtype=file_info.initial_type,
            path=file_info.relative_path,
            name=Path(file_info.relative_path).name,
            metadata={},
            content={'raw': '', 'structured': None}
        )
    
    def _generate_artifact_id(self, relative_path: str) -> str:
        """Generate a unique ID for an artifact."""
        return hashlib.md5(relative_path.encode()).hexdigest()[:12]
    
    def _build_knowledge_model(
        self,
        repo_root: str,
        artifacts: ArtifactCollection,
        relationships: RelationshipGraph
    ) -> Dict[str, Any]:
        """
        Build the final repository knowledge model.
        
        Args:
            repo_root: Repository root path
            artifacts: Collection of artifacts
            relationships: Relationship graph
            
        Returns:
            Dictionary matching the knowledge model schema
        """
        repo_path = Path(repo_root)
        repo_name = repo_path.name
        
        # Convert artifacts to dict format
        artifacts_list = []
        for artifact in artifacts.artifacts:
            artifacts_list.append({
                'id': artifact.id,
                'type': artifact.type.value if isinstance(artifact.type, ArtifactType) else artifact.type,
                'subtype': artifact.subtype,
                'path': artifact.path,
                'name': artifact.name,
                'metadata': artifact.metadata,
                'content': artifact.content,
                'relationships': artifact.relationships,
                'tags': artifact.tags,
                'summary': artifact.summary,
                'extracted_at': artifact.extracted_at.isoformat()
            })
        
        # Build relationship structure
        relationship_dict = {}
        for from_id, rels in relationships.relationships.items():
            relationship_dict[from_id] = [
                {'type': rel_type, 'to': to_id}
                for rel_type, to_id in rels
            ]
        
        # Generate repository summary
        summary = self._generate_repository_summary(artifacts)
        
        return {
            'repository': {
                'id': self._generate_repo_id(repo_root),
                'name': repo_name,
                'url': '',  # Would need git remote info
                'default_branch': 'main',  # Would need git info
                'scanned_at': datetime.now().isoformat(),
                'scan_version': '1.0.0'
            },
            'artifacts': artifacts_list,
            'relationships': relationship_dict,
            'summary': summary
        }
    
    def _generate_repo_id(self, repo_root: str) -> str:
        """Generate a unique ID for the repository."""
        # Convert Path objects to string
        repo_root_str = str(repo_root)
        return hashlib.md5(repo_root_str.encode()).hexdigest()[:16]
    
    def _generate_repository_summary(self, artifacts: ArtifactCollection) -> Dict[str, Any]:
        """Generate high-level repository summary."""
        # Count artifact types
        type_counts = {}
        languages = set()
        package_managers = set()
        ci_platforms = set()
        
        for artifact in artifacts.artifacts:
            artifact_type = artifact.type.value if isinstance(artifact.type, ArtifactType) else artifact.type
            type_counts[artifact_type] = type_counts.get(artifact_type, 0) + 1
            
            if artifact.type == ArtifactType.DEPENDENCY_MANIFEST:
                pm = artifact.metadata.get('package_manager', '')
                if pm:
                    package_managers.add(pm)
            
            if artifact.type == ArtifactType.WORKFLOW:
                platform = artifact.metadata.get('platform', '')
                if platform:
                    ci_platforms.add(platform)
            
            if artifact.type == ArtifactType.SOURCE:
                lang = artifact.metadata.get('language', '')
                if lang:
                    languages.add(lang)
        
        # Determine primary language
        primary_language = max(languages, key=lambda l: sum(
            1 for a in artifacts.artifacts
            if a.metadata.get('language') == l
        )) if languages else 'unknown'
        
        # Determine project type
        project_type = 'unknown'
        if type_counts.get('workflow', 0) > 0:
            project_type = 'application'
        if type_counts.get('iac', 0) > 0:
            project_type = 'infrastructure'
        
        return {
            'primary_language': primary_language,
            'project_type': project_type,
            'ci_platform': list(ci_platforms)[0] if ci_platforms else 'none',
            'containerization': type_counts.get('dockerfile', 0) > 0,
            'dependency_managers': list(package_managers),
            'infrastructure_tools': list(set(
                a.subtype for a in artifacts.artifacts
                if a.type == ArtifactType.IAC
            ))
        }

