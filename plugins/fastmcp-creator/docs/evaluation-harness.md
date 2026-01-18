# Evaluation Harness Guide

This guide explains how to use the included evaluation harness to test your MCP server's effectiveness with LLMs.

## Overview

The evaluation harness tests whether Claude (or other LLMs) can effectively use your MCP server to answer realistic, complex questions. This is the best way to validate that your server provides useful, well-designed tools.

## Purpose

Unlike traditional unit tests that check individual functions, evaluations test:
- Can an LLM discover the right tools for a task?
- Are tool descriptions clear enough for proper tool selection?
- Can an LLM combine multiple tools to solve complex problems?
- Do error messages guide the LLM toward correct usage?
- Is the tool output format consumable by LLMs?

## Installation

### Prerequisites

- Python 3.11+
- Anthropic API key
- Your MCP server (Python or TypeScript)

### Install Dependencies

```bash
cd plugins/fastmcp-creator/skills/fastmcp-creator
pip install -r scripts/requirements.txt
```

This installs:
- `anthropic` - Claude API client
- `httpx` - HTTP client for server connections
- `python-dotenv` - Environment variable management

## Creating Evaluations

### Evaluation XML Format

```xml
<evaluation>
  <qa_pair>
    <question>What is the most popular repository in the python-sdk organization?</question>
    <answer>fastmcp</answer>
  </qa_pair>

  <qa_pair>
    <question>How many open issues are there in the fastmcp repository?</question>
    <answer>42</answer>
  </qa_pair>
</evaluation>
```

### Question Guidelines

Each question MUST be:

**Independent**: Not dependent on other questions or previous state
```xml
<!-- GOOD -->
<question>What is the title of issue #123?</question>

<!-- BAD - depends on previous question -->
<question>What is the status of that issue?</question>
```

**Read-Only**: Only uses non-destructive operations
```xml
<!-- GOOD -->
<question>How many files are in the src/ directory?</question>

<!-- BAD - modifies state -->
<question>Create a new file and count how many files exist</question>
```

**Complex**: Requires multiple tool calls and deep exploration
```xml
<!-- GOOD -->
<question>Which user has contributed the most code to repositories with Python in their description?</question>

<!-- BAD - single tool call -->
<question>List all repositories</question>
```

**Realistic**: Based on real use cases humans would care about
```xml
<!-- GOOD -->
<question>What are the most common error types in failed CI runs this month?</question>

<!-- BAD - artificial scenario -->
<question>Calculate the sum of all issue numbers</question>
```

**Verifiable**: Single, clear answer that can be verified by string comparison
```xml
<!-- GOOD -->
<question>What is the current version in package.json?</question>
<answer>1.2.3</answer>

<!-- BAD - ambiguous answer -->
<question>What is the project about?</question>
<answer>It helps with stuff</answer>
```

**Stable**: Answer won't change over time
```xml
<!-- GOOD - uses fixed issue number -->
<question>What was the title of issue #1?</question>

<!-- BAD - answer changes daily -->
<question>How many issues were opened today?</question>
```

### Creating Your Evaluation File

1. **Inspect Available Tools**
   ```
   Ask Claude: "List all tools available in this MCP server"
   ```

2. **Explore Available Data**
   ```
   Use read-only operations to understand what data exists:
   - List repositories
   - Check existing issues
   - View file contents
   - Browse available resources
   ```

3. **Generate 10 Complex Questions**
   ```
   Ask Claude: "Based on these tools, generate 10 complex, realistic questions
   that would require multiple tool calls to answer"
   ```

4. **Verify Each Answer**
   ```
   Solve each question yourself using the tools to verify the correct answer
   ```

5. **Save as XML**
   ```xml
   <evaluation>
     <qa_pair>
       <question>Your complex question here</question>
       <answer>Single verifiable answer</answer>
     </qa_pair>
     <!-- ... 9 more qa_pairs -->
   </evaluation>
   ```

## Running Evaluations

### Basic Usage

```bash
# Set API key
export ANTHROPIC_API_KEY=your_api_key

# Run evaluation
python scripts/evaluation.py \
  -t stdio \
  -c python \
  -a path/to/your_server.py \
  evaluation.xml
```

### Transport Options

#### STDIO Transport (Default)

For servers using STDIO (standard input/output):

```bash
python scripts/evaluation.py \
  -t stdio \
  -c python \
  -a my_server.py \
  evaluation.xml
```

**Parameters**:
- `-t stdio` - Use STDIO transport
- `-c python` - Command to run server (python, node, npx, etc.)
- `-a my_server.py` - Server file path

**Examples**:
```bash
# Python server
python scripts/evaluation.py -t stdio -c python -a github_mcp.py eval.xml

# Node server
python scripts/evaluation.py -t stdio -c node -a dist/server.js eval.xml

# npx with package
python scripts/evaluation.py -t stdio -c npx -a -y @org/mcp-server eval.xml
```

#### HTTP Transport

For servers using HTTP:

```bash
# Start your server first
python my_server.py --transport http --port 8000

# In another terminal
python scripts/evaluation.py \
  -t http \
  -u http://localhost:8000 \
  evaluation.xml
```

**Parameters**:
- `-t http` - Use HTTP transport
- `-u URL` - Server URL

### Command Options

```
usage: evaluation.py [-h] -t {stdio,http} [-c COMMAND] [-a ARGS [ARGS ...]]
                     [-u URL] [--model MODEL] [--max-tokens MAX_TOKENS]
                     evaluation_file

Run MCP server evaluations

positional arguments:
  evaluation_file       Path to XML evaluation file

optional arguments:
  -h, --help            Show help message
  -t {stdio,http}       Transport type
  -c COMMAND            Command to run server (for stdio)
  -a ARGS               Server arguments (for stdio)
  -u URL                Server URL (for http)
  --model MODEL         Claude model (default: claude-sonnet-4-20250514)
  --max-tokens MAX_TOKENS
                        Max tokens per response (default: 4096)
```

### Example Output

```
Running evaluation with 10 questions...

Question 1: What is the most popular repository?
Expected: fastmcp
LLM Answer: fastmcp
✓ PASS

Question 2: How many open issues in fastmcp?
Expected: 42
LLM Answer: 45
✗ FAIL

...

Results: 8/10 passed (80%)
```

## Interpreting Results

### High Pass Rate (80-100%)

Your server is working well:
- Tool descriptions are clear
- Tools provide useful functionality
- Error messages are helpful
- Output formats are consumable

### Medium Pass Rate (50-79%)

Areas to improve:
- Review failed questions for patterns
- Check if tool descriptions are clear
- Ensure tools return actionable information
- Verify error messages guide toward correct usage

### Low Pass Rate (0-49%)

Significant issues:
- Tools may not provide needed functionality
- Tool descriptions may be unclear or misleading
- Output format may be too complex or truncated
- Error handling may need improvement
- Tools may not compose well for complex workflows

## Debugging Failed Questions

### Step 1: Run Question Manually

```
Start MCP server in tmux:
$ tmux new -s mcp
$ python my_server.py

Open Claude Desktop and manually try to answer the failed question.
Observe:
- Which tools does Claude attempt to use?
- Are error messages clear?
- Does output format make sense?
- Does Claude need tools that don't exist?
```

### Step 2: Check Tool Usage

```python
# Add logging to your tools
@mcp.tool()
def my_tool(param: str) -> dict:
    logger.info(f"my_tool called with param={param}")
    # ... implementation
```

Review logs to see:
- Are tools being called with expected parameters?
- Are tools returning expected data?
- Are errors being raised appropriately?

### Step 3: Improve Based on Findings

**Common Issues and Fixes**:

| Issue | Fix |
|-------|-----|
| Tool not selected | Improve description with trigger keywords |
| Wrong parameters used | Add Field() descriptions with examples |
| Output too verbose | Add truncation and concise mode |
| Error not helpful | Return actionable guidance in error message |
| Missing functionality | Add new tool or extend existing tool |
| Tool combinations fail | Add composite tool for common workflow |

## Best Practices

### Do's

✅ **Create 10+ questions** for comprehensive coverage
✅ **Test edge cases** like empty results, rate limits, errors
✅ **Vary complexity** from simple lookups to multi-step workflows
✅ **Use realistic scenarios** based on actual use cases
✅ **Verify answers yourself** before using in evaluation
✅ **Run regularly** as you modify tools
✅ **Keep stable** by using fixed test data when possible

### Don'ts

❌ **Don't use time-dependent questions** (today, now, latest)
❌ **Don't use destructive operations** (create, delete, update)
❌ **Don't make questions dependent** on each other
❌ **Don't use ambiguous answers** (subjective, approximate)
❌ **Don't test a single tool** per question (too simple)
❌ **Don't skip verification** of expected answers

## Continuous Improvement

### Iteration Cycle

1. **Create initial evaluation** with 10 questions
2. **Run evaluation** and note pass rate
3. **Debug failures** by running questions manually
4. **Improve tools** based on findings
5. **Re-run evaluation** to verify improvements
6. **Add new questions** for uncovered scenarios
7. **Repeat** until pass rate is 90%+

### When to Update Evaluations

- After adding new tools
- After modifying existing tools
- When discovering new use cases
- When users report confusion
- Before releasing new versions
- As data sources evolve

## Example: GitHub MCP Server Evaluation

```xml
<evaluation>
  <qa_pair>
    <question>What is the full name (owner/repo format) of the repository with the most stars in the octocat organization?</question>
    <answer>octocat/Hello-World</answer>
  </qa_pair>

  <qa_pair>
    <question>How many Python files are in the src directory of the octocat/linguist repository?</question>
    <answer>23</answer>
  </qa_pair>

  <qa_pair>
    <question>What is the title of the oldest open issue in the octocat/Hello-World repository?</question>
    <answer>Add documentation for API endpoints</answer>
  </qa_pair>

  <qa_pair>
    <question>Which user has the most commits across all repositories in the octocat organization?</question>
    <answer>octocat</answer>
  </qa_pair>

  <qa_pair>
    <question>What is the programming language with the most bytes of code in the octocat/linguist repository?</question>
    <answer>Ruby</answer>
  </qa_pair>

  <qa_pair>
    <question>How many repositories in the octocat organization have continuous integration configured?</question>
    <answer>15</answer>
  </qa_pair>

  <qa_pair>
    <question>What is the most common label across all open issues in octocat organization repositories?</question>
    <answer>bug</answer>
  </qa_pair>

  <qa_pair>
    <question>Which repository in the octocat organization was most recently updated?</question>
    <answer>octocat/test-repo</answer>
  </qa_pair>

  <qa_pair>
    <question>How many lines of code were added in the most recent commit to the octocat/Hello-World repository?</question>
    <answer>127</answer>
  </qa_pair>

  <qa_pair>
    <question>What is the file path of the largest Python file in the octocat/linguist repository?</question>
    <answer>src/language_detection/detector.py</answer>
  </qa_pair>
</evaluation>
```

Each question:
- ✅ Independent (can be answered alone)
- ✅ Read-only (list, get, search operations only)
- ✅ Complex (requires multiple tool calls)
- ✅ Realistic (based on actual GitHub use cases)
- ✅ Verifiable (single, clear answer)
- ✅ Stable (uses fixed organization and repositories)

## Troubleshooting

### Server Connection Errors

**Problem**: `Failed to connect to MCP server`

**Solutions**:
```bash
# Check server syntax
python -m py_compile my_server.py

# Test server starts
timeout 5s python my_server.py
# Should hang (indicating server is running)

# Check transport matches
# If server uses HTTP, use -t http
# If server uses STDIO, use -t stdio
```

### API Key Errors

**Problem**: `anthropic.AuthenticationError`

**Solution**:
```bash
# Set API key
export ANTHROPIC_API_KEY=your_api_key

# Or use .env file
echo "ANTHROPIC_API_KEY=your_api_key" > .env
```

### Timeout Errors

**Problem**: Questions timing out

**Solutions**:
- Increase max tokens: `--max-tokens 8192`
- Simplify questions to require fewer tool calls
- Optimize tool performance (add caching, reduce API calls)
- Check for rate limiting in server logs

### Inconsistent Results

**Problem**: Same question passes sometimes, fails other times

**Causes**:
- Time-dependent data (use fixed test data)
- Rate limiting (add delays between questions)
- Non-deterministic tool behavior (add caching)
- Model variability (expected, rerun to verify)

## Additional Resources

- [Evaluation Guide Reference](../skills/fastmcp-creator/references/evaluation-guide.md) - Complete evaluation creation guidance
- [Example Evaluation](../skills/fastmcp-creator/scripts/example_evaluation.xml) - Sample evaluation format
- [MCP Best Practices](../skills/fastmcp-creator/references/mcp-best-practices.md) - Tool design guidelines
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) - Framework reference
