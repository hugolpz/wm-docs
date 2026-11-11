"""Fetch the Meta-Wiki expense pages of Category:Wikimédia_France/Finances/Dépense/Traitée/index
(one page per expense, each holding a {{Dépense Wikimédia France}} template) into
sources/meta_expenses.json."""
import json
import os
import time
import urllib.parse
import urllib.request

from spendings_format import META_JSON

API = "https://meta.wikimedia.org/w/api.php"
CATEGORY = "Category:Wikimédia France/Finances/Dépense/Traitée/index"
USER_AGENT = "LinguaLibreDashboardBot/1.0 (bot@lingualibre.org)"


def api_get(params):
    params = {**params, "format": "json", "formatversion": 2, "maxlag": 5}
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req) as r:
            data = json.load(r)
        if data.get("error", {}).get("code") == "maxlag":  # servers lagging: back off
            time.sleep(5 * (attempt + 1))
            continue
        return data
    raise RuntimeError("Meta API still lagging")


def fetch_pages():
    """Return [{'title', 'content'}] for every page of the category, following continuation."""
    params = {
        "action": "query", "generator": "categorymembers", "gcmtitle": CATEGORY,
        "gcmlimit": 50,  # 50 is the cap when page contents are requested without bot rights
        "prop": "revisions", "rvprop": "content", "rvslots": "main",
    }
    pages = []
    while True:
        data = api_get(params)
        for page in data.get("query", {}).get("pages", []):
            revs = page.get("revisions") or []
            if revs:
                pages.append({"title": page["title"], "content": revs[0]["slots"]["main"]["content"]})
        if "continue" not in data:
            return sorted(pages, key=lambda p: p["title"])
        params.update(data["continue"])


def main():
    pages = fetch_pages()
    os.makedirs(os.path.dirname(META_JSON), exist_ok=True)
    with open(META_JSON, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=1)
    print(f"Fetched {len(pages)} pages from {CATEGORY} into {META_JSON}")


if __name__ == "__main__":
    main()
