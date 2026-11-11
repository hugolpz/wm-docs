"""Download the WMFR expense PDFs listed in Commons' Category:Wikimedia_France_expenses into sources/pdfs/."""
import json
import os
import urllib.parse
import urllib.request

from spendings_format import PDF_DIR

API = "https://commons.wikimedia.org/w/api.php"
CATEGORY = "Category:Wikimedia_France_expenses"
USER_AGENT = "LinguaLibreDashboardBot/1.0 (bot@lingualibre.org)"
SOURCES_DIR = PDF_DIR


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req) as r:
        return r.read()


def list_pdfs():
    """Return {filename: url} for every PDF in the category, following API continuation."""
    params = {
        "action": "query", "generator": "categorymembers", "gcmtitle": CATEGORY,
        "gcmtype": "file", "gcmlimit": 500, "prop": "imageinfo", "iiprop": "url|mime",
        "format": "json", "formatversion": 2,
    }
    pdfs = {}
    while True:
        data = json.loads(fetch(API + "?" + urllib.parse.urlencode(params)))
        for page in data.get("query", {}).get("pages", []):
            info = (page.get("imageinfo") or [{}])[0]
            if info.get("mime") == "application/pdf":
                url = info["url"].split("?")[0]
                pdfs[os.path.basename(urllib.parse.unquote(url))] = url
        if "continue" not in data:
            return pdfs
        params.update(data["continue"])


def main():
    os.makedirs(SOURCES_DIR, exist_ok=True)
    pdfs = list_pdfs()
    print(f"{len(pdfs)} PDFs in {CATEGORY}")
    for name, url in sorted(pdfs.items()):
        path = os.path.join(SOURCES_DIR, name)
        if os.path.exists(path) and os.path.getsize(path) > 0:
            continue
        print(f"Downloading {name}")
        with open(path, "wb") as f:
            f.write(fetch(url))


if __name__ == "__main__":
    main()
