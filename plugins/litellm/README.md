<p align="center">
  <img src="./assets/hero.png" alt="LiteLLM" width="800" />
</p>

# LiteLLM

Teaches Claude the correct patterns for calling LLM APIs from Python using the LiteLLM library — a unified interface for 100+ providers including OpenAI, Anthropic, Google, AWS Bedrock, and local servers like llamafile and Ollama.

## Why Install This?

LiteLLM's unified `completion()` API hides provider-specific quirks, but getting it right requires knowing exact model name prefixes, URL formats, exception types, and async patterns. Without this plugin, Claude writes code that looks correct but fails at runtime — wrong model prefix, wrong endpoint path, unhandled provider-specific errors, missing retry configuration.

## What Changes

With this plugin installed, Claude will:

- Use correct model name prefixes for every provider (`llamafile/gemma-3-3b`, `bedrock/claude-3-5-sonnet`, `gemini/gemini-1.5-pro`)
- Connect to local servers with the right endpoint format (`http://localhost:8080/v1` — the `/v1` path is required)
- Handle exceptions using LiteLLM's OpenAI-compatible error hierarchy with proper retry logic
- Choose sync vs async patterns correctly, including async streaming
- Configure retry counts, timeouts, and fallback providers
- Set up a LiteLLM proxy for centralized LLM gateway deployments
- Calculate costs and track usage across providers

## Installation

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install litellm@jamie-bitflight-skills
```

## Usage

Install and ask Claude to write LLM-calling Python code. The skill activates automatically when:

- Your code imports `litellm` or uses `completion()` patterns
- You're connecting to a local llamafile or Ollama server
- You need to switch between OpenAI, Anthropic, and local providers
- You're adding retry or fallback logic to LLM calls

### Example

```text
"Write Python code to call my local llamafile server with retry logic"
"Add streaming support to this LiteLLM completion call"
"How do I handle rate limit errors from OpenAI using LiteLLM?"
"Set up LiteLLM with fallback from Anthropic to OpenAI"
```

## When to Use

- Building CLI tools that call LLMs (commit message generators, code review scripts)
- Writing Python services that need provider flexibility
- Integrating llamafile or Ollama into existing Python projects
- Adding production-grade retry and fallback logic
- Setting up a centralized LLM proxy for a team or application

## Supported Providers

| Category | Providers |
|----------|-----------|
| Cloud | OpenAI, Anthropic, Google Gemini, Azure, AWS Bedrock |
| Local | llamafile, Ollama, LocalAI, vLLM |
| All others | 100+ via unified `completion()` — same API, same exception types |

## Requirements

- Claude Code v2.0+
- Python 3.11+ in your project
