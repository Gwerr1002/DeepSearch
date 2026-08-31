import httpx
import pymupdf
from bs4 import BeautifulSoup
from config.config import cnf

def clean_text(soup):
    for element in soup([
        "script",
        "style",
        "noscript",
        "nav",
        "header",
        "footer",
        "aside",
    ]):
        element.decompose()
    #
    main = soup.find("main")
    #
    if main:
        return main.get_text(separator=" ", strip=True)
    #
    return soup.get_text(separator=" ", strip=True)

def is_block_content(self,txt:str):
    txt = txt.lower()
    for w in cnf.BLOCK_PATTERNS:
        if w in txt:
            return True
    return False

def fetch(url):
    #
    response = httpx.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
        follow_redirects=True,
        timeout=30,
    )
    #
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    #
    if "application/pdf" in content_type:
        document = pymupdf.open(
            stream=response.content,
            filetype="pdf"
        )
        text = "\n".join(
            page.get_text()
            for page in document
        )
        return text[:20000]
    #
    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )
    #
    return soup.get_text(separator=" ",
        strip=True)[:20000]