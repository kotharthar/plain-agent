"""A tiny MCP server. Exposes two text utilities to any MCP-compatible agent."""

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
