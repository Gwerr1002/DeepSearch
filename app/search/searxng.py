import httpx


SEARXNG_URL = "http://host.docker.internal:8080"
RETRIES = 3

def search(query: str):
    #
    params = {
        "q": query,
        "format": "json",
        "categories": "general,science,scientific publications,news,books,repos"
    }
    #
    attempt,go = 0,True
    while go:
        try:
            response = httpx.get(
                f"{SEARXNG_URL}/search",
                params = params,
                timeout=30,
            )
            #
            response.raise_for_status()
            go = False
        except httpx.ReadTimeout:
            print(f"[WEB SEARCH] timeout ({attempt}/{RETRIES})")
        except httpx.HTTPStatusError as e:
            print(
                f"[WEB SEARCH] HTTP {e.response.status_code} "
                f"({attempt}/{RETRIES})"
            )
    data = response.json()
    #
    """
    results = ["results"]
        for result in data["results"]:
            results.append({
                "title": result.get("title"),
                "url": result.get("url"),
                "content": result.get("content"),
                "publishedDate": result.get("publishedDate"),
                "engines":result.get("engines"),
                "category":result.get("category")
            })
        #
    """
    return data["results"]
