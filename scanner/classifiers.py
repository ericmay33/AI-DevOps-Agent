"""
Phase 2: Classification - Artifact classifiers for different file types.
"""

import re
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml

from .models import Artifact, ArtifactType, FileInfo


def generate_artifact_id(relative_path: str) -> str:
    """Generate a unique ID for an artifact based on its path."""
    return hashlib.md5(relative_path.encode()).hexdigest()[:12]


class ArtifactClassifier:
    """Base class for artifact classifiers."""
    
    def can_handle(self, file_info: FileInfo) -> bool:
        """Check if this classifier can handle this file."""
        raise NotImplementedError
    
    def classify(self, file_info: FileInfo) -> Artifact:
        """Classify file and extract metadata."""
        raise NotImplementedError
    
    def get_priority(self) -> int:
        """Return priority (lower = higher priority)."""
        raise NotImplementedError


class WorkflowClassifier(ArtifactClassifier):
    """Classifier for CI/CD workflow files."""
    
    PATTERNS = [
        r'\.github/workflows/.*\.ya?ml$',
        r'\.gitlab-ci\.ya?ml$',
        r'\.circleci/config\.ya?ml$',
        r'Jenkinsfile$',
        r'\.jenkinsfile$',
        r'azure-pipelines\.ya?ml$',
        r'\.travis\.ya?ml$'
    ]
    
    def can_handle(self, file_info: FileInfo) -> bool:
        normalized_path = file_info.relative_path.replace('\\', '/')
        return any(re.search(p, normalized_path, re.IGNORECASE) for p in self.PATTERNS)
    
    def get_priority(self) -> int:
        return 1
    
    def classify(self, file_info: FileInfo) -> Artifact:
        content = self._read_file(file_info.path)
        parsed = self._parse_yaml(content) if content else {}
        
        platform = self._detect_platform(file_info.relative_path)
        metadata = {
            'platform': platform,
            'workflow_name': parsed.get('name', ''),
            'workflow_id': self._extract_workflow_id(parsed, platform),
            'triggers': self._extract_triggers(parsed, platform),
            'jobs': self._extract_jobs(parsed, platform),
            'env_vars': self._extract_env_vars(parsed, platform),
            'secrets': self._extract_secrets(parsed, platform)
        }
        
        return Artifact(
            id=generate_artifact_id(file_info.relative_path),
            type=ArtifactType.WORKFLOW,
            subtype=platform,
            path=file_info.relative_path,
            name=metadata['workflow_name'] or Path(file_info.relative_path).name,
            metadata=metadata,
            content={'raw': content or '', 'structured': parsed}
        )
    
    def _read_file(self, path: str) -> Optional[str]:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except (OSError, PermissionError):
            return None
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError:
            return {}
    
    def _detect_platform(self, path: str) -> str:
        normalized = path.replace('\\', '/').lower()
        if '.github/workflows' in normalized:
            return 'github_actions'
        elif 'gitlab-ci' in normalized:
            return 'gitlab_ci'
        elif '.circleci' in normalized:
            return 'circleci'
        elif 'jenkinsfile' in normalized:
            return 'jenkins'
        elif 'azure-pipelines' in normalized:
            return 'azure_devops'
        elif '.travis' in normalized:
            return 'travis'
        return 'unknown'
    
    def _extract_workflow_id(self, parsed: Dict, platform: str) -> str:
        if platform == 'github_actions':
            return parsed.get('name', '')
        return ''
    
    def _extract_triggers(self, parsed: Dict, platform: str) -> Dict[str, Any]:
        triggers = {}
        if platform == 'github_actions':
            triggers['push'] = parsed.get('on', {}).get('push', {})
            triggers['pull_request'] = parsed.get('on', {}).get('pull_request', {})
            triggers['schedule'] = parsed.get('on', {}).get('schedule', [])
            triggers['workflow_dispatch'] = parsed.get('on', {}).get('workflow_dispatch', False)
        elif platform == 'gitlab_ci':
            triggers['default'] = True
        return triggers
    
    def _extract_jobs(self, parsed: Dict, platform: str) -> List[Dict[str, Any]]:
        jobs = []
        if platform == 'github_actions':
            for job_id, job_def in parsed.get('jobs', {}).items():
                job = {
                    'job_id': job_id,
                    'name': job_def.get('name', job_id),
                    'runs_on': job_def.get('runs-on', ''),
                    'steps': self._extract_steps(job_def),
                    'needs': job_def.get('needs', []),
                    'docker_image': self._extract_docker_image(job_def)
                }
                jobs.append(job)
        return jobs
    
    def _extract_steps(self, job_def: Dict) -> List[Dict[str, Any]]:
        steps = []
        for step in job_def.get('steps', []):
            step_info = {
                'name': step.get('name', ''),
                'type': 'action' if 'uses' in step else 'run',
                'uses': step.get('uses', ''),
                'run': step.get('run', ''),
                'env': step.get('env', {})
            }
            steps.append(step_info)
        return steps
    
    def _extract_docker_image(self, job_def: Dict) -> Optional[str]:
        container = job_def.get('container', {})
        if isinstance(container, str):
            return container
        return container.get('image', '')
    
    def _extract_env_vars(self, parsed: Dict, platform: str) -> List[str]:
        env_vars = []
        # Extract from workflow level
        if 'env' in parsed:
            env_vars.extend(parsed['env'].keys())
        # Extract from jobs
        for job in parsed.get('jobs', {}).values():
            if 'env' in job:
                env_vars.extend(job['env'].keys())
        return list(set(env_vars))
    
    def _extract_secrets(self, parsed: Dict, platform: str) -> List[str]:
        secrets = []
        # Look for ${{ secrets.* }} patterns in content
        content = str(parsed)
        secret_pattern = r'secrets\.(\w+)'
        secrets.extend(re.findall(secret_pattern, content))
        return list(set(secrets))


class DockerfileClassifier(ArtifactClassifier):
    """Classifier for Docker-related files."""
    
    PATTERNS = [
        r'Dockerfile$',
        r'Dockerfile\..*$',
        r'.*\.dockerfile$',
        r'docker-compose\.ya?ml$'
    ]
    
    def can_handle(self, file_info: FileInfo) -> bool:
        normalized_path = file_info.relative_path.replace('\\', '/')
        return any(re.search(p, normalized_path, re.IGNORECASE) for p in self.PATTERNS)
    
    def get_priority(self) -> int:
        return 3
    
    def classify(self, file_info: FileInfo) -> Artifact:
        content = self._read_file(file_info.path)
        
        if 'docker-compose' in file_info.relative_path.lower():
            return self._classify_docker_compose(file_info, content)
        else:
            return self._classify_dockerfile(file_info, content)
    
    def _read_file(self, path: str) -> Optional[str]:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except (OSError, PermissionError):
            return None
    
    def _classify_dockerfile(self, file_info: FileInfo, content: Optional[str]) -> Artifact:
        metadata = {
            'base_image': '',
            'base_image_tag': '',
            'exposed_ports': [],
            'env_vars': [],
            'volume_mounts': [],
            'build_args': [],
            'stages': []
        }
        
        if content:
            metadata.update(self._parse_dockerfile(content))
        
        return Artifact(
            id=generate_artifact_id(file_info.relative_path),
            type=ArtifactType.DOCKERFILE,
            subtype='dockerfile',
            path=file_info.relative_path,
            name=Path(file_info.relative_path).name,
            metadata=metadata,
            content={'raw': content or '', 'structured': None}
        )
    
    def _classify_docker_compose(self, file_info: FileInfo, content: Optional[str]) -> Artifact:
        parsed = self._parse_yaml(content) if content else {}
        
        metadata = {
            'services': list(parsed.get('services', {}).keys()) if parsed else [],
            'version': parsed.get('version', '') if parsed else ''
        }
        
        return Artifact(
            id=generate_artifact_id(file_info.relative_path),
            type=ArtifactType.DOCKERFILE,
            subtype='docker_compose',
            path=file_info.relative_path,
            name=Path(file_info.relative_path).name,
            metadata=metadata,
            content={'raw': content or '', 'structured': parsed}
        )
    
    def _parse_dockerfile(self, content: str) -> Dict[str, Any]:
        lines = content.split('\n')
        stages = []
        current_stage = None
        exposed_ports = []
        env_vars = []
        volume_mounts = []
        build_args = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('#'):
                continue
            
            # FROM command
            if line_stripped.upper().startswith('FROM'):
                if current_stage:
                    stages.append(current_stage)
                parts = line_stripped.split()
                base_image = parts[1] if len(parts) > 1 else ''
                current_stage = {
                    'base_image': base_image,
                    'commands': []
                }
            # EXPOSE command
            elif line_stripped.upper().startswith('EXPOSE'):
                ports = line_stripped.split()[1:]
                exposed_ports.extend(ports)
            # ENV command
            elif line_stripped.upper().startswith('ENV'):
                env_parts = line_stripped.split(maxsplit=2)
                if len(env_parts) > 1:
                    env_vars.append(env_parts[1])
            # VOLUME command
            elif line_stripped.upper().startswith('VOLUME'):
                volumes = line_stripped.split()[1:]
                volume_mounts.extend(volumes)
            # ARG command
            elif line_stripped.upper().startswith('ARG'):
                args = line_stripped.split()[1:]
                build_args.extend(args)
            # Other commands
            elif current_stage:
                current_stage['commands'].append(line_stripped)
        
        if current_stage:
            stages.append(current_stage)
        
        base_image = stages[0]['base_image'] if stages else ''
        base_image_tag = ''
        if ':' in base_image:
            base_image, base_image_tag = base_image.rsplit(':', 1)
        
        return {
            'base_image': base_image,
            'base_image_tag': base_image_tag,
            'exposed_ports': list(set(exposed_ports)),
            'env_vars': list(set(env_vars)),
            'volume_mounts': list(set(volume_mounts)),
            'build_args': list(set(build_args)),
            'stages': stages
        }
    
    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError:
            return {}


class DependencyManifestClassifier(ArtifactClassifier):
    """Classifier for dependency manifest files."""
    
    PATTERNS = {
        'package.json': 'npm',
        'requirements.txt': 'pip',
        'pyproject.toml': 'pip',
        'Pipfile': 'pipenv',
        'setup.py': 'pip',
        'pom.xml': 'maven',
        'build.gradle': 'gradle',
        'build.gradle.kts': 'gradle',
        'Cargo.toml': 'cargo',
        'go.mod': 'go',
        'Gemfile': 'gem',
        'composer.json': 'composer',
        'pubspec.yaml': 'pub'
    }
    
    def can_handle(self, file_info: FileInfo) -> bool:
        filename = Path(file_info.relative_path).name
        return filename in self.PATTERNS or file_info.extension in ['.csproj', '.sln']
    
    def get_priority(self) -> int:
        return 2
    
    def classify(self, file_info: FileInfo) -> Artifact:
        content = self._read_file(file_info.path)
        filename = Path(file_info.relative_path).name
        
        package_manager = self.PATTERNS.get(filename, 'unknown')
        if file_info.extension == '.csproj':
            package_manager = 'nuget'
        elif file_info.extension == '.sln':
            package_manager = 'dotnet'
        
        metadata = {
            'package_manager': package_manager,
            'lock_file_present': False,
            'lock_file_path': '',
            'dependencies': {'direct': []},
            'scripts': {}
        }
        
        if content:
            metadata.update(self._parse_manifest(filename, content, package_manager))
        
        return Artifact(
            id=generate_artifact_id(file_info.relative_path),
            type=ArtifactType.DEPENDENCY_MANIFEST,
            subtype=package_manager,
            path=file_info.relative_path,
            name=filename,
            metadata=metadata,
            content={'raw': content or '', 'structured': self._parse_structured(filename, content)}
        )
    
    def _read_file(self, path: str) -> Optional[str]:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except (OSError, PermissionError):
            return None
    
    def _parse_manifest(self, filename: str, content: str, package_manager: str) -> Dict[str, Any]:
        metadata = {}
        
        if filename == 'package.json':
            parsed = json.loads(content)
            metadata['dependencies'] = {
                'direct': [{'name': k, 'version': v, 'type': 'runtime'} 
                          for k, v in parsed.get('dependencies', {}).items()]
            }
            metadata['scripts'] = parsed.get('scripts', {})
        elif filename == 'requirements.txt':
            deps = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse requirement line (e.g., "package==1.0.0")
                    parts = re.split(r'[=<>!]+', line, 1)
                    name = parts[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else ''
                    deps.append({'name': name, 'version': version, 'type': 'runtime'})
            metadata['dependencies'] = {'direct': deps}
        elif filename == 'go.mod':
            # Simple parsing for go.mod
            deps = []
            for line in content.split('\n'):
                if line.strip().startswith('require '):
                    parts = line.split()
                    if len(parts) >= 2:
                        deps.append({'name': parts[1], 'version': parts[2] if len(parts) > 2 else '', 'type': 'runtime'})
            metadata['dependencies'] = {'direct': deps}
        
        return metadata
    
    def _parse_structured(self, filename: str, content: Optional[str]) -> Optional[Dict[str, Any]]:
        if not content:
            return None
        
        try:
            if filename in ['package.json', 'composer.json']:
                return json.loads(content)
            elif filename in ['pyproject.toml', 'Cargo.toml', 'Pipfile']:
                # Would need tomllib or toml library
                return None
            elif filename in ['pubspec.yaml']:
                return yaml.safe_load(content)
        except (json.JSONDecodeError, yaml.YAMLError):
            return None
        
        return None


class ConfigFileClassifier(ArtifactClassifier):
    """Classifier for configuration files."""
    
    def can_handle(self, file_info: FileInfo) -> bool:
        normalized = file_info.relative_path.replace('\\', '/').lower()
        patterns = [
            r'\.env',
            r'config/.*\.(ya?ml|json)$',
            r'.*\.config\.(js|ts)$',
            r'[Mm]akefile$',
            r'\.nvmrc$',
            r'\.node-version$',
            r'\.python-version$',
            r'\.ruby-version$'
        ]
        return any(re.search(p, normalized) for p in patterns)
    
    def get_priority(self) -> int:
        return 5
    
    def classify(self, file_info: FileInfo) -> Artifact:
        content = self._read_file(file_info.path)
        
        return Artifact(
            id=generate_artifact_id(file_info.relative_path),
            type=ArtifactType.CONFIG,
            subtype=self._detect_config_type(file_info.relative_path),
            path=file_info.relative_path,
            name=Path(file_info.relative_path).name,
            metadata={},
            content={'raw': content or '', 'structured': None}
        )
    
    def _read_file(self, path: str) -> Optional[str]:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except (OSError, PermissionError):
            return None
    
    def _detect_config_type(self, path: str) -> str:
        normalized = path.lower()
        if '.env' in normalized:
            return 'env_file'
        elif 'makefile' in normalized:
            return 'makefile'
        elif '.nvmrc' in normalized or '.node-version' in normalized:
            return 'node_version'
        elif '.python-version' in normalized:
            return 'python_version'
        elif '.ruby-version' in normalized:
            return 'ruby_version'
        else:
            return 'config_file'


class IacClassifier(ArtifactClassifier):
    """Classifier for Infrastructure as Code files."""
    
    PATTERNS = [
        r'.*\.tf$',
        r'.*\.tfvars$',
        r'serverless\.ya?ml$',
        r'(k8s|kubernetes|manifests)/.*\.ya?ml$',
        r'.*\.bicep$'
    ]
    
    def can_handle(self, file_info: FileInfo) -> bool:
        normalized_path = file_info.relative_path.replace('\\', '/')
        return any(re.search(p, normalized_path, re.IGNORECASE) for p in self.PATTERNS)
    
    def get_priority(self) -> int:
        return 4
    
    def classify(self, file_info: FileInfo) -> Artifact:
        content = self._read_file(file_info.path)
        iac_type = self._detect_iac_type(file_info.relative_path)
        
        return Artifact(
            id=generate_artifact_id(file_info.relative_path),
            type=ArtifactType.IAC,
            subtype=iac_type,
            path=file_info.relative_path,
            name=Path(file_info.relative_path).name,
            metadata={'iac_type': iac_type},
            content={'raw': content or '', 'structured': None}
        )
    
    def _read_file(self, path: str) -> Optional[str]:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except (OSError, PermissionError):
            return None
    
    def _detect_iac_type(self, path: str) -> str:
        normalized = path.lower()
        if '.tf' in normalized:
            return 'terraform'
        elif 'serverless' in normalized:
            return 'serverless'
        elif 'k8s' in normalized or 'kubernetes' in normalized or 'manifests' in normalized:
            return 'kubernetes'
        elif '.bicep' in normalized:
            return 'bicep'
        return 'iac'


class SourceCodeClassifier(ArtifactClassifier):
    """Classifier for source code files."""
    
    def can_handle(self, file_info: FileInfo) -> bool:
        # This is a catch-all for files that don't match other classifiers
        # Only handle if it's clearly source code
        source_extensions = {'.py', '.js', '.ts', '.go', '.rs', '.java', '.rb', 
                           '.php', '.cpp', '.c', '.h', '.cs', '.dart'}
        return file_info.extension in source_extensions
    
    def get_priority(self) -> int:
        return 6
    
    def classify(self, file_info: FileInfo) -> Artifact:
        return Artifact(
            id=generate_artifact_id(file_info.relative_path),
            type=ArtifactType.SOURCE,
            subtype=file_info.extension[1:] if file_info.extension else 'source',
            path=file_info.relative_path,
            name=Path(file_info.relative_path).name,
            metadata={'language': file_info.extension[1:] if file_info.extension else 'unknown'},
            content={'raw': '', 'structured': None},
            is_metadata_only=True  # Don't load full source code content
        )


def get_classifiers() -> List[ArtifactClassifier]:
    """Get all classifiers in priority order."""
    return [
        WorkflowClassifier(),
        DependencyManifestClassifier(),
        DockerfileClassifier(),
        IacClassifier(),
        ConfigFileClassifier(),
        SourceCodeClassifier()
    ]

