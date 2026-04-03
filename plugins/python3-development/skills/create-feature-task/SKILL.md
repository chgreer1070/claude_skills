---
name: create-feature-task
description: Use when creating a new feature task with structured tracking, phases, and documentation. Activates on "create a feature task", "set up development tracking", or "plan a feature implementation" requests. Produces a comprehensive feature development task with acceptance criteria, phase breakdown, and tracking artifacts ready for SAM pipeline execution.
argument-hint: <feature_name_and_description>
user-invocable: true
---

# Create Feature Development Task

Set up a comprehensive feature development task with proper tracking, phases, and documentation.

## Execution Steps

Consult `../python3-development/references/python3-standards.md` when applying shared architecture, typing, testing, or CLI rules; full standards, graphs, and amendment process are documented there.

### 1. Parse Feature Requirements

- Extract feature name and description from arguments
- Identify key requirements and constraints
- Determine complexity and scope

### 2. Generate Task Structure

- Customize phases based on feature type
- Add specific acceptance criteria
- Include relevant technical considerations

### 3. Create Task Documentation

Create task file at `.claude/tasks/{feature-name}.md` with:

```markdown
# Feature: {Feature Name}

## Overview
{Brief description}

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Technical Approach
{High-level design}

## Phases

### Phase 1: Design
- [ ] Review existing patterns
- [ ] Create interface definitions
- [ ] Document edge cases

### Phase 2: Implementation
- [ ] Core functionality
- [ ] Error handling
- [ ] Integration points

### Phase 3: Testing
- [ ] Unit tests (80% minimum coverage)
- [ ] Integration tests
- [ ] Edge case coverage

### Phase 4: Documentation
- [ ] Code documentation
- [ ] Usage examples
- [ ] API documentation (if applicable)

## Acceptance Criteria
- [ ] All tests pass
- [ ] Coverage meets minimum
- [ ] Documentation complete
- [ ] Code review approved

## Context Preservation
- Initial requirements: {captured}
- Key decisions: {recorded}
- Dependencies: {identified}
- Risks: {noted}
```

### 4. Set Up Tracking

- Add task to TODO list using TaskCreate tool
- Create initial checkpoints
- Set up progress markers

## Context Preservation

When creating tasks, preserve:

- Initial requirements from user
- Key technical decisions made
- File locations involved
- Dependencies identified
- Risk factors noted

## Integration

| Step          | Command/Action                                         |
| ------------- | ------------------------------------------------------ |
| Prerequisites | Clear feature requirements                             |
| Follow-up     | Use `python3-development:python-cli-architect` agent for implementation    |
| Related       | `comprehensive-test-review`, `python3-development:python-pytest-architect` |

## Example Usage

```text
/python3-development:create-feature-task Add user authentication with OAuth2 support
/python3-development:create-feature-task Implement rate limiting for API endpoints
/python3-development:create-feature-task Create CLI command for database migrations
```
