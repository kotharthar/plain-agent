import os

from openai import OpenAI


def build_cloud_client():
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def build_ollama_client():
    return OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",
    )
