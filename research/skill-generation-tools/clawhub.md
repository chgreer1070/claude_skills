# ClawHub

**Research Date**: 2026-02-20
**Source URL**: <https://www.clawhub.ai/skills>
**GitHub Repository**: Not found
**Version at Research**: Unknown
**License**: Unknown

---

## Overview

ClawHub is described as "a fast skill registry for agents, with vector search." The platform appears to be a web-based registry for discovering and potentially sharing AI agent skills, utilizing vector search technology for semantic skill discovery. The site is built as a React-based single-page application.

---

## Problem Addressed

| Problem | Solution |
|---------|----------|
| Difficulty discovering relevant agent skills | Provides a centralized registry with search functionality |
| Manual skill matching for agent tasks | Implements vector search for semantic skill discovery |
| Fragmented skill documentation | Creates standardized skill registry (assumed) |

---

## Key Statistics

| Metric | Value | Date Gathered |
|--------|-------|---------------|
| Website Status | Active | 2026-02-20 |
| GitHub Organization | Not found | 2026-02-20 |
| Public Repositories | None identified | 2026-02-20 |
| Community Size | Unknown | 2026-02-20 |

**Note**: Limited public information available. Site uses client-side rendering with React/TanStack Router, making automated data extraction difficult.

---

## Key Features

### Skill Registry

- Centralized repository for agent skills
- Web-based interface for browsing skills
- Skill discovery and search capabilities (claimed)

### Vector Search

- Semantic search functionality for finding relevant skills
- Vector-based matching (implementation details unverified)

### Technical Implementation

- React-based single-page application
- TanStack Router for client-side routing
- Modern JavaScript module system
- Responsive design (mobile viewport support)

---

## Technical Architecture

**Frontend**:

- Built with React
- Uses TanStack Router for routing
- Module preloading for performance
- Server-side rendering support (SSR flags present)

**Backend**:

- API structure not publicly documented
- No public API endpoints discovered
- Implementation details unavailable

**Infrastructure**:

- Domain: clawhub.ai
- No GitHub organization found at <https://github.com/clawhub>
- No public repositories identified

---

## Installation & Usage

**Access**:

```bash
# Web interface
open https://www.clawhub.ai/skills
```

**Integration**:

Integration methods, API access, and programmatic usage patterns are not publicly documented at this time.

---

## Relevance to Claude Code Development

### Applications

- **Skill Discovery**: If ClawHub provides a public API, it could be integrated as a skill discovery tool for Claude Code marketplace
- **Vector Search Patterns**: The vector search implementation for semantic skill matching could inform similar features in Claude Code plugin ecosystem
- **Registry Architecture**: Understanding how ClawHub structures and categorizes skills may provide insights for marketplace organization

### Patterns Worth Adopting

- **Semantic Search**: Vector-based skill discovery could improve Claude Code skill matching
- **Centralized Registry**: A well-structured skill registry pattern may be valuable for skill management
- **Modern Frontend Architecture**: React SPA with SSR support demonstrates performance-oriented approach

### Integration Opportunities

**Currently Limited**:

- No public API documented
- No GitHub repositories for collaboration
- No clear integration points

**Potential Future Integration**:

- If API becomes available: Skill discovery integration
- If open-sourced: Contribute to or fork registry implementation
- If documented: Adopt architectural patterns

---

## Research Limitations

<research_limitations>

This entry has significant limitations due to restricted public information:

**Unverified Claims**:

- Actual vector search implementation
- Skill registry structure and content
- Number of available skills
- User base and community size
- Pricing model (free vs. paid)
- Authentication and access control
- API availability

**Investigation Attempts**:

1. Website scraping: Limited by React SPA architecture
2. GitHub search: No organization or repositories found
3. API discovery: No public endpoints found at /api/skills or similar paths
4. Community search: No Reddit, Hacker News, or forum discussions found
5. Domain information: WHOIS lookup provided no actionable details

**Recommendation**: This entry should be re-researched when:

- Public API documentation becomes available
- GitHub repository is published
- Community discussions emerge
- Integration documentation is released

</research_limitations>

---

## References

- [ClawHub Skills Website](https://www.clawhub.ai/skills) (accessed 2026-02-20)
- [ClawHub Homepage](https://www.clawhub.ai) (accessed 2026-02-20)
- Site meta description: "ClawHub — a fast skill registry for agents, with vector search." (accessed 2026-02-20)

---

## Freshness Tracking

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-20 |
| Version at Verification | Unknown |
| Next Review Recommended | 2026-05-20 |
| Review Priority | High — Limited initial data, may reveal more features over time |

**Review Triggers**:

- Public API documentation released
- GitHub repository published
- Integration guides published
- Community discussions emerge
- Service becomes widely referenced in agent development discussions
