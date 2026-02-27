# perl-development

Comprehensive Perl 5.30+ development plugin with modular skills for scripting, CPAN ecosystem,
environment setup, testing, linting, and validation. Includes specialized agents for script
development, code auditing, and CLI architecture.

## What it does

Provides end-to-end Perl development support. Skills cover modern Perl idioms, CPAN module
management with cpanm and Carton, environment setup with local::lib, test design with
Test::More, linting with Perl::Critic, and script validation. Agents handle new script
development, existing code auditing, and Perl CLI application architecture.

## Skills

- `perl-development` — Core Perl 5.30+ scripting guidance with modern best practices
- `perl-cpan-ecosystem` — CPAN module installation, cpanfile management, cpanm, and Carton
- `perl-environment-setup` — Setting up Perl development environments and local::lib
- `perl-testing` — Test design and Test::More patterns for Perl scripts and modules
- `perl-lint` — Linting with Perl::Critic and static analysis
- `perl-validate` — Validation patterns for Perl scripts and data handling

## Agents

- `perl-script-developer` — Writes new Perl scripts from requirements using modern Perl patterns
- `perl-script-auditor` — Reviews existing scripts for correctness, style, and security issues
- `perl-cli-architect` — Designs and builds full Perl CLI applications with structured argument handling

## Installation

```bash
/plugin install perl-development@jamie-bitflight-skills
```

## Usage

```text
/perl-development "write a script to parse CSV files and output summary statistics"
/perl-development:perl-lint "review my Perl script for Perl::Critic violations"
```
