# Section 1.1: Scanning Approach - Detailed Implementation Specification

## Overview
This document provides the detailed implementation specification for the three-phase scanning approach. It includes algorithms, data structures, and step-by-step processes for Eric to implement.

---

## Phase 1: Initial Discovery Phase

### Objective
Walk the entire repository tree, build a file inventory, and perform initial file type identification.

### Algorithm

```
function initialDiscovery(repoRoot: string) -> FileInventory:
    inventory = new FileInventory()
    gitignorePatterns = loadGitignorePatterns(repoRoot)
    visitedSymlinks = new Set()
    
    function walkDirectory(dirPath: string, depth: int = 0, symlinkDepth: int = 0):
        if symlinkDepth > 3:
            return  // Prevent symlink cycles
        
        for each entry in listDirectory(dirPath):
            fullPath = join(dirPath, entry.name)
            relativePath = getRelativePath(fullPath, repoRoot)
            
            // Check gitignore
            if matchesGitignore(relativePath, gitignorePatterns):
                continue
            
            // Handle symlinks
            if isSymlink(fullPath):
                if fullPath in visitedSymlinks:
                    continue  // Skip already visited symlinks
                visitedSymlinks.add(fullPath)
                targetPath = resolveSymlink(fullPath)
                if isDirectory(targetPath):
                    walkDirectory(targetPath, depth + 1, symlinkDepth + 1)
                else:
                    processFile(fullPath, relativePath, symlinkDepth + 1)
                continue
            
            // Process files and directories
            if isDirectory(fullPath):
                walkDirectory(fullPath, depth + 1, symlinkDepth)
            else:
                processFile(fullPath, relativePath, symlinkDepth)
    
    function processFile(fullPath: string, relativePath: string, symlinkDepth: int):
        fileInfo = {
            path: fullPath,
            relativePath: relativePath,
            size: getFileSize(fullPath),
            modifiedTime: getModifiedTime(fullPath),
            isBinary: detectBinary(fullPath),
            extension: getExtension(fullPath),
            initialType: identifyInitialType(fullPath, relativePath)
        }
        
        inventory.add(fileInfo)
    
    walkDirectory(repoRoot)
    return inventory
```

### Data Structures

#### FileInventory
```python
class FileInventory:
    files: List[FileInfo]
    directories: List[str]
    totalSize: int
    fileCount: int
    
class FileInfo:
    path: str                    # Absolute path
    relativePath: str           # Path relative to repo root
    size: int                   # File size in bytes
    modifiedTime: datetime      # Last modification time
    isBinary: bool              # Binary file detection result
    extension: str              # File extension (e.g., ".yml")
    initialType: str            # Initial type guess (see below)
    symlinkDepth: int           # Depth if reached via symlink
```

### Initial Type Identification

The `identifyInitialType()` function performs a quick classification based on:

1. **Path Patterns** (highest priority):
   ```python
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
   ```

2. **Extension Mapping** (fallback):
   ```python
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
       # ... etc
   }
   ```

3. **Content Sniffing** (for files without clear patterns):
   - Read first 512 bytes
   - Check for shebang (`#!/`)
   - Check for common file signatures (YAML, JSON, etc.)

### Binary File Detection

```python
def detectBinary(filePath: str) -> bool:
    # Method 1: Check file extension against known binary extensions
    binary_extensions = {'.exe', '.dll', '.so', '.dylib', '.bin', '.jpg', 
                         '.png', '.gif', '.pdf', '.zip', '.tar', '.gz'}
    if getExtension(filePath) in binary_extensions:
        return True
    
    # Method 2: Read first 512 bytes and check for null bytes
    try:
        with open(filePath, 'rb') as f:
            chunk = f.read(512)
            if b'\x00' in chunk:
                return True
            # Check for text encoding
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except:
        return True  # Assume binary if can't read
```

### Gitignore Handling

```python
def loadGitignorePatterns(repoRoot: str) -> List[Pattern]:
    patterns = []
    gitignorePath = join(repoRoot, '.gitignore')
    
    if exists(gitignorePath):
        with open(gitignorePath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Convert gitignore pattern to regex
                    pattern = gitignoreToRegex(line)
                    patterns.append(pattern)
    
    # Also check .git/info/exclude
    excludePath = join(repoRoot, '.git', 'info', 'exclude')
    if exists(excludePath):
        # Same processing as .gitignore
    
    return patterns

def matchesGitignore(path: str, patterns: List[Pattern]) -> bool:
    for pattern in patterns:
        if pattern.match(path):
            return True
    return False
```

---

## Phase 2: Classification Phase

### Objective
Categorize files into recognized artifact types, extract metadata, and build relationships.

### Algorithm

```
function classificationPhase(inventory: FileInventory) -> ArtifactCollection:
    artifacts = new ArtifactCollection()
    classifiers = [
        new WorkflowClassifier(),
        new DockerfileClassifier(),
        new DependencyManifestClassifier(),
        new ConfigFileClassifier(),
        new IacClassifier(),
        new SourceCodeClassifier()
    ]
    
    for each fileInfo in inventory.files:
        // Skip binary files (except special cases)
        if fileInfo.isBinary and not isSpecialBinary(fileInfo):
            continue
        
        // Skip files over size limit (metadata only)
        if fileInfo.size > MAX_FILE_SIZE:
            artifact = createMetadataOnlyArtifact(fileInfo)
            artifacts.add(artifact)
            continue
        
        // Try each classifier in priority order
        artifact = null
        for classifier in classifiers:
            if classifier.canHandle(fileInfo):
                artifact = classifier.classify(fileInfo)
                break
        
        // If no classifier matched, create generic artifact
        if artifact is null:
            artifact = createGenericArtifact(fileInfo)
        
        artifacts.add(artifact)
    
    // Build relationships
    relationshipBuilder = new RelationshipBuilder()
    relationships = relationshipBuilder.build(artifacts)
    
    return artifacts, relationships
```

### Classifier Interface

```python
class ArtifactClassifier:
    def canHandle(self, fileInfo: FileInfo) -> bool:
        """Check if this classifier can handle this file"""
        raise NotImplementedError
    
    def classify(self, fileInfo: FileInfo) -> Artifact:
        """Classify file and extract metadata"""
        raise NotImplementedError
    
    def getPriority(self) -> int:
        """Return priority (lower = higher priority)"""
        raise NotImplementedError
```

### Classification Priority Order

1. WorkflowClassifier (priority: 1)
2. DependencyManifestClassifier (priority: 2)
3. DockerfileClassifier (priority: 3)
4. IacClassifier (priority: 4)
5. ConfigFileClassifier (priority: 5)
6. SourceCodeClassifier (priority: 6)

### Example: Workflow Classifier

```python
class WorkflowClassifier(ArtifactClassifier):
    def canHandle(self, fileInfo: FileInfo) -> bool:
        patterns = [
            r'\.github/workflows/.*\.ya?ml$',
            r'\.gitlab-ci\.ya?ml$',
            # ... other patterns
        ]
        return any(re.match(p, fileInfo.relativePath) for p in patterns)
    
    def classify(self, fileInfo: FileInfo) -> Artifact:
        content = readFile(fileInfo.path)
        parsed = parseYaml(content)  # or parseYaml with error handling
        
        metadata = {
            'platform': self.detectPlatform(fileInfo.relativePath),
            'workflow_name': parsed.get('name', ''),
            'workflow_id': self.extractWorkflowId(parsed),
            'triggers': self.extractTriggers(parsed),
            'jobs': self.extractJobs(parsed),
            'env_vars': self.extractEnvVars(parsed),
            'secrets': self.extractSecrets(parsed)
        }
        
        return Artifact(
            id=generateId(fileInfo.relativePath),
            type='workflow',
            subtype=metadata['platform'],
            path=fileInfo.relativePath,
            name=metadata['workflow_name'],
            metadata=metadata,
            content={'raw': content, 'structured': parsed}
        )
    
    def extractJobs(self, yaml: dict) -> List[dict]:
        jobs = []
        for jobId, jobDef in yaml.get('jobs', {}).items():
            job = {
                'job_id': jobId,
                'name': jobDef.get('name', jobId),
                'runs_on': jobDef.get('runs-on', ''),
                'steps': self.extractSteps(jobDef),
                'needs': jobDef.get('needs', []),
                'docker_image': self.extractDockerImage(jobDef)
            }
            jobs.append(job)
        return jobs
```

### Relationship Building

```python
class RelationshipBuilder:
    def build(self, artifacts: ArtifactCollection) -> RelationshipGraph:
        graph = RelationshipGraph()
        
        # Build workflow → dockerfile relationships
        workflows = artifacts.filter(type='workflow')
        dockerfiles = artifacts.filter(type='dockerfile')
        
        for workflow in workflows:
            # Find docker image references in workflow
            dockerRefs = self.findDockerReferences(workflow)
            for dockerRef in dockerRefs:
                matchingDockerfile = self.findMatchingDockerfile(
                    dockerRef, dockerfiles
                )
                if matchingDockerfile:
                    graph.addRelationship(
                        workflow.id, 
                        'uses', 
                        matchingDockerfile.id
                    )
        
        # Build workflow → dependency manifest relationships
        manifests = artifacts.filter(type='dependency_manifest')
        for workflow in workflows:
            # Check if workflow references dependency files
            manifestRefs = self.findManifestReferences(workflow, manifests)
            for manifest in manifestRefs:
                graph.addRelationship(
                    workflow.id,
                    'depends_on',
                    manifest.id
                )
        
        # Build dockerfile → dependency manifest relationships
        for dockerfile in dockerfiles:
            # Check COPY commands for dependency files
            manifestRefs = self.findManifestInDockerfile(dockerfile, manifests)
            for manifest in manifestRefs:
                graph.addRelationship(
                    dockerfile.id,
                    'uses',
                    manifest.id
                )
        
        return graph
```

---

## Phase 3: Content Extraction Phase

### Objective
Read and parse file contents, extract structured data, and prepare content for LLM analysis.

### Algorithm

```
function contentExtractionPhase(artifacts: ArtifactCollection) -> EnrichedArtifacts:
    enriched = []
    
    for artifact in artifacts:
        if artifact.isMetadataOnly:
            continue  // Skip large files
        
        // Read raw content
        try:
            rawContent = readFile(artifact.path)
        except Exception as e:
            logError(f"Failed to read {artifact.path}: {e}")
            artifact.content = {'raw': '', 'error': str(e)}
            enriched.append(artifact)
            continue
        
        // Parse structured content based on type
        structured = null
        if artifact.type in ['workflow', 'dockerfile', 'config', 'iac']:
            structured = parseStructuredContent(artifact, rawContent)
        
        // Update artifact with content
        artifact.content = {
            'raw': rawContent,
            'structured': structured
        }
        
        enriched.append(artifact)
    
    return enriched
```

### Structured Content Parsing

```python
def parseStructuredContent(artifact: Artifact, content: str) -> dict:
    if artifact.extension in ['.yml', '.yaml']:
        return parseYaml(content)
    elif artifact.extension == '.json':
        return parseJson(content)
    elif artifact.extension == '.toml':
        return parseToml(content)
    elif artifact.type == 'dockerfile':
        return parseDockerfile(content)
    else:
        return None

def parseYaml(content: str) -> dict:
    try:
        import yaml
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        return {'error': str(e), 'partial': True}

def parseDockerfile(content: str) -> dict:
    # Parse Dockerfile into structured format
    lines = content.split('\n')
    stages = []
    currentStage = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('FROM'):
            if currentStage:
                stages.append(currentStage)
            currentStage = {
                'base_image': extractBaseImage(line),
                'commands': []
            }
        elif currentStage:
            currentStage['commands'].append(line)
    
    if currentStage:
        stages.append(currentStage)
    
    return {
        'stages': stages,
        'exposed_ports': extractExposedPorts(content),
        'env_vars': extractEnvVars(content)
    }
```

### Size Limit Handling

```python
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

def shouldLoadFullContent(fileInfo: FileInfo) -> bool:
    return fileInfo.size <= MAX_FILE_SIZE

def createMetadataOnlyArtifact(fileInfo: FileInfo) -> Artifact:
    # For large files, only store metadata
    return Artifact(
        id=generateId(fileInfo.relativePath),
        type=fileInfo.initialType,
        path=fileInfo.relativePath,
        name=basename(fileInfo.relativePath),
        metadata={
            'size': fileInfo.size,
            'size_exceeded_limit': True
        },
        content={
            'raw': None,
            'metadata_only': True
        }
    )
```

---

## Complete Scanning Flow

```
function scanRepository(repoRoot: string) -> RepositoryKnowledge:
    // Phase 1: Discovery
    inventory = initialDiscovery(repoRoot)
    
    // Phase 2: Classification
    artifacts, relationships = classificationPhase(inventory)
    
    // Phase 3: Content Extraction
    enrichedArtifacts = contentExtractionPhase(artifacts)
    
    // Build final knowledge model
    knowledge = RepositoryKnowledge(
        repository={
            'id': generateRepoId(repoRoot),
            'name': basename(repoRoot),
            'url': getRepoUrl(repoRoot),
            'default_branch': getDefaultBranch(repoRoot),
            'scanned_at': now(),
            'scan_version': '1.0.0'
        },
        artifacts=enrichedArtifacts,
        relationships=relationships,
        summary=generateRepositorySummary(enrichedArtifacts)
    )
    
    return knowledge
```

---

## Error Handling

### File Reading Errors
- Log error but continue scanning
- Mark artifact with error flag
- Include error message in artifact metadata

### Parsing Errors
- Store partial parse results if possible
- Include error in structured content
- Keep raw content for LLM fallback

### Permission Errors
- Skip files that can't be read
- Log warning
- Continue with rest of repository

---

## Performance Considerations

1. **Parallel Processing**: Process files in parallel where possible (with thread safety)
2. **Lazy Loading**: Only read file contents when needed for classification
3. **Caching**: Cache parsed results to avoid re-parsing
4. **Streaming**: For large files, use streaming parsers

---

## Implementation Checklist for Eric

- [ ] Implement `initialDiscovery()` with gitignore support
- [ ] Implement binary file detection
- [ ] Implement symlink handling with depth limit
- [ ] Create `FileInventory` and `FileInfo` data structures
- [ ] Implement initial type identification (path patterns + extensions)
- [ ] Create classifier interface and base class
- [ ] Implement all 6 classifiers (Workflow, Dockerfile, Dependency, Config, IaC, Source)
- [ ] Implement relationship builder
- [ ] Implement content extraction with size limits
- [ ] Implement structured parsing (YAML, JSON, TOML, Dockerfile)
- [ ] Add error handling throughout
- [ ] Add logging for debugging
- [ ] Test with various repository structures

---

**Document Version**: 1.0  
**Status**: Ready for Implementation

