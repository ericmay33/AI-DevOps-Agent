# 01: Failure Classification

## What This Does

The failure classifier analyzes CI/CD failure logs and categorizes them into specific failure types. This classification is the first step in understanding what went wrong and how to fix it.

---

## Failure Categories

The system recognizes the following failure categories:

### 1. Dependency Failures

**Subtypes:**
- `dependency_version_mismatch` - Required version doesn't exist or is incompatible
- `dependency_missing` - Package not found in registry
- `dependency_conflict` - Multiple packages require incompatible versions
- `dependency_install_failed` - Installation process failed

**Common Patterns:**
- `ERROR: Could not find a version that satisfies the requirement`
- `PackageNotFoundError`
- `No matching distribution found`
- `Resolving dependencies failed`

**Example:**
```
ERROR: Could not find a version that satisfies the requirement pytest==7.0.0
```

### 2. Configuration Errors

**Subtypes:**
- `missing_environment_variable` - Required env var not set
- `invalid_configuration` - Config file has errors
- `missing_config_file` - Required config file not found
- `invalid_path` - File or directory path doesn't exist

**Common Patterns:**
- `Error: MISSING_API_KEY is not set`
- `FileNotFoundError: [Errno 2] No such file or directory`
- `ConfigurationError`
- `Invalid configuration`

**Example:**
```
Error: MISSING_API_KEY is not set
exit 1
```

### 3. Test Failures

**Subtypes:**
- `test_assertion_failure` - Test assertion failed
- `test_timeout` - Test exceeded time limit
- `test_setup_failure` - Test setup/teardown failed
- `test_runner_error` - Test framework error

**Common Patterns:**
- `AssertionError`
- `Test failed`
- `TimeoutError`
- `FAILED`

**Example:**
```
AssertionError: expected True but got False
```

### 4. Build Errors

**Subtypes:**
- `compilation_error` - Code doesn't compile
- `syntax_error` - Syntax error in source code
- `build_timeout` - Build process exceeded time limit
- `build_dependency_missing` - Build tool or dependency missing

**Common Patterns:**
- `SyntaxError`
- `CompilationError`
- `Build failed`
- `error: failed to compile`

**Example:**
```
SyntaxError: invalid syntax (line 42)
```

### 5. Permission Errors

**Subtypes:**
- `file_permission_denied` - Cannot read/write file
- `directory_permission_denied` - Cannot access directory
- `execution_permission_denied` - Cannot execute command

**Common Patterns:**
- `PermissionError`
- `Permission denied`
- `EACCES`
- `Access denied`

**Example:**
```
PermissionError: [Errno 13] Permission denied: '/path/to/file'
```

### 6. Network/Timeout Errors

**Subtypes:**
- `network_timeout` - Network request timed out
- `connection_failed` - Cannot connect to server
- `dns_resolution_failed` - DNS lookup failed
- `ssl_error` - SSL/TLS handshake failed

**Common Patterns:**
- `TimeoutError`
- `ConnectionError`
- `Failed to connect`
- `SSL: CERTIFICATE_VERIFY_FAILED`

**Example:**
```
TimeoutError: The read operation timed out
```

### 7. Runtime Errors

**Subtypes:**
- `runtime_exception` - Unhandled exception during execution
- `memory_error` - Out of memory
- `import_error` - Cannot import module
- `attribute_error` - Object doesn't have attribute

**Common Patterns:**
- `RuntimeError`
- `MemoryError`
- `ImportError`
- `AttributeError`

**Example:**
```
ImportError: cannot import name 'function' from 'module'
```

### 8. Workflow/CI Errors

**Subtypes:**
- `workflow_syntax_error` - Workflow YAML has syntax errors
- `workflow_step_failed` - Workflow step failed
- `workflow_timeout` - Workflow exceeded time limit
- `workflow_permission_denied` - Workflow lacks permissions

**Common Patterns:**
- `Workflow syntax error`
- `Step failed with exit code`
- `Workflow timeout`
- `Insufficient permissions`

**Example:**
```
Error: Workflow syntax error at line 15: invalid key
```

### 9. Unknown/Other

**Subtypes:**
- `unknown_error` - Cannot classify into known categories
- `multiple_failures` - Multiple different failure types
- `cascading_failure` - One failure caused others

**When to use:**
- Error doesn't match any known pattern
- Multiple unrelated errors occurred
- Root cause is unclear

---

## Classification Process

### Step 1: Pattern Matching

The classifier first uses heuristics to identify common patterns:

```python
def classify_by_pattern(log_content: str) -> Optional[str]:
    patterns = {
        'dependency_version_mismatch': [
            r'Could not find a version',
            r'No matching distribution',
        ],
        'missing_environment_variable': [
            r'is not set',
            r'Environment variable.*required',
        ],
        # ... more patterns
    }
    
    for failure_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, log_content, re.IGNORECASE):
                return failure_type
    
    return None
```

### Step 2: LLM Classification

If pattern matching doesn't yield high confidence, the LLM analyzes the log:

**Prompt:**
```
Analyze this CI/CD failure log and classify the failure type.

Log content:
{log_content}

Repository context:
- Language: {language}
- CI Platform: {platform}
- Job: {job_name}
- Step: {step_name}

Classify into one of these categories:
1. dependency_version_mismatch
2. dependency_missing
3. missing_environment_variable
4. test_assertion_failure
5. compilation_error
6. ... (all categories)

Respond with JSON:
{
  "failure_type": "...",
  "confidence": 0.0-1.0,
  "reasoning": "..."
}
```

### Step 3: Confidence Scoring

Confidence is calculated based on:
- Pattern match quality (exact vs. fuzzy)
- LLM confidence score
- Evidence strength (multiple log lines vs. single line)
- Context correlation (matches repository artifacts)

**Confidence Levels:**
- **High (0.8-1.0)**: Clear pattern match, strong evidence
- **Medium (0.5-0.8)**: Likely match, some evidence
- **Low (0.0-0.5)**: Uncertain, weak evidence

---

## Classification Examples

### Example 1: Dependency Version Mismatch

**Log:**
```
ERROR: Could not find a version that satisfies the requirement pytest==7.0.0
ERROR: No matching distribution found for pytest==7.0.0
```

**Classification:**
- Type: `dependency_version_mismatch`
- Confidence: 0.95
- Reasoning: Clear error message indicating version not available

### Example 2: Missing Environment Variable

**Log:**
```
Error: MISSING_API_KEY is not set
exit 1
```

**Classification:**
- Type: `missing_environment_variable`
- Confidence: 0.90
- Reasoning: Explicit error message about missing env var

### Example 3: Test Failure

**Log:**
```
FAILED tests/test_example.py::test_function
AssertionError: expected True but got False
```

**Classification:**
- Type: `test_assertion_failure`
- Confidence: 0.85
- Reasoning: Test framework output with assertion error

---

## Integration with Repository Context

The classifier uses repository context to improve accuracy:

**Correlation Examples:**

1. **Dependency Error + requirements.txt exists:**
   - High confidence it's a dependency issue
   - Can identify which file needs fixing

2. **Config Error + .env.example exists:**
   - Suggests missing environment variable
   - Can reference example file

3. **Test Error + test/ directory exists:**
   - Confirms it's a test failure
   - Can identify test file location

---

## Classification Output

The classifier produces:

```python
{
    "failure_type": "dependency_version_mismatch",
    "subtype": "version_not_available",
    "confidence": 0.92,
    "evidence": [
        "Line 15: ERROR: Could not find a version...",
        "Line 16: ERROR: No matching distribution..."
    ],
    "affected_artifacts": ["requirements.txt"],
    "reasoning": "Error message clearly indicates pytest==7.0.0 is not available"
}
```

This output feeds into the root cause analysis step.

