import csv
from spendings_format import LEGACY_TSV, OUTPUT_JSON, LEGACY_SOURCE, normalize_date, prepend_rows

tsv_path = LEGACY_TSV

with open(tsv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    new_entries = []
    for row in reader:
        # identifiant	Date	Moti	Personne associée	Projet associée	Étape	Montant TTC
        # Handle typo in header 'Moti'
        motif = row.get('Moti', '') or row.get('Motif', '')
        
        # Format amount - insert space before Euro sign if not present
        montant = row.get('Montant TTC', '').strip()
        if montant.endswith('€') and not montant.endswith(' €'):
            montant = montant[:-1] + ' €'
            
        entry = {
            "Date": normalize_date(row.get('Date', '')),
            "Montant TTC": montant,
            "Motif": motif,
            "Projet associé": row.get('Projet associée', ''),
            "Personne associée": row.get('Personne associée', ''),
            "Identifiant": row.get('identifiant', row.get('Identifiant', '')),
            "Source": LEGACY_SOURCE
        }
        new_entries.append(entry)

added, kept = prepend_rows(new_entries, lambda r: r["Source"] == LEGACY_SOURCE)
print(f"Added {added} legacy entries to {OUTPUT_JSON} ({kept} others kept)")
