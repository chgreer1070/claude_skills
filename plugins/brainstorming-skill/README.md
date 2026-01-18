# Brainstorming Skill Plugin

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Claude Code](https://img.shields.io/badge/claude--code-compatible-purple)

A comprehensive Claude Code plugin providing 30+ research-validated brainstorming patterns and prompt templates for systematic idea generation across any domain.

## Features

- **30+ Documented Patterns** - Research-validated brainstorming techniques from 14 authoritative sources
- **14 Pattern Categories** - Organized approaches including perspective multiplication, constraint variation, inversion, analogical transfer, and more
- **Exact Prompt Templates** - Ready-to-use templates with specified output formats and success metrics
- **Domain-Specific Applications** - Specialized patterns for marketing, product development, QA testing, business strategy, and creative writing
- **Evidence-Based Approach** - All patterns verified against original sources with documented effectiveness metrics
- **Progressive Disclosure** - Main skill file with on-demand reference loading for efficient context usage

## Installation

### Prerequisites

- Claude Code 2.1 or later
- No external dependencies required

### Install Plugin

```bash
# Method 1: From plugin directory (if in this repository)
cc plugin install /home/user/claude_skills/plugins/brainstorming-skill

# Method 2: Manual installation
cp -r /home/user/claude_skills/plugins/brainstorming-skill ~/.claude/plugins/
cc plugin reload
```

## Quick Start

The plugin automatically activates when you need idea generation or creative problem-solving:

```text
User: Help me brainstorm marketing campaign ideas for our new product launch

Claude: [Automatically activates brainstorming-skill]
I'll use the Perspective Multiplication pattern to generate ideas from multiple stakeholder viewpoints...

1. Customer Success Manager Perspective:
   - Launch a "Success Stories Early Access" campaign...

2. Sales VP Perspective:
   - Create a "First 100 Customers VIP Program"...

3. Product Manager Perspective:
   - Develop a "Behind the Build" content series...
```

## Capabilities

| Type | Name | Description | User Invocable |
|------|------|-------------|----------------|
| Skill | brainstorming-skill | Research-validated brainstorming patterns and prompt templates for systematic idea generation | Yes |

## Usage

### When to Use

The brainstorming-skill activates automatically when you need:

- **Idea Generation** - Products, features, content, campaigns
- **Creative Problem-Solving** - Systematic exploration of solution spaces
- **Strategic Planning** - Business strategy, decision-making frameworks
- **Content Creation** - Blog posts, social media, presentations
- **Innovation Workshops** - Facilitation and structured ideation
- **Breaking Creative Blocks** - Novel approaches when conventional thinking fails

### Pattern Categories

The skill organizes brainstorming techniques into 14 systematic categories:

1. **Perspective Multiplication** - Generate ideas from multiple viewpoints
2. **Constraint Variation** - Explore idea space through artificial constraints
3. **Inversion & Negative Space** - Reverse thinking for novel solutions
4. **Analogical Transfer** - Apply patterns from different domains
5. **Systematic Feature Decomposition** - SCAMPER and attribute-based ideation
6. **Scenario Exploration** - Future-based and "what if" thinking
7. **Constraint-Based Structured Ideation** - Build within hard constraints
8. **Chain-of-Thought Reasoning** - Multi-step refinement processes
9. **Combination & Morphological Exploration** - Force novel feature combinations
10. **Assumption Challenge** - Question premises and invert assumptions
11. **Fill-in-the-Blank Templates** - Structured completion formats
12. **Competitive Positioning** - Differentiation matrix approaches
13. **Extreme Scaling** - 10x thinking and exponential scenarios
14. **Stakeholder & Empathy-Based** - Customer journey and persona patterns

For detailed pattern documentation, see [Skills Reference](./docs/skills.md).

### Quick Pattern Selection

- **Rapid Quantity (8-15 ideas)** - Use Perspective Multiplication
- **Quality/Depth** - Use Multi-stage refinement with constraint variation
- **Breakthrough Innovation** - Combine Inversion + Extreme Scaling
- **Practical Implementation** - Use Constraint-Based patterns
- **Market Differentiation** - Use Competitive Positioning
- **Customer-Centric Features** - Use Stakeholder & Empathy patterns

## Key Research Findings

The skill is built on empirical research showing:

- Constraint-based patterns generate **20-30% MORE ideas** than open-ended prompts
- Specifying output format (table/numbered list) **improves quality without reducing quantity**
- Multiple perspective iteration (3-5 viewpoints) **consistently outperforms single-perspective**
- Requiring reasoning visibility ("explain why") **increases implementability by 40%**
- Successful patterns share: role definition, constraint specification, output format, reasoning requirements

## Examples

### Marketing Campaign Ideation

```text
User: Generate marketing campaign ideas for a B2B SaaS product targeting enterprise customers

Claude: I'll apply the Perspective Multiplication pattern with three enterprise stakeholder roles:

**CTO Perspective:**
1. "Technical Excellence Showcase" - Whitepaper series demonstrating architecture
2. "Security & Compliance Fast-Track" - Certification guarantee program

**Operations Director Perspective:**
1. "ROI Calculator Challenge" - Interactive tool showing efficiency gains
2. "Process Automation Playbook" - Implementation templates

**CFO Perspective:**
1. "Cost Transparency Commitment" - No hidden fees guarantee
2. "TCO Comparison Dashboard" - Vs. current solutions

Each idea targets specific pain points and decision criteria for these roles.
```

### Product Feature Brainstorming with Constraints

```text
User: Brainstorm features for our mobile app with $20k budget and 4-week timeline

Claude: Using Constraint-Based Structured Ideation with your resource constraints:

| Feature | Implementation | Budget | Timeline | Impact |
|---------|---------------|---------|----------|--------|
| Push notification system | Firebase integration | $2k | 1 week | High retention |
| Offline mode for core features | Local storage + sync | $8k | 2 weeks | Critical UX |
| Social sharing widgets | Pre-built SDK | $1k | 3 days | Viral growth |
| Usage analytics dashboard | Analytics SDK + basic UI | $5k | 1 week | Decision support |
| Dark mode theme | CSS variables + toggle | $1k | 2 days | User preference |

Total: $17k, 3.5 weeks - leaves buffer for testing and polish.
```

### Breakthrough Innovation

```text
User: Help us rethink user onboarding - current approach isn't working

Claude: I'll combine Inversion + Analogical Transfer for breakthrough thinking:

**Step 1: Worst Possible Onboarding (Inversion)**
- Force users through 20-step tutorial before any value
- Require complete profile before accessing features
- Show all features at once without guidance

**Step 2: Flip These to Novel Solutions**
- Inverse: Zero-step onboarding with immediate value access
- Inverse: Optional profile enrichment AFTER seeing value
- Inverse: Progressive feature reveal based on behavior

**Step 3: Cross-Domain Analogies**
- Netflix approach: Instant streaming, personalization emerges from usage
- Hotel check-in: Express option vs. full concierge experience
- Video game: Tutorial disguised as first mission with real outcomes

**Breakthrough Concept:** "Value-First Onboarding"
Users start using core feature immediately (no signup), account creation happens when they try to save/share. Onboarding is the natural product usage, not a separate step.
```

For more examples, see [docs/examples.md](./docs/examples.md).

## Documentation

- [Skills Reference](./docs/skills.md) - Detailed skill documentation
- [Reference Materials](./docs/references.md) - Guide to 6,600+ lines of pattern documentation
- [Usage Examples](./docs/examples.md) - Real-world application scenarios

## Reference Library

The skill includes extensive reference materials:

- **Primary Pattern Documentation** (1,300+ lines) - Complete pattern templates and metrics
- **Domain-Specific Applications** - Marketing, product, QA, business strategy, creative writing
- **Research Sources** - ITONICS, Vanderbilt, PromptHub, Machine Learning Mastery, and more
- **Pattern Selection Guide** - Decision framework for choosing techniques
- **Comprehensive Template Library** - Ready-to-use prompt templates

All patterns are verified against original sources with documented citations.

## Troubleshooting

### Skill Not Activating

If the brainstorming-skill doesn't activate automatically:

1. **Check plugin status**: `/plugin list` - ensure brainstorming-skill is enabled
2. **Use explicit keywords**: Mention "brainstorm", "ideas", "creative solutions" in your request
3. **Manual activation**: Type `@brainstorming-skill` to force activation

### Pattern Not Matching Use Case

If suggested pattern doesn't fit your needs:

- **Request specific category**: "Use constraint-based patterns" or "apply perspective multiplication"
- **Combine patterns**: "Use inversion first, then analogical transfer"
- **Reference specific sources**: "Apply the SCAMPER method" or "use Six Thinking Hats approach"

## Contributing

This plugin is part of the claude_skills repository. To contribute:

1. Fork the repository
2. Create a feature branch
3. Add or improve patterns with proper source citations
4. Verify patterns against original sources
5. Submit pull request with documentation updates

## License

MIT

## Credits

**Author**: Jamie Spence

**Research Sources**: This skill synthesizes patterns from 14+ authoritative sources including ITONICS Innovation Platform, Vanderbilt University prompt engineering research, PromptHub empirical studies, Machine Learning Mastery, and domain experts in marketing, product development, and creative facilitation.

All patterns are documented with source citations in the references directory.
