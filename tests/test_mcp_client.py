import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from mini_agent.mcp_client import mcp_session


SERVER_PATH = Path(__file__).resolve().parent.parent / "servers" / "mcp_server.py"


def test_mcp_session_lists_and_calls():
    with mcp_session(sys.executable, [str(SERVER_PATH)]) as bundle:
        names = {t["function"]["name"] for t in bundle.tools}
        assert "to_uppercase" in names
        assert "count_words" in names

        assert bundle.tool_functions["to_uppercase"](text="hi") == "HI"
        assert bundle.tool_functions["count_words"](text="hi there friend") == "3"
