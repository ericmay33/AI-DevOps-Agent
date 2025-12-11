"""
Data models for the repository scanner.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum

# Constants
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB


class ArtifactType(str, Enum):
    """Recognized artifact types."""
    WORKFLOW = "workflow"
    DOCKERFILE = "dockerfile"
    DEPENDENCY_MANIFEST = "dependency_manifest"
    CONFIG = "config"
    IAC = "iac"
    SOURCE = "source"
    GENERIC = "generic"


@dataclass
class FileInfo:
    """Represents a file discovered during scanning."""
    path: str
    relative_path: str
    size: int
    modified_time: datetime
    is_binary: bool
    extension: str
    initial_type: str
    symlink_depth: int = 0


@dataclass
class FileInventory:
    """Collection of files discovered in the repository."""
    files: List[FileInfo] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)
    total_size: int = 0
    file_count: int = 0
    
    def add(self, file_info: FileInfo):
        """Add a file to the inventory."""
        self.files.append(file_info)
        self.total_size += file_info.size
        self.file_count += 1


@dataclass
class Artifact:
    """Represents a classified repository artifact."""
    id: str
    type: ArtifactType
    subtype: str
    path: str
    name: str
    metadata: Dict[str, Any]
    content: Dict[str, Any]
    relationships: Dict[str, List[str]] = field(default_factory=lambda: {
        "depends_on": [],
        "used_by": [],
        "references": []
    })
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    extracted_at: datetime = field(default_factory=datetime.now)
    is_metadata_only: bool = False


@dataclass
class ArtifactCollection:
    """Collection of classified artifacts."""
    artifacts: List[Artifact] = field(default_factory=list)
    
    def add(self, artifact: Artifact):
        """Add an artifact to the collection."""
        self.artifacts.append(artifact)
    
    def filter(self, **kwargs) -> List[Artifact]:
        """Filter artifacts by attributes."""
        results = self.artifacts
        for key, value in kwargs.items():
            results = [a for a in results if getattr(a, key, None) == value]
        return results
    
    def get_by_id(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID."""
        for artifact in self.artifacts:
            if artifact.id == artifact_id:
                return artifact
        return None


@dataclass
class RelationshipGraph:
    """Graph of relationships between artifacts."""
    relationships: Dict[str, List[tuple]] = field(default_factory=dict)
    
    def add_relationship(self, from_id: str, relation_type: str, to_id: str):
        """Add a relationship between two artifacts."""
        if from_id not in self.relationships:
            self.relationships[from_id] = []
        self.relationships[from_id].append((relation_type, to_id))

