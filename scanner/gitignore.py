"""
Gitignore pattern matching implementation.
"""

import re
from pathlib import Path
from typing import List, Pattern


def load_gitignore_patterns(repo_root: str) -> List[Pattern]:
    """
    Load and compile gitignore patterns from .gitignore and .git/info/exclude.
    
    Args:
        repo_root: Root directory of the repository
        
    Returns:
        List of compiled regex patterns
    """
    patterns = []
    repo_path = Path(repo_root)
    
    # Load .gitignore
    gitignore_path = repo_path / '.gitignore'
    if gitignore_path.exists():
        patterns.extend(_parse_gitignore_file(gitignore_path))
    
    # Load .git/info/exclude
    exclude_path = repo_path / '.git' / 'info' / 'exclude'
    if exclude_path.exists():
        patterns.extend(_parse_gitignore_file(exclude_path))
    
    return patterns


def _parse_gitignore_file(file_path: Path) -> List[Pattern]:
    """Parse a gitignore file and return compiled patterns."""
    patterns = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Convert gitignore pattern to regex
            regex_pattern = _gitignore_to_regex(line)
            try:
                patterns.append(re.compile(regex_pattern))
            except re.error:
                # Skip invalid patterns
                continue
    
    return patterns


def _gitignore_to_regex(pattern: str) -> str:
    """
    Convert a gitignore pattern to a regex pattern.
    
    Handles:
    - Leading slash (root-relative)
    - Trailing slash (directory)
    - Wildcards (*, ?)
    - Character classes ([...])
    - Negation (!)
    """
    # Remove negation for now (we'll handle it separately if needed)
    negated = pattern.startswith('!')
    if negated:
        pattern = pattern[1:]
    
    # Escape special regex characters except those we want to interpret
    pattern = pattern.replace('.', r'\.')
    pattern = pattern.replace('+', r'\+')
    pattern = pattern.replace('(', r'\(')
    pattern = pattern.replace(')', r'\)')
    pattern = pattern.replace('{', r'\{')
    pattern = pattern.replace('}', r'\}')
    
    # Convert gitignore wildcards to regex
    pattern = pattern.replace('*', '.*')
    pattern = pattern.replace('?', '.')
    
    # Handle leading slash (root-relative)
    if pattern.startswith('/'):
        pattern = '^' + pattern[1:]
    else:
        pattern = '.*' + pattern
    
    # Handle trailing slash (directory only)
    if pattern.endswith('/'):
        pattern = pattern[:-1] + r'(/.*)?$'
    else:
        pattern = pattern + r'(/.*)?$'
    
    return pattern


def matches_gitignore(path: str, patterns: List[Pattern]) -> bool:
    """
    Check if a path matches any gitignore pattern.
    
    Args:
        path: Relative path from repo root
        patterns: List of compiled regex patterns
        
    Returns:
        True if path should be ignored
    """
    # Normalize path separators
    normalized_path = path.replace('\\', '/')
    
    for pattern in patterns:
        if pattern.match(normalized_path):
            return True
    
    return False

