import httpx


SEARXNG_URL = "http://host.docker.internal:8080"


def search(query: str):
    #
    response = httpx.get(
        f"{SEARXNG_URL}/search",
        params={
            "q": query,
            "format": "json",
        },
        timeout=30,
    )
    #
    response.raise_for_status()
    data = response.json()
    #
    results = []
    for result in data["results"]:
        results.append({
            "title": result.get("title"),
            "url": result.get("url"),
            "content": result.get("content"),
            "publishedDate": result.get("publishedDate"),
        })
    #
    return results
