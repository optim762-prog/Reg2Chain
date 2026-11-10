"""
Section 3 - Rule-based component of the Entity Extraction Agent.

Entities: gazetteers built automatically from the DEVELOPMENT annotations only, complemented
by domain vocabulary defined outside the test set (the eight legal oil categories and the
Annex I analytical parameters), plus patterns for legal references, numeric values and quoted
label wordings. Non-overlapping spans are selected by priority, then length.

Relations (also usable on gold entities with --gold-entities):
  REFERS_TO  : entity followed by 'referred to in' / 'within the meaning of' /
               'in accordance with' / 'laid down in' + LEGAL_REF
  LIMIT      : Annex units, PRODUCT + (PARAMETER, VALUE) pairs
  OBLIGATION / PERMISSION / PROHIBITION : modal verb of the clause; subjects = PRODUCT/ACTOR
               entities before the modal, object = first LABEL_ITEM/PROCESS/PRODUCT after it
  CONDITION  : 'only if' / 'only where' / 'below' ... VALUE attached to the LABEL_ITEM

  python extract_rules.py gold_test.jsonl pred_rules.jsonl --dev=gold_dev.jsonl [--gold-entities]
"""
import re
import sys

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_common import dedup_relations, load_jsonl, save_jsonl, select_non_overlapping

# Domain vocabulary defined OUTSIDE the test set:
#  - the eight legal categories of olive oils (Regulation (EU) No 1308/2013, Annex VII, Part VIII)
#  - the analytical parameters of the quality characteristics (column headings of Annex I, Table A)
DOMAIN = {
    "PRODUCT": ["extra virgin olive oil", "virgin olive oil", "lampante olive oil", "refined olive oil",
                "olive oil composed of refined olive oils and virgin olive oils", "crude olive-pomace oil",
                "refined olive-pomace oil", "olive-pomace oil"],
    "PARAMETER": ["Acidity (%)", "Peroxide value (mEq O2/kg)", "K232", "K268 or K270", "ΔK",
                  "Median of defect (Md)", "Fruity median (Mf)", "Fatty acid ethyl esters (mg/kg)"],
}
GAZ_TYPES = ["PARAMETER", "LABEL_ITEM", "PRODUCT", "ACTOR", "PROCESS"]


def build_gazetteers(dev_path):
    """Gazetteers = domain vocabulary + entity texts annotated in the DEVELOPMENT units only."""
    gaz = {t: set(DOMAIN.get(t, [])) for t in GAZ_TYPES}
    if dev_path:
        for g in load_jsonl(dev_path):
            for e in g["entities"]:
                if e["label"] in gaz and not QUOTE.fullmatch(e["text"]):
                    gaz[e["label"]].add(e["text"])
    return {t: sorted(v, key=len, reverse=True) for t, v in gaz.items()}


PRIO = {"LABEL_ITEM_Q": 9, "LEGAL_REF": 8, "VALUE": 7, "PARAMETER": 6, "LABEL_ITEM": 5,
        "PRODUCT": 4, "ACTOR": 3, "PROCESS": 2}

QUOTE = re.compile(r"‘[^’]{2,}’")
VALUE_RES = [
    re.compile(r"(?:≤|≥|<|>|=)\s?\d+(?:,\d+)?"),
    re.compile(r"\b(?:more than|less than|at least|at most|below|above|exceeding|not exceeding)\s\d+(?:,\d+)?\s?(?:%|° ?C|litres|kg|mg/kg)", re.I),
    re.compile(r"\b\d+(?:,\d+)?\s?(?:%|° ?C|litres)"),
]
REF_START = re.compile(r"\b(?:Articles?|Annex|Part|points?|paragraphs?|Directive|"
                       r"(?:Commission |Council )?(?:Delegated |Implementing )?Regulations?)\b")
REF_TOKEN = re.compile(r"\s*(?:\(\w{1,4}\)|\d+(?:/\d+)*(?:\(\d+\))?|[IVXL]+\b|[a-h]\b|and\b|or\b|to\b|of\b|in\b|,|"
                       r"Annex\b|Part\b|points?\b|paragraphs?\b|Tables?\b|[AB]\b|Articles?\b|No\b|"
                       r"(?:Commission |Council )?(?:Delegated |Implementing )?Regulations?\b|"
                       r"\((?:EU|EEC|EC)\)|this Regulation\b|this Article\b|that paragraph\b|"
                       r"\d{2,}/\d+/EEC\b|EEC\b)")
TRAIL = re.compile(r"(?:\s*(?:,|and|or|to|of|in))+$")


def legal_refs(text):
    out, pos = [], 0
    for m in REF_START.finditer(text):
        if m.start() < pos:
            continue
        end = m.end()
        while True:
            t = REF_TOKEN.match(text, end)
            if not t or t.end() == end:
                break
            end = t.end()
        span = TRAIL.sub("", text[m.start():end])
        if re.search(r"\d|[IVX]{1,4}\b|this Regulation|that paragraph", span) and len(span) > 4:
            out.append({"text": span, "label": "LEGAL_REF", "start": m.start(), "end": m.start() + len(span),
                        "prio": PRIO["LEGAL_REF"]})
            pos = m.start() + len(span)
    return out


def gazetteer(text, terms, label):
    out = []
    for t in terms:
        for m in re.finditer(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", text, re.I):
            out.append({"text": text[m.start():m.end()], "label": label, "start": m.start(), "end": m.end(),
                        "prio": PRIO[label]})
    return out


def extract_entities(text, gaz):
    c = [{"text": m.group(0), "label": "LABEL_ITEM", "start": m.start(), "end": m.end(),
          "prio": PRIO["LABEL_ITEM_Q"]} for m in QUOTE.finditer(text)]
    c += legal_refs(text)
    for rx in VALUE_RES:
        c += [{"text": m.group(0), "label": "VALUE", "start": m.start(), "end": m.end(),
               "prio": PRIO["VALUE"]} for m in rx.finditer(text)]
    if text.startswith("Annex I, Table A"):            # calibration rule: header not annotated
        hdr = text.index(":")
        c = [e for e in c if e["start"] > hdr or e["label"] == "PRODUCT"]
    for label in GAZ_TYPES:
        c += gazetteer(text, gaz[label], label)
    if text.startswith("Annex I, Table A"):
        hdr = text.index(":")
        c = [e for e in c if not (e["start"] < hdr and e["label"] != "PRODUCT")]
    return select_non_overlapping(c)


# ------------------------------------------------------------------ relations
LINKERS = re.compile(r"^\s*,?\s*(?:as\s+)?(?:referred to in|within the meaning of|in accordance with|laid down in|"
                     r"as defined in|determined in accordance with)\s*$", re.I)
NEG = re.compile(r"\b(?:shall not|may not|must not|no\b[^.;:]*\bshall)", re.I)
MODAL = re.compile(r"\b(shall|must|may)\b", re.I)


def extract_relations(text, ents):
    ents = sorted(ents, key=lambda e: e["start"])
    rels = []
    # REFERS_TO
    for i, e in enumerate(ents):
        if e["label"] == "LEGAL_REF":
            continue
        for f in ents[i + 1:i + 3]:
            if f["label"] == "LEGAL_REF" and LINKERS.match(text[e["end"]:f["start"]]):
                rels.append({"subject": e["text"], "predicate": "REFERS_TO", "object": f["text"]})
                break
    # LIMIT (Annex Table A units)
    if text.startswith("Annex I, Table A"):
        prod = next((e for e in ents if e["label"] == "PRODUCT"), None)
        for a, b in zip(ents, ents[1:]):
            if prod and a["label"] == "PARAMETER" and b["label"] == "VALUE":
                rels.append({"subject": prod["text"], "predicate": "LIMIT", "object": b["text"],
                             "qualifier": a["text"]})
        return dedup_relations(rels)
    # deontic relations, clause by clause
    for clause in re.finditer(r"[^.;:]+", text):
        cs, ce = clause.start(), clause.end()
        m = MODAL.search(text, cs, ce)
        if not m:
            continue
        pred = "PROHIBITION" if NEG.search(text[cs:ce]) else (
            "PERMISSION" if m.group(1).lower() == "may" else "OBLIGATION")
        inside = [e for e in ents if cs <= e["start"] < ce]
        subjects = [e for e in inside if e["start"] < m.start() and e["label"] in ("PRODUCT", "ACTOR")]
        after = [e for e in inside if e["start"] > m.start()]
        obj = next((e for e in after if e["label"] in ("LABEL_ITEM", "PROCESS")), None) or \
            next((e for e in after if e["label"] == "PRODUCT"), None)
        if obj is None and subjects and pred != "PROHIBITION":
            # 'X may bear Y' where Y precedes the modal is rare; nothing to link
            continue
        if obj is None:
            continue
        for s in subjects:
            if s is not obj:
                rels.append({"subject": s["text"], "predicate": pred, "object": obj["text"]})
        # CONDITION: value or process after 'only if/where', 'below', 'more than' in the same clause
        if re.search(r"\bonly (?:if|where|when)\b|\bbelow\b|\bmore than\b", text[cs:ce], re.I):
            target = obj if obj["label"] == "LABEL_ITEM" else None
            for v in after:
                if target and v["label"] == "VALUE":
                    q = next((p["text"] for p in inside if p["label"] == "PARAMETER"), "")
                    rels.append({"subject": target["text"], "predicate": "CONDITION", "object": v["text"],
                                 "qualifier": q})
    return dedup_relations(rels)


def main(gold_path, out_path, *flags):
    use_gold = "--gold-entities" in flags
    dev = next((f.split("=", 1)[1] for f in flags if f.startswith("--dev=")), None)
    gaz = build_gazetteers(dev)
    preds = []
    for g in load_jsonl(gold_path):
        ents = g["entities"] if use_gold else extract_entities(g["sentence"], gaz)
        preds.append({"unit_id": g["unit_id"], "entities": ents,
                      "relations": extract_relations(g["sentence"], ents)})
    save_jsonl(preds, out_path)
    print(f"rules{' (gold entities)' if use_gold else ''}: {sum(len(p['entities']) for p in preds)} entities, "
          f"{sum(len(p['relations']) for p in preds)} relations -> {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:])
