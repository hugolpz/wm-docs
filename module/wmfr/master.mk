# Rebuild the module's generated data:
#  - data/spendings_data.json: WMFR PDFs (Commons) + legacy TSV + Meta-Wiki expense pages
# Usage: make -f master.mk [PYTHON=path/to/python]
# Requires: pdfplumber
PYTHON ?= python3
DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))scripts/

.PHONY: all download fetch_meta extract merge
all: merge

# Fetch the PDFs of Commons' Category:Wikimedia_France_expenses into sources/pdfs/ (skips existing)
download:
	$(PYTHON) $(DIR)download_pdfs.py

# Re-extract every sources/pdfs/WMFR_Depenses_*.pdf into spendings_data.json
extract: download
	$(PYTHON) $(DIR)extract.py

# Fetch the Meta-Wiki expense pages into sources/meta_expenses.json
fetch_meta:
	$(PYTHON) $(DIR)fetch_meta.py

# The merge scripts prepend their rows to extract.py's output, so they must follow a fresh extract
merge: extract fetch_meta
	$(PYTHON) $(DIR)merge_tsv.py
	$(PYTHON) $(DIR)merge_meta.py
