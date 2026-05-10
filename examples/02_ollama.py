"""Phase 3 demo — same agent, swapped to a local model via Ollama."""

from mini_agent.agent import run_agent
from mini_agent.clients import build_ollama_client


if __name__ == "__main__":
    client = build_ollama_client()
    task = "What's today's date? Also, what is 15% of 847? And what's the weather in Tokyo?"
    print(f"Task: {task}")
    answer = run_agent(task, client, model="qwen2.5")
    print(f"\nAnswer: {answer}")
