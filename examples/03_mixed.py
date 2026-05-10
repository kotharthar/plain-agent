"""Phase 4 demo — local orchestrator delegates hard questions to the cloud."""

from mini_agent.agent import run_agent
from mini_agent.clients import build_ollama_client


if __name__ == "__main__":
    client = build_ollama_client()
    task = (
        "What is 2+2? Also, explain the philosophical implications of "
        "consciousness in machines."
    )
    print(f"Task: {task}")
    answer = run_agent(task, client, model="qwen2.5")
    print(f"\nAnswer: {answer}")
