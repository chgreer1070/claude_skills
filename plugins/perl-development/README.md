<p align="center">
  <img src="./assets/hero.png" alt="Perl Development" width="800" />
</p>

# perl-development

Comprehensive Perl 5.30+ development plugin. Covers modern Perl idioms, CPAN dependency management, environment setup, testing with Test::More, linting with Perl::Critic, and validation — plus three specialized agents for writing, auditing, and architecting Perl code.

## What It Does

Gives Claude deep knowledge of modern Perl development practices. Use it when writing new Perl scripts, reviewing existing code for correctness and style, managing dependencies via CPAN, or building structured Perl CLI applications. The plugin targets Perl 5.30+ and enforces contemporary idioms: strict/warnings, signatures, Path::Tiny, Try::Tiny, and cpanfile-based dependency management.

## Skills

| Skill | What It Covers |
|-------|---------------|
| `perl-development` | Core Perl 5.30+ scripting — pragmas, module imports, variable declaration, error handling patterns |
| `perl-cpan-ecosystem` | CPAN module installation with cpanm, cpanfile authoring, Carton for reproducible installs, local::lib isolation |
| `perl-environment-setup` | Perl version management, perlbrew/plenv, setting up a development environment from scratch |
| `perl-testing` | Test design with Test::More, test structure, coverage, and best practices for Perl scripts and modules |
| `perl-lint` | Static analysis with Perl::Critic — running at configurable severity levels, interpreting output, fixing violations |
| `perl-validate` | Validation patterns for input data, command-line arguments, and file content in Perl scripts |

## Agents

| Agent | What It Does |
|-------|-------------|
| `@perl-script-developer` | Writes new Perl scripts from requirements using modern Perl patterns and proper structure |
| `@perl-script-auditor` | Reviews existing scripts for security vulnerabilities, Perl::Critic violations, anti-patterns, and code smells |
| `@perl-cli-architect` | Designs and builds full Perl CLI applications — complex option parsing, subcommands, TTY detection, ANSI color |

## Installation

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install perl-development@jamie-bitflight-skills
```

## Usage

```text
/perl-development "write a script to parse CSV files and output summary statistics"
/perl-development:perl-lint "review my Perl script for Perl::Critic violations"
/perl-development:perl-testing "write Test::More tests for this module"
/perl-development:perl-cpan-ecosystem "create a cpanfile for these dependencies"
```

To use a specialized agent, mention it by role:

```text
"Use the perl-script-auditor to review this script for security issues"
"Ask the perl-cli-architect to design a CLI tool with subcommands"
```

## When to Use

- Writing new Perl 5.30+ scripts with modern idioms
- Auditing legacy Perl code for correctness, style, and vulnerabilities
- Setting up CPAN dependency management with cpanm, cpanfile, or Carton
- Building Perl CLI tools with structured argument handling
- Adding Test::More test suites to Perl code
- Running Perl::Critic and fixing violations
- Setting up a Perl development environment on a new machine

## Requirements

- Claude Code v2.0+
- Perl 5.30+ in your environment (for running Perl code)
