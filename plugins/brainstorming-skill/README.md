<p align="center">
  <img src="./assets/hero.png" alt="Brainstorming Skill" width="800" />
</p>

# Brainstorming Skill

Teaches Claude 30+ research-validated ideation techniques. Claude applies them automatically
when you ask for ideas, and runs a structured design dialogue before writing any code or content.

## Problem

Unassisted Claude brainstorming tends to produce:

- Generic ideas that ignore your constraints (budget, timeline, audience)
- Shallow lists without reasoning or trade-offs
- A single perspective when the problem needs several
- Immediate implementation when you actually need to explore the solution space first

## Installation

First, add the marketplace (one-time setup):

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
```

Then install the plugin:

```bash
/plugin install brainstorming-skill@jamie-bitflight-skills
```

## Quick Start

Just describe what you want to brainstorm. The plugin activates automatically:

```text
"Help me brainstorm features for a project management app for freelancers"
"What are some approaches to reducing churn in our SaaS product?"
"Generate marketing angles for a developer tool launch"
"I need ideas for the onboarding flow — budget is tight"
```

Claude will ask one clarifying question at a time (constraints, stakeholders, success criteria)
before generating ideas. It will not write code or create content until you have approved a design.

## What Changes

**Before this plugin** — "Help me brainstorm features":

```
Here are some ideas: task lists, calendar view, team chat, file sharing, notifications...
```

**After this plugin** — same request:

```
To generate the most relevant ideas, a few quick questions:
- Who are your primary users?
- What's your budget and timeline?

[After you answer]

From the freelancer perspective (within your $20k / 6-week constraint):
  1. Invoice generation integrated with time tracking — $3k, 1 week
     Reasoning: invoicing is the #1 cited pain point; eliminates billing friction
  2. Client portal with branded workspace — $4k, 1.5 weeks
     Reasoning: reduces email back-and-forth, builds client trust

From the client perspective:
  ...

From the accountant perspective:
  ...
```

## The Hard Gate

The skill enforces a design-before-build gate. Claude will not invoke an implementation skill,
write code, scaffold a project, or take any implementation action until the brainstorming
process is complete and you have approved a design. This applies to every project regardless
of perceived simplicity.

## Ideation Framework

14 systematic pattern categories including:

- **Perspective Multiplication** — stakeholder angles, role-based viewpoints
- **Constraint Variation** — artificial constraints to open the idea space
- **Inversion and Negative Space** — reverse thinking to find non-obvious solutions
- **Analogical Transfer** — apply patterns from unrelated domains
- **Systematic Feature Decomposition** — SCAMPER and attribute-based analysis
- **Scenario Exploration** — future-based and "what if" framing
- And 8 more documented pattern categories

## When It Activates

The skill activates on:

- Software feature design and component planning
- Marketing and content campaigns
- Strategic planning and decision-making
- Creative writing (plots, characters, themes)
- Test case generation
- Any explicit "brainstorm", "generate ideas", or "explore approaches" request

---

> **The Ancient Woe**
>
> *The wretched playwright, staring at a blank piece of parchment for three fortnights, waiting for a Muse that is currently passed out in a tavern.*

> **The Bard's Decree**
>
> *"Strike the flint! Turn the world upside down! If the tragedy doth not write itself, look at it from the perspective of the jester, the king, and the beggar until the spark catches flame!"*
