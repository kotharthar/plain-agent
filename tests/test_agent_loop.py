"""Tests for the deterministic loop, using a fake LLM client.

No network. We script the sequence of `chat.completions.create` returns and
assert the loop dispatches tools, threads results back, and exits exactly
when the model stops requesting tools.
"""

from types import SimpleNamespace

from mini_agent.agent import run_agent


class _FakeCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = self.responses.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeClient:
    def __init__(self, responses):
        self.chat = SimpleNamespace(completions=_FakeCompletions(responses))


def msg(content=None, tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls)


def tc(call_id, name, args_json):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=args_json),
    )


def test_returns_immediately_when_no_tool_calls():
    client = FakeClient([msg(content="hello")])
    result = run_agent("hi", client, model="test", tools=[], tool_functions={})
    assert result == "hello"
    assert len(client.chat.completions.calls) == 1


def test_dispatches_one_tool_then_returns():
    seen = []

    def my_tool(x):
        seen.append(x)
        return f"got {x}"

    client = FakeClient([
        msg(tool_calls=[tc("c1", "my_tool", '{"x": 42}')]),
        msg(content="done"),
    ])

    result = run_agent(
        "task",
        client,
        model="test",
        tools=[{"type": "function", "function": {"name": "my_tool",
                "parameters": {"type": "object",
                               "properties": {"x": {"type": "integer"}}}}}],
        tool_functions={"my_tool": my_tool},
    )

    assert result == "done"
    assert seen == [42]
    # Second call should include the tool result message
    second_call_messages = client.chat.completions.calls[1]["messages"]
    tool_msgs = [m for m in second_call_messages if isinstance(m, dict)
                 and m.get("role") == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0]["tool_call_id"] == "c1"
    assert tool_msgs[0]["content"] == "got 42"


def test_parallel_tool_calls_in_one_turn():
    calls = []

    def a():
        calls.append("a")
        return "A"

    def b():
        calls.append("b")
        return "B"

    client = FakeClient([
        msg(tool_calls=[
            tc("1", "a", "{}"),
            tc("2", "b", "{}"),
        ]),
        msg(content="ok"),
    ])

    result = run_agent(
        "task", client, model="test",
        tools=[], tool_functions={"a": a, "b": b},
    )
    assert result == "ok"
    assert calls == ["a", "b"]


def test_unknown_tool_does_not_crash():
    client = FakeClient([
        msg(tool_calls=[tc("1", "ghost", "{}")]),
        msg(content="recovered"),
    ])
    result = run_agent("task", client, model="test",
                       tools=[], tool_functions={})
    assert result == "recovered"
    second_call_messages = client.chat.completions.calls[1]["messages"]
    tool_msgs = [m for m in second_call_messages if isinstance(m, dict)
                 and m.get("role") == "tool"]
    assert "Unknown tool" in tool_msgs[0]["content"]
