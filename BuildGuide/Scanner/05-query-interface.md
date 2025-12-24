# 05: Query Interface

## What This Does

The query interface allows you to search and analyze the repository knowledge model. You can find specific artifacts, search by meaning, or ask questions about the repository structure.

**Think of it as**: A search engine for your repository knowledge.

---

## Three Query Types

### 1. Direct Artifact Queries

**Purpose**: Find specific artifacts by filtering

**Use when**: You know what you're looking for (e.g., "all workflows", "Dockerfiles in the root directory")

**Query format**:
```json
{
  "type": "artifact_query",
  "filters": {
    "artifact_type": "workflow",           // Filter by type
    "path_pattern": "*.yml",               // Filter by path (glob pattern)
    "tags": ["testing", "ci"],             // Filter by tags
    "metadata": {                          // Filter by metadata
      "platform": "github_actions"
    }
  },
  "include_content": true,                  // Include file content?
  "include_relationships": true            // Include relationships?
}
```

**Response**:
```json
{
  "artifacts": [
    {
      "id": "wf1",
      "type": "workflow",
      "path": ".github/workflows/test.yml",
      "name": "Test Workflow",
      "summary": "...",
      "tags": ["testing", "ci"],
      "metadata": {...},
      "content": {...}  // If include_content=true
    }
  ],
  "relationships": {...}  // If include_relationships=true
}
```

**Examples**:

Find all workflows:
```python
result = query_engine.query({
    "type": "artifact_query",
    "filters": {
        "artifact_type": "workflow"
    }
})
```

Find Dockerfiles in root:
```python
result = query_engine.query({
    "type": "artifact_query",
    "filters": {
        "artifact_type": "dockerfile",
        "path_pattern": "Dockerfile*"
    }
})
```

Find artifacts with specific tags:
```python
result = query_engine.query({
    "type": "artifact_query",
    "filters": {
        "tags": ["testing", "ci"]
    }
})
```

---

### 2. Semantic Queries

**Purpose**: Find artifacts by meaning/intent (natural language search)

**Use when**: You want to find things by what they do, not by exact names

**Query format**:
```json
{
  "type": "semantic_query",
  "query": "artifacts related to running tests",  // Natural language
  "limit": 10,                                    // Max results
  "threshold": 0.3                                // Minimum relevance score
}
```

**Response**: Same as artifact query (list of matching artifacts)

**How it works** (current implementation):
1. Extracts keywords from query
2. Scores artifacts based on keyword matches in:
   - Summary (weighted highest)
   - Tags
   - Path/name
   - Metadata
3. Returns top N results sorted by relevance

**Examples**:

Find test-related artifacts:
```python
result = query_engine.query({
    "type": "semantic_query",
    "query": "artifacts related to running tests",
    "limit": 10
})
```

Find deployment configurations:
```python
result = query_engine.query({
    "type": "semantic_query",
    "query": "how is the application deployed",
    "limit": 5
})
```

**Future enhancement**: Will use embeddings/vector search for better semantic matching.

---

### 3. Analysis Queries

**Purpose**: Ask questions about the repository structure

**Use when**: You want to understand relationships or get answers about the codebase

**Query format**:
```json
{
  "type": "analysis_query",
  "question": "Which Dockerfiles are used by workflows?",
  "context": {
    "artifact_ids": ["wf1", "wf2"],  // Optional: focus on specific artifacts
    "relationship_depth": 2          // How deep to follow relationships
  }
}
```

**Response**:
```json
{
  "answer": "Found 2 Dockerfile(s): Dockerfile.prod, Dockerfile.dev",
  "supporting_artifacts": ["df1", "df2"],  // Artifact IDs that support the answer
  "confidence": 0.9                         // Confidence score (0-1)
}
```

**Question types supported**:

**"Which" / "What" questions**:
- "Which workflows run on push?"
- "What Dockerfiles are in this repository?"
- "Which dependencies are used?"

**"How many" questions**:
- "How many workflows are there?"
- "How many Dockerfiles use Python?"

**"Does" / "Is" questions**:
- "Does this project use Docker?"
- "Is there a CI workflow?"

**Examples**:

Which Dockerfiles are referenced in workflows:
```python
result = query_engine.query({
    "type": "analysis_query",
    "question": "Which Dockerfiles are referenced in CI workflows?",
    "context": {
        "relationship_depth": 2
    }
})
# Answer: "Found 2 Dockerfile(s): Dockerfile.prod, Dockerfile.test"
```

How many workflows:
```python
result = query_engine.query({
    "type": "analysis_query",
    "question": "How many CI workflows are there?"
})
# Answer: "There are 3 workflow(s)."
```

---

## Usage

### Basic Setup

```python
from scanner import RepositoryScanner, QueryEngine

# Scan repository
scanner = RepositoryScanner()
knowledge = scanner.scan('/path/to/repo')

# Create query engine
query_engine = QueryEngine(knowledge)
```

### Query Examples

**Find all workflows**:
```python
result = query_engine.query({
    "type": "artifact_query",
    "filters": {"artifact_type": "workflow"},
    "include_content": True
})

for artifact in result.artifacts:
    print(f"{artifact['name']}: {artifact['path']}")
```

**Semantic search**:
```python
result = query_engine.query({
    "type": "semantic_query",
    "query": "test configuration and setup",
    "limit": 5
})

for artifact in result.artifacts:
    print(f"{artifact['name']}: {artifact['summary']}")
```

**Ask a question**:
```python
result = query_engine.query({
    "type": "analysis_query",
    "question": "What package managers are used in this project?"
})

print(result.answer)  # "Found npm and pip package managers."
print(f"Confidence: {result.confidence}")  # 0.85
```

---

## How It Works Internally

### Query Engine Process

1. **Receives query** in structured format
2. **Determines query type** (artifact, semantic, analysis)
3. **Retrieves relevant artifacts**:
   - Direct: Filter artifacts by criteria
   - Semantic: Score and rank artifacts
   - Analysis: Find artifacts relevant to question
4. **Constructs response**:
   - Direct: Return filtered artifacts
   - Semantic: Return top N scored artifacts
   - Analysis: Generate answer from relevant artifacts
5. **Returns structured result**

### Indexing

The query engine builds indexes for fast lookup:
- **By type**: All workflows, all dockerfiles, etc.
- **By path**: Quick path lookups
- **By tag**: Tag-based filtering

### Scoring (Semantic Queries)

Artifacts are scored based on keyword matches:
- Summary matches: 2.0x weight
- Tag matches: 1.5x weight
- Path/name matches: 1.0x weight
- Metadata matches: 0.5x weight

Scores are normalized to 0-1 range.

---

## Use Cases

1. **CI Failure Analysis** (Sprint 2):
   - Find workflows that failed
   - Find dependencies used by failed workflows
   - Understand workflow relationships

2. **Patch Generation** (Sprint 3):
   - Find files that need to be modified
   - Understand dependencies before making changes
   - Check for related artifacts

3. **Repository Understanding**:
   - Get overview of project structure
   - Find all configuration files
   - Understand deployment setup

---

## Implementation Files

- `scanner/query.py` - QueryEngine implementation
- `scanner/models.py` - QueryResult data model

---

## Future Enhancements

1. **Vector Search**: Use embeddings for better semantic matching
2. **LLM-Powered Analysis**: Use LLM for more sophisticated question answering
3. **Query Caching**: Cache frequent queries
4. **Advanced Filters**: More complex filtering options

---

**Next Steps**: The query interface enables CI failure analysis → Sprint 2

