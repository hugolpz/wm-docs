# wmfr

Searchable table of the Wikimedia France (WMFR) spendings: every column is filterable, filters live in the URL (`#/wmfr?project=wikipages&date=2024`), and the total of the filtered rows is shown.

| Path | Content |
|---|---|
| `WmfrView.vue` | The view: breadcrumb + the table |
| `components/Spendings.vue` | The table |
| `data/spendings_data.json` | Generated data, imported by `Spendings.vue` |
| `scripts/`, `master.mk` | Python pipeline that builds the data |
| `sources/` | `legacy_table.tsv` (2020-07 – 2021); git-ignored downloads: `pdfs/`, `meta_expenses.json` |

## Refresh the data

```bash
pip install pdfplumber
make -f module/wmfr/master.mk      # download → extract → merge
```

1. `download_pdfs.py` fetches every PDF of Commons' `Category:Wikimedia_France_expenses` into `sources/pdfs/` (existing files are skipped).
2. `extract.py` parses `sources/pdfs/WMFR_Depenses_*.pdf` (2021-07 onwards) and rebuilds `spendings_data.json`. It repairs project labels garbled by the PDF text layer.
3. `fetch_meta.py` downloads the pages of Meta's `Category:Wikimédia France/Finances/Dépense/Traitée/index` (2018 – 2020/04, one `{{Dépense Wikimédia France}}` template each) into `sources/meta_expenses.json`.
4. `merge_tsv.py` and `merge_meta.py` prepend the legacy-table rows (2020-07 – 2021) and the Meta rows. They replace their own previous rows, so re-running is safe, but they must run after `extract.py`.

`spendings_data.json` columns: `Date` (`YYYY/MM/DD`, or `YYYY/MM/xx` when only the month is known), `Montant TTC`, `Motif`, `Projet associé`, `Personne associée`, `Identifiant`, `Source` (HTML link to the Commons file, the Meta 2020-2021 table, or the Meta page).

## Meta-Wiki rows: differences to know about

- **Skipped:** pages with status `demandée` (not approved), test pages, pages without an amount.
- **Motif:** `page name – motif`. **Personne associée:** `approver – requester` (usernames from the `[[User:...]]` links; free-text names are kept as written).
- **Projet associé:** the label of the `projet` link, not an `N.N.L - Name` code like the PDF rows, so these rows won't group with PDF projects.
- **Identifiant:** the page title without its `Wikimédia France/Finances/Dépense/` prefix (the template has no ID).
