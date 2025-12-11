"""
Phase 1: Initial Discovery - File system traversal and inventory building.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Set, Optional

from .models import FileInfo, FileInventory
from .gitignore import load_gitignore_patterns, matches_gitignore


# Path patterns for initial type identification
PATH_PATTERNS = {
    'workflow': [
        r'\.github/workflows/.*\.ya?ml$',
        r'\.gitlab-ci\.ya?ml$',
        r'\.circleci/config\.ya?ml$',
        r'Jenkinsfile$',
        r'\.jenkinsfile$',
        r'azure-pipelines\.ya?ml$',
        r'\.travis\.ya?ml$'
    ],
    'dockerfile': [
        r'Dockerfile$',
        r'Dockerfile\..*$',
        r'.*\.dockerfile$',
        r'docker-compose\.ya?ml$'
    ],
    'dependency_manifest': [
        r'package\.json$',
        r'requirements\.txt$',
        r'pyproject\.toml$',
        r'Pipfile$',
        r'setup\.py$',
        r'pom\.xml$',
        r'build\.gradle$',
        r'build\.gradle\.kts$',
        r'Cargo\.toml$',
        r'go\.mod$',
        r'Gemfile$',
        r'composer\.json$',
        r'pubspec\.yaml$',
        r'.*\.csproj$',
        r'.*\.sln$'
    ],
    'config': [
        r'\.env.*$',
        r'.*\.env$',
        r'config/.*\.(ya?ml|json)$',
        r'.*\.config\.(js|ts)$',
        r'[Mm]akefile$',
        r'\.nvmrc$',
        r'\.node-version$',
        r'\.python-version$',
        r'\.ruby-version$'
    ],
    'iac': [
        r'.*\.tf$',
        r'.*\.tfvars$',
        r'.*\.tf\.json$',
        r'serverless\.ya?ml$',
        r'(k8s|kubernetes|manifests)/.*\.ya?ml$',
        r'.*\.bicep$',
        r'.*\.(cf|cfn)$'
    ]
}

# Extension mapping for fallback type identification
EXTENSION_MAP = {
    '.yml': 'yaml_file',
    '.yaml': 'yaml_file',
    '.json': 'json_file',
    '.toml': 'toml_file',
    '.py': 'source_code',
    '.js': 'source_code',
    '.ts': 'source_code',
    '.go': 'source_code',
    '.rs': 'source_code',
    '.java': 'source_code',
    '.rb': 'source_code',
    '.php': 'source_code',
    '.cpp': 'source_code',
    '.c': 'source_code',
    '.h': 'source_code',
    '.hpp': 'source_code',
    '.cs': 'source_code',
    '.dart': 'source_code',
    '.sh': 'shell_script',
    '.bash': 'shell_script',
    '.zsh': 'shell_script',
    '.fish': 'shell_script',
    '.md': 'markdown',
    '.txt': 'text',
    '.xml': 'xml_file',
    '.html': 'html_file',
    '.css': 'css_file',
}

# Binary file extensions
BINARY_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.bin', '.jpg', '.jpeg', '.png', '.gif',
    '.pdf', '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar', '.deb',
    '.rpm', '.iso', '.img', '.dmg', '.pkg', '.msi', '.woff', '.woff2',
    '.ttf', '.otf', '.eot', '.ico', '.svg', '.mp3', '.mp4', '.avi', '.mov'
}

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB


def initial_discovery(repo_root: str) -> FileInventory:
    """
    Perform initial discovery phase: walk repository and build file inventory.
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        FileInventory containing all discovered files
    """
    inventory = FileInventory()
    gitignore_patterns = load_gitignore_patterns(repo_root)
    visited_symlinks: Set[str] = set()
    repo_path = Path(repo_root).resolve()
    
    def walk_directory(dir_path: Path, symlink_depth: int = 0):
        """Recursively walk directory and process files."""
        if symlink_depth > 3:
            return  # Prevent symlink cycles
        
        try:
            entries = list(dir_path.iterdir())
        except (PermissionError, OSError) as e:
            # Skip directories we can't read
            return
        
        for entry in entries:
            try:
                # Get relative path from repo root
                try:
                    relative_path = str(entry.relative_to(repo_path))
                except ValueError:
                    # Entry is outside repo root (symlink case)
                    continue
                
                # Normalize path separators
                relative_path = relative_path.replace('\\', '/')
                
                # Check gitignore
                if matches_gitignore(relative_path, gitignore_patterns):
                    continue
                
                # Handle symlinks
                if entry.is_symlink():
                    if str(entry.resolve()) in visited_symlinks:
                        continue  # Skip already visited symlinks
                    visited_symlinks.add(str(entry.resolve()))
                    
                    try:
                        target_path = entry.resolve()
                        if target_path.is_dir():
                            walk_directory(target_path, symlink_depth + 1)
                        else:
                            process_file(entry, relative_path, symlink_depth + 1)
                    except (OSError, RuntimeError):
                        # Broken symlink or can't resolve
                        continue
                    continue
                
                # Process files and directories
                if entry.is_dir():
                    inventory.directories.append(relative_path)
                    walk_directory(entry, symlink_depth)
                elif entry.is_file():
                    process_file(entry, relative_path, symlink_depth)
                    
            except (PermissionError, OSError) as e:
                # Skip files we can't access
                continue
    
    def process_file(file_path: Path, relative_path: str, symlink_depth: int):
        """Process a single file and add to inventory."""
        try:
            stat = file_path.stat()
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Get extension
            extension = file_path.suffix.lower()
            
            # Detect binary
            is_binary = detect_binary(file_path, extension)
            
            # Identify initial type
            initial_type = identify_initial_type(relative_path, extension)
            
            file_info = FileInfo(
                path=str(file_path.resolve()),
                relative_path=relative_path,
                size=file_size,
                modified_time=modified_time,
                is_binary=is_binary,
                extension=extension,
                initial_type=initial_type,
                symlink_depth=symlink_depth
            )
            
            inventory.add(file_info)
            
        except (OSError, PermissionError) as e:
            # Skip files we can't read
            pass
    
    # Start walking from repo root
    walk_directory(repo_path)
    
    return inventory


def detect_binary(file_path: Path, extension: str) -> bool:
    """
    Detect if a file is binary.
    
    Args:
        file_path: Path to the file
        extension: File extension
        
    Returns:
        True if file appears to be binary
    """
    # Check extension first
    if extension in BINARY_EXTENSIONS:
        return True
    
    # Read first 512 bytes and check for null bytes
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(512)
            if b'\x00' in chunk:
                return True
            # Try to decode as UTF-8
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except (OSError, PermissionError):
        # If we can't read it, assume binary
        return True


def identify_initial_type(relative_path: str, extension: str) -> str:
    """
    Identify initial file type based on path patterns and extension.
    
    Args:
        relative_path: Relative path from repo root
        extension: File extension
        
    Returns:
        Initial type identifier
    """
    # Normalize path
    normalized_path = relative_path.replace('\\', '/')
    
    # Check path patterns (highest priority)
    for type_name, patterns in PATH_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized_path, re.IGNORECASE):
                return type_name
    
    # Fallback to extension mapping
    if extension in EXTENSION_MAP:
        return EXTENSION_MAP[extension]
    
    # Default
    return 'unknown'

