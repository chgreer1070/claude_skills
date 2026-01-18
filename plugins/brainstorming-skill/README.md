# Brainstorming Skill

Structured idea generation using 30+ research-validated prompt patterns across 14 categories. Use when you need creative solutions, strategic planning, content ideation, or systematic exploration of possibilities.

## Installation

**From Marketplace:**

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install brainstorming-skill@jamie-bitflight-skills
```

**For Development:**

```bash
claude --plugin-dir /home/user/claude_skills/plugins/brainstorming-skill
```

## Capabilities

| Type | Name | Description |
|------|------|-------------|
| Skill | [brainstorming-skill](./skills/brainstorming-skill/SKILL.md) | This skill should be used when users need to generate ideas, explore creative solutions, or systematically brainstorm approaches to problems. Use when users request help with ideation, content planning, product features, marketing campaigns, strategic planning, creative writing, or any task requiring structured idea generation. The skill provides 30+ research-validated prompt patterns across 14 categories with exact templates, success metrics, and domain-specific applications. |

## Quick Start

Activate the skill when you need idea generation:

```text
@brainstorming-skill
I need to brainstorm features for a mobile app that helps remote teams collaborate better.
```

The skill will apply appropriate brainstorming patterns such as:
- Perspective Multiplication (from different user roles)
- SCAMPER technique (modify existing collaboration patterns)
- Constraint-Based Ideation (within technical or budget limits)
- Analogical Transfer (from other successful collaboration tools)

## Pattern Categories

The skill includes 14 systematic pattern categories:

1. Perspective Multiplication - Multiple viewpoints and stakeholder angles
2. Constraint Variation - Explore idea space through artificial constraints
3. Inversion & Negative Space - Reverse thinking for novel solutions
4. Analogical Transfer - Apply patterns from different domains
5. Systematic Feature Decomposition - SCAMPER and attribute-based ideation
6. Scenario Exploration - Future-based and "what if" thinking
7. Constraint-Based Structured Ideation - Build within hard constraints
8. Chain-of-Thought Reasoning - Multi-step refinement processes
9. Combination & Morphological Exploration - Force novel feature combinations
10. Assumption Challenge - Question premises and invert assumptions
11. Fill-in-the-Blank Templates - Structured completion formats
12. Competitive Positioning - Differentiation matrix approaches
13. Trend Extrapolation - Project current trends forward
14. Domain-Specific Prompt Frameworks - Specialized patterns for specific industries

Each pattern includes exact prompt templates, output format specifications, concrete examples, and reported success metrics.

## License

Version 1.0.0
