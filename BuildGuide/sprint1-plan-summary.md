# Sprint 1: Repository Intelligence Design - Plan Summary

## Quick Overview
Design the system for scanning, representing, and querying repository knowledge to enable CI failure analysis and future infrastructure policy scanning.

---

## Deliverables

### 1. Repository Scanning Strategy ✅
- **Hierarchical traversal** with `.gitignore` support
- **Three-phase approach**: Discovery → Classification → Content Extraction
- **Size limits**: Files > 1MB indexed but not fully loaded
- **Binary file handling**: Skipped except for special cases

### 2. File Recognition Rules ✅
**Recognized Types:**
- CI/CD Workflows (GitHub Actions, GitLab CI, CircleCI, Jenkins, etc.)
- Docker Artifacts (Dockerfile, docker-compose)
- Dependency Manifests (package.json, requirements.txt, pom.xml, etc.)
- Configuration Files (.env, config files, Makefiles)
- Infrastructure as Code (Terraform, Kubernetes, CloudFormation)
- Source Code Structure

**Classification Priority:** Workflows → Dependencies → Docker → IaC → Config → Source

### 3. Repository Knowledge Model ✅
**Core Structure:**
```json
{
  "repository": { id, name, url, scanned_at },
  "artifacts": [
    {
      "id", "type", "path", "name",
      "metadata": { /* type-specific */ },
      "content": { "raw", "structured" },
      "relationships": { "depends_on", "used_by" },
      "tags": [], "summary": ""
    }
  ],
  "relationships": { /* cross-artifact links */ },
  "summary": { /* repo-level summary */ }
}
```

### 4. AI Summarization & Tagging ✅
- **Per-artifact**: 1-2 sentence summary + 3-10 tags
- **Repository-level**: Project type, tech stack, architecture patterns
- **Prompt templates** defined for consistent output

### 5. LLM Query Interface ✅
**Three Query Types:**
1. **Direct Artifact Queries**: Filter by type, path, tags, metadata
2. **Semantic Queries**: Natural language search using embeddings
3. **Analysis Queries**: Ask questions about repo structure

**Interface**: Prompt-based system that retrieves artifacts, constructs context, and returns structured responses

### 6. Future-Proofing ✅
- **Extensible type system**: New artifact types don't break existing code
- **Generic relationship graph**: Supports any relationship type
- **Additive metadata**: New fields are optional
- **Infrastructure policy scans** can plug in using existing IaC artifact types

---

## Key Design Decisions

1. **JSON as primary format**: Portable, LLM-friendly, human-readable
2. **Metadata + Content separation**: Enables efficient querying without loading full content
3. **Relationship graph**: Enables dependency analysis and impact assessment
4. **Tag-based categorization**: Enables semantic search and filtering
5. **Versioned snapshots**: Each scan produces a new version for change tracking

---

## Next Steps for Implementation (Eric)

1. Build directory walker with `.gitignore` support
2. Implement file classification logic
3. Create metadata extractors for each artifact type
4. Build relationship detection (e.g., workflow → Dockerfile references)
5. Serialize to JSON matching the schema
6. Integrate with LLM for summarization (optional in Sprint 1)

---

## Success Criteria

✅ **Specification Complete** when:
- All scanning rules defined
- All file types recognized
- Complete data schema documented
- Query interface designed
- Future-proofing strategy clear
- Eric can implement without ambiguity

---

**Full Specification**: See `sprint1-repository-intelligence-spec.md`  
**Status**: ✅ Specification Complete - Ready for Eric's Implementation

