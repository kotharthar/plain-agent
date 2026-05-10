"""Phase 6 + 7 demo — agent uses tools served by an external MCP process."""

import sys
from pathlib import Path

from mini_agent.agent import run_agent
from mini_agent.clients import build_cloud_client
from mini_agent.mcp_client import mcp_session
from mini_agent.tools import TOOLS, TOOL_FUNCTIONS


if __name__ == "__main__":
    server_path = Path(__file__).resolve().parent.parent / "servers" / "mcp_server.py"
    client = build_cloud_client()
    task = "Uppercase the phrase 'hello world' and tell me how many words it has."

    with mcp_session(sys.executable, [str(server_path)]) as bundle:
        tools = TOOLS + bundle.tools
        tool_functions = {**TOOL_FUNCTIONS, **bundle.tool_functions}
        print(f"Task: {task}")
        answer = run_agent(task, client, model="gpt-4o",
                           tools=tools, tool_functions=tool_functions)
        print(f"\nAnswer: {answer}")
