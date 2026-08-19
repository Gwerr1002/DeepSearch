from search.searxng import search
from search.web import fetch

def search_web(query: str):
    return search(query)

def open_webpage(url: str):
    return fetch(url)

SEARCH_WEB_TOOL = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Busca información en Internet usando un motor de búsqueda web.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Consulta que se desea buscar en Internet.",
                }
            },
            "required": ["query"],
        },
    },
}

OPEN_WEBPAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "open_webpage",
        "description": "Abre una página web y extrae su contenido textual.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL de la página que se desea abrir.",
                }
            },
            "required": ["url"],
        },
    },
}

