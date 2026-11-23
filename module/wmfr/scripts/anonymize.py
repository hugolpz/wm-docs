"""Derive data/spendings_data.public.json from spendings_data.json.

In "Personne associée" (parts separated by " – "):
  - process notes ("Par µFi", ...) and organisations are kept
  - any person, username or typo is replaced by a pseudonym such as [Pink-Koala]; staff of Wikimédia France
    (names seen with a "WMFr" suffix, typos tolerated) get a _WMFr suffix: [Fire-Jay_WMFr]
  - all spellings of the same person share one pseudonym ("Adélaïde", "ADÉLAÏDE Calais WMFr", "Adé"...)
Names to hide are listed in sources/names.tsv, the replacement table sources/pseudonyms.tsv (pseudonym, person, original text) is human-editable: change the
pseudonym of a line to merge or split people, add lines for spellings the script missed. Lines are never
overwritten, new spellings are appended. Names found elsewhere ("Motif", "Identifiant", the visible text of "Source") are masked the same way.
Names come from the "Personne associée" column, sources/names.tsv. The href of a
"Source" link is left alone so the link keeps working.
"""
import argparse, csv, difflib, hashlib, json, os, re, unicodedata

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(DIR, "sources", "anonymized_items.tsv")
TABLE = os.path.join(DIR, "sources", "pseudonyms.tsv")
SRC = os.path.join(DIR, "data", "spendings_data.json")
OUT = os.path.join(DIR, "data", "spendings_data.public.json")

NAMES = os.path.join(DIR, "sources", "names.tsv")

def load_names(path):
    """Seed names (kept out of git) from sources/names.tsv, see the header of that file"""
    if not os.path.exists(path):
        raise SystemExit(f"{path} is missing: it lists the names to hide (kinds: staff, staff_token, name, first, surname, token)")
    kinds = {}
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.reader((l for l in f if not l.startswith("#")), delimiter="\t"):
            if len(row) >= 2 and row[0] != "kind": kinds.setdefault(row[0], []).append((row[1], row[2] if len(row) > 2 else ""))
    return kinds
SEED = load_names(NAMES)
STAFF = [v for v, _ in SEED.get("staff", [])]
KEEP = re.compile(r"^(par\s|les ateliers)", re.I)
# (original text, tag) -> {column: count}, filled while masking and written to REPORT for manual review
FOUND = {}
CURRENT = [""]
def record(original, tag):
    FOUND.setdefault((original.strip(), tag), {}).setdefault(CURRENT[0], 0)
    FOUND[(original.strip(), tag)][CURRENT[0]] += 1

# A "person" is a string: the staff member's full name, or "~<key>" for anyone else
def person_key(text):
    return "~" + "".join(sorted(norm(t) for t in text.split()))

def staff_match(part):
    """Staff member (name from STAFF) closest to this text, or None"""
    k = norm(part)
    if not k: return None
    best = max(zip(STAFF, STAFF_KEYS), key=lambda x: difflib.SequenceMatcher(None, k, x[1]).ratio())
    return best[0] if difflib.SequenceMatcher(None, k, best[1]).ratio() >= 0.9 else None

def person_of(text):
    return staff_match(text) or person_key(text)

ANIMALS = """Fox Koala Jay Gibbon Sparrow Otter Lynx Heron Panda Gecko Ibis Newt Lemur Alpaca Hare Crane Finch Seal Moth Wren
Bison Eagle Osprey Robin Pelican Tapir Marmot Yak Zebu Badger Beaver Gazelle Caribou Egret Ferret Gull Bunting Impala Kiwi Lark
Marten Narwhal Ocelot Puffin Quail Raven Plover Dolphin Vole Falcon Okapi Pika Civet Dove Eel Mink Orca Swan Tern Auk""".split()
ADJECTIVES = """Fire Pink Steamy Cloud Green Light Quiet Swift Brave Calm Sunny Eager Fancy Grand Happy Icy Jolly Keen Brisk Merry
Noble Olive Proud Copper Shiny Nimble Vivid Witty Young Zesty Amber Blue Coral Lilac Early Frosty Golden Hazy Indigo Jade Kind
Lucky Misty Neat Orange Mellow Quick Red Silver Teal Violet Windy Yellow Bold Crisp Deft Fuzzy Gentle""".split()

class Pseudonyms:
    """Human-editable table: pseudonym, person, original text. Exact spelling wins, then the person's pseudonym."""
    def __init__(self, path):
        self.path, self.by_text, self.by_person, self.rows, self.used = path, {}, {}, [], set()
        if os.path.exists(path):
            with open(path, encoding="utf-8", newline="") as f:
                for row in csv.reader(f, delimiter="\t"):
                    if len(row) < 3 or row[0] == "pseudonym": continue
                    self.add(*row[:3], new=False)
    def add(self, pseudo, person, text, new=True):
        self.rows.append((pseudo, person, text))
        self.by_text.setdefault(text, pseudo)
        self.by_person.setdefault(person, pseudo)
        self.used.add(pseudo)
        self.changed = getattr(self, "changed", False) or new
    def fresh(self, person, staff):
        # Deterministic start from the person, then probe until the pseudonym is unused
        h = int(hashlib.md5(person.encode()).hexdigest(), 16)
        suffix = "_WMFr" if staff else ""
        for i in range(len(ADJECTIVES) * len(ANIMALS)):
            n = (h + i) % (len(ADJECTIVES) * len(ANIMALS))
            p = f"[{ADJECTIVES[n % len(ADJECTIVES)]}-{ANIMALS[n // len(ADJECTIVES)]}{suffix}]"
            if p not in self.used: return p
        raise RuntimeError("out of pseudonyms")
    def get(self, person, text):
        text = text.strip()
        if text in self.by_text: return self.by_text[text]
        pseudo = self.by_person.get(person) or self.fresh(person, not person.startswith("~"))
        self.add(pseudo, person, text)
        return pseudo
    def save(self):
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["pseudonym", "person", "original text"])
            w.writerows(sorted(set(self.rows), key=lambda r: (r[1].lower(), r[0], r[2].lower(), r[2])))

PSEUDO = None

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"wmfr", "", s)
    return re.sub(r"[^a-z]", "", s)

STAFF_KEYS = [norm(n) for n in STAFF]

def is_staff(part):
    return staff_match(part) is not None

# Names seen in free text but not (or differently written) in "Personne associée". (text, same person as, or None)
EXTRA_NAMES = [(v, o or None) for v, o in SEED.get("name", [])]

def strip_accents(text):
    # Same length as the input, so spans found on it apply to the original
    return "".join(unicodedata.normalize("NFD", c)[0] for c in text).lower()

def looks_like_name(part):
    toks = re.sub(r"(?i)\bwmfr\b", "", part).split()
    return (len(toks) >= 2 and len({t.lower() for t in toks}) == len(toks)
            and all(re.fullmatch(r"[^\W\d_][\w'’.\-]*", t) for t in toks) and not KEEP.match(part))

def build_name_patterns(rows):
    names = {}
    for n in STAFF: names[n] = n
    for r in rows:
        for part in re.split(r"\s+–\s+", r.get("Personne associée", "")):
            part = re.sub(r"(?i)\s*\bwmfr\b", "", part).strip()
            if looks_like_name(part): names.setdefault(part, person_of(part))
    for n, same in EXTRA_NAMES: names.setdefault(n, person_of(same or n))
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
EXTRA_FIRST = [v for v, _ in SEED.get("first", [])]
SURNAMES = [v for v, _ in SEED.get("surname", [])]
# Words that are also given names or sit in a place/organisation name: never masked on their own
NOT_NAMES = {"universite", "guyane", "les", "par", "ben", "saint"}

# Single words that are a person in free text but not (or only partly) in "Personne associée"
STAFF_TOKENS = [v for v, _ in SEED.get("staff_token", [])]
STAFF_TOKEN_OWNERS = [o for _, o in SEED.get("staff_token", [])]
OTHER_TOKENS = [v for v, _ in SEED.get("token", [])]

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
            person = person_of(part)
            for t in cands:
                k = strip_accents(t)
                if len(k) >= 5 and k not in lower_words and k not in NOT_NAMES:
                    tokens.setdefault(k, person if looks_like_name(part) else person_of(t))
    surname_of = {}  # surname -> person, when only one full name has it
    for r in rows:
        for part in re.split(r"\s+–\s+", r.get("Personne associée", "")):
            part = re.sub(r"(?i)\s*\bwmfr\b", "", part).strip()
            if looks_like_name(part):
                surname_of.setdefault(strip_accents(part.split()[-1]), set()).add(person_of(part))
    for t in OTHER_TOKENS:
        k = strip_accents(t); owners = surname_of.get(k, set())
        tokens[k] = next(iter(owners)) if len(owners) == 1 else person_key(t)
    for t, n in zip(STAFF_TOKENS, STAFF_TOKEN_OWNERS): tokens[strip_accents(t)] = n
    rx = re.compile(r"(?<![\w-])(?:" + "|".join(sorted(map(re.escape, tokens), key=len, reverse=True)) + r")(?![\w])")
    return rx, tokens

def build_first_names(rows):
    firsts = {}
    seen = {}  # first name -> people having it
    for r in rows:
        for part in re.split(r"\s+–\s+", r.get("Personne associée", "")):
            part = re.sub(r"(?i)\s*\bwmfr\b", "", part).strip()
            if looks_like_name(part):
                f = strip_accents(part.split()[0])
                if len(f) > 2 and f not in NOT_NAMES: seen.setdefault(f, set()).add(person_of(part))
    for n in EXTRA_FIRST: seen.setdefault(strip_accents(n), set())
    # A first name alone is the person when only one has it; "Luc" or "Céline" alone are staff
    for f, people in seen.items():
        firsts[f] = next(iter(people)) if len(people) == 1 else person_key(f)
    for n in STAFF: firsts[strip_accents(n.split()[0])] = n
    return firsts

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
            tag = firsts.get(word.split("-")[0].split("_")[0]) or person_key(word)
            if end != m.end(): tag = person_of(text[m.start():end])
            spans.append((m.start(), end, tag))
    if tok:
        for m in tok[0].finditer(plain):
            if not any(m.start() < e and s < m.end() for s, e, _ in spans): spans.append((m.start(), m.end(), tok[1][m.group()]))
    for rx, tag in patterns:
        for m in rx.finditer(plain):
            spans = [x for x in spans if not (m.start() <= x[0] and x[1] <= m.end())]
            if not any(m.start() < e and s < m.end() for s, e, _ in spans): spans.append((m.start(), m.end(), tag))
    for st, en, person in sorted(spans, reverse=True):
        tag = PSEUDO.get(person, text[st:en])
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
        else:
            tag = PSEUDO.get(person_of(re.sub(r"(?i)\s*\bwmfr\b", "", part)), part)
            out.append(tag); record(part, tag)
    return " – ".join(out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", metavar="TSV", help="also write every change (original -> masked) to this TSV file. "
                    "It contains the real names: keep it out of git.")
    args = ap.parse_args()
    rows = json.load(open(SRC, encoding="utf-8"))
    PSEUDO = Pseudonyms(TABLE)
    patterns = build_name_patterns(rows)
    tok = build_token_pattern(rows)
    firsts = build_first_names(rows)
    first_rx = first_name_pattern(firsts)
    fn = dict(first_rx=first_rx, firsts=firsts, tok=tok)
    changes = []
    for i, r in enumerate(rows):
        for col in ("Motif", "Identifiant", "Source", "Personne associée"):
            old = r.get(col)
            if not old: continue
            CURRENT[0] = col
            new = (mask_source(old, patterns, **fn) if col == "Source"
                   else mask(old) if col == "Personne associée" else mask_text(old, patterns, **fn))
            if new != old:
                r[col] = new
                changes.append((i + 1, col, old, new))
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    PSEUDO.save()
    with open(REPORT, "w", encoding="utf-8", newline="") as f:
        f.write("masked as\toriginal text\tcolumns (count)\n")
        for (orig, tag), cols in sorted(FOUND.items(), key=lambda x: (x[0][1].lower(), x[0][0].lower())):
            f.write(f"{tag}\t{orig}\t{', '.join(f'{c} ({n})' for c, n in cols.items())}\n")
    print(f"{len(rows)} rows, {len(changes)} masked values -> {OUT}")
    print(f"{len({t for _, t in FOUND})} pseudonyms; table -> {TABLE}, report -> {REPORT}")
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["row", "column", "original", "masked"])
            w.writerows(changes)
        print(f"report -> {args.report}")
