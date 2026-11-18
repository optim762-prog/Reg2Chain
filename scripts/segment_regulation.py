"""
Step 1 - Segment Regulation (EU) 2022/2104 into provision units for annotation.

Scope: enacting terms (Articles 1-14) + Annex I, Table A (quality characteristics,
linearised one unit per category). Recitals are excluded (not normative).

Unit granularity: one unit per numbered paragraph. A paragraph longer than
MAX_LEN characters with lettered points (a), (b)... is split into its lead-in and
one unit per point (no text is duplicated across units).

Output: units.csv  (unit_id, article, title, split, double_annotation, text)
Usage:  python segment_regulation.py regulation_text.txt units.csv
"""
import csv
import random
import re
import sys

MAX_LEN = 600
DEV_RATIO = 0.25          # dev units: used to design rules / prompts only
DOUBLE_RATIO = 0.30       # share of TEST units annotated by both annotators
SEED = 2104

HEADER_PATTERNS = [
    r"^EN$", r"^Official Journal of the European Union\s*$", r"^L 284/\d+\s*$",
    r"^\d{1,2}\.\d{1,2}\.\d{4}\s*$",
]


def clean_lines(text):
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if any(re.match(p, s) for p in HEADER_PATTERNS):
            continue
        lines.append(s)
    return lines


def join(lines):
    t = " ".join(l for l in lines if l)
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\(\s+", "(", t)
    return t.strip()


def enacting_terms(lines):
    start = lines.index("HAS ADOPTED THIS REGULATION:") + 1
    end = next(i for i, l in enumerate(lines) if l.startswith("This Regulation shall be binding in its entirety"))
    body = lines[start:end]
    # drop footnotes "(12) Council Regulation ..." at the end of Article 14
    body = [l for l in body if not re.match(r"^\(\d{2}\) Council Regulation", l)
            and not re.match(r"^22\.7\.1989|^\(OJ L", l)]
    articles, cur = [], None
    i = 0
    while i < len(body):
        m = re.match(r"^Article (\d+)$", body[i])
        if m:
            cur = {"num": int(m.group(1)), "title": body[i + 1], "lines": []}
            articles.append(cur)
            i += 2
            continue
        if cur is not None:
            cur["lines"].append(body[i])
        i += 1
    return articles


def split_paragraphs(lines):
    paras, cur = [], {"num": None, "lines": []}
    for l in lines:
        m = re.match(r"^(\d+)\.$", l)
        if m:
            if cur["lines"]:
                paras.append(cur)
            cur = {"num": m.group(1), "lines": []}
        else:
            cur["lines"].append(l)
    if cur["lines"]:
        paras.append(cur)
    return paras


def split_points(text):
    """Split 'lead-in (a) ... (b) ...' at top-level lettered points."""
    parts = re.split(r"(?<=[:;])\s*(?=\([a-h]\)\s)|(?<=[:;] or)\s*(?=\([a-h]\)\s)", text)
    if len(parts) == 1:
        parts = re.split(r"\s(?=\([a-h]\)\s)", text)
    out = []
    for p in parts:
        m = re.match(r"^\(([a-h])\)\s*(.*)$", p.strip())
        out.append((m.group(1), m.group(2)) if m else (None, p.strip()))
    return out


def article_units(articles):
    units = []
    for a in articles:
        for p in split_paragraphs(a["lines"]):
            text = join(p["lines"])
            base = f"ART{a['num']}" + (f".{p['num']}" if p["num"] else "")
            if len(text) > MAX_LEN and re.search(r"\([a-h]\)\s", text):
                for letter, t in split_points(text):
                    if t:
                        units.append((base + (f".{letter}" if letter else ".lead"), a, t))
            else:
                units.append((base, a, text))
    return units


TABLE_A_PARAMS = [
    "Acidity (%)", "Peroxide value (mEq O2/kg)", "K232", "K268 or K270", "ΔK",
    "Median of defect (Md)", "Fruity median (Mf)", "Fatty acid ethyl esters (mg/kg)",
]


def annex_table_a(lines):
    """Linearise Annex I Table A: one unit per category."""
    s = lines.index("A. Quality characteristics")
    e = next(i for i in range(s, len(lines)) if lines[i].startswith("(1) The median of the defects"))
    rows = lines[s:e]
    units, i = [], 0
    while i < len(rows):
        m = re.match(r"^(\d)\. (.+)$", rows[i])
        if m:
            name = m.group(2)
            j = i + 1
            if not rows[j].startswith(("≤", ">", "—", "Md", "Mf")):
                name += " " + rows[j]
                j += 1
            vals = []
            while j < len(rows) and not re.match(r"^\d\. ", rows[j]):
                vals.append(rows[j])
                j += 1
            vals = [re.sub(r"^(Md|Mf)\s+", "", re.sub(r"\s*\(\d\)$", "", v)) for v in vals]
            pairs = [f"{p} {v}" for p, v in zip(TABLE_A_PARAMS, vals) if v != "—"]
            text = (f"Annex I, Table A, quality characteristics of {name.lower()}: "
                    + ("; ".join(pairs) if pairs else "no limits set") + ".")
            units.append((f"ANX1.A.{m.group(1)}", {"num": "Annex I", "title": "Quality characteristics"}, text))
            i = j
        else:
            i += 1
    return units


def main(src, dst):
    lines = clean_lines(open(src, encoding="utf-8").read())
    units = article_units(enacting_terms(lines)) + annex_table_a(lines)

    rnd = random.Random(SEED)
    ids = [u[0] for u in units]
    dev = set(rnd.sample(ids, round(DEV_RATIO * len(ids))))
    test = [i for i in ids if i not in dev]
    double = set(rnd.sample(test, round(DOUBLE_RATIO * len(test))))

    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["unit_id", "article", "title", "split", "double_annotation", "text"])
        for uid, a, text in units:
            w.writerow([uid, a["num"], a["title"], "dev" if uid in dev else "test",
                        "Y" if uid in double else "N", text])
    n_dev = len(dev)
    print(f"{len(units)} units -> {dst}  (dev {n_dev}, test {len(units) - n_dev}, double-annotated {len(double)})")


if __name__ == "__main__":
    main(*sys.argv[1:3])
