# Stack Profile Template

Use this template when adding a new stack profile.

---

## Template

```markdown
# Stack Profile: {display_name}

**Stack ID**: {stack-id}
**Language**: {language}
**Extends**: {parent-stack} (optional)

---

## Architecture Patterns

- {Reference to architecture docs or research/}

---

## Toolchain Presets

### pyproject.toml (Python)

```toml
[snippet]
```

### package.json (Node/TypeScript)

```json
{snippet}
```

---

## Reference Examples

- {Path to example project}
- {Path to task template}

---

## Research References

- research/{category}/{entry}.md

---

## Output Contract

STATUS: DONE | BLOCKED | FAILED
SUMMARY: ...
ARTIFACTS: ...
VALIDATION: ...
NOTES: ...
```

---

## Checklist

- [ ] Stack ID is unique
- [ ] Language matches parent manifest
- [ ] Architecture patterns documented
- [ ] Toolchain presets tested
- [ ] Research refs added
