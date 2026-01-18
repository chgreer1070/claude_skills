# Skills Reference

This document provides detailed reference for the brainstorming-skill included in this plugin.

## brainstorming-skill

**Location**: `skills/brainstorming-skill/SKILL.md`

**Description**: This skill should be used when users need to generate ideas, explore creative solutions, or systematically brainstorm approaches to problems. Use when users request help with ideation, content planning, product features, marketing campaigns, strategic planning, creative writing, or any task requiring structured idea generation. The skill provides 30+ research-validated prompt patterns across 14 categories with exact templates, success metrics, and domain-specific applications.

**User Invocable**: Yes

**Model**: Inherits from session default

**Allowed Tools**: Inherits from session default

### When to Use

Activate this skill when users need:

- **Idea generation** for products, features, or content
- **Creative problem-solving** approaches
- **Marketing campaign** concepts
- **Strategic planning** and decision-making
- **Content creation** (blog posts, social media, presentations)
- **Product feature** ideation
- **Business strategy** development
- **Creative writing** (plot development, character creation)
- **QA test case** brainstorming
- **Innovation workshops** or facilitation
- **Breaking through creative blocks**
- **Systematic exploration** of solution spaces

### Activation

The skill activates automatically when Claude detects brainstorming-related requests. You can also invoke it explicitly:

```text
@brainstorming-skill

or

Skill(command: "brainstorming-skill")
```

### Pattern Categories

The skill organizes brainstorming techniques into 14 systematic categories, each with specific use cases and expected outcomes:

#### 1. Perspective Multiplication

Generate ideas from multiple viewpoints and stakeholder angles.

**Use Cases:**
- Understanding diverse customer needs
- Identifying stakeholder concerns
- Building empathy in product design
- Creating inclusive solutions

**Expected Output:** 8-15 ideas from 3-5 different perspectives with reasoning for each

#### 2. Constraint Variation

Explore idea space through artificial constraints.

**Use Cases:**
- Working with limited resources
- Forcing creative problem-solving
- Finding innovative solutions within boundaries
- Testing idea resilience

**Expected Output:** 5-10 ideas with explicit constraint satisfaction analysis

#### 3. Inversion & Negative Space

Use reverse thinking to find novel solutions.

**Use Cases:**
- Breaking conventional thinking
- Identifying hidden assumptions
- Finding contrarian approaches
- Avoiding common pitfalls

**Expected Output:** 3-7 breakthrough ideas that challenge norms

#### 4. Analogical Transfer

Apply patterns from different domains.

**Use Cases:**
- Cross-industry innovation
- Learning from successful models
- Adapting proven approaches
- Inspiration from unexpected sources

**Expected Output:** 5-10 ideas with explicit analogies explained

#### 5. Systematic Feature Decomposition

SCAMPER and attribute-based ideation.

**Use Cases:**
- Improving existing products
- Feature enhancement
- Systematic exploration
- Incremental innovation

**Expected Output:** 7-12 variations with transformation method identified

#### 6. Scenario Exploration

Future-based and "what if" thinking.

**Use Cases:**
- Strategic planning
- Risk assessment
- Future-proofing
- Contingency planning

**Expected Output:** 3-5 detailed scenarios with implications

#### 7. Constraint-Based Structured Ideation

Build within hard constraints.

**Use Cases:**
- Budget-limited projects
- Time-sensitive development
- Resource-constrained environments
- Practical implementation focus

**Expected Output:** 5-8 implementable ideas with resource breakdown

#### 8. Chain-of-Thought Reasoning

Multi-step refinement processes.

**Use Cases:**
- Deep analysis needed
- Complex problem-solving
- Quality over quantity
- Iterative improvement

**Expected Output:** 3-5 deeply refined ideas with reasoning chains

#### 9. Combination & Morphological Exploration

Force novel feature combinations.

**Use Cases:**
- Innovation through recombination
- Feature matrix exploration
- Systematic combination testing
- Discovering synergies

**Expected Output:** 10-20 combinations with viability assessment

#### 10. Assumption Challenge

Question premises and invert assumptions.

**Use Cases:**
- Challenging status quo
- Finding hidden constraints
- Breaking paradigms
- Uncovering biases

**Expected Output:** 3-7 assumption-free ideas

#### 11. Fill-in-the-Blank Templates

Structured completion formats.

**Use Cases:**
- Rapid ideation
- Consistent format needed
- Team workshops
- Templated outputs

**Expected Output:** 5-15 completed templates

#### 12. Competitive Positioning

Differentiation matrix approaches.

**Use Cases:**
- Market analysis
- Competitive strategy
- Differentiation planning
- Value proposition development

**Expected Output:** Matrix with 5-10 positioning options

#### 13. Extreme Scaling

10x thinking and exponential scenarios.

**Use Cases:**
- Breakthrough innovation
- Disruption planning
- Ambitious goal setting
- Moonshot thinking

**Expected Output:** 3-5 radical ideas with scaling implications

#### 14. Stakeholder & Empathy-Based

Customer journey and persona patterns.

**Use Cases:**
- User-centric design
- Customer experience improvement
- Empathy-driven innovation
- Journey mapping

**Expected Output:** 5-10 ideas mapped to customer touchpoints

### Pattern Selection Guide

Choose patterns based on your objectives:

| Objective | Recommended Patterns | Expected Output |
|-----------|---------------------|-----------------|
| Rapid quantity (8-15 ideas) | Perspective Multiplication | Multiple viewpoints, 15+ ideas |
| Quality/depth | Multi-stage refinement with constraint variation | 3-5 deeply refined ideas |
| Breakthrough innovation | Inversion + Extreme Scaling | 3-7 paradigm-shifting concepts |
| Practical implementation | Constraint-Based patterns | 5-8 implementable ideas with resources |
| Market differentiation | Competitive Positioning | Matrix with 5-10 unique positions |
| Customer-centric features | Stakeholder & Empathy-Based | 5-10 user journey-mapped ideas |

### Key Research Findings

The patterns in this skill are based on empirical research:

- **Constraint effectiveness**: Constraint-based patterns generate 20-30% MORE ideas than open-ended prompts
- **Format specification impact**: Specifying output format (table/numbered list) improves quality without reducing quantity
- **Perspective iteration**: Multiple perspective iteration (3-5 viewpoints) consistently outperforms single-perspective approaches
- **Reasoning visibility**: Requiring reasoning visibility ("explain why") increases implementability by 40%
- **Pattern structure**: Successful patterns share: role definition, constraint specification, output format, reasoning requirements

### Output Format Optimization

The skill uses research-validated output format specifications:

- **Numbered lists** > bullet points (better for idea tracking)
- **Table format** with columns: Idea | Reasoning | Implementation | Trade-offs (forces completeness)
- **Explicit reasoning** requirement (increases quality 40%)
- **Word count ranges** (200-400 words prevents both brevity and verbosity)

### Reference Files

The skill includes extensive reference materials for progressive disclosure:

**Main Pattern Library:**
- [pattern-categories-and-documentation.md](../skills/brainstorming-skill/references/pattern-categories-and-documentation.md) - All 14 categories with 30+ patterns (1,303 lines)

**Domain Applications:**
- [domain-specific-applications-and-variations.md](../skills/brainstorming-skill/references/domain-specific-applications-and-variations.md) - Marketing, Product Development, QA Testing, Business Strategy, Creative Writing

**Supporting Guides:**
- [pattern-selection-guide.md](../skills/brainstorming-skill/references/pattern-selection-guide.md) - Decision framework
- [synthesis-what-makes-these-patterns-work.md](../skills/brainstorming-skill/references/synthesis-what-makes-these-patterns-work.md) - Effectiveness analysis
- [comprehensive-prompt-library-ready-to-use-templates.md](../skills/brainstorming-skill/references/comprehensive-prompt-library-ready-to-use-templates.md) - Ready-to-use templates
- [executive-summary.md](../skills/brainstorming-skill/references/executive-summary.md) - High-level overview

**Research Sources:**
- [itonics-innovation-platform.md](../skills/brainstorming-skill/references/itonics-innovation-platform.md) - 79 documented prompts
- [machine-learning-mastery.md](../skills/brainstorming-skill/references/machine-learning-mastery.md) - ARCC framework
- [medium-shushant-lakhyani.md](../skills/brainstorming-skill/references/medium-shushant-lakhyani.md) - 10 creative + 10 LinkedIn templates
- [vanderbilt-prompt-patterns.md](../skills/brainstorming-skill/references/vanderbilt-prompt-patterns.md) - 15 academic patterns
- [prompthub-role-prompting.md](../skills/brainstorming-skill/references/prompthub-role-prompting.md) - Empirical validation
- [learn-prompting.md](../skills/brainstorming-skill/references/learn-prompting.md) - Chain-of-Thought patterns
- [better-creator.md](../skills/brainstorming-skill/references/better-creator.md) - 20 content creator techniques
- [linkedin-ruben-hassid.md](../skills/brainstorming-skill/references/linkedin-ruben-hassid.md) - Scaling methodology
- [clickup-templates.md](../skills/brainstorming-skill/references/clickup-templates.md) - Product management prompts
- [software-testing-prompts.md](../skills/brainstorming-skill/references/software-testing-prompts.md) - QA patterns

**Bibliographic Materials:**
- [bibliography-and-source-documentation.md](../skills/brainstorming-skill/references/bibliography-and-source-documentation.md) - Complete citations
- [verification-note.md](../skills/brainstorming-skill/references/verification-note.md) - Evidence strength assessment

See [Reference Materials Guide](./references.md) for detailed descriptions of each file.

### Usage Workflow

**Step 1**: Identify the brainstorming goal (quantity, quality, innovation level, domain)

**Step 2**: Consult Pattern Selection Guide (above) to choose appropriate pattern category

**Step 3**: Claude loads relevant pattern documentation for exact templates

**Step 4**: Pattern applied with your specific context

**Step 5**: If needed, patterns combined or iterated with constraint variation

### Best Practices

When using this skill:

- **Verify pattern match**: Ensure chosen pattern category matches actual need
- **Use exact templates**: Reference patterns use original prompt structures, not paraphrased versions
- **Cite sources**: When discussing specific patterns, skill cites source files
- **Combine patterns**: Single pattern may be insufficient for complex challenges
- **Adjust to context**: Templates adapted to specific situation while preserving structural elements
- **Progressive disclosure**: Start with pattern overview, load detailed references as needed

### Examples

See [docs/examples.md](./examples.md) for real-world usage scenarios demonstrating:
- Marketing campaign ideation
- Product feature brainstorming with constraints
- Breakthrough innovation approaches
- Strategic planning sessions
- Content creation workflows
- QA test case generation

---

[← Back to README](../README.md)
