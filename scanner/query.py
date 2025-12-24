"""
Section 5: LLM Query Interface
Provides query capabilities for the repository knowledge model.
"""

import re
import fnmatch
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field

from .models import ArtifactType


@dataclass
class QueryResult:
    """Result of a query operation."""
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    relationships: Dict[str, Any] = field(default_factory=dict)
    answer: Optional[str] = None
    supporting_artifacts: List[str] = field(default_factory=list)
    confidence: float = 0.0
    query_type: str = ""


class QueryEngine:
    """
    Query engine for repository knowledge model.
    Supports direct artifact queries, semantic queries, and analysis queries.
    """
    
    def __init__(self, knowledge: Dict[str, Any]):
        """
        Initialize query engine with knowledge model.
        
        Args:
            knowledge: Repository knowledge model (from scanner)
        """
        self.knowledge = knowledge
        self.artifacts = knowledge.get('artifacts', [])
        self.relationships = knowledge.get('relationships', {})
        
        # Build indexes for efficient querying
        self._build_indexes()
    
    def _build_indexes(self):
        """Build indexes for efficient querying."""
        self._by_type: Dict[str, List[Dict]] = {}
        self._by_path: Dict[str, Dict] = {}
        self._by_tag: Dict[str, List[Dict]] = {}
        
        for artifact in self.artifacts:
            # Index by type
            artifact_type = artifact.get('type', 'generic')
            if artifact_type not in self._by_type:
                self._by_type[artifact_type] = []
            self._by_type[artifact_type].append(artifact)
            
            # Index by path
            path = artifact.get('path', '')
            self._by_path[path] = artifact
            
            # Index by tags
            tags = artifact.get('tags', [])
            for tag in tags:
                if tag not in self._by_tag:
                    self._by_tag[tag] = []
                self._by_tag[tag].append(artifact)
    
    def query(self, query: Dict[str, Any]) -> QueryResult:
        """
        Execute a query against the knowledge model.
        
        Args:
            query: Query dictionary with 'type' and query-specific fields
            
        Returns:
            QueryResult with query results
        """
        query_type = query.get('type', '')
        
        if query_type == 'artifact_query':
            return self._handle_artifact_query(query)
        elif query_type == 'semantic_query':
            return self._handle_semantic_query(query)
        elif query_type == 'analysis_query':
            return self._handle_analysis_query(query)
        else:
            return QueryResult(
                query_type=query_type,
                answer=f"Unknown query type: {query_type}"
            )
    
    def _handle_artifact_query(self, query: Dict[str, Any]) -> QueryResult:
        """
        Handle direct artifact queries.
        
        Args:
            query: Query dict with 'filters', 'include_content', 'include_relationships'
            
        Returns:
            QueryResult with filtered artifacts
        """
        filters = query.get('filters', {})
        include_content = query.get('include_content', False)
        include_relationships = query.get('include_relationships', False)
        
        # Start with all artifacts or filtered by type
        artifact_type = filters.get('artifact_type', 'all')
        if artifact_type == 'all':
            candidates = self.artifacts.copy()
        else:
            candidates = self._by_type.get(artifact_type, []).copy()
        
        # Apply filters
        filtered = []
        for artifact in candidates:
            if self._matches_filters(artifact, filters):
                filtered.append(artifact)
        
        # Build result artifacts (optionally exclude content)
        result_artifacts = []
        for artifact in filtered:
            result_artifact = {
                'id': artifact.get('id'),
                'type': artifact.get('type'),
                'path': artifact.get('path'),
                'name': artifact.get('name'),
                'summary': artifact.get('summary', ''),
                'tags': artifact.get('tags', []),
                'metadata': artifact.get('metadata', {})
            }
            
            if include_content:
                result_artifact['content'] = artifact.get('content', {})
            
            result_artifacts.append(result_artifact)
        
        # Build relationships if requested
        relationships = {}
        if include_relationships:
            for artifact in filtered:
                artifact_id = artifact.get('id')
                artifact_rels = artifact.get('relationships', {})
                if artifact_rels:
                    relationships[artifact_id] = artifact_rels
        
        return QueryResult(
            query_type='artifact_query',
            artifacts=result_artifacts,
            relationships=relationships
        )
    
    def _matches_filters(self, artifact: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if artifact matches all filters."""
        # Path pattern filter
        path_pattern = filters.get('path_pattern')
        if path_pattern:
            artifact_path = artifact.get('path', '')
            if not fnmatch.fnmatch(artifact_path, path_pattern):
                return False
        
        # Tags filter
        tags_filter = filters.get('tags', [])
        if tags_filter:
            artifact_tags = set(artifact.get('tags', []))
            if not any(tag in artifact_tags for tag in tags_filter):
                return False
        
        # Metadata filter
        metadata_filter = filters.get('metadata', {})
        if metadata_filter:
            artifact_metadata = artifact.get('metadata', {})
            for key, value in metadata_filter.items():
                if artifact_metadata.get(key) != value:
                    return False
        
        return True
    
    def _handle_semantic_query(self, query: Dict[str, Any]) -> QueryResult:
        """
        Handle semantic queries (heuristic keyword matching for now).
        
        Args:
            query: Query dict with 'query', 'limit', 'threshold'
            
        Returns:
            QueryResult with matching artifacts
        """
        query_text = query.get('query', '').lower()
        limit = query.get('limit', 10)
        threshold = query.get('threshold', 0.0)
        
        # Extract keywords from query
        keywords = self._extract_keywords(query_text)
        
        # Score artifacts based on keyword matches
        scored_artifacts = []
        for artifact in self.artifacts:
            score = self._score_artifact_semantic(artifact, keywords)
            if score >= threshold:
                scored_artifacts.append((score, artifact))
        
        # Sort by score (descending) and take top N
        scored_artifacts.sort(key=lambda x: x[0], reverse=True)
        top_artifacts = [artifact for _, artifact in scored_artifacts[:limit]]
        
        # Build result
        result_artifacts = []
        for artifact in top_artifacts:
            result_artifacts.append({
                'id': artifact.get('id'),
                'type': artifact.get('type'),
                'path': artifact.get('path'),
                'name': artifact.get('name'),
                'summary': artifact.get('summary', ''),
                'tags': artifact.get('tags', []),
                'metadata': artifact.get('metadata', {})
            })
        
        return QueryResult(
            query_type='semantic_query',
            artifacts=result_artifacts
        )
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from query text."""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'where', 'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'}
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = {w for w in words if w not in stop_words and len(w) > 2}
        
        return keywords
    
    def _score_artifact_semantic(self, artifact: Dict[str, Any], keywords: Set[str]) -> float:
        """Score artifact based on keyword matches."""
        score = 0.0
        
        # Check summary
        summary = artifact.get('summary', '').lower()
        summary_matches = sum(1 for kw in keywords if kw in summary)
        score += summary_matches * 2.0  # Summary matches weighted higher
        
        # Check tags
        tags = [tag.lower() for tag in artifact.get('tags', [])]
        tag_matches = sum(1 for kw in keywords if any(kw in tag for tag in tags))
        score += tag_matches * 1.5
        
        # Check path
        path = artifact.get('path', '').lower()
        path_matches = sum(1 for kw in keywords if kw in path)
        score += path_matches * 1.0
        
        # Check name
        name = artifact.get('name', '').lower()
        name_matches = sum(1 for kw in keywords if kw in name)
        score += name_matches * 1.0
        
        # Check metadata (platform, package_manager, etc.)
        metadata = artifact.get('metadata', {})
        metadata_str = str(metadata).lower()
        metadata_matches = sum(1 for kw in keywords if kw in metadata_str)
        score += metadata_matches * 0.5
        
        # Normalize score (divide by number of keywords to get 0-1 range)
        if keywords:
            score = score / (len(keywords) * 2.0)  # Normalize to roughly 0-1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _handle_analysis_query(self, query: Dict[str, Any]) -> QueryResult:
        """
        Handle analysis queries (question answering).
        
        Args:
            query: Query dict with 'question' and optional 'context'
            
        Returns:
            QueryResult with answer, supporting artifacts, and confidence
        """
        question = query.get('question', '')
        context = query.get('context', {})
        artifact_ids = context.get('artifact_ids', [])
        relationship_depth = context.get('relationship_depth', 1)
        
        # Parse question to determine intent
        question_lower = question.lower()
        
        # Find relevant artifacts
        relevant_artifacts = self._find_relevant_artifacts(question, artifact_ids, relationship_depth)
        
        # Generate answer based on question type
        answer, confidence = self._generate_answer(question, relevant_artifacts)
        
        # Get supporting artifact IDs
        supporting_ids = [a.get('id') for a in relevant_artifacts]
        
        return QueryResult(
            query_type='analysis_query',
            answer=answer,
            supporting_artifacts=supporting_ids,
            confidence=confidence
        )
    
    def _find_relevant_artifacts(self, question: str, artifact_ids: List[str], depth: int) -> List[Dict[str, Any]]:
        """Find artifacts relevant to the question."""
        relevant = []
        
        # If specific artifact IDs provided, start from those
        if artifact_ids:
            for aid in artifact_ids:
                artifact = self._by_path.get(aid) or next(
                    (a for a in self.artifacts if a.get('id') == aid), None
                )
                if artifact:
                    relevant.append(artifact)
        else:
            # Extract keywords and find matching artifacts
            keywords = self._extract_keywords(question.lower())
            for artifact in self.artifacts:
                score = self._score_artifact_semantic(artifact, keywords)
                if score > 0.1:  # Threshold for relevance
                    relevant.append(artifact)
        
        # Expand by relationships if depth > 1
        if depth > 1:
            expanded = set(a.get('id') for a in relevant)
            for artifact in relevant:
                rels = artifact.get('relationships', {})
                for rel_type, target_ids in rels.items():
                    for tid in target_ids:
                        if tid not in expanded:
                            target = next((a for a in self.artifacts if a.get('id') == tid), None)
                            if target:
                                relevant.append(target)
                                expanded.add(tid)
        
        return relevant
    
    def _generate_answer(self, question: str, artifacts: List[Dict[str, Any]]) -> tuple[str, float]:
        """Generate answer to question based on artifacts (heuristic)."""
        question_lower = question.lower()
        
        # Question type: "which X are Y"
        if 'which' in question_lower or 'what' in question_lower:
            return self._answer_which_what(question, artifacts)
        
        # Question type: "how many"
        if 'how many' in question_lower:
            return self._answer_how_many(question, artifacts)
        
        # Question type: "does" or "is"
        if 'does' in question_lower or 'is' in question_lower:
            return self._answer_yes_no(question, artifacts)
        
        # Default: summarize relevant artifacts
        if artifacts:
            summary = f"Found {len(artifacts)} relevant artifacts: "
            names = [a.get('name', a.get('path', '')) for a in artifacts[:5]]
            summary += ', '.join(names)
            if len(artifacts) > 5:
                summary += f" and {len(artifacts) - 5} more"
            return summary, 0.7
        
        return "No relevant artifacts found.", 0.0
    
    def _answer_which_what(self, question: str, artifacts: List[Dict[str, Any]]) -> tuple[str, float]:
        """Answer 'which' or 'what' questions."""
        if not artifacts:
            return "None found.", 0.0
        
        # Extract what we're looking for
        question_lower = question.lower()
        
        # Check for specific types
        if 'workflow' in question_lower or 'ci' in question_lower:
            workflows = [a for a in artifacts if a.get('type') == 'workflow']
            if workflows:
                names = [a.get('name', a.get('path', '')) for a in workflows]
                return f"Found {len(workflows)} workflow(s): {', '.join(names)}", 0.9
        
        if 'dockerfile' in question_lower or 'docker' in question_lower:
            dockerfiles = [a for a in artifacts if a.get('type') == 'dockerfile']
            if dockerfiles:
                names = [a.get('name', a.get('path', '')) for a in dockerfiles]
                return f"Found {len(dockerfiles)} Dockerfile(s): {', '.join(names)}", 0.9
        
        # Generic answer
        names = [a.get('name', a.get('path', '')) for a in artifacts[:10]]
        answer = f"Found {len(artifacts)} artifact(s): {', '.join(names)}"
        if len(artifacts) > 10:
            answer += f" and {len(artifacts) - 10} more"
        return answer, 0.7
    
    def _answer_how_many(self, question: str, artifacts: List[Dict[str, Any]]) -> tuple[str, float]:
        """Answer 'how many' questions."""
        count = len(artifacts)
        
        # Check for specific types
        question_lower = question.lower()
        if 'workflow' in question_lower:
            count = len([a for a in artifacts if a.get('type') == 'workflow'])
            return f"There are {count} workflow(s).", 0.9
        
        if 'dockerfile' in question_lower:
            count = len([a for a in artifacts if a.get('type') == 'dockerfile'])
            return f"There are {count} Dockerfile(s).", 0.9
        
        return f"There are {count} relevant artifact(s).", 0.7
    
    def _answer_yes_no(self, question: str, artifacts: List[Dict[str, Any]]) -> tuple[str, float]:
        """Answer yes/no questions."""
        if artifacts:
            return "Yes.", 0.8
        return "No.", 0.6

