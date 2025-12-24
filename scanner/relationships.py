"""
Relationship building between artifacts.
"""

import re
from typing import List, Dict

from .models import ArtifactCollection, RelationshipGraph, Artifact


class RelationshipBuilder:
    """Builds relationships between artifacts."""
    
    def build(self, artifacts: ArtifactCollection) -> RelationshipGraph:
        """
        Build relationship graph from artifacts.
        
        Args:
            artifacts: Collection of classified artifacts
            
        Returns:
            RelationshipGraph with all relationships
        """
        graph = RelationshipGraph()
        
        workflows = artifacts.filter(type='workflow')
        dockerfiles = artifacts.filter(type='dockerfile')
        manifests = artifacts.filter(type='dependency_manifest')
        
        # Build workflow → dockerfile relationships
        for workflow in workflows:
            docker_refs = self._find_docker_references(workflow)
            for docker_ref in docker_refs:
                matching_dockerfile = self._find_matching_dockerfile(
                    docker_ref, dockerfiles
                )
                if matching_dockerfile:
                    graph.add_relationship(
                        workflow.id,
                        'uses',
                        matching_dockerfile.id
                    )
                    workflow.relationships['depends_on'].append(matching_dockerfile.id)
                    matching_dockerfile.relationships['used_by'].append(workflow.id)
        
        # Build workflow → dependency manifest relationships
        for workflow in workflows:
            manifest_refs = self._find_manifest_references(workflow, manifests)
            for manifest in manifest_refs:
                graph.add_relationship(
                    workflow.id,
                    'depends_on',
                    manifest.id
                )
                workflow.relationships['depends_on'].append(manifest.id)
                manifest.relationships['used_by'].append(workflow.id)
        
        # Build dockerfile → dependency manifest relationships
        for dockerfile in dockerfiles:
            manifest_refs = self._find_manifest_in_dockerfile(dockerfile, manifests)
            for manifest in manifest_refs:
                graph.add_relationship(
                    dockerfile.id,
                    'uses',
                    manifest.id
                )
                dockerfile.relationships['depends_on'].append(manifest.id)
                manifest.relationships['used_by'].append(dockerfile.id)
        
        return graph
    
    def _find_docker_references(self, workflow: Artifact) -> List[str]:
        """Find Docker image references in a workflow."""
        docker_refs = []
        content = workflow.content.get('raw', '')
        
        # Look for docker image references in workflow content
        # Pattern: image: <image_name>
        image_pattern = r'image:\s*([^\s\n]+)'
        docker_refs.extend(re.findall(image_pattern, content, re.IGNORECASE))
        
        # Look in structured content (jobs)
        jobs = workflow.metadata.get('jobs', [])
        for job in jobs:
            docker_image = job.get('docker_image', '')
            if docker_image:
                docker_refs.append(docker_image)
        
        return list(set(docker_refs))
    
    def _find_matching_dockerfile(self, docker_ref: str, dockerfiles: List[Artifact]) -> Artifact:
        """Find a Dockerfile that matches a Docker reference."""
        # Extract image name (you have to remove tag)
        image_name = docker_ref.split(':')[0].split('/')[-1]
        
        for dockerfile in dockerfiles:
            # Check if dockerfile path or maybe the name matches
            dockerfile_name = dockerfile.name.lower()
            if image_name.lower() in dockerfile_name or \
               'dockerfile' in dockerfile_name:
                # Check if the base image matchse
                base_image = dockerfile.metadata.get('base_image', '')
                if base_image and image_name.lower() in base_image.lower():
                    return dockerfile
        
        return None
    
    def _find_manifest_references(self, workflow: Artifact, manifests: List[Artifact]) -> List[Artifact]:
        """Find dependency manifest files referenced in a workflow."""
        referenced = []
        content = workflow.content.get('raw', '').lower()
        
        for manifest in manifests:
            manifest_name = manifest.name.lower()
            # Check if workflow content mentions the manifest file
            if manifest_name in content or \
               any(keyword in content for keyword in [
                   'npm install', 'pip install', 'mvn', 'gradle',
                   'go mod', 'bundle install', 'composer install'
               ]):
                referenced.append(manifest)
        
        return referenced
    
    def _find_manifest_in_dockerfile(self, dockerfile: Artifact, manifests: List[Artifact]) -> List[Artifact]:
        """Find dependency manifests referenced in a Dockerfile."""
        referenced = []
        content = dockerfile.content.get('raw', '').lower()
        
        for manifest in manifests:
            manifest_name = manifest.name.lower()
            # Check COPY commands for manifest files
            copy_pattern = rf'copy.*{re.escape(manifest_name)}'
            if re.search(copy_pattern, content, re.IGNORECASE):
                referenced.append(manifest)
        
        return referenced

