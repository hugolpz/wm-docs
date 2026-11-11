"""Formatting shared by extract.py and merge_tsv.py."""
import os
import re
from datetime import datetime

# Module root: this file lives in <module>/scripts/
MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(MODULE_DIR, "sources", "pdfs")
LEGACY_TSV = os.path.join(MODULE_DIR, "sources", "legacy_table.tsv")
OUTPUT_JSON = os.path.join(MODULE_DIR, "data", "spendings_data.json")

LEGACY_SOURCE = (
    '<a href="https://meta.wikimedia.org/wiki/Wikimédia_France/Finances/Dépense/2020-2021">'
    "2020-2021 table</a>"
)


def source_link(filename):
    """HTML link to the Commons file page of a WMFR PDF."""
    return f'<a href="https://commons.wikimedia.org/wiki/File:{filename}">{filename}</a>'


def normalize_date(value, filename=""):
    """Return YYYY/MM/DD. An empty or unparsable date falls back to YYYY/MM/xx from a
    WMFR_Depenses_YYYYMM.pdf filename, else ''."""
    value = (value or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y/%m/%d")
        except ValueError:
            pass
    m = re.search(r"(\d{4})(\d{2})\.pdf$", filename)
    return f"{m.group(1)}/{m.group(2)}/xx" if m else ""

META_JSON = os.path.join(MODULE_DIR, "sources", "meta_expenses.json")


def prepend_rows(new_rows, is_own_row):
    """Prepend new_rows to OUTPUT_JSON, first dropping rows already added by the same source
    (is_own_row), so merging twice does not duplicate anything."""
    import json
    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        data = [r for r in json.load(f) if not is_own_row(r)]
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(new_rows + data, f, ensure_ascii=False, indent=2)
    return len(new_rows), len(data)
