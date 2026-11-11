import os
import glob
import json
import re
import pdfplumber
from spendings_format import PDF_DIR, OUTPUT_JSON, source_link, normalize_date

def extract_tables_from_pdf(pdf_path):
    print(f"Extracting tables from {pdf_path}")
    extracted_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables({"snap_tolerance": 3, "intersection_tolerance": 3})
            for table in tables:
                if not table: continue
                # find header row
                header_idx = -1
                for i, row in enumerate(table):
                    row_texts = [str(x).lower().strip() if x else '' for x in row]
                    if any('date' in x for x in row_texts) and any('montant' in x for x in row_texts):
                        header_idx = i
                        break
                
                if header_idx != -1:
                    # Parse from header_idx + 1
                    headers_list = [str(h).strip().replace('\n', ' ') if h else '' for h in table[header_idx]]
                    
                    for row in table[header_idx+1:]:
                        if not row: continue
                        if all(x is None or str(x).strip() == '' for x in row): continue
                        
                        entry = {}
                        for i, cell in enumerate(row):
                            val = str(cell).strip().replace('\n', ' ') if cell else ""
                            if i < len(headers_list) and headers_list[i]:
                                entry[headers_list[i]] = val
                        
                        if entry:
                            extracted_data.append(entry)

    return extracted_data

PROJECT_RE = re.compile(r"^\d\.\d\.[A-Z] - \S")

def is_subsequence(needle, haystack):
    it = iter(haystack)
    return all(ch in it for ch in needle)

def repair_projects(rows):
    """PDF text extraction sometimes interleaves stray letters into the project cell
    (e.g. '2u.e3 .dDe -s Micro-financement France'). Restore it from the well-formed
    project labels found elsewhere: the unique one whose characters all appear, in order,
    in the garbled string (longest wins)."""
    key = "Projet associé"
    known = {r[key] for r in rows if PROJECT_RE.match(r[key])}
    for r in rows:
        value = r[key]
        if not value or PROJECT_RE.match(value):
            continue
        matches = [k for k in known if len(value) - len(k) <= 12 and is_subsequence(k, value)]
        # Several labels can fit ('... Wiki Franca' vs '... WikiFranca'): the longest is the most specific
        best = [k for k in matches if len(k) == max(map(len, matches))] if matches else []
        if len(best) == 1:
            r[key] = best[0]
        else:
            print(f"Unrepaired project in {r['Source']}: {value!r} ({len(matches)} candidates)")

def main():
    pdf_files = sorted(glob.glob(os.path.join(PDF_DIR, "WMFR_Depenses_*.pdf")))

    all_spendings = []
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        try:
            data = extract_tables_from_pdf(pdf_path)
            # Tag with the source
            for d in data:
                d['SourcePDF'] = filename
            all_spendings.extend(data)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    # Normalize headers
    output_data = []
    for row in all_spendings:
        normalized_row = {
            "Date": "",
            "Montant TTC": "",
            "Motif": "",
            "Projet associé": "",
            "Personne associée": "",
            "Identifiant": "",
            "Source": row.get("SourcePDF", "")
        }
        for k, v in row.items():
            k_lower = k.lower()
            if 'date' in k_lower:
                normalized_row['Date'] = v
            elif 'montant' in k_lower:
                normalized_row['Montant TTC'] = v
            elif 'motif' in k_lower or 'libell' in k_lower or 'description' in k_lower:
                normalized_row['Motif'] = v
            elif 'projet' in k_lower:
                normalized_row['Projet associé'] = v
            elif 'personne' in k_lower or 'bénéficiaire' in k_lower or 'acteur' in k_lower:
                normalized_row['Personne associée'] = v
            elif 'identifiant' in k_lower or 'id ' in k_lower or ' réf ' in k_lower or k_lower == 'id':
                normalized_row['Identifiant'] = v
        
        # Keep it if at least Date or Montant or Motif are present
        # Dates as YYYY/MM/DD, or YYYY/MM/xx from the file name when the cell is empty
        filename = normalized_row["Source"]
        normalized_row["Date"] = normalize_date(normalized_row["Date"], filename)
        normalized_row["Source"] = source_link(filename)

        if normalized_row['Date'] or normalized_row['Montant TTC'] or normalized_row['Motif']:
            output_data.append(normalized_row)
            
    repair_projects(output_data)

    out_json = OUTPUT_JSON
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print(f"Extraction complete. Wrote {len(output_data)} entries to {out_json}")

if __name__ == "__main__":
    main()
