#!/usr/bin/env python3
"""Generate site/publications.html from tools/publications.bib.

Usage: python build_publications.py  (from any directory; paths resolve
relative to this file). Stdlib only; no dependencies.

The bib file is shared with the owner's LaTeX CV. Conventions the script
relies on:
  - \\textbf{...} in an author field marks Kevin; \\uline{...} marks lab
    members. Both render as <strong>. Entries with neither marker are
    support citations and are skipped.
  - note containing "under review" or "submitted" puts the entry in an
    Under Review subsection; "rejected" excludes it.
  - @misc entries are talks or duplicates and are skipped (talks are
    personal-page/news material, not lab publications).
  - Entry type sets the section (article -> Journal Papers,
    inproceedings -> Conference Papers, incollection -> Book Chapters)
    unless the note contains "poster"/"abstract" or the entry key is in
    SECTION_OVERRIDES below. New abstracts should carry "[poster]" or
    similar in the note so no override is needed.
  - keywords containing "selected" puts the entry in the Selected
    Publications cards at the top (it also stays in its normal section).
    Curate highlights by adding/removing that keyword.
  - Award text shown on the site lives in AWARDS below, keyed by entry.

The HTML page template at the bottom is site chrome. A chrome edit
(nav, header, footer) must be applied here AND to every page in site/
in the same session.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "tools" / "publications.bib"
OUT = ROOT / "site" / "publications.html"

# Collaborations where the lab appears inside "and others": include anyway.
INCLUDE_KEYS = {"cancers14235756", "pradoSymptoms2022", "VIP_ASEE_2017"}

# Entries superseded by a later version also present in the bib.
EXCLUDE_KEYS = {"albanese2025towards"}

# Award text displayed on the site (badge on cards, bracketed note in lists).
# Kept here rather than in the bib so the shared CV file is unaffected;
# migrate into bib notes if the CV should show them too.
AWARDS = {
    "fu2023pedShac": "Outstanding Paper Award",
    "RadAnatomy_AMIA_2022": "Student Paper Competition Finalist",
}

# Keys whose section cannot be inferred from type + note.
SECTION_OVERRIDES = {
    "sdoh_editorial": "nonrefereed",
    "elyazori2023exploring": "nonrefereed",
    "resapu2025evaluating_apha": "abstracts",
    "zhang2025semiautomatedposter": "abstracts",
    "abdulrazzaq2025capturing": "abstracts",
    "zhang2024semiposter": "abstracts",
    "camirAbstract2022": "abstracts",
    "SHAC_abstract_2020": "abstracts",
    "CACT_abstract_2020": "abstracts",
    "SDOH_poster_2019": "abstracts",
    "AMIA_NLP_WG_2018": "abstracts",
    "VGEENS_main_podium_2017": "abstracts",
    "quantifying_uncertainty_2010": "abstracts",
    "site_suitability_2010": "abstracts",
}

LATEX_CHARS = [
    (r'{\"O}', "\u00d6"), (r'{\"o}', "\u00f6"), (r'{\"u}', "\u00fc"),
    (r'{\"a}', "\u00e4"), (r"{\'i}", "\u00ed"), (r"{\'e}", "\u00e9"),
    (r"{\~n}", "\u00f1"), (r"{\'a}", "\u00e1"), (r"{\'o}", "\u00f3"),
    (r"{\'c}", "\u0107"), (r"{\`e}", "\u00e8"), (r'\"O', "\u00d6"),
    (r"\~n", "\u00f1"), (r"\dag", "\u2020"), (r"\&", "&"),
    (r"\%", "%"), (r"~", " "), (r"``", "\u201c"), (r"''", "\u201d"),
]

MONTHS = {"jan": "January", "feb": "February", "mar": "March", "apr": "April",
          "may": "May", "jun": "June", "jul": "July", "aug": "August",
          "sep": "September", "oct": "October", "nov": "November",
          "dec": "December"}


def parse_bib(text):
    """Minimal BibTeX parser for this file's conventions."""
    entries = []
    # Strip full-line comments.
    text = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("%"))
    for m in re.finditer(r"@(\w+)\s*\{", text):
        etype = m.group(1).lower()
        i = m.end()
        depth = 1
        j = i
        while j < len(text) and depth:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        body = text[i:j - 1]
        key, _, rest = body.partition(",")
        entries.append({"type": etype, "key": key.strip(),
                        "fields": parse_fields(rest), "order": len(entries)})
    return entries


def parse_fields(body):
    fields = {}
    i = 0
    n = len(body)
    while i < n:
        m = re.compile(r"\s*([\w-]+)\s*=\s*").match(body, i)
        if not m:
            break
        name = m.group(1).lower()
        i = m.end()
        if i >= n:
            break
        c = body[i]
        if c == "{":
            depth = 1
            j = i + 1
            while j < n and depth:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            val = body[i + 1:j - 1]
            i = j
        elif c == '"':
            # Closing quote counts only at brace depth 0 ({\"O} is content).
            j = i + 1
            depth = 0
            while j < n and not (body[j] == '"' and depth == 0):
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            val = body[i + 1:j]
            i = j + 1
        else:  # bare token (month macro, number)
            m2 = re.compile(r"[^,\s]+").match(body, i)
            val = m2.group(0)
            i = m2.end()
        fields[name] = re.sub(r"\s+", " ", val).strip()
        comma = body.find(",", i)
        if comma == -1:
            break
        i = comma + 1
    return fields


def latex_clean(s):
    for a, b in LATEX_CHARS:
        s = s.replace(a, b)
    s = re.sub(r"\\textsuperscript\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\(?:emph|textit)\{([^}]*)\}", r"<em>\1</em>", s)
    s = s.replace("---", "-").replace("--", "-")
    # Strip remaining grouping braces but keep content.
    s = re.sub(r"[{}]", "", s)
    return s.strip()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "[[LT]]").replace(">", "[[GT]]") \
            .replace("[[LT]]", "&lt;").replace("[[GT]]", "&gt;")


def link(url, text):
    return f'<a href="{url}">{text}</a>'


def format_author(raw):
    """One raw bib author -> (html, is_lab_member)."""
    member = "\\textbf{" in raw or "\\uline{" in raw
    s = re.sub(r"\\(?:textbf|uline)\{([^}]*)\}", r"\1", raw)
    s = latex_clean(s)
    if s == "others":
        return ("et al.", False)
    if "," in s:
        last, _, first = s.partition(",")
        name = f"{initials(first.strip())} {last.strip()}".strip()
    else:
        parts = s.split()
        if len(parts) == 1:
            name = s
        else:
            # Keep trailing suffixes (IV, Jr.) with the surname.
            surname = parts[-1]
            k = len(parts) - 1
            if surname in ("IV", "III", "Jr.", "Jr") and len(parts) > 2:
                surname = " ".join(parts[-2:])
                k = len(parts) - 2
            name = f"{initials(' '.join(parts[:k]))} {surname}"
    name = esc(name)
    return (f"<strong>{name}</strong>" if member else name, member)


def initials(given):
    out = []
    for tok in given.split():
        if "\u2020" in tok and len(tok) <= 2:
            out.append(tok)
        elif re.fullmatch(r"[A-Z]\.", tok) or tok in ("et", "al."):
            out.append(tok)
        else:
            dag = "\u2020" if tok.endswith("\u2020") else ""
            out.append(tok[0].upper() + "." + dag)
    return " ".join(out)


def author_list(field):
    raws = re.split(r"\s+and\s+", field.replace("\n", " "))
    names = [format_author(r)[0] for r in raws]
    any_member = any(format_author(r)[1] for r in raws)
    if not names:
        return "", any_member
    if names[-1] == "et al.":
        return ", ".join(names[:-1]) + ", et al.", any_member
    if len(names) == 1:
        return names[0], any_member
    if len(names) == 2:
        return f"{names[0]} and {names[1]}", any_member
    return ", ".join(names[:-1]) + f", and {names[-1]}", any_member


def clean_note(note):
    """Drop status words; convert links; keep substance."""
    s = note
    s = re.sub(r"\\href\{([^}]*)\}\{([^}]*)\}",
               lambda m: link(m.group(1), latex_clean(m.group(2))), s)
    s = re.sub(r"\\url\{([^}]*)\}", lambda m: link(m.group(1), "link"), s)
    s = latex_clean(s)
    s = re.sub(r"(?i)\b(under review|submitted[^,;.]*|rejected|accepted)\b", "", s)
    s = re.sub(r"(?i)poster presentation", "[poster]", s)
    s = s.strip(" .,;")
    return s


def render(e):
    f = e["fields"]
    authors, _ = author_list(f.get("author", ""))
    title = esc(latex_clean(f.get("title", "")))
    year = re.sub(r"[^0-9]", "", f.get("year", "")) or f.get("year", "")
    sep = " " if authors.endswith(".") else ". "
    bits = [f"{authors}{sep}{title}."] if authors else [f"{title}."]
    t = e["type"]
    if t == "article" and f.get("journal"):
        v = f"<em>{esc(latex_clean(f['journal']))}</em>"
        volnum = f.get("volume", "")
        if f.get("number"):
            volnum += f"({f['number']})"
        if f.get("pages"):
            volnum += f":{latex_clean(f['pages'])}" if volnum else latex_clean(f["pages"])
        seg = f"{v}, {volnum}, {year}." if volnum else f"{v}, {year}."
        bits.append(seg)
    elif t in ("inproceedings", "incollection") and f.get("booktitle"):
        v = f"In <em>{esc(latex_clean(f['booktitle']))}</em>"
        if f.get("pages"):
            v += f", pages {latex_clean(f['pages'])}"
        if t == "incollection" and f.get("publisher"):
            v += f". {esc(f['publisher'])}"
        bits.append(f"{v}, {year}.")
    else:
        bits.append(f"{year}.")
    doi = f.get("doi", "").strip()
    if doi:
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
        bits.append(f'doi: {link("https://doi.org/" + doi, doi)}.')
    note = clean_note(f.get("note", ""))
    if note:
        bits.append(note + ("." if not note.endswith((".", "]", ")")) else ""))
    if e["key"] in AWARDS:
        bits.append(f'<span class="award">{AWARDS[e["key"]]}</span>')
    return "<li>" + " ".join(b for b in bits if b) + "</li>"


def venue_line(e):
    f = e["fields"]
    year = re.sub(r"[^0-9]", "", f.get("year", "")) or f.get("year", "")
    if f.get("journal"):
        return f"<em>{esc(latex_clean(f['journal']))}</em>, {year}"
    if f.get("booktitle"):
        return f"<em>{esc(latex_clean(f['booktitle']))}</em>, {year}"
    return year


def render_card(e):
    f = e["fields"]
    authors, _ = author_list(f.get("author", ""))
    title = esc(latex_clean(f.get("title", "")))
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", f.get("doi", "").strip())
    url = f"https://doi.org/{doi}" if doi else ""
    if not url:  # fall back to a URL in the note (\url or \href)
        m = re.search(r"\\(?:url|href)\{(https?://[^}]+)\}", f.get("note", ""))
        url = m.group(1) if m else ""
    title_html = (f'<a class="title" href="{url}">{title}</a>'
                  if url else f'<span class="title">{title}</span>')
    badge = (f'<p><span class="award">{AWARDS[e["key"]]}</span></p>'
             if e["key"] in AWARDS else "")
    return (f'<li class="highlight-card">{title_html}'
            f'<p class="card-authors">{authors}</p>'
            f'<p class="venue">{venue_line(e)}</p>{badge}</li>')


def classify(e):
    f = e["fields"]
    note = f.get("note", "").lower()
    author = f.get("author", "")
    if ("\\textbf{" not in author and "\\uline{" not in author
            and e["key"] not in INCLUDE_KEYS):
        return None, None            # support citation or authorless talk
    if e["type"] == "misc":
        return None, None            # talks: personal page / news, not here
    if e["key"] in EXCLUDE_KEYS:
        return None, None
    if "rejected" in note:
        return None, None
    status = "review" if ("under review" in note or "submitted" in note) else "published"
    if e["key"] in SECTION_OVERRIDES:
        section = SECTION_OVERRIDES[e["key"]]
    elif "poster" in note or "abstract" in note:
        section = "abstracts"
    elif e["type"] == "incollection":
        section = "chapters"
    elif e["type"] == "article":
        section = "journal"
    else:
        section = "conference"
    return section, status


def year_key(e):
    y = re.sub(r"[^0-9]", "", e["fields"].get("year", "0"))
    return (-int(y or 0), e["order"])


def section_html(title, entries, split_status=True, collapsed=False):
    if not entries:
        return ""
    if collapsed:
        out = [f'<details class="pub-collapse"><summary><h2>{title} '
               f'({len(entries)})</h2></summary>']
    else:
        out = [f"<h2>{title}</h2>"]
    if split_status:
        pub = [e for e in entries if e["_status"] == "published"]
        rev = [e for e in entries if e["_status"] == "review"]
        if pub:
            if rev:
                out.append("<h3>Published</h3>")
            out.append("<ol class=\"pub-list\">")
            out += [render(e) for e in sorted(pub, key=year_key)]
            out.append("</ol>")
        if rev:
            out.append("<h3>Under Review</h3>")
            out.append("<ol class=\"pub-list\">")
            out += [render(e) for e in sorted(rev, key=year_key)]
            out.append("</ol>")
    else:
        out.append("<ol class=\"pub-list\">")
        out += [render(e) for e in sorted(entries, key=year_key)]
        out.append("</ol>")
    if collapsed:
        out.append("</details>")
    return "\n".join(out)


def main():
    entries = parse_bib(BIB.read_text(encoding="utf-8"))
    sections = {"chapters": [], "journal": [], "conference": [],
                "nonrefereed": [], "abstracts": []}
    skipped = []
    for e in entries:
        section, status = classify(e)
        if section is None:
            skipped.append(e["key"])
            continue
        e["_status"] = status
        sections[section].append(e)
    selected = sorted(
        (e for v in sections.values() for e in v
         if "selected" in e["fields"].get("keywords", "").lower()),
        key=year_key)
    highlights = ""
    if selected:
        highlights = ('<h2>Selected Publications</h2>\n<ul class="highlight-grid">\n'
                      + "\n".join(render_card(e) for e in selected) + "\n</ul>")
    body = "\n".join([
        "<h1>Publications</h1>",
        highlights,
        section_html("Book Chapters", sections["chapters"]),
        section_html("Journal Papers", sections["journal"]),
        section_html("Conference Papers", sections["conference"]),
        section_html("Non-refereed Papers", sections["nonrefereed"], False),
        section_html("Abstracts and Posters", sections["abstracts"], False,
                     collapsed=True),
    ])
    OUT.write_text(TEMPLATE.replace("[[BODY]]", body), encoding="utf-8")
    total = sum(len(v) for v in sections.values())
    print(f"Wrote {OUT} ({total} entries; skipped {len(skipped)}: "
          + ", ".join(skipped) + ")")


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Publications - Lybarger Language Lab</title>
<meta name="description" content="Publications of the Lybarger Language Lab at George Mason University: NLP and AI for health, clinical information extraction, and conversational agents.">
<meta property="og:site_name" content="Lybarger Language Lab">
<meta property="og:type" content="website">
<meta property="og:title" content="Publications - Lybarger Language Lab">
<meta property="og:description" content="Publications of the Lybarger Language Lab at George Mason University: NLP and AI for health, clinical information extraction, and conversational agents.">
<meta property="og:url" content="https://www.lybargerlanguagelab.org/publications.html">
<meta property="og:image" content="https://www.lybargerlanguagelab.org/assets/images/social-card.png">
<meta property="og:image:alt" content="Lybarger Language Lab: natural language processing and AI for health, George Mason University">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="https://www.lybargerlanguagelab.org/publications.html">
<link rel="icon" href="assets/images/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/css/styles.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html"><img class="brand-mark" src="assets/images/favicon.svg" alt="">Lybarger <span>Language Lab</span></a>
    <nav aria-label="Main">
      <ul>
        <li><a href="index.html">Home</a></li>
        <li><a href="people.html">People</a></li>
        <li><a href="projects.html">Projects</a></li>
        <li><a href="news.html">News</a></li>
        <li><a href="publications.html" aria-current="page">Publications</a></li>
        <li><a href="contact.html">Contact</a></li>
      </ul>
    </nav>
  </div>
</header>
<main id="main" class="wrap">
[[BODY]]
</main>
<footer class="site-footer">
  <div class="wrap">
    <p>Lybarger Language Lab &middot; Department of Information Sciences and Technology &middot; George Mason University</p>
  </div>
</footer>
</body>
</html>
"""

if __name__ == "__main__":
    sys.exit(main())
