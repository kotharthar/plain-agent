"""Phase 1 + 2 demo — cloud (OpenAI) agent with three tools."""

from mini_agent.agent import run_agent
from mini_agent.clients import build_cloud_client


if __name__ == "__main__":
    client = build_cloud_client()
    task = "What's today's date? Also, what is 15% of 847? And what's the weather in Tokyo?"
    print(f"Task: {task}")
    answer = run_agent(task, client, model="gpt-4o")
    print(f"\nAnswer: {answer}")
