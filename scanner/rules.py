"""
Section 1.2: Scanning Rules
Defines configurable rules that govern file scanning behavior.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Set, List, Optional, Pattern
from collections import defaultdict

from .gitignore import load_gitignore_patterns, matches_gitignore


@dataclass
class ScanningRules:
    """
    Configuration for scanning rules.
    All rules are configurable to allow customization.
    """
    # Size limits
    max_file_size: int = 1 * 1024 * 1024  # 1MB default
    max_total_size: Optional[int] = None   # Optional total repo size limit
    
    # Binary files
    skip_binary_files: bool = True
    binary_extensions: Set[str] = field(default_factory=lambda: {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.jpg', '.jpeg', '.png', '.gif',
        '.pdf', '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar', '.deb',
        '.rpm', '.iso', '.img', '.dmg', '.pkg', '.msi', '.woff', '.woff2',
        '.ttf', '.otf', '.eot', '.ico', '.svg', '.mp3', '.mp4', '.avi', '.mov',
        '.wav', '.flac', '.ogg', '.webm', '.mkv'
    })
    
    # Symlinks
    follow_symlinks: bool = True
    max_symlink_depth: int = 3
    
    # Hidden files
    include_hidden_files: bool = True
    hidden_file_patterns: List[str] = field(default_factory=lambda: [
        r'\.github/.*',                    # GitHub workflows and configs
        r'\.gitlab-ci\.ya?ml$',            # GitLab CI
        r'\.env.*',                        # Environment files
        r'\.dockerignore',                 # Docker ignore
        r'\.circleci/.*',                  # CircleCI configs
        r'\.travis\.ya?ml$',               # Travis CI
        r'\.nvmrc$',                       # Node version
        r'\.node-version$',                # Node version
        r'\.python-version$',               # Python version
        r'\.ruby-version$',               # Ruby version
        r'\.gitignore$',                   # Git ignore
        r'\.git/info/exclude$',            # Git exclude
        r'\.dockerfile$',                  # Dockerfile variants
        r'\.jenkinsfile$',                 # Jenkinsfile
        r'\.editorconfig$',                # Editor config
        r'\.prettierrc.*',                 # Prettier config
        r'\.eslintrc.*',                   # ESLint config
        r'\.babelrc.*',                    # Babel config
    ])
    
    # Gitignore
    respect_gitignore: bool = True
    additional_ignore_patterns: List[str] = field(default_factory=list)
    
    # Special file handling
    always_include_patterns: List[str] = field(default_factory=lambda: [
        r'\.gitignore$',
        r'\.git/info/exclude$',
    ])
    
    # Exclude patterns (even if they match include patterns)
    always_exclude_patterns: List[str] = field(default_factory=lambda: [
        r'\.git/objects/.*',              # Git objects
        r'\.git/refs/.*',                  # Git refs
        r'\.git/logs/.*',                  # Git logs
        r'\.git/hooks/.*',                 # Git hooks (unless needed)
        r'\.git/config$',                  # Git config
        r'\.git/HEAD$',                    # Git HEAD
        r'\.git/description$',             # Git description
        r'\.git/shallow$',                  # Git shallow
        r'node_modules/.*',                # Node modules
        r'\.venv/.*',                      # Python venv
        r'venv/.*',                        # Python venv
        r'\.env$',                         # .env (may contain secrets)
    ])


class RuleEngine:
    """
    Engine that applies scanning rules to files.
    """
    
    def __init__(self, rules: ScanningRules, repo_root: str):
        self.rules = rules
        self.repo_root = Path(repo_root).resolve()
        self.gitignore_patterns: List[Pattern] = []
        self.hidden_patterns: List[Pattern] = []
        self.always_include_patterns: List[Pattern] = []
        self.always_exclude_patterns: List[Pattern] = []
        self.visited_symlinks: Set[str] = set()
        self.symlink_chains: defaultdict = defaultdict(int)  # Track depth per chain
        
        # Load gitignore patterns
        if self.rules.respect_gitignore:
            self.gitignore_patterns = load_gitignore_patterns(str(self.repo_root))
            # Add additional ignore patterns
            for pattern_str in self.rules.additional_ignore_patterns:
                try:
                    self.gitignore_patterns.append(re.compile(pattern_str))
                except re.error:
                    pass
        
        # Compile hidden file patterns
        for pattern_str in self.rules.hidden_file_patterns:
            try:
                self.hidden_patterns.append(re.compile(pattern_str))
            except re.error:
                pass
        
        # Compile always include patterns
        for pattern_str in self.rules.always_include_patterns:
            try:
                self.always_include_patterns.append(re.compile(pattern_str))
            except re.error:
                pass
        
        # Compile always exclude patterns
        for pattern_str in self.rules.always_exclude_patterns:
            try:
                self.always_exclude_patterns.append(re.compile(pattern_str))
            except re.error:
                pass
    
    def should_scan_file(self, file_path: Path, relative_path: str, is_hidden: bool = False) -> tuple[bool, str]:
        """
        Check if a file should be scanned.
        
        Args:
            file_path: Absolute path to the file
            relative_path: Relative path from repo root
            is_hidden: Whether the file is hidden (starts with .)
            
        Returns:
            Tuple of (should_scan: bool, reason: str)
        """
        normalized_path = relative_path.replace('\\', '/')
        
        # Check always exclude patterns first (highest priority)
        for pattern in self.always_exclude_patterns:
            if pattern.search(normalized_path):
                return False, f"Matches always-exclude pattern: {pattern.pattern}"
        
        # Check always include patterns (override other rules)
        for pattern in self.always_include_patterns:
            if pattern.search(normalized_path):
                return True, f"Matches always-include pattern: {pattern.pattern}"
        
        # Check gitignore
        if self.rules.respect_gitignore:
            if matches_gitignore(normalized_path, self.gitignore_patterns):
                return False, "Matches gitignore pattern"
        
        # Check hidden files
        if is_hidden:
            if not self.rules.include_hidden_files:
                return False, "Hidden file and include_hidden_files is False"
            
            # Check if hidden file matches any pattern
            matches_pattern = any(
                pattern.search(normalized_path) for pattern in self.hidden_patterns
            )
            
            if not matches_pattern:
                return False, "Hidden file does not match any include pattern"
        
        return True, "Passes all rules"
    
    def should_load_content(self, file_size: int) -> tuple[bool, str]:
        """
        Check if file content should be loaded.
        
        Args:
            file_size: Size of the file in bytes
            
        Returns:
            Tuple of (should_load: bool, reason: str)
        """
        if file_size > self.rules.max_file_size:
            return False, f"File size ({file_size} bytes) exceeds limit ({self.rules.max_file_size} bytes)"
        
        return True, "Within size limit"
    
    def is_binary_file(self, file_path: Path, extension: str) -> bool:
        """
        Check if a file is binary.
        
        Args:
            file_path: Path to the file
            extension: File extension (with dot)
            
        Returns:
            True if file appears to be binary
        """
        if not self.rules.skip_binary_files:
            return False
        
        # Check extension first (fast)
        if extension.lower() in self.rules.binary_extensions:
            return True
        
        # Check content (read first 512 bytes)
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
    
    def should_follow_symlink(self, symlink_path: Path, current_depth: int) -> tuple[bool, str]:
        """
        Check if a symlink should be followed.
        
        Args:
            symlink_path: Path to the symlink
            current_depth: Current symlink depth in the chain
            
        Returns:
            Tuple of (should_follow: bool, reason: str)
        """
        if not self.rules.follow_symlinks:
            return False, "Symlinks disabled"
        
        if current_depth >= self.rules.max_symlink_depth:
            return False, f"Symlink depth ({current_depth}) exceeds limit ({self.rules.max_symlink_depth})"
        
        # Check if we've already visited this symlink target
        try:
            resolved = symlink_path.resolve()
            resolved_str = str(resolved)
            
            # Check if this creates a cycle
            if resolved_str in self.visited_symlinks:
                # Check if it's in the current chain
                chain_key = f"{symlink_path.parent}_{current_depth}"
                if self.symlink_chains[chain_key] > 0:
                    return False, "Symlink creates a cycle"
            
            # Mark as visited for this chain
            self.visited_symlinks.add(resolved_str)
            chain_key = f"{symlink_path.parent}_{current_depth}"
            self.symlink_chains[chain_key] += 1
            
            return True, "Symlink can be followed"
            
        except (OSError, RuntimeError) as e:
            return False, f"Broken symlink: {str(e)}"
    
    def reset_symlink_tracking(self):
        """Reset symlink tracking (call when starting a new traversal)."""
        self.visited_symlinks.clear()
        self.symlink_chains.clear()
    
    def is_hidden_file(self, relative_path: str) -> bool:
        """
        Check if a file is hidden (starts with .).
        
        Args:
            relative_path: Relative path from repo root
            
        Returns:
            True if file is hidden
        """
        parts = relative_path.replace('\\', '/').split('/')
        return any(part.startswith('.') for part in parts if part)


def get_default_rules() -> ScanningRules:
    """Get default scanning rules."""
    return ScanningRules()


def create_custom_rules(**kwargs) -> ScanningRules:
    """
    Create custom scanning rules with overrides.
    
    Example:
        rules = create_custom_rules(
            max_file_size=2 * 1024 * 1024,  # 2MB
            skip_binary_files=False
        )
    """
    default = get_default_rules()
    return ScanningRules(**{**vars(default), **kwargs})

