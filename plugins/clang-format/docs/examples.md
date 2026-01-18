# Usage Examples

Concrete, real-world examples of using the clang-format Configuration plugin with Claude Code.

## Example 1: Minimal-Disruption Configuration for Legacy Codebase

**Scenario**: You're introducing clang-format to a 50,000-line C++ codebase with 5 years of git history. The code has established formatting conventions but they were never codified. You want clang-format to enforce consistency going forward without creating massive whitespace-only diffs that complicate rebasing and code review.

**Steps**:

1. Request code style analysis:

```
Analyze the formatting patterns in src/ and generate a .clang-format configuration that preserves our existing style with minimal changes
```

2. Claude examines representative files and identifies patterns:
   - Brace placement: K&R style (opening brace on same line)
   - Indentation: 4 spaces, no tabs
   - Column limit: Varies, mostly 100 columns
   - Pointer alignment: `int* ptr` (pointer on type)
   - Spacing: Spaces around operators, no space before semicolon

3. Claude generates 3 configuration hypotheses:

```
Hypothesis 1: Based on LLVM style
Hypothesis 2: Based on Google style (modified)
Hypothesis 3: Based on WebKit style
```

4. Claude tests each hypothesis on 5 representative files and scores them:

```
Configuration Impact Scores:

Hypothesis 1 (LLVM-based):
  Line changes: 47 × 10 = 470
  Whitespace changes: 312 × 1 = 312
  Total impact: 782

Hypothesis 2 (Google-based, modified):
  Line changes: 12 × 10 = 120
  Whitespace changes: 89 × 1 = 89
  Total impact: 209

Hypothesis 3 (WebKit-based):
  Line changes: 23 × 10 = 230
  Whitespace changes: 156 × 1 = 156
  Total impact: 386
```

5. Claude presents the winning configuration (Hypothesis 2) with example diffs:

```diff
# src/core/engine.cpp (before)
-  if (condition) {
+  if (condition) {
     doSomething();
   }

# Whitespace adjustment only - no structural changes
```

6. Claude provides test commands:

```bash
# Test on your own files
clang-format --style="/tmp/myproject/hypothesis_2.clang-format" src/core/engine.cpp | diff - src/core/engine.cpp

# Test on entire directory
find src/ -name '*.cpp' | while read f; do
  clang-format --style="/tmp/myproject/hypothesis_2.clang-format" "$f" | diff -u "$f" - | diffstat
done
```

7. You approve the configuration

8. Claude writes the final configuration to `.clang-format`

**Result**: You have a .clang-format file that matches your existing style with only 209 total impact points (12 line changes, 89 whitespace adjustments across 5 representative files). Future commits will maintain this style consistently.

---

## Example 2: Setting Up New Project with Google C++ Style

**Scenario**: Starting a new C++ project and your team uses Google C++ Style Guide. You want 4-space indentation, 120-column limit, and automatic formatting in git commits.

**Steps**:

1. Request configuration:

```
Create a .clang-format file using Google C++ style with 4-space indentation and 120-column limit
```

2. Claude copies the template:

```bash
# Claude executes
cp ~/.claude/plugins/clang-format/skills/clang-format/assets/configs/google-cpp-modified.clang-format /path/to/project/.clang-format
```

3. Claude verifies the configuration:

```yaml
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 120
# ... additional Google-specific options
```

4. Request git hook setup:

```
Set up a git hook to automatically format staged C++ files before commit
```

5. Claude creates `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-clang-format
    rev: v19.1.7
    hooks:
      - id: clang-format
```

6. Claude installs the hook:

```bash
pre-commit install
```

7. Test the setup:

```bash
# Create test file with poor formatting
echo 'int main(){int x=5;return 0;}' > test.cpp
git add test.cpp
git commit -m "Test formatting"

# Hook runs and formats the file automatically
```

**Result**: Your project has Google C++ formatting enforced automatically on every commit. All team members get consistent formatting without manual intervention.

---

## Example 3: Troubleshooting Unexpected Brace Placement

**Scenario**: You've configured clang-format but it's putting opening braces on the next line (Allman style) when you want them on the same line (K&R style). You're not sure which option controls this.

**Steps**:

1. Describe the problem:

```
clang-format is putting opening braces on a new line after function definitions, but I want them on the same line. How do I fix this?
```

2. Claude verifies your current configuration:

```bash
clang-format --dump-config src/main.cpp | grep -i brace
```

Output shows:

```yaml
BreakBeforeBraces: Allman
```

3. Claude consults references/03-braces.md and explains:

```
The BreakBeforeBraces option controls brace placement.

Current setting: Allman (braces on new line)
Desired setting: Attach or K&R (braces on same line)

For K&R style (opening brace on same line for functions):
BreakBeforeBraces: Linux

For modern C++ style (opening brace on same line for everything):
BreakBeforeBraces: Attach
```

4. Claude suggests configuration change:

```yaml
# Change from:
BreakBeforeBraces: Allman

# To:
BreakBeforeBraces: Attach
```

5. Claude provides test command:

```bash
# Test the change
clang-format --style="{BasedOnStyle: llvm, BreakBeforeBraces: Attach}" src/main.cpp | diff - src/main.cpp
```

6. Verify the fix:

```cpp
// Before (Allman):
void function()
{
  // body
}

// After (Attach):
void function() {
  // body
}
```

**Result**: You understand which option controls brace placement and have updated your configuration to achieve K&R style.

---

## Example 4: Multi-Language Configuration for Monorepo

**Scenario**: Your repository contains C++, JavaScript, and Java code. Each language needs different formatting rules (C++ uses 4-space indent, JavaScript uses 2-space indent, Java uses 4-space indent with different brace style).

**Steps**:

1. Request multi-language configuration:

```
Create a .clang-format file that formats C++ with 4-space indent, JavaScript with 2-space indent, and Java with 4-space indent but Allman brace style
```

2. Claude uses the multi-language template as a starting point:

```yaml
---
# C++ configuration (default)
BasedOnStyle: Google
Language: Cpp
IndentWidth: 4
BreakBeforeBraces: Attach
---
# JavaScript configuration
Language: JavaScript
IndentWidth: 2
BreakBeforeBraces: Attach
---
# Java configuration
Language: Java
IndentWidth: 4
BreakBeforeBraces: Allman
```

3. Claude explains the structure:

```
Each language section starts with --- separator
First section without Language: key applies to all languages (defaults)
Subsequent sections override defaults for specific languages
```

4. Test on each language:

```bash
# C++
clang-format src/main.cpp | diff - src/main.cpp

# JavaScript
clang-format src/app.js | diff - src/app.js

# Java
clang-format src/Main.java | diff - src/Main.java
```

5. Verify correct indentation for each:

```cpp
// C++ - 4 spaces
class Example {
    void method() {
        int x = 5;
    }
};
```

```javascript
// JavaScript - 2 spaces
class Example {
  method() {
    const x = 5;
  }
}
```

```java
// Java - 4 spaces, Allman braces
class Example
{
    void method()
    {
        int x = 5;
    }
}
```

**Result**: Single .clang-format file correctly formats all three languages according to their specific requirements.

---

## Example 5: CI/CD Formatting Enforcement

**Scenario**: You want to enforce formatting in your CI/CD pipeline. Pull requests should fail if code is not properly formatted, without modifying files.

**Steps**:

1. Request CI configuration:

```
Set up a CI check that fails if any C++ files are not formatted according to our .clang-format
```

2. Claude provides GitHub Actions workflow:

```yaml
name: Code Formatting Check

on: [push, pull_request]

jobs:
  format-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install clang-format
        run: sudo apt-get install -y clang-format

      - name: Check formatting
        run: |
          find src include -name '*.cpp' -o -name '*.h' | \
          xargs clang-format --dry-run --Werror
```

3. Explain the options:

```
--dry-run: Preview changes without modifying files
--Werror: Treat formatting issues as errors (non-zero exit code)

The pipeline fails if any file would be changed by clang-format
```

4. Test locally before pushing:

```bash
# Run the same check locally
find src include -name '*.cpp' -o -name '*.h' | xargs clang-format --dry-run --Werror

# If changes needed, apply them:
find src include -name '*.cpp' -o -name '*.h' | xargs clang-format -i
```

5. Add helpful CI output:

```yaml
- name: Check formatting (with diff)
  run: |
    NEEDS_FORMAT=$(find src include -name '*.cpp' -o -name '*.h' | \
                   xargs clang-format --dry-run --Werror 2>&1)
    if [ -n "$NEEDS_FORMAT" ]; then
      echo "The following files need formatting:"
      echo "$NEEDS_FORMAT"
      echo ""
      echo "Run: find src include -name '*.cpp' -o -name '*.h' | xargs clang-format -i"
      exit 1
    fi
```

**Result**: Your CI pipeline enforces consistent formatting. Contributors receive clear feedback about formatting issues and know exactly how to fix them.

---

## Example 6: Gradual Adoption with Include Patterns

**Scenario**: You have a large codebase and want to gradually adopt clang-format, starting with the `src/new-feature/` directory before rolling it out to the entire codebase.

**Steps**:

1. Request gradual adoption strategy:

```
I want to use clang-format only on src/new-feature/ for now, not the entire codebase. How do I set this up?
```

2. Claude explains the approach:

```
clang-format doesn't have built-in directory filtering in .clang-format
Instead, control which files are formatted using git hooks or CI configuration
```

3. Claude provides git hook for selective formatting:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Only format files in src/new-feature/
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '^src/new-feature/.*\.\(cpp\|h\)$'); do
  clang-format -i "$file"
  git add "$file"
done
```

4. Claude provides selective CI check:

```yaml
- name: Check formatting (new-feature only)
  run: |
    find src/new-feature -name '*.cpp' -o -name '*.h' | \
    xargs clang-format --dry-run --Werror
```

5. Test the setup:

```bash
# Create test files
mkdir -p src/new-feature src/legacy
echo 'int main(){return 0;}' > src/new-feature/test.cpp
echo 'int main(){return 0;}' > src/legacy/test.cpp

# Stage both
git add src/new-feature/test.cpp src/legacy/test.cpp

# Commit (hook formats only new-feature)
git commit -m "Test selective formatting"

# Verify: new-feature is formatted, legacy is not
```

6. Document the strategy:

```markdown
# Formatting Policy

- `src/new-feature/`: Enforced via git hooks and CI
- Rest of codebase: Manual formatting only

As modules are refactored, move them to formatted directories.
```

**Result**: You can adopt clang-format incrementally without disrupting existing code. New features get consistent formatting while legacy code remains untouched until refactoring.

---

[← Back to README](../README.md) | [Skills Reference](./skills.md)
