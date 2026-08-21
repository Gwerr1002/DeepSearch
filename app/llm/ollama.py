import httpx


OLLAMA_URL = "http://host.docker.internal:11434"
MODEL = "qwen3:8b"


def generate(prompt: str) -> str:
    #
    response = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=300,
    )
    #
    response.raise_for_status()
    #
    return response.json()["response"]

def chat(
    messages: list,
    tools: list | None = None,
    format: str | dict | None = None,
    ):
    #
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }
    #
    if tools:
        payload["tools"] = tools
    if format:
        payload["format"] = format
    #
    response = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json=payload,
        timeout=300,
    )
    #
    response.raise_for_status()
    return response.json()
