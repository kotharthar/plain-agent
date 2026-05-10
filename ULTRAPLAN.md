# Ultraplan: Recreate `mini_agent`

A staged plan to rebuild the project from *Building an AI Agent from Scratch — No Magic, Just a Deterministic Loop*. Each phase is self-contained, runnable, and adds exactly one capability over the previous one. No framework dependencies; just `openai`, `ollama` (binary), and `mcp` for the final phases.

Reference repo from the article: `github.com/sergenes/mini_agent`.

---

## 0. Project layout (final state)

```
mini_agent/
├── README.md
├── pyproject.toml              # or requirements.txt
├── .env.example                # OPENAI_API_KEY=...
├── .gitignore
├── mini_agent/
│   ├── __init__.py
│   ├── agent.py                # run_agent(): the deterministic loop
│   ├── tools.py                # TOOL_FUNCTIONS + TOOLS schemas
│   ├── prompts.py              # SYSTEM_PROMPT
│   ├── clients.py              # build_openai_client / build_ollama_client
│   ├── mcp_client.py           # MCP client: subprocess + JSON-RPC adapter
│   └── cli.py                  # `python -m mini_agent "task..."`
├── servers/
│   └── mcp_server.py           # FastMCP server (to_uppercase, count_words)
├── examples/
│   ├── 01_cloud.py             # Phase 1 demo
│   ├── 02_ollama.py            # Phase 3 demo
│   ├── 03_mixed.py             # Phase 4 demo
│   └── 04_mcp.py               # Phase 6 demo
└── tests/
    ├── test_tools.py
    ├── test_agent_loop.py      # uses a fake LLM client
    └── test_mcp_client.py
```

Rule of thumb: every phase ends with a runnable script under `examples/` and a test under `tests/`.

---

## 1. Phase 1 — Minimal cloud agent (~50 lines)

**Goal:** the deterministic `while` loop calling OpenAI with tool-calling enabled.

**Files**
- `mini_agent/prompts.py` → `SYSTEM_PROMPT` (verbatim from article: "You are a helpful assistant. Use tools when needed. When you have a final answer, respond with it directly.").
- `mini_agent/agent.py` → `run_agent(task, client, model="gpt-4o")`.
- `mini_agent/tools.py` → empty placeholders (`TOOLS = []`, `TOOL_FUNCTIONS = {}`).

**`run_agent` contract (from article, lines 53–97):**
1. Seed `messages` with system + user.
2. `while True`:
   - `client.chat.completions.create(model, messages, tools=TOOLS, tool_choice="auto")`.
   - Append the assistant message.
   - **Exit condition**: `if not message.tool_calls: return message.content`.
   - Otherwise iterate `message.tool_calls`, dispatch via `TOOL_FUNCTIONS`, append a `{"role": "tool", "tool_call_id": ..., "content": result}` for each.
3. No retry, no exception handling — match the article's "no safety net".

**Dependencies:** `openai>=1.0`.

**Acceptance:** an empty-tools task ("Say hi") completes in one turn and returns text.

---

## 2. Phase 2 — Three concrete tools

Implement verbatim from article (lines 118–185):

- `get_current_date()` → `datetime.now().strftime("%Y-%m-%d %H:%M:%S")`.
- `calculate(expression)` → `eval(expression, {"__builtins__": {}}, {})` wrapped in try/except. **Note**: `eval` is intentional per the source; flag clearly in `tools.py` that it's unsafe and only acceptable for the demo. Don't replace it — fidelity matters here.
- `get_weather(city)` → static stub string.

Register them in `TOOL_FUNCTIONS` and the `TOOLS` JSON schema list.

**Demo task (line 193):**
> "What's today's date? Also, what is 15% of 847? And what's the weather in Tokyo?"

**Acceptance:** trace prints three `-> calling …` lines, then a single final answer.

**Test:** `tests/test_tools.py` — direct calls to each function. Skip live OpenAI calls in CI.

---

## 3. Phase 3 — Local model via Ollama

Add `build_ollama_client()` in `clients.py`:

```python
OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
```

**Setup docs (in README):**
```bash
ollama pull qwen2.5
ollama serve
```

**Default local model:** `qwen2.5` (article's recommendation, line 257).

**Pitfall to document explicitly** (lines 239–263): models that *do not* support structured tool calls (mistral 7B, sometimes phi3/deepseek-r1) will hallucinate prose tool calls, the loop sees no `tool_calls`, and exits immediately. Add a short section in README titled *"If your agent returns immediately"* and reproduce Table 1 (qwen2.5, llama3.1/3.2, mistral-nemo OK; mistral 7B not OK; phi3/deepseek-r1 inconsistent).

**Example:** `examples/02_ollama.py` runs the same Phase-2 task against `qwen2.5`.

---

## 4. Phase 4 — Mixed mode (local orchestrator, cloud delegate)

Add `ask_cloud_expert(question)` to `tools.py` (article lines 272–280): instantiates a fresh cloud `OpenAI` client, calls `gpt-4`, returns the content. Register schema + function.

**Demo task (line 286):**
> "What is 2+2? Also, explain the philosophical implications of consciousness in machines."

Expected behavior: local model dispatches `calculate` for the first part and `ask_cloud_expert` for the second.

**Acceptance:** trace shows exactly one cloud call, not many.

---

## 5. Phase 5 — File and search tools

From article lines 304–331:

- `web_search(query)` — stub returning a fixed string. Article notes "Replace with Brave Search API, SerpAPI, or similar"; leave the integration as a TODO comment.
- `read_file(path)` → `Path(path).read_text()`.
- `write_file(path, content)` → writes, returns `f"Wrote {len(content)} chars to {path}"`.

Article notes (line 331) the real repo adds path validation + error handling. For this recreation: add minimal `Path.resolve()` + reject paths escaping the project root, but do **not** over-engineer.

After this phase, the agent has six tools: date, calc, weather, web_search, read_file, write_file.

---

## 6. Phase 6 — MCP client

Goal: make external (subprocess) MCP tools indistinguishable from local Python tools at the agent layer.

**File:** `mini_agent/mcp_client.py`.

**Responsibilities:**
1. Spawn an MCP server process (e.g. `python servers/mcp_server.py`) with stdio pipes.
2. Perform the JSON-RPC handshake (`initialize`, `tools/list`).
3. Translate each MCP tool description into the OpenAI tool schema shape and append to `TOOLS`.
4. Register a synthesized callable into `TOOL_FUNCTIONS` that issues `tools/call` over JSON-RPC and returns the textual result.
5. Provide a `with mcp_session(...) as tools:` context manager so the subprocess is cleaned up.

**Dependency:** the `mcp` Python SDK (recommended over hand-rolling JSON-RPC, but a minimal hand-rolled client is also fine — the article emphasizes the boundary, not the library).

**Agent contract is unchanged.** The whole point: `agent.py` doesn't import `mcp_client` — `cli.py` (or the example) merges MCP tools into `TOOLS`/`TOOL_FUNCTIONS` before calling `run_agent`.

---

## 7. Phase 7 — MCP server

**File:** `servers/mcp_server.py`. Verbatim from article (lines 369–387):

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mini_tools")

@mcp.tool()
def to_uppercase(text: str) -> str:
    """Convert text to uppercase."""
    return text.upper()

@mcp.tool()
def count_words(text: str) -> int:
    """Count the number of words in a string."""
    return len(text.split())

if __name__ == "__main__":
    mcp.run()
```

**Dependency:** `fastmcp` (or `mcp[server]`).

**End-to-end demo** (`examples/04_mcp.py`): launch the server via the client, ask the agent "Uppercase the phrase 'hello world' and tell me how many words it has." Confirm trace shows two MCP-routed tool calls.

---

## 8. Cross-cutting concerns

**Configuration**
- `.env` for `OPENAI_API_KEY`.
- `MINI_AGENT_MODE` env var: `cloud` | `ollama` | `mixed` to drive `cli.py`.

**CLI** (`mini_agent/cli.py`)
- `python -m mini_agent "task"` — defaults to cloud + all built-in tools.
- `--mode {cloud,ollama,mixed}`, `--model NAME`, `--mcp servers/mcp_server.py` flags.
- Print every `-> calling tool(args)` line as the article does (line 86).

**Tests** (`tests/`)
- `test_tools.py`: pure unit tests for `calculate`, `get_current_date`, file ops.
- `test_agent_loop.py`: build a fake client whose `chat.completions.create` returns scripted responses (first turn: tool calls; second turn: final text). Assert messages-list shape, exit on no-tool-calls, multiple parallel tool calls in one turn.
- `test_mcp_client.py`: launch `servers/mcp_server.py`, verify `tools/list` discovery + a `tools/call` round-trip. Skip if `mcp` not installed.

No live LLM calls in CI.

**Faithful-to-article scope (do NOT add)**
- No retry/backoff on tool failure.
- No human-in-the-loop confirmation gates.
- No persistent memory across runs.
- No subagents / context compression.
- No structured logging beyond the `print` trace.

These are the explicit "what my agent doesn't have" list (lines 401–405). Recreating them would be a *different* project.

---

## 9. Build & ship order (commit-by-commit)

1. Repo skeleton, `pyproject.toml`, `.gitignore`, README stub.
2. `prompts.py`, `agent.py` with the empty-tools loop. `examples/01_cloud.py` runs end-to-end.
3. Add three tools (Phase 2). Demo task passes.
4. Add `clients.py` + `examples/02_ollama.py`. Document local-model caveat.
5. Add `ask_cloud_expert` + `examples/03_mixed.py`.
6. Add file + search tools.
7. `mcp_client.py` + tests.
8. `servers/mcp_server.py` + `examples/04_mcp.py` end-to-end.
9. README pass: install, run, model table, "comparing to Claude Code" framing from the article's closing.

Each commit should be runnable on its own. If a commit doesn't run, it's too big.

---

## 10. Done criteria

- `python examples/01_cloud.py` answers the three-part demo task with three tool calls.
- `python examples/02_ollama.py` does the same against `qwen2.5` with no code change to `agent.py`.
- `python examples/03_mixed.py` produces exactly one `ask_cloud_expert` call for the philosophy half of its task.
- `python examples/04_mcp.py` answers via two MCP-routed tool calls.
- `pytest` is green without any network access.
- `agent.py` is under ~60 lines and contains the entire control flow. If it grew, something leaked out of `tools.py` or `mcp_client.py`.
