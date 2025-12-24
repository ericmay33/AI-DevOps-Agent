# Section 1.2: Scanning Rules - Implementation Plan

## Overview
Section 1.2 defines the rules and constraints that govern how the scanner processes files. While some rules are partially implemented in 1.1, this section makes them robust, configurable, and well-structured.

---

## Requirements from Specification

### 1. Respect `.gitignore`
- Files ignored by git are excluded from scanning
- Must handle `.gitignore` and `.git/info/exclude`
- Support gitignore pattern syntax

### 2. Size Limits
- Files > 1MB are indexed but not fully loaded (metadata only)
- Configurable threshold
- Track which files exceeded limit

### 3. Binary Files
- Detected binary files are skipped
- Exception: Docker images (handled separately - future work)
- Binary detection via extension and content analysis

### 4. Symlinks
- Followed with depth limit of 3 to prevent cycles
- Track visited symlinks to prevent infinite loops
- Handle broken symlinks gracefully

### 5. Hidden Files
- Included if they match recognized patterns (e.g., `.github/workflows/*.yml`)
- Exclude hidden files that don't match patterns
- Pattern matching for important hidden files

---

## Implementation Plan

### Phase 1: Create Scanning Rules Configuration System

**Goal**: Centralize all scanning rules in a configurable, testable system.

**Components**:
1. `ScanningRules` class - Configuration object
2. `RuleEngine` class - Applies rules to files
3. Rule validators - Check if files pass rules

**Features**:
- Configurable thresholds (size limits, symlink depth)
- Rule enable/disable flags
- Pattern matching for hidden files
- Binary file detection configuration

### Phase 2: Enhance Existing Implementations

**Current State** (from 1.1):
- ✅ Basic gitignore support
- ✅ Size limit check (hardcoded 1MB)
- ✅ Binary detection (basic)
- ✅ Symlink handling (basic depth limit)
- ⚠️ Hidden files (partially handled)

**Enhancements Needed**:
1. **Gitignore**: Better pattern matching, handle edge cases
2. **Size Limits**: Make configurable, better tracking
3. **Binary Files**: Improved detection, special case handling
4. **Symlinks**: Better cycle detection, visited tracking
5. **Hidden Files**: Explicit pattern-based inclusion rules

### Phase 3: Rule Application Integration

**Integration Points**:
- Discovery phase: Apply rules during file traversal
- Classification phase: Skip files that violate rules
- Content extraction: Apply size limits

---

## Detailed Design

### 1. ScanningRules Configuration Class

```python
@dataclass
class ScanningRules:
    # Size limits
    max_file_size: int = 1 * 1024 * 1024  # 1MB
    max_total_size: Optional[int] = None   # Optional total repo size limit
    
    # Binary files
    skip_binary_files: bool = True
    binary_extensions: Set[str] = field(default_factory=lambda: {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.jpg', '.png', ...
    })
    
    # Symlinks
    follow_symlinks: bool = True
    max_symlink_depth: int = 3
    
    # Hidden files
    include_hidden_files: bool = True
    hidden_file_patterns: List[str] = field(default_factory=lambda: [
        r'\.github/.*',
        r'\.gitlab-ci\.ya?ml$',
        r'\.env.*',
        r'\.dockerignore',
        ...
    ])
    
    # Gitignore
    respect_gitignore: bool = True
    additional_ignore_patterns: List[str] = field(default_factory=list)
```

### 2. Rule Engine

```python
class RuleEngine:
    def __init__(self, rules: ScanningRules):
        self.rules = rules
        self.gitignore_matcher = None
        self.visited_symlinks = set()
    
    def should_scan_file(self, file_info: FileInfo, repo_root: str) -> bool:
        """Check if file should be scanned based on all rules."""
        # Check gitignore
        if not self._passes_gitignore(file_info, repo_root):
            return False
        
        # Check hidden files
        if not self._passes_hidden_file_rule(file_info):
            return False
        
        # Check binary files
        if not self._passes_binary_rule(file_info):
            return False
        
        return True
    
    def should_load_content(self, file_info: FileInfo) -> bool:
        """Check if file content should be loaded."""
        # Check size limit
        if file_info.size > self.rules.max_file_size:
            return False
        return True
```

### 3. Hidden File Pattern Matching

**Patterns to Include**:
- `.github/**/*` - GitHub workflows and configs
- `.gitlab-ci.yml` - GitLab CI
- `.env*` - Environment files
- `.dockerignore` - Docker ignore files
- `.circleci/**/*` - CircleCI configs
- `.travis.yml` - Travis CI
- `.nvmrc`, `.node-version` - Node version files
- `.python-version`, `.ruby-version` - Language version files

**Patterns to Exclude**:
- `.git/**/*` - Git internals (except .gitignore, .git/info/exclude)
- `.*` - Other hidden files that don't match patterns

### 4. Enhanced Binary Detection

**Methods**:
1. Extension-based (fast)
2. Content-based (read first bytes, check for null bytes)
3. MIME type detection (future enhancement)

**Special Cases**:
- Docker images (future: extract metadata)
- Lock files (package-lock.json, etc.) - should be scanned
- Binary configs (future: handle special formats)

### 5. Symlink Cycle Prevention

**Strategy**:
1. Track resolved symlink targets (not just paths)
2. Depth counter per symlink chain
3. Skip if already visited in current chain
4. Handle broken symlinks gracefully

---

## Implementation Structure

```
scanner/
  rules.py              # ScanningRules class and RuleEngine
  discovery.py         # Updated to use RuleEngine
  extraction.py        # Updated to use size limits from rules
```

---

## Testing Strategy

1. **Gitignore Tests**:
   - Test various gitignore patterns
   - Test nested .gitignore files
   - Test .git/info/exclude

2. **Size Limit Tests**:
   - Files exactly at limit
   - Files over limit
   - Very large files

3. **Binary Detection Tests**:
   - Various binary extensions
   - Text files that look binary
   - Edge cases

4. **Symlink Tests**:
   - Simple symlinks
   - Symlink cycles
   - Broken symlinks
   - Nested symlinks

5. **Hidden File Tests**:
   - Hidden files matching patterns
   - Hidden files not matching patterns
   - Various hidden file scenarios

---

## Definition of Done

- [ ] `ScanningRules` class with all configuration options
- [ ] `RuleEngine` class that applies rules
- [ ] Enhanced gitignore pattern matching
- [ ] Configurable size limits
- [ ] Improved binary file detection
- [ ] Better symlink cycle prevention
- [ ] Hidden file pattern-based inclusion
- [ ] Integration with discovery and extraction phases
- [ ] Unit tests for all rule types
- [ ] Documentation and examples

---

**Status**: Plan Complete - Ready for Implementation

