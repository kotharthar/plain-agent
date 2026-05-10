import json

from .prompts import SYSTEM_PROMPT
from .tools import TOOLS as DEFAULT_TOOLS
from .tools import TOOL_FUNCTIONS as DEFAULT_TOOL_FUNCTIONS


def run_agent(task, client, model="gpt-4o", tools=None, tool_functions=None):
    tools = DEFAULT_TOOLS if tools is None else tools
    tool_functions = DEFAULT_TOOL_FUNCTIONS if tool_functions is None else tool_functions

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            return message.content

        for tool_call in message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"-> calling {name}({args})")

            fn = tool_functions.get(name)
            result = fn(**args) if fn else f"Unknown tool: {name}"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })
