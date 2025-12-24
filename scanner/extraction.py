"""
Phase 3: Content Extraction - Read and parse file contents.
"""

import json
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from .models import Artifact, ArtifactCollection

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB


def content_extraction_phase(artifacts: ArtifactCollection) -> ArtifactCollection:
    """
    Perform content extraction phase: read and parse file contents.
    
    Args:
        artifacts: Collection of classified artifacts
        
    Returns:
        Enriched artifacts with content loaded
    """
    enriched = ArtifactCollection()
    
    for artifact in artifacts.artifacts:
        # Skip if already marked as metadata-only
        if artifact.is_metadata_only:
            enriched.add(artifact)
            continue
        
        # Check file size
        file_path = Path(artifact.path)
        if file_path.exists():
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                # Mark as metadata-only for large files
                artifact.is_metadata_only = True
                artifact.content = {
                    'raw': None,
                    'metadata_only': True,
                    'size': file_size
                }
                enriched.add(artifact)
                continue
        
        # Read raw content
        try:
            raw_content = read_file(artifact.path)
        except Exception as e:
            artifact.content = {
                'raw': '',
                'error': str(e)
            }
            enriched.add(artifact)
            continue
        
        # Parse structured content based on type
        structured = None
        if artifact.type in ['workflow', 'dockerfile', 'config', 'iac']:
            structured = parse_structured_content(artifact, raw_content)
        
        # Update artifact with content
        artifact.content = {
            'raw': raw_content or '',
            'structured': structured
        }
        
        enriched.add(artifact)
    
    return enriched


def read_file(path: str) -> Optional[str]:
    """
    Read file content with error handling.
    
    Args:
        path: Path to file
        
    Returns:
        File content or None if error
    """
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except (OSError, PermissionError, UnicodeDecodeError) as e:
        raise Exception(f"Failed to read file: {e}")


def parse_structured_content(artifact: Artifact, content: str) -> Optional[Dict[str, Any]]:
    """
    Parse structured content based on artifact type and extension.
    
    Args:
        artifact: The artifact to parse
        content: Raw file content
        
    Returns:
        Parsed structured content or None
    """
    if not content:
        return None
    
    extension = Path(artifact.path).suffix.lower()
    
    if extension in ['.yml', '.yaml']:
        return parse_yaml(content)
    elif extension == '.json':
        return parse_json(content)
    elif extension == '.toml':
        # Would need tomllib or toml library
        return None
    elif artifact.type == 'dockerfile':
        return parse_dockerfile(content)
    else:
        return None


def parse_yaml(content: str) -> Optional[Dict[str, Any]]:
    """Parse YAML content."""
    try:
        return yaml.safe_load(content) or {}
    except yaml.YAMLError as e:
        return {'error': str(e), 'partial': True}


def parse_json(content: str) -> Optional[Dict[str, Any]]:
    """Parse JSON content."""
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        return {'error': str(e), 'partial': True}


def parse_dockerfile(content: str) -> Dict[str, Any]:
    """
    Parse Dockerfile into structured format.
    
    Args:
        content: Dockerfile content
        
    Returns:
        Structured representation
    """
    lines = content.split('\n')
    stages = []
    current_stage = None
    exposed_ports = []
    env_vars = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('#'):
            continue
        
        if line_stripped.upper().startswith('FROM'):
            if current_stage:
                stages.append(current_stage)
            parts = line_stripped.split()
            base_image = parts[1] if len(parts) > 1 else ''
            current_stage = {
                'base_image': base_image,
                'commands': []
            }
        elif line_stripped.upper().startswith('EXPOSE'):
            ports = line_stripped.split()[1:]
            exposed_ports.extend(ports)
        elif line_stripped.upper().startswith('ENV'):
            env_parts = line_stripped.split(maxsplit=2)
            if len(env_parts) > 1:
                env_vars.append(env_parts[1])
        elif current_stage:
            current_stage['commands'].append(line_stripped)
    
    if current_stage:
        stages.append(current_stage)
    
    return {
        'stages': stages,
        'exposed_ports': list(set(exposed_ports)),
        'env_vars': list(set(env_vars))
    }

