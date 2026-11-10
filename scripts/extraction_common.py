"""Shared helpers for the Entity Extraction Agent and its evaluation (Section 3)."""
import json
import re
import unicodedata

ENTITY_TYPES = ["PRODUCT", "PARAMETER", "VALUE", "LABEL_ITEM", "ACTOR", "LEGAL_REF", "PROCESS"]
RELATION_TYPES = ["OBLIGATION", "PERMISSION", "PROHIBITION", "LIMIT", "CONDITION", "REFERS_TO"]


def norm(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = re.sub(r"\s+", " ", s).strip(" .;:,")
    return re.sub(r"^(the|a|an) ", "", s)


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def save_jsonl(rows, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def select_non_overlapping(cands):
    """Greedy: higher priority first, then longer span, then earlier start."""
    chosen = []
    for c in sorted(cands, key=lambda e: (-e.get("prio", 0), -(e["end"] - e["start"]), e["start"])):
        if all(c["end"] <= o["start"] or c["start"] >= o["end"] for o in chosen):
            chosen.append(c)
    return sorted(({k: v for k, v in c.items() if k != "prio"} for c in chosen), key=lambda e: e["start"])


def locate(text, span, taken=()):
    """Character offsets of `span` in `text` (exact, then case-insensitive), avoiding taken spans."""
    for hay, needle in ((text, span), (text.lower(), span.lower())):
        start = hay.find(needle)
        while start >= 0:
            end = start + len(needle)
            if all(end <= a or start >= b for a, b in taken):
                return start, end
            start = hay.find(needle, start + 1)
    return None


def dedup_relations(rels):
    seen, out = set(), []
    for r in rels:
        key = (norm(r["subject"]), r["predicate"], norm(r["object"]), norm(r.get("qualifier", "")))
        if key not in seen:
            seen.add(key)
            out.append({"subject": r["subject"], "predicate": r["predicate"], "object": r["object"],
                        "qualifier": r.get("qualifier", "")})
    return out
