"""Small wikitext helpers shared by merge_meta.py and build_supports.py."""
import re

WIKILINK = re.compile(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]")


def iter_templates(text, name):
    """Yield {param: value} for every {{name ...}} in text. Pipes nested in [[links]] and
    {{templates}} do not split parameters."""
    opening = re.compile(r"\{\{\s*" + re.escape(name) + r"\s*(?=[|}\n])", re.I)
    for m in opening.finditer(text):
        parts, buf, depth, i = [], "", 0, m.end()
        while i < len(text):
            two = text[i:i + 2]
            if two in ("{{", "[["):
                depth += 1
                buf += two
                i += 2
            elif two in ("}}", "]]"):
                if depth == 0:
                    break
                depth -= 1
                buf += two
                i += 2
            else:
                if text[i] == "|" and depth == 0:
                    parts.append(buf)
                    buf = ""
                else:
                    buf += text[i]
                i += 1
        parts.append(buf)
        params = {}
        for part in parts[1:]:
            if "=" in part:
                key, value = part.split("=", 1)
                params[key.strip()] = value.strip()
        yield params


def unlink(text, last_segment=False):
    """[[target|label]] -> label, [[target]] -> target (or its last path segment)."""
    def repl(m):
        label = m.group(2) or (m.group(1).split("/")[-1] if last_segment else m.group(1))
        return label.strip()
    return WIKILINK.sub(repl, text)


def clean_text(text):
    """Plain text of a wikitext value: no comments, translate/tvar markup or links."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<tvar[^>]*>.*?</tvar>", "", text, flags=re.S)  # translatable variables
    text = re.sub(r"</?translate>", "", text)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    return re.sub(r"\s+", " ", unlink(text)).strip()
