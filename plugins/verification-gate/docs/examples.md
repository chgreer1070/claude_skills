# Usage Examples

Real-world examples demonstrating the verification gate skill in action.

---

## Example 1: Dependency Resolution (PEP 723 Script)

**Scenario**: User runs a Python script that fails with `ModuleNotFoundError: No module named 'pydantic'`

### Without Verification Gate ❌

**Observation**: `ModuleNotFoundError: No module named 'pydantic'`

**Claude's Response** (pattern-matching):

```text
I see the pydantic module is missing. Let me install it:

Bash(command="uv sync")
```

**Result**: Command executes but doesn't fix the issue because `uv sync` operates on `pyproject.toml`, not PEP 723 inline script dependencies.

---

### With Verification Gate ✓

**Observation**: `ModuleNotFoundError: No module named 'pydantic'`

**Claude's Response** (verification-gated):

```text
I need to verify the dependency management system before acting.

CHECKPOINT 1 - State Hypothesis:
Hypothesis: The script uses PEP 723 inline dependencies and pydantic is missing from the # /// script block.

CHECKPOINT 2 - Verify Hypothesis:
Let me read the script to verify:
```

```python
Read(file_path="packages/reset_all_tokens/cli.py", limit=50)
```

**File Contents**:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich"
# ]
# ///

from pydantic import BaseModel  # Import present
```

**Verification Result**:

```text
Evidence: Lines 1-8 show # /// script block with dependencies.
pydantic is NOT in dependencies list but IS imported at line 10.

CHECKPOINT 3 - Verify Alignment:
┌─────────────────────────────────────────────────────────┐
│ HYPOTHESIS SYSTEM: PEP 723 inline script metadata      │
├─────────────────────────────────────────────────────────┤
│ ACTION SYSTEM:     PEP 723 inline script metadata      │
│                    (Edit # /// script block)            │
├─────────────────────────────────────────────────────────┤
│ ALIGNMENT CHECK:   ✓ SAME SYSTEM - Proceed             │
└─────────────────────────────────────────────────────────┘

CHECKPOINT 4 - Pattern-Matching Check:
✓ Verified by reading actual script file (lines 1-10)
✓ Confirmed PEP 723 block exists and lacks pydantic
✓ Not assuming "standard" dependency management

VERIFICATION COMPLETE - All checkpoints passed
EXECUTING: Add pydantic to # /// script dependencies
```

```python
Edit(
    file_path="packages/reset_all_tokens/cli.py",
    old_string='# dependencies = [\n#     "typer",\n#     "rich"\n# ]',
    new_string='# dependencies = [\n#     "typer",\n#     "rich",\n#     "pydantic"\n# ]'
)
```

**Result**: Correct fix applied to the right system.

---

## Example 2: Configuration Not Applied

**Scenario**: User reports that changing timeout value in `config.yaml` has no effect on application behavior.

### Without Verification Gate ❌

**Observation**: Application ignores timeout changes in config.yaml

**Claude's Response** (pattern-matching):

```text
Let me check the config.yaml format and fix it:
```

```python
Read(file_path="config.yaml")
# Sees: timeout: 30
# Assumes format is wrong
Edit(file_path="config.yaml", ...)
```

**Result**: Changes config.yaml format but application still ignores it because it reads from environment variables first.

---

### With Verification Gate ✓

**Observation**: Application ignores timeout changes in config.yaml

**Claude's Response** (verification-gated):

```text
CHECKPOINT 1 - State Hypothesis:
Initial hypothesis too vague: "Configuration not working"
Need to investigate which configuration source is being used.

CHECKPOINT 2 - Gather Evidence:
Let me find the configuration loading code:
```

```python
Grep(
    pattern="timeout.*config|load.*yaml",
    path="src/",
    output_mode="content"
)
```

**Grep Result**:

```python
src/app.py:15: timeout = os.getenv('TIMEOUT', load_config_yaml().get('timeout', 30))
```

**Evidence Analysis**:

```text
Evidence: src/app.py line 15 shows configuration precedence:
1. Environment variable TIMEOUT (first)
2. config.yaml timeout field (fallback)

CHECKPOINT 1 REFINED:
Hypothesis: Application reads TIMEOUT environment variable first,
which overrides config.yaml. User's config.yaml changes have no
effect because env var is set.

CHECKPOINT 3 - Verify Alignment:
┌─────────────────────────────────────────────────────────┐
│ HYPOTHESIS SYSTEM: Environment variable TIMEOUT        │
├─────────────────────────────────────────────────────────┤
│ ACTION SYSTEM:     Environment variable (set/export)    │
├─────────────────────────────────────────────────────────┤
│ ALIGNMENT CHECK:   ✓ SAME SYSTEM - Proceed             │
└─────────────────────────────────────────────────────────┘

CHECKPOINT 4 - Pattern-Matching Check:
✓ Verified by reading actual config loading code (src/app.py:15)
✓ Not assuming "configs usually work this way"
✓ Found evidence of precedence: env var > config file

VERIFICATION COMPLETE
EXECUTING: Set environment variable instead of modifying config.yaml
```

```bash
Bash(command="export TIMEOUT=60")
```

**Result**: Correct fix applied to the system that actually controls the timeout.

---

## Example 3: Docker Container Network Issue

**Scenario**: Container cannot reach external API at api.example.com

### Without Verification Gate ❌

**Observation**: Container networking not working

**Claude's Response** (pattern-matching):

```text
Network connectivity issue. Let me check host DNS:
```

```bash
Bash(command="cat /etc/resolv.conf")
Edit(file_path="/etc/resolv.conf", ...)  # Modifies host
```

**Result**: Changes host DNS but container uses bridge network with own DNS configuration.

---

### With Verification Gate ✓

**Observation**: Container cannot reach external API

**Claude's Response** (verification-gated):

```text
CHECKPOINT 1 - State Hypothesis:
Too vague: "Network connectivity issue"
Need to specify which network layer.

CHECKPOINT 2 - Gather Evidence:
Let me check container network configuration:
```

```bash
Bash(command="docker inspect my-container | grep -A 10 NetworkSettings")
```

**Output**:

```json
"NetworkSettings": {
    "Bridge": "",
    "Networks": {
        "bridge": {
            "IPAddress": "172.17.0.2",
            "Gateway": "172.17.0.1",
            "MacAddress": "02:42:ac:11:00:02"
        }
    }
}
```

```bash
Bash(command="docker exec my-container cat /etc/resolv.conf")
```

**Output**:

```text
nameserver 127.0.0.11
```

**Evidence Analysis**:

```text
Evidence gathered:
1. Container uses bridge network (docker inspect output)
2. Container DNS: 127.0.0.11 (embedded Docker DNS)
3. Host DNS: Not relevant (container has own network namespace)

CHECKPOINT 1 REFINED:
Hypothesis: Container bridge network's embedded DNS (127.0.0.11)
cannot resolve external domain api.example.com. This is a Docker
network DNS configuration issue, not a host network issue.

CHECKPOINT 3 - Verify Alignment:
┌─────────────────────────────────────────────────────────┐
│ HYPOTHESIS SYSTEM: Docker bridge network DNS config    │
├─────────────────────────────────────────────────────────┤
│ ACTION SYSTEM:     Docker network settings (--dns flag) │
├─────────────────────────────────────────────────────────┤
│ ALIGNMENT CHECK:   ✓ SAME SYSTEM (Docker networking)   │
└─────────────────────────────────────────────────────────┘

CHECKPOINT 4 - Pattern-Matching Check:
✓ Verified via docker inspect and docker exec
✓ Not assuming "network issue" means "host networking"
✓ Identified correct layer: container network, not host network

VERIFICATION COMPLETE
EXECUTING: Configure Docker container with external DNS
```

```bash
Bash(command="docker run --dns 8.8.8.8 my-container")
```

**Result**: Correct fix applied to Docker container network layer.

---

## Example 4: Test Failure - Fix Test or Fix Code?

**Scenario**: Test fails after refactoring with assertion error

### Without Verification Gate ❌

**Observation**: Test `test_calculate_total` fails

**Claude's Response** (pattern-matching):

```text
Test is failing. Let me update the test assertion:
```

```python
Edit(
    file_path="tests/test_calculations.py",
    old_string="assert result == 100",
    new_string="assert result == 110"
)
```

**Result**: Test passes but code regression is hidden. Test was correct, code behavior changed.

---

### With Verification Gate ✓

**Observation**: Test `test_calculate_total` fails with `AssertionError: assert 110 == 100`

**Claude's Response** (verification-gated):

```text
CHECKPOINT 1 - State Hypothesis:
Cannot form hypothesis without understanding what test expects vs what code does.

CHECKPOINT 2 - Gather Evidence:
```

```python
Read(file_path="tests/test_calculations.py", limit=50)
```

**Test Code**:

```python
def test_calculate_total():
    """Total should be sum of items without any fees"""
    items = [30, 40, 30]
    result = calculate_total(items)
    assert result == 100  # Expects sum only
```

```python
Read(file_path="src/calculations.py")
```

**Implementation Code**:

```python
def calculate_total(items):
    """Calculate total with 10% service fee"""
    subtotal = sum(items)
    return subtotal + (subtotal * 0.10)  # Recently added fee
```

```bash
Bash(command="git log --oneline -5 -- src/calculations.py")
```

**Git Log**:

```text
a1b2c3d Add 10% service fee to calculate_total
d4e5f6g Initial implementation of calculate_total
```

**Evidence Analysis**:

```text
Evidence:
1. Test expects: sum only (100) per docstring "without any fees"
2. Code returns: sum + 10% (110) per recent commit "Add 10% service fee"
3. Behavior changed: commit a1b2c3d added fee calculation
4. Test expectation: Unchanged since initial implementation

CHECKPOINT 1 REFINED:
Hypothesis: Code behavior changed (added fee) but test expectation
was not updated. Need to determine if fee is intentional or regression.

Question: Was 10% fee intentional feature or unintended change?

Evidence: Git commit message says "Add 10% service fee" (intentional).

Refined hypothesis: Test expectation is outdated. Test should be
updated to reflect intentional new feature.

CHECKPOINT 3 - Verify Alignment:
┌─────────────────────────────────────────────────────────┐
│ HYPOTHESIS SYSTEM: Test expectation (outdated)         │
├─────────────────────────────────────────────────────────┤
│ ACTION SYSTEM:     Test expectation (update assertion)  │
├─────────────────────────────────────────────────────────┤
│ ALIGNMENT CHECK:   ✓ SAME SYSTEM - Proceed             │
└─────────────────────────────────────────────────────────┘

CHECKPOINT 4 - Pattern-Matching Check:
✓ Read test code to understand expectation
✓ Read implementation code to understand behavior
✓ Checked git history to understand if change was intentional
✓ Not reflexively changing test without verification

VERIFICATION COMPLETE
EXECUTING: Update test to reflect intentional feature change
```

```python
Edit(
    file_path="tests/test_calculations.py",
    old_string='"""Total should be sum of items without any fees"""\n    items = [30, 40, 30]\n    result = calculate_total(items)\n    assert result == 100  # Expects sum only',
    new_string='"""Total should be sum of items with 10% service fee"""\n    items = [30, 40, 30]\n    result = calculate_total(items)\n    assert result == 110  # Sum (100) + 10% fee (10) = 110'
)
```

**Result**: Test updated correctly after verifying the behavior change was intentional, not a regression.

---

## Example 5: Python Virtual Environment Confusion

**Scenario**: `pip install requests` succeeds but script still shows `ModuleNotFoundError: No module named 'requests'`

### Without Verification Gate ❌

**Observation**: Module not found after installing

**Claude's Response** (pattern-matching):

```text
Let me reinstall it properly:
```

```bash
Bash(command="pip install --upgrade requests")
```

**Result**: Still fails because pip installs to different environment than script uses.

---

### With Verification Gate ✓

**Observation**: Script fails with `ModuleNotFoundError: No module named 'requests'` after running `pip install requests`

**Claude's Response** (verification-gated):

```text
CHECKPOINT 1 - State Hypothesis:
Initial: "requests package not installed"
But user said they already installed it. Need to verify environment scope.

CHECKPOINT 2 - Gather Evidence:
```

```bash
Bash(command="which python && which pip && python -c 'import sys; print(sys.prefix)'")
```

**Output**:

```text
/usr/bin/python
/usr/local/bin/pip
/usr
```

```bash
Bash(command="head -1 ./scripts/fetch_data.py")
```

**Output**:

```bash
#!/home/user/projects/myapp/.venv/bin/python
```

```bash
Bash(command="pip show requests | grep Location")
```

**Output**:

```text
Location: /usr/local/lib/python3.11/site-packages
```

**Evidence Analysis**:

```text
Evidence:
1. Active python: /usr/bin/python (system Python)
2. Active pip: /usr/local/bin/pip (system pip)
3. System Python prefix: /usr
4. Script shebang: /home/user/projects/myapp/.venv/bin/python (venv)
5. requests installed to: /usr/local/lib (system packages)

CHECKPOINT 1 REFINED:
Hypothesis: Script runs with virtual environment Python
(/home/user/projects/myapp/.venv/bin/python) but requests was
installed to system Python (/usr/local/lib). Different environments.

CHECKPOINT 3 - Verify Alignment:
┌─────────────────────────────────────────────────────────┐
│ HYPOTHESIS SYSTEM: Virtual environment at .venv        │
├─────────────────────────────────────────────────────────┤
│ ACTION SYSTEM:     Virtual environment pip              │
│                    (.venv/bin/pip or python -m pip)     │
├─────────────────────────────────────────────────────────┤
│ ALIGNMENT CHECK:   ✓ SAME SYSTEM (venv) - Proceed      │
└─────────────────────────────────────────────────────────┘

CHECKPOINT 4 - Pattern-Matching Check:
✓ Verified which Python interpreter script uses (shebang)
✓ Verified where requests was installed (pip show)
✓ Not assuming "pip install" targets correct environment
✓ Identified environment mismatch through evidence

VERIFICATION COMPLETE
EXECUTING: Install requests to correct virtual environment
```

```bash
Bash(command="/home/user/projects/myapp/.venv/bin/pip install requests")
```

**Result**: Correct fix - package installed to same environment script uses.

---

## Common Patterns Summary

| Scenario | Without Gate | With Gate | Key Checkpoint |
|----------|--------------|-----------|----------------|
| Dependency error | Pattern-match → wrong system | Verify → correct system | Checkpoint 3 (Alignment) |
| Config not applied | Assume config format wrong | Verify precedence order | Checkpoint 2 (Evidence) |
| Network issue | Guess at network layer | Verify which layer affected | Checkpoint 1 (Specific hypothesis) |
| Test failure | Reflexively fix test | Verify which is correct | Checkpoint 2 (Evidence) |
| Import error | Retry same command | Verify environment scope | Checkpoint 4 (Pattern-matching) |

---

[Back to README](../README.md) | [Skills Reference](./skills.md)
