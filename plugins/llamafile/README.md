<p align="center">
  <img src="./assets/hero.png" alt="Llamafile" width="800" />
</p>

# Llamafile

Teaches Claude how to install, configure, and manage Mozilla Llamafile — the cross-platform single-file executable format for running GGUF models locally with an OpenAI-compatible API.

## Why Install This?

Local LLM inference with llamafile requires knowing platform-specific download commands, correct server flags, GPU acceleration options, and exact API endpoint formats. Without this plugin, Claude gives generic advice but misses specifics like the required `/v1` path prefix, the default port 8080, the `--embedding` flag for embedding endpoints, and integration patterns for LiteLLM and the OpenAI SDK.

## What Changes

With this plugin installed, Claude will:

- Provide exact download commands for llamafile binaries and GGUF model files
- Generate correct server startup commands with optimal flags for your hardware
- Integrate llamafile with Python code via LiteLLM (`model="llamafile/model-name"`) or the OpenAI SDK (`api_base="http://localhost:8080/v1"`)
- Debug connection errors (refused connections, wrong ports, missing `/v1` prefix)
- Configure GPU acceleration (CUDA, Metal, Vulkan) vs CPU-only fallback
- Set up llamafile as a persistent background service
- Validate API responses via the `/health` endpoint

## Installation

```bash
/plugin marketplace add Jamie-BitFlight/claude_skills
/plugin install llamafile@jamie-bitflight-skills
```

## Usage

Install and ask Claude about llamafile setup, integration, or troubleshooting:

```text
"Help me install llamafile and run Mistral 7B locally"
"I'm getting connection refused errors with my llamafile server"
"Write Python code to use llamafile with LiteLLM"
"How do I enable GPU acceleration for llamafile on macOS?"
"Create a script to start llamafile as a background service"
"Generate embeddings using llamafile"
```

## When to Use

- Setting up local AI inference without cloud API costs
- Air-gapped or offline environments
- Privacy-sensitive workloads where data must stay on-device
- Building developer tools (commit message generators, code reviewers) backed by local models
- Experimenting with different GGUF models without API charges
- Integrating local LLMs into Python applications

## OpenAI-Compatible API

Llamafile exposes a local OpenAI-compatible API when started with `--server`:

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:8080/v1/chat/completions` | Chat completions |
| `http://localhost:8080/v1/completions` | Text completions |
| `http://localhost:8080/v1/embeddings` | Embeddings (requires `--embedding` flag) |
| `http://localhost:8080/health` | Health check |

Supported platforms: macOS, Windows, Linux, FreeBSD, OpenBSD, NetBSD — AMD64 and ARM64.

## Requirements

- Claude Code v2.0+
