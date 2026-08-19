from llm.ollama import chat
from agent.tools import (
    search_web,
    open_webpage,
    SEARCH_WEB_TOOL,
    OPEN_WEBPAGE_TOOL,
)
from agent.syspromt import SYSTEM_PROMPT

def run(question: str):
    #
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": question,
        }
    ]
    tools = [SEARCH_WEB_TOOL, OPEN_WEBPAGE_TOOL]
    #
    searched = False
    opened_source = False
    while True:

        response = chat(messages, tools)

        tool_calls = response["message"].get("tool_calls", [])

        if not tool_calls:
            if searched and not opened_source:
                messages.append({
                    "role": "user",
                    "content": (
                        "Has realizado una búsqueda, pero todavía no has "
                        "abierto ninguna fuente. Abre al menos una fuente "
                        "relevante antes de responder."
                    ),
                })
                continue
            return response["message"]["content"]

        messages.append(response["message"])

        for tool_call in tool_calls:

            name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            print(f"[AGENT] Ejecutando herramienta: {name}")
            print(f"[AGENT] Argumentos: {arguments}")

            if name == "search_web":

                result = search_web(arguments["query"])
                searched = True

            elif name == "open_webpage":

                try:
                    result = open_webpage(arguments["url"])
                    if len(result) >= 1000:
                        opened_source = True
                    else:
                        result = (
                            "The source could not be reliably extracted. "
                            "Only a very small amount of content was retrieved. "
                            "Do not use this source as evidence. Try another source."
                        )
                except Exception as e:
                    result = (
                        f"The source could not be accessed.\n"
                        f"URL: {arguments['url']}\n"
                        f"Error: {str(e)}\n"
                        f"Do not rely on this source. Try another relevant source."
                    )

            else:

                result = f"Herramienta desconocida: {name}"
            print(f"[AGENT] Resultado obtenido: {len(str(result))} caracteres")
            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": str(result),
            })
