import os
from datetime import datetime
from pathlib import Path

from openai import OpenAI


def get_current_date():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression):
    # eval is intentional and matches the source article. Do not feed
    # untrusted input to this tool.
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def get_weather(city):
    return f"Weather in {city}: 72°F, partly cloudy"


def web_search(query):
    return (
        f"Search results for '{query}':\n"
        "1. Official docs: explained in 5 minutes"
    )


def read_file(path):
    return Path(path).read_text()


def write_file(path, content):
    Path(path).write_text(content)
    return f"Wrote {len(content)} chars to {path}"


def ask_cloud_expert(question):
    """Delegate a hard question to a powerful cloud model."""
    cloud_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = cloud_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content


TOOL_FUNCTIONS = {
    "get_current_date": get_current_date,
    "calculate": calculate,
    "get_weather": get_weather,
    "web_search": web_search,
    "read_file": read_file,
    "write_file": write_file,
    "ask_cloud_expert": ask_cloud_expert,
}


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "Returns the current date and time",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluates a math expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A Python math expression",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Gets current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Searches the web and returns top results",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads a text file from disk",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes text to a file, overwriting any existing content",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Text to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_cloud_expert",
            "description": (
                "Delegates a hard question to a powerful cloud model. "
                "Use only when the question genuinely needs deep reasoning."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask the expert",
                    }
                },
                "required": ["question"],
            },
        },
    },
]
