"""Turn the Meta-Wiki expense pages fetched by fetch_meta.py into spendings rows and
prepend them to data/spendings_data.json. Idempotent."""
import html
import json
import re
import urllib.parse

from spendings_format import META_JSON, LEGACY_SOURCE, prepend_rows, normalize_date
from wikitext import iter_templates, unlink

TEMPLATE = "{{Dépense Wikimédia France"
TITLE_PREFIX = re.compile(r"^Wikim[ée]dia France/Finances/Dépense/")
OK_STATUS = {"", "approuvée", "exécutée", "archivée", "vérifiée"}  # 'demandée' = not approved yet
USER_LINK = re.compile(r"\[\[(?:User|Utilisateur|Utilisatrice):([^|\]]+)", re.I)
SIGNATURE_TAIL = re.compile(r"\(\[\[[^\]]*\]\]\)|\d{1,2}:\d\d, \d{1,2} \w+ \d{4} \(UTC\)")


def template_params(text):
    return next(iter_templates(text, "Dépense Wikimédia France"))


def clean_text(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return re.sub(r"\s+", " ", unlink(text)).strip()


def clean_person(text):
    """Username of the first [[User:...]] link; otherwise the free text without signature
    timestamps or links ('John Smith', 'Par µFi')."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    m = USER_LINK.search(text)
    if m:
        return m.group(1).strip()
    contrib = re.search(r"\[\[Special:Contributions/([^|\]]+)", text, re.I)
    if contrib:
        return contrib.group(1).strip()
    return re.sub(r"\s+", " ", unlink(SIGNATURE_TAIL.sub("", text))).strip(" ,;-")


def clean_amount(text):
    """'86,10€', '1 846.8 €', 'env. 206.98€', '100 euros (A/R)' -> '86,10 €' (empty if no number)."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S).replace(" ", " ")
    m = re.search(r"\d[\d ]*(?:[.,]\d+)?", text)
    if not m:
        return ""
    number = m.group(0).replace(" ", "").replace(",", ".")
    return f"{float(number):.2f}".replace(".", ",") + " €"


def page_date(params, title):
    date = normalize_date(clean_text(params.get("date", "")))
    if date:
        return date
    in_title = re.search(r"/(\d{4})/(\d\d)/", title)
    for candidate in (clean_text(params.get("mois exécution", "")),
                      f"{in_title.group(1)}/{in_title.group(2)}" if in_title else ""):
        m = re.fullmatch(r"(\d{4})/(\d\d)", candidate)
        if m:
            return f"{m.group(1)}/{m.group(2)}/xx"
    return ""


def row_from_page(page):
    params = template_params(page["content"])
    title = page["title"]
    short = TITLE_PREFIX.sub("", title)
    leaf = re.sub(r"^\d{4}/\d\d/", "", short)  # page name; it may itself contain "/"
    motif = clean_text(params.get("motif", ""))
    if leaf.lower() == "test":
        return None, "test page"
    status = clean_text(params.get("statut", "")).lower()
    if status not in OK_STATUS:
        return None, f"status {status!r}"
    amount = clean_amount(params.get("montant", ""))
    if not amount:
        return None, f"no amount ({params.get('montant', '')!r})"
    people = []
    for name in (clean_person(params.get("approbation", "")), clean_person(params.get("signature demande", ""))):
        if name and name not in people:
            people.append(name)
    href = "https://meta.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"), safe="/:")
    return {
        "Date": page_date(params, title),
        "Montant TTC": amount,
        "Motif": leaf if not motif or motif.lower() == leaf.lower() else f"{leaf} – {motif}",
        "Projet associé": unlink(clean_text(params.get("projet", "")), last_segment=True),
        "Personne associée": " – ".join(people),
        "Identifiant": short,
        "Source": f'<a href="{html.escape(href, quote=True)}">{html.escape(short)}</a>',
    }, ""


def is_meta_row(row):
    return row["Source"].startswith('<a href="https://meta.wikimedia.org/') and row["Source"] != LEGACY_SOURCE


def main():
    with open(META_JSON, "r", encoding="utf-8") as f:
        pages = json.load(f)
    rows = []
    for page in pages:
        if TEMPLATE not in page["content"]:
            print(f"Skipped {page['title']}: no template")
            continue
        row, reason = row_from_page(page)
        if row:
            rows.append(row)
        else:
            print(f"Skipped {page['title']}: {reason}")
    rows.sort(key=lambda r: r["Date"])
    for r in rows:
        if not re.fullmatch(r"\d{4}/\d\d/(\d\d|xx)", r["Date"]):
            print(f"Warning: unusable date {r['Date']!r} in {r['Identifiant']}")
    added, kept = prepend_rows(rows, is_meta_row)
    print(f"Added {added} Meta-Wiki entries ({kept} others kept)")


if __name__ == "__main__":
    main()
