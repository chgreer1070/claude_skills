# Testing Your Agent

Testing checklist, methods, common failures, and iterative process for validating a new agent.

---

## Testing Checklist

- [ ] Agent file saved to `.claude/agents/{name}.md`
- [ ] YAML frontmatter parses correctly (no syntax errors)
- [ ] Name follows constraints (lowercase, hyphens, max 64 chars)
- [ ] Description includes trigger keywords
- [ ] All referenced skills exist

## Testing Methods

### Method 1: Direct Invocation Test

Create a simple test prompt that should trigger your agent:

<eg>

```text
# For a code review agent
"Please review the authentication code in src/auth.py for security issues"

# For a documentation agent
"Generate API documentation for the User model"

# For a test writer agent
"Write pytest tests for the calculate_total function"
```

</eg>

**What to observe:**

- Does Claude invoke your agent automatically?
- If not, the description may need better trigger keywords
- Does the agent have the tools it needs?
- Does it produce the expected output format?

### Method 2: Explicit Agent Test

Force invocation using the Task tool:

<eg>

```text
Test my new agent explicitly:

Task(
  agent="my-agent-name",
  prompt="Test task: Review this simple Python function for issues: def add(a, b): return a + b"
)
```

</eg>

**What to observe:**

- Agent loads successfully (no missing skills error)
- Agent has required tool access
- Agent follows its workflow
- Output matches specified format

### Method 3: Tool Restriction Test

Verify tool restrictions work as intended:

```yaml
# Agent configured with restricted tools
tools: Read, Grep, Glob
permissionMode: dontAsk
```

Test prompts:

- "Read and analyze file.py" → Should work
- "Fix the bug in file.py" → Should fail or report inability

**What to observe:**

- Agent correctly blocked from disallowed tools
- Error messages are clear
- Agent doesn't try to work around restrictions

### Method 4: Edge Case Testing

Test boundary conditions:

**For read-only agents:**

- Prompt that asks for code changes → Should decline or report limitation
- Prompt that asks for analysis → Should work

**For write agents:**

- Prompt with missing information → Should ask for clarification or block
- Prompt with clear requirements → Should proceed

**For research agents:**

- Large codebase exploration → Should handle without context overflow
- Specific file search → Should be fast and focused

## Common Test Failures

| Symptom                     | Likely Cause                              | Fix                               |
| --------------------------- | ----------------------------------------- | --------------------------------- |
| Agent never invokes         | Description lacks trigger keywords        | Add keywords to description       |
| "Skill not found" error     | Typo in skill name or skill doesn't exist | Check skill names, verify paths   |
| "Tool not available" error  | Tool restrictions too restrictive         | Add needed tools to `tools` field |
| Agent does wrong task       | Description too broad                     | Make description more specific    |
| Constant permission prompts | Wrong permission mode                     | Use `acceptEdits` or `dontAsk`    |
| Agent produces wrong format | Missing output format specification       | Add explicit format in agent body |

## Iterative Testing Process

1. **Create initial agent** using workflow
2. **Test with simple prompt** - does it invoke?
3. **Review agent output** - does it match expectations?
4. **Identify issues** - wrong tools, wrong format, unclear instructions?
5. **Edit agent file** - fix identified issues
6. **Test again** - verify fixes work
7. **Test edge cases** - boundary conditions and failures
8. **Document learnings** - add notes to agent if needed

## Testing Tips

**Start simple**: Test with trivial examples before complex real-world tasks

**Test tool access**: Explicitly verify the agent can (and cannot) use tools as intended

**Test skills loading**: If agent uses skills, verify skill content is available in agent's context

**Test descriptions**: Try variations of trigger phrases to ensure agent activates appropriately

**Test with different models**: If using `inherit`, test with different parent models to verify behavior

**Read the output**: Actually read what the agent produces, don't just check for absence of errors
