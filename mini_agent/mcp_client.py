"""Minimal MCP client over stdio + JSON-RPC.

Spawns an MCP server as a subprocess, performs the initialize handshake,
discovers its tools, and exposes them as OpenAI-compatible tool schemas plus
a callable dispatch table — so the agent can't tell the difference between
an in-process Python tool and an MCP-routed one.
"""

import json
import subprocess
import threading
from contextlib import contextmanager


class _StdioJsonRpc:
    def __init__(self, proc):
        self.proc = proc
        self._next_id = 0
        self._lock = threading.Lock()

    def _send(self, payload):
        line = json.dumps(payload) + "\n"
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

    def _read(self):
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("MCP server closed stdout before responding")
        return json.loads(line)

    def request(self, method, params=None):
        with self._lock:
            self._next_id += 1
            req_id = self._next_id
            payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
            if params is not None:
                payload["params"] = params
            self._send(payload)

            while True:
                msg = self._read()
                # Responses have an id; notifications don't. Skip notifications.
                if msg.get("id") != req_id:
                    continue
                if "error" in msg:
                    raise RuntimeError(f"MCP error: {msg['error']}")
                return msg.get("result")

    def notify(self, method, params=None):
        with self._lock:
            payload = {"jsonrpc": "2.0", "method": method}
            if params is not None:
                payload["params"] = params
            self._send(payload)


class MCPToolBundle:
    def __init__(self, tools, tool_functions):
        self.tools = tools
        self.tool_functions = tool_functions


def _extract_text(result):
    parts = []
    for c in result.get("content", []) or []:
        if c.get("type") == "text":
            parts.append(c.get("text", ""))
    if parts:
        return "\n".join(parts)
    return json.dumps(result)


@contextmanager
def mcp_session(command, args=None):
    """Start an MCP server subprocess and yield its tools as an MCPToolBundle."""
    args = args or []
    proc = subprocess.Popen(
        [command, *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    rpc = _StdioJsonRpc(proc)

    try:
        rpc.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mini_agent", "version": "0.1.0"},
            },
        )
        rpc.notify("notifications/initialized")

        list_result = rpc.request("tools/list")

        tools = []
        tool_functions = {}

        for t in list_result.get("tools", []):
            name = t["name"]
            schema = t.get("inputSchema") or {"type": "object", "properties": {}}
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": t.get("description", ""),
                        "parameters": schema,
                    },
                }
            )

            def make_caller(tool_name):
                def call(**kwargs):
                    result = rpc.request(
                        "tools/call",
                        {"name": tool_name, "arguments": kwargs},
                    )
                    return _extract_text(result)
                return call

            tool_functions[name] = make_caller(name)

        yield MCPToolBundle(tools, tool_functions)
    finally:
        try:
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
