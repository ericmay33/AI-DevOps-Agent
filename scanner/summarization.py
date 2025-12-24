"""
Section 4: AI Summarization & Tagging
Heuristic summarization and tagging engine with optional LLM hook.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

from .models import Artifact, ArtifactCollection, ArtifactType


@dataclass
class SummarizationConfig:
    """Configuration for summarization and tagging."""
    enabled: bool = False
    provider: str = "heuristic"  # Future: "openai", "anthropic", etc.
    max_preview_chars: int = 2000
    max_tags: int = 10


class SummarizationEngine:
    """Generate summaries and tags for artifacts and repository."""

    def __init__(self, config: SummarizationConfig):
        self.config = config

    def summarize_artifacts(self, artifacts: ArtifactCollection) -> None:
        """
        Populate summary and tags for each artifact in-place.
        Uses heuristics by default; provides hook for LLM providers.
        """
        for artifact in artifacts.artifacts:
            summary, tags = self._summarize_artifact(artifact)
            artifact.summary = summary
            artifact.tags = tags[: self.config.max_tags]

    def summarize_repository(self, knowledge: Dict) -> Dict:
        """
        Create a high-level repository summary based on artifacts.
        Returns a summary dict that can replace knowledge['summary'].
        """
        artifacts = knowledge.get("artifacts", [])
        ci_platforms = set()
        dependency_managers = set()
        languages = set()
        has_container = False
        project_type = "application"
        key_characteristics: List[str] = []

        for artifact in artifacts:
            a_type = artifact.get("type")
            subtype = artifact.get("subtype", "")

            if a_type == "workflow":
                ci_platforms.add(subtype)
                key_characteristics.append("ci-workflow")
            if a_type == "dockerfile":
                has_container = True
                key_characteristics.append("containerized")
            if a_type == "dependency_manifest":
                pm = artifact.get("metadata", {}).get("package_manager")
                if pm:
                    dependency_managers.add(pm)
            if a_type == "source":
                lang = artifact.get("metadata", {}).get("language")
                if lang:
                    languages.add(lang)
            if a_type == "iac":
                project_type = "infrastructure"
                key_characteristics.append("iac-present")

        primary_language = next(iter(languages), "unknown")
        tech_stack = sorted(list(languages | dependency_managers))
        ci_platform = next(iter(ci_platforms), "none")

        return {
            "project_type": project_type,
            "primary_language": primary_language,
            "tech_stack": tech_stack,
            "ci_approach": ci_platform,
            "architecture": "monorepo" if self._is_monorepo(artifacts) else "single_repo",
            "key_characteristics": list(dict.fromkeys(key_characteristics)),
        }

    # ----------------- Helpers -----------------

    def _summarize_artifact(self, artifact: Artifact) -> tuple[str, List[str]]:
        """
        Heuristic artifact summarization and tagging.
        Returns (summary, tags).
        """
        a_type = artifact.type.value if isinstance(artifact.type, ArtifactType) else artifact.type
        subtype = artifact.subtype
        path = artifact.path
        metadata = artifact.metadata or {}

        # Build tags
        tags: List[str] = []
        tags.append(a_type)
        if subtype:
            tags.append(subtype)

        # Type-specific summaries
        summary = ""

        if a_type == "workflow":
            wf_name = metadata.get("workflow_name") or artifact.name
            triggers = metadata.get("triggers", {})
            jobs = metadata.get("jobs", [])
            trigger_keys = [k for k, v in triggers.items() if v]
            summary = f"Workflow {wf_name} with {len(jobs)} jobs; triggers: {', '.join(trigger_keys) or 'manual/default'}."
            tags.extend(["ci-workflow", f"jobs:{len(jobs)}"])
            if trigger_keys:
                tags.extend([f"trigger:{t}" for t in trigger_keys])

        elif a_type == "dockerfile":
            base = metadata.get("base_image", "")
            exposed = metadata.get("exposed_ports", [])
            summary = f"Dockerfile based on {base or 'unspecified'}; exposes {', '.join(exposed) or 'no ports'}."
            tags.extend(["docker", "container"])
            if base:
                tags.append(f"base:{base}")

        elif a_type == "dependency_manifest":
            pm = metadata.get("package_manager", "unknown")
            deps = metadata.get("dependencies", {}).get("direct", [])
            summary = f"Dependency manifest ({pm}) with {len(deps)} direct dependencies."
            tags.extend(["dependencies", f"pm:{pm}"])

        elif a_type == "config":
            summary = f"Configuration file ({subtype or 'config'}) at {path}."
            tags.extend(["config"])

        elif a_type == "iac":
            summary = f"Infrastructure as Code ({subtype or 'iac'}) at {path}."
            tags.extend(["iac"])

        elif a_type == "source":
            lang = metadata.get("language", "code")
            summary = f"Source code file ({lang}) at {path}."
            tags.extend(["source", f"lang:{lang}"])

        else:
            summary = f"File at {path} ({subtype or 'generic'})."
            tags.append("generic")

        # Add tech tags from metadata where obvious
        self._add_metadata_tags(tags, metadata)

        # Deduplicate tags, preserve order
        tags = list(dict.fromkeys(tags))

        return summary, tags

    def _add_metadata_tags(self, tags: List[str], metadata: Dict) -> None:
        # Package manager
        pm = metadata.get("package_manager")
        if pm:
            tags.append(pm)
        # Workflow platform
        platform = metadata.get("platform")
        if platform:
            tags.append(platform)
        # Language
        lang = metadata.get("language")
        if lang:
            tags.append(lang)

    def _is_monorepo(self, artifacts: List[Dict]) -> bool:
        # Simple heuristic: multiple top-level service folders or multiple lockfiles
        lockfiles = 0
        top_levels = set()
        for a in artifacts:
            path = a.get("path", "")
            if path.count("/") == 0:
                continue
            top_levels.add(path.split("/")[0])
            name = a.get("name", "").lower()
            if "package-lock" in name or "yarn.lock" in name or "pnpm-lock" in name:
                lockfiles += 1
        return len(top_levels) > 5 or lockfiles > 1


def get_default_summarization_config() -> SummarizationConfig:
    """Return default summarization config (disabled)."""
    return SummarizationConfig()

