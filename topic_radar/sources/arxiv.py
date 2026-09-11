"""arXiv source — free, no auth. Recent papers from cs.AI / cs.CL / cs.LG."""

import xml.etree.ElementTree as ET

import requests

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch(limit: int = 15) -> list:
    params = {
        "search_query": "cat:cs.AI OR cat:cs.CL OR cat:cs.LG",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": limit,
    }
    resp = requests.get(ARXIV_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)

    items = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title = entry.find("atom:title", ATOM_NS).text.strip().replace("\n", " ")
        link = entry.find("atom:id", ATOM_NS).text.strip()
        published = entry.find("atom:published", ATOM_NS).text.strip()
        summary = entry.find("atom:summary", ATOM_NS).text.strip().replace("\n", " ")
        items.append({
            "title": title,
            "url": link,
            "source": "arXiv",
            "signal": "new paper",
            "published_at": published,
            "summary": summary[:300],
        })
    return items
