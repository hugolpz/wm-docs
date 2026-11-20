"""Derive data/spendings_data.public.json from spendings_data.json.

In "Personne associée" (parts separated by " – "):
  - staff of Wikimédia France (names seen with a "WMFr" suffix, typos tolerated) -> [WMFR_staff]
  - process notes ("Par µFi", ...) and organisations are kept
  - any other person, username or typo -> [name in source]
Names found elsewhere ("Motif", "Identifiant", the visible text of "Source") are masked the same way.
Names come from the "Personne associée" column, the STAFF list and EXTRA_NAMES below. The href of a
"Source" link is left alone so the link keeps working.
"""
import argparse, csv, difflib, json, os, re, unicodedata

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(DIR, "sources", "anonymized_items.tsv")
SRC = os.path.join(DIR, "data", "spendings_data.json")
OUT = os.path.join(DIR, "data", "spendings_data.public.json")

STAFF = ["Cindy David", "Jonathan Balima", "Rémy Gerbet", "Adélaïde Calais", "Sarah Krichen",
         "Mathieu Denel", "Xavier Cailleau", "Michaël Barbereau", "Amélie Cabon",
         "Alejandra Reyes", "Naphsica Papanicolaou", "Sylvain Boissel",
         "Luc Hervier", "Céline Husetowski"]
KEEP = re.compile(r"^(par\s|les ateliers)", re.I)
# (original text, tag) -> {column: count}, filled while masking and written to REPORT for manual review
FOUND = {}
CURRENT = [""]
def record(original, tag):
    FOUND.setdefault((original.strip(), tag), {}).setdefault(CURRENT[0], 0)
    FOUND[(original.strip(), tag)][CURRENT[0]] += 1

STAFF_TAG, OTHER_TAG = "[WMFR_staff]", "[name in source]"

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"wmfr", "", s)
    return re.sub(r"[^a-z]", "", s)

STAFF_KEYS = [norm(n) for n in STAFF]

def is_staff(part):
    k = norm(part)
    return bool(k) and any(difflib.SequenceMatcher(None, k, s).ratio() >= 0.9 for s in STAFF_KEYS)

# Names seen in free text but not (or differently written) in "Personne associée". (text, tag)
EXTRA_NAMES = [
    ("Hugo Lopez", OTHER_TAG), ("Yug", OTHER_TAG), ("Pierre-Yves Mevel", OTHER_TAG), ("P-Y Mevel", OTHER_TAG),
    ("N. Vignero", OTHER_TAG), ("Vigneron", OTHER_TAG), ("Anne-Laure et Nicolas", OTHER_TAG), ("Anne Laure et Nicolas", OTHER_TAG),
]

def strip_accents(text):
    # Same length as the input, so spans found on it apply to the original
    return "".join(unicodedata.normalize("NFD", c)[0] for c in text).lower()

def looks_like_name(part):
    toks = re.sub(r"(?i)\bwmfr\b", "", part).split()
    return (len(toks) >= 2 and len({t.lower() for t in toks}) == len(toks)
            and all(re.fullmatch(r"[^\W\d_][\w'’.\-]*", t) for t in toks) and not KEEP.match(part))

def build_name_patterns(rows):
    names = {}
    for n in STAFF: names[n] = STAFF_TAG
    for r in rows:
        for part in re.split(r"\s+–\s+", r.get("Personne associée", "")):
            part = re.sub(r"(?i)\s*\bwmfr\b", "", part).strip()
            if looks_like_name(part): names.setdefault(part, STAFF_TAG if is_staff(part) else OTHER_TAG)
    for n, tag in EXTRA_NAMES: names.setdefault(n, tag)
    patterns = []  # (regex, tag), longest names first
    for n, tag in sorted(names.items(), key=lambda x: -len(x[0])):
        toks = [re.escape(strip_accents(t)) for t in n.split()]
        sep = r"[\s_\-]+"
        forms = [sep.join(toks)]
        if len(toks) == 2: forms.append(sep.join(reversed(toks)))
        for f in forms: patterns.append((re.compile(r"(?<!\w)" + f + r"(?!\w)"), tag))
    return patterns

# Given names that appear alone in free text ("Accueil Isabelle et Luc"). Names from the "Personne associée"
# column are added automatically. A surname right after one is masked when it is ALL CAPS or in SURNAMES.
EXTRA_FIRST = ["Alexandra", "Alexis", "Isabelle", "Marion", "Charlotte", "Morgane", "Pierre", "Françoise", "Didier",
               "Ibrahim", "Jean-Marie", "Jean", "Carine", "Hélène", "Saidou", "Nfana", "Afek", "Lyokoi"]
SURNAMES = ["Lerouge", "Boudeau", "Yao Kouamé", "Diop", "Allard", "Chantraine", "Ben Chahed", "Babada", "Sara"]
# Words that are also given names or sit in a place/organisation name: never masked on their own
NOT_NAMES = {"universite", "guyane", "les", "par", "ben", "saint"}

# Single words that are a person in free text but not (or only partly) in "Personne associée"
STAFF_TOKENS = ["Cindu", "Amél", "Xav", "Adé"]
OTHER_TOKENS = """Abdallah Abel Abida Aman Ado Anna Brahim Caroline Clément Diakité Diop Eliane Eric Faguer Faraji
Faroni Faure Fayçal Florence Gaston Genet Georges Gonzalez Habida Hamadou Houssem Ibrahima Ilaria Ivonne 
Jones Joss Kayser Kergourlay Koreis Kozlenko Lacroix Laugriville Lavy Levenez Lhoussine Léa Maryana Matéo
Maxime Maximoff Mekkia Mlouhi Mohammed Natacha Nonhouegnon Nunez Oumarou Patty Paulin Reda Richard Rezkallah Santos
Sami Soumana Sylvie Sébastien Takouti Thomas Théodore Zayneb Zeineb Zergaoui Sterenn Baidakov Bennama
Bentayfaste Diterlizzi Fodouop Gouglov Handgod Martelet Norbis Poncutelle Shasaid Micka Nick Fcuny Forestier Devouard Bola """.split()

def build_token_pattern(rows):
    """Usernames and surnames from "Personne associée", plus the lists above, masked when they appear alone.
    A token is skipped when it is also an ordinary lowercase word of the data (e.g. "train")."""
    lower_words = set()
    for r in rows:
        lower_words.update(strip_accents(w) for w in re.findall(r"[^\W\d_][\w'’]*", r.get("Motif", "") + " " + r.get("Identifiant", "")) if w[0].islower())
    tokens = {}
    for r in rows:
        for part in re.split(r"\s+–\s+", r.get("Personne associée", "")):
            part = re.sub(r"(?i)\s*\bwmfr\b", "", part).strip()
            if KEEP.match(part) or not part: continue
            toks = part.split()
            cands = toks if looks_like_name(part) else (toks if len(toks) == 1 else [])
            if looks_like_name(part): cands = toks[1:]
            staff = is_staff(part)
            for t in cands:
                k = strip_accents(t)
                if len(k) >= 5 and k not in lower_words and k not in NOT_NAMES:
                    tokens.setdefault(k, STAFF_TAG if staff else OTHER_TAG)
    for t in OTHER_TOKENS: tokens[strip_accents(t)] = OTHER_TAG
    for t in STAFF_TOKENS: tokens[strip_accents(t)] = STAFF_TAG
    rx = re.compile(r"(?<![\w-])(?:" + "|".join(sorted(map(re.escape, tokens), key=len, reverse=True)) + r")(?![\w])")
    return rx, tokens

def build_first_names(rows):
    firsts = {}
    for n in STAFF: firsts[strip_accents(n.split()[0])] = STAFF_TAG
    for r in rows:
        for part in re.split(r"\s+–\s+", r.get("Personne associée", "")):
            part = re.sub(r"(?i)\s*\bwmfr\b", "", part).strip()
            if looks_like_name(part):
                f = strip_accents(part.split()[0])
                if len(f) > 2 and f not in NOT_NAMES: firsts.setdefault(f, OTHER_TAG)
    for n in EXTRA_FIRST: firsts.setdefault(strip_accents(n), OTHER_TAG)
    # "Luc" or "Céline" alone is a staff member, but Pascal, Jonathan Mouton... are volunteers
    return {f: (t if f in LONE_STAFF_FIRST else OTHER_TAG) for f, t in firsts.items()}

LONE_STAFF_FIRST = {strip_accents(n.split()[0]) for n in STAFF}

def first_name_pattern(firsts):
    surn = "|".join(re.escape(strip_accents(x)).replace(r"\ ", r"[\s_]+") for x in SURNAMES)
    first = "|".join(sorted((re.escape(f) for f in firsts), key=len, reverse=True))
    # first name, then optionally a known surname; ALL CAPS surnames are handled by the caller on the original text
    return re.compile(r"(?<![\w-])(?:" + first + r")(?:[\s_\-]+(?:" + surn + r"))?(?![\w])")

def mask_text(text, patterns, first_rx=None, firsts=None, tok=None):
    plain = strip_accents(text)
    spans = []
    if first_rx:
        for m in first_rx.finditer(plain):
            # A trailing ALL CAPS surname in the original text belongs to the name
            end = m.end()
            tail = re.match(r"[\s_]+(?:[A-ZÀ-Ý][A-ZÀ-Ý'’\-]{3,}|[A-ZÀ-Ý]\.?)(?![\w])", text[end:])
            if tail: end += tail.end()
            if text[:m.start()].rstrip().lower().endswith("saint-") or text[max(0, m.start()-6):m.start()].lower() == "saint-": continue
            word = plain[m.start():m.end()].split()[0]
            tag = firsts.get(word.split("-")[0].split("_")[0], OTHER_TAG)
            tag = tag if end == m.end() else OTHER_TAG if tag == OTHER_TAG else (STAFF_TAG if is_staff(text[m.start():end]) else OTHER_TAG)
            spans.append((m.start(), end, tag))
    if tok:
        for m in tok[0].finditer(plain):
            if not any(m.start() < e and s < m.end() for s, e, _ in spans): spans.append((m.start(), m.end(), tok[1][m.group()]))
    for rx, tag in patterns:
        for m in rx.finditer(plain):
            spans = [x for x in spans if not (m.start() <= x[0] and x[1] <= m.end())]
            if not any(m.start() < e and s < m.end() for s, e, _ in spans): spans.append((m.start(), m.end(), tag))
    for st, en, tag in sorted(spans, reverse=True):
        record(text[st:en], tag)
        text = text[:st] + tag + text[en:]
    return text

def mask_source(html, patterns, first_rx=None, firsts=None, tok=None):
    # Mask the visible text between tags only: the href keeps the page title so the link works
    return re.sub(r"(>)([^<]+)(<)", lambda m: m.group(1) + mask_text(m.group(2), patterns, first_rx, firsts, tok) + m.group(3), html)

def mask(value):
    out = []
    for part in re.split(r"\s+–\s+", value):
        if KEEP.match(part.strip()): out.append(part)
        elif is_staff(part): out.append(STAFF_TAG); record(part, STAFF_TAG)
        else: out.append(OTHER_TAG); record(part, OTHER_TAG)
    return " – ".join(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", metavar="TSV", help="also write every change (original -> masked) to this TSV file. "
                    "It contains the real names: keep it out of git.")
    args = ap.parse_args()
    rows = json.load(open(SRC, encoding="utf-8"))
    patterns = build_name_patterns(rows)
    changes = []
    for i, r in enumerate(rows):
        for col in ("Motif", "Identifiant", "Source", "Personne associée"):
            old = r.get(col)
            if not old: continue
            new = (mask_source(old, patterns) if col == "Source"
                   else mask(old) if col == "Personne associée" else mask_text(old, patterns))
            if new != old:
                r[col] = new
                changes.append((i + 1, col, old, new))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"{len(rows)} rows, {len(changes)} masked values -> {OUT}")
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["row", "column", "original", "masked"])
            w.writerows(changes)
        print(f"report -> {args.report}")
