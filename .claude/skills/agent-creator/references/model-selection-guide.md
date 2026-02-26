# Model Selection Guide

Cost/speed/capability comparison and decision tree for choosing `model` in agent frontmatter.

---

| Model     | Cost   | Speed    | Capability | Use When                                             |
| --------- | ------ | -------- | ---------- | ---------------------------------------------------- |
| `haiku`   | Low    | Fast     | Basic      | Simple read-only analysis, quick searches            |
| `sonnet`  | Medium | Balanced | Strong     | Most agents - code review, debugging, docs           |
| `opus`    | High   | Slower   | Maximum    | Complex reasoning, difficult debugging, architecture |
| `inherit` | Parent | Parent   | Parent     | Agent should match conversation context              |

## Decision Tree

1. Is it read-only exploration? → `haiku`
2. Does it need to reason about complex code? → `sonnet`
3. Does it need deep architectural understanding? → `opus`
4. Should it match the user's current model? → `inherit`
