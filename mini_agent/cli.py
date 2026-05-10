import argparse
import sys

from .agent import run_agent
from .clients import build_cloud_client, build_ollama_client
from .tools import TOOLS, TOOL_FUNCTIONS


def main():
    parser = argparse.ArgumentParser(prog="mini-agent")
    parser.add_argument("task", help="The task to give the agent")
    parser.add_argument(
        "--mode",
        default="cloud",
        choices=["cloud", "ollama", "mixed"],
        help="Where the orchestrating LLM runs.",
    )
    parser.add_argument("--model", default=None, help="Override the model name.")
    parser.add_argument(
        "--mcp",
        default=None,
        help="Path to an MCP server script to spawn and merge tools from.",
    )
    args = parser.parse_args()

    if args.mode in {"ollama", "mixed"}:
        client = build_ollama_client()
        model = args.model or "qwen2.5"
    else:
        client = build_cloud_client()
        model = args.model or "gpt-4o"

    tools = list(TOOLS)
    tool_functions = dict(TOOL_FUNCTIONS)

    if args.mcp:
        from .mcp_client import mcp_session

        with mcp_session(sys.executable, [args.mcp]) as bundle:
            tools = tools + bundle.tools
            tool_functions = {**tool_functions, **bundle.tool_functions}
            answer = run_agent(args.task, client, model, tools, tool_functions)
    else:
        answer = run_agent(args.task, client, model, tools, tool_functions)

    print(f"\nAnswer: {answer}")


if __name__ == "__main__":
    main()
