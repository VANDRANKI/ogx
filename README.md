<h1 align="center">OGX</h1>

<p align="center">
  <a href="https://pypi.org/project/ogx/"><img src="https://img.shields.io/pypi/v/ogx?logo=pypi" alt="PyPI Version"></a>
  <a href="https://pypi.org/project/ogx/"><img src="https://img.shields.io/pypi/dm/ogx" alt="PyPI Downloads"></a>
  <a href="https://hub.docker.com/u/ogx"><img src="https://img.shields.io/docker/pulls/ogx/distribution-starter?logo=docker" alt="Docker Hub Pulls"></a>
  <a href="https://github.com/ogx-ai/ogx/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/ogx.svg" alt="License"></a>
  <a href="https://discord.gg/ZAFjsrcw"><img src="https://img.shields.io/discord/1257833999603335178?color=5865F2&logo=discord&logoColor=ffffff" alt="Discord"></a>
  <a href="https://github.com/ogx-ai/ogx/actions/workflows/unit-tests.yml?query=branch%3Amain"><img src="https://github.com/ogx-ai/ogx/actions/workflows/unit-tests.yml/badge.svg?branch=main" alt="Unit Tests"></a>
  <a href="https://github.com/ogx-ai/ogx/actions/workflows/integration-tests.yml?query=branch%3Amain"><img src="https://github.com/ogx-ai/ogx/actions/workflows/integration-tests.yml/badge.svg?branch=main" alt="Integration Tests"></a>
  <a href="https://ogx-ai.github.io/docs/api-openai/conformance"><img src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fogx-ai%2Fogx%2Fmain%2Fdocs%2Fstatic%2Fopenai-coverage.json&query=%24.summary.conformance.score&suffix=%25&label=OpenResponses%20Conformance&color=brightgreen" alt="OpenResponses Conformance"></a>
  <a href="https://deepwiki.com/ogx-ai/ogx"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>

[**Quick Start**](https://ogx-ai.github.io/docs/getting_started/quickstart) | [**Documentation**](https://ogx-ai.github.io/docs) | [**OpenAI API Compatibility**](https://ogx-ai.github.io/docs/api-openai) | [**Discord**](https://discord.gg/ZAFjsrcw)

> [!IMPORTANT]
> **Llama Stack is now OGX.** The name changed, and so did the mission — model-agnostic, multi-SDK, production-grade. [Read the full announcement →](https://ogx-ai.github.io/blog/from-llama-stack-to-ogx)

**Open-source agentic API server for building AI applications. OpenAI-compatible. Any model, any infrastructure.**

<p align="center">
  <img src="docs/static/img/architecture-animated.svg" alt="OGX Architecture" width="100%">
</p>

OGX is a drop-in replacement for the OpenAI API that you can run anywhere — your laptop, your datacenter, or the cloud. Use any OpenAI-compatible client or agentic framework. Swap between Llama, GPT, Gemini, Mistral, or any model without changing your application code.

## Quick Start

```bash
# Install via uv (recommended)
uv pip install ogx[starter]

# Or one-line install script
curl -LsSf https://github.com/ogx-ai/ogx/raw/main/scripts/install.sh | bash

# Start the server (uses the starter distribution with Ollama)
uv run ogx stack run starter
```

The server listens on `http://localhost:8321` by default. Point any OpenAI-compatible client at it:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="fake")
response = client.chat.completions.create(
    model="llama-3.3-70b",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

## What you get

| Feature | Endpoint | Notes |
| ------- | -------- | ----- |
| Chat Completions | `/v1/chat/completions` | Full streaming support |
| Text Completions | `/v1/completions` | Legacy completions |
| Embeddings | `/v1/embeddings` | Dense vector embeddings |
| Responses API | `/v1/responses` | Server-side agentic orchestration with tool calling |
| Vector Stores | `/v1/vector_stores` | Managed document storage and retrieval |
| Files | `/v1/files` | Upload and manage files for RAG |
| Batches | `/v1/batches` | Offline / async batch processing |
| Anthropic Messages | `/v1/messages` | Native Anthropic SDK support |
| Google GenAI | `/v1alpha/interactions` | Native Google GenAI SDK support |

- **[Open Responses](https://www.openresponses.org/) conformant** — the Responses API implementation passes the Open Responses conformance test suite
- **Multi-SDK support** — use the [Anthropic SDK](https://docs.anthropic.com/en/api/messages) or [Google GenAI SDK](https://ai.google.dev/gemini-api/docs/interactions) natively alongside the OpenAI API

## Usage Examples

### OpenAI SDK (Chat Completions)

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="fake")

# Streaming response
with client.chat.completions.stream(
    model="llama-3.3-70b",
    messages=[{"role": "user", "content": "Explain async/await in Python"}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### Anthropic SDK

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://localhost:8321",
    api_key="fake",
)
message = client.messages.create(
    model="llama-3.3-70b",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)
print(message.content[0].text)
```

### Responses API (Agentic, with built-in tool calling)

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="fake")

response = client.responses.create(
    model="llama-3.3-70b",
    tools=[{"type": "web_search_preview"}],
    input="What's the latest news about open-source LLMs?",
)
print(response.output_text)
```

### Embeddings

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="fake")

result = client.embeddings.create(
    model="all-minilm",
    input=["OGX is an open-source AI server", "It supports any model"],
)
for item in result.data:
    print(f"Embedding dim: {len(item.embedding)}")
```

## Use any model, use any infrastructure

OGX has a pluggable provider architecture. Develop locally with Ollama, deploy to production with vLLM, or connect to a managed service — the API stays the same.

| Provider | Type | Use Case |
| -------- | ---- | -------- |
| Ollama | Local | Development and local testing |
| vLLM | Self-hosted | High-throughput production inference |
| OpenAI | Remote | GPT-4o, GPT-4o-mini, and other OpenAI models |
| Azure OpenAI | Remote | Enterprise OpenAI deployments |
| Amazon Bedrock | Remote | AWS-managed model hosting |
| WatsonX | Remote | IBM-managed model hosting |
| Fireworks | Remote | Fast inference API |
| Together | Remote | Open-source model hosting |

See the [provider documentation](https://ogx-ai.github.io/docs/providers) for the full list.

## Resources

- [Documentation](https://ogx-ai.github.io/docs) — full reference
- [OpenAI API Compatibility](https://ogx-ai.github.io/docs/api-openai) — endpoint coverage and provider matrix
- [Getting Started Notebook](./docs/getting_started.ipynb) — text and vision inference walkthrough
- [Contributing](CONTRIBUTING.md) — how to contribute

**Client SDKs:**

| Language | SDK | Package |
| :----: | :----: | :----: |
| Python | [ogx-client-python](https://github.com/ogx-ai/ogx-client-python) | [![PyPI version](https://img.shields.io/pypi/v/ogx_client.svg)](https://pypi.org/project/ogx_client/) |
| TypeScript | [ogx-client-typescript](https://github.com/ogx-ai/ogx-client-typescript) | [![NPM version](https://img.shields.io/npm/v/ogx-client.svg)](https://npmjs.org/package/ogx-client) |

## Community

We hold regular community calls every Thursday at 09:00 AM PST — see the [Community Event on Discord](https://discord.gg/ZAFjsrcw) for details.

[![Star History Chart](https://api.star-history.com/svg?repos=ogx-ai/ogx&type=Date)](https://www.star-history.com/#ogx-ai/ogx&Date)

Thanks to all our amazing contributors!

<a href="https://github.com/ogx-ai/ogx/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ogx-ai/ogx" alt="OGX contributors" />
</a>
