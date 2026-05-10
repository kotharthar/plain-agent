# mini_agent

A tiny ReAct-style AI agent. No LangChain, no LangGraph, no CrewAI — just an LLM, some tools, and a `while` loop.

Recreated from *Building an AI Agent from Scratch — No Magic, Just a Deterministic Loop*. See `ULTRAPLAN.md` for the staged build-up.

## Install

```bash
pip install -e .
# optional, for MCP demos:
pip install -e ".[mcp]"
# tests:
pip install -e ".[dev]"
```

## Run

Cloud (OpenAI):
```bash
export OPENAI_API_KEY=sk-...
python examples/01_cloud.py
```

Local (Ollama):
```bash
ollama pull qwen2.5
ollama serve
python examples/02_ollama.py
```

Mixed mode — local model orchestrates, delegates hard questions to GPT-4 via the `ask_cloud_expert` tool:
```bash
python examples/03_mixed.py
```

MCP — tools come from a separate server process:
```bash
python examples/04_mcp.py
```

CLI:
```bash
python -m mini_agent "What is 15% of 847?"
python -m mini_agent --mode ollama --model qwen2.5 "..."
python -m mini_agent --mcp servers/mcp_server.py "Uppercase 'hello world'."
```

## Local-model gotcha

If your agent returns immediately without calling any tools, the model probably doesn't support OpenAI-style structured tool calling — it described the call in prose instead of emitting it. Swap to one of:

| Model | Tool support |
|-------|--------------|
| qwen2.5 | yes |
| llama3.1, llama3.2 | yes |
| mistral-nemo | yes |
| mistral (7B) | no |
| phi3, deepseek-r1 | inconsistent |

## Layout

```
mini_agent/        the agent + tools + clients + MCP client
servers/           sample MCP server
examples/          one runnable demo per phase
tests/             pytest, no network
```

## Non-goals

No retries, no human-in-the-loop, no persistent memory, no subagents. That's where frameworks like LangGraph come in — see the closing of the article.
