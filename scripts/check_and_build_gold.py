"""
Step 1 - Check annotations, build the gold standard and compute inter-annotator agreement.

  python check_and_build_gold.py units.csv Reg2Chain_annotation_A1.xlsx [Reg2Chain_annotation_A2.xlsx] OUT_DIR

Checks (printed as a list of problems to fix in the workbook):
  - unit_id exists; entity text found in the unit (exact copy) at the given occurrence
  - entity type / relation type valid; entities do not overlap
  - relation subject/object (and qualifier) are annotated entities of the same unit
  - every unit has at least one row (or type NONE)

Outputs:
  gold_dev.jsonl, gold_test.jsonl : {"unit_id","sentence","entities":[{text,label,start,end}],
                                     "relations":[{subject,predicate,object,qualifier}]}
  agreement.txt                   : A1 vs A2 on the double-annotated units
     - entity span agreement (strict and untyped F1, A1 as reference)
     - Cohen's kappa at token level (entity type per token, 'O' outside entities)
     - relation agreement (strict F1)
"""
import csv
import json
import os
import re
import sys
from collections import Counter

from openpyxl import load_workbook

ENTITY_TYPES = {"PRODUCT", "PARAMETER", "VALUE", "LABEL_ITEM", "ACTOR", "LEGAL_REF", "PROCESS"}
RELATION_TYPES = {"OBLIGATION", "PERMISSION", "PROHIBITION", "LIMIT", "CONDITION", "REFERS_TO"}


def cell(v):
    return "" if v is None else str(v).strip()


def norm(s):
    return re.sub(r"\s+", " ", s.strip()).lower()


def read_sheet(wb, name):
    ws = wb[name]
    rows = list(ws.iter_rows(values_only=True))
    header = [cell(h) for h in rows[0]]
    return [dict(zip(header, [cell(v) for v in r])) for r in rows[1:] if any(v is not None for v in r)], header


def find_occurrence(text, span, occ, placed):
    """occ-th occurrence of span that does not overlap an already placed (longer) entity."""
    found, start = 0, -1
    while True:
        start = text.find(span, start + 1)
        if start < 0:
            return None
        end = start + len(span)
        # skip occurrences inside a longer, different entity; same-text entities still count
        if all(end <= e["start"] or start >= e["end"] or e["text"] == span for e in placed):
            found += 1
            if found == max(1, occ):
                return start


def load_annotations(path, units):
    wb = load_workbook(path, data_only=True)
    ents_rows, eh = read_sheet(wb, "Entities")
    rels_rows, rh = read_sheet(wb, "Relations")
    e_text, e_type, e_occ = eh[1], eh[2], eh[3]
    r_subj, r_rel, r_obj, r_q = rh[1], rh[2], rh[3], rh[4]
    problems = []
    ents = {u: [] for u in units}
    rels = {u: [] for u in units}
    seen_units = set()

    # longest spans first, so a short entity is never placed inside a longer one
    order = sorted(enumerate(ents_rows, start=2), key=lambda x: -len(x[1][e_text]))
    for i, r in order:
        uid, span, typ = r["unit_id"], r[e_text], r[e_type].upper()
        if uid not in units:
            problems.append(f"Entities row {i}: unknown unit_id '{uid}'")
            continue
        seen_units.add(uid)
        if typ == "NONE":
            continue
        if typ not in ENTITY_TYPES:
            problems.append(f"Entities row {i} ({uid}): invalid type '{typ}'")
            continue
        try:
            occ = int(float(r[e_occ])) if r[e_occ] else 1
        except ValueError:
            occ = 1
        start = find_occurrence(units[uid]["text"], span, occ, ents[uid])
        if start is None:
            problems.append(f"Entities row {i} ({uid}): text not found exactly in unit: '{span}'")
            continue
        ents[uid].append({"text": span, "label": typ, "start": start, "end": start + len(span)})

    for uid, lst in ents.items():
        lst.sort(key=lambda e: e["start"])
        for a, b in zip(lst, lst[1:]):
            if b["start"] < a["end"]:
                problems.append(f"{uid}: overlapping entities '{a['text']}' and '{b['text']}'")

    for i, r in enumerate(rels_rows, start=2):
        uid, rel = r["unit_id"], r[r_rel].upper()
        if uid not in units:
            problems.append(f"Relations row {i}: unknown unit_id '{uid}'")
            continue
        seen_units.add(uid)
        if rel not in RELATION_TYPES:
            problems.append(f"Relations row {i} ({uid}): invalid relation '{rel}'")
            continue
        names = {norm(e["text"]) for e in ents[uid]}
        for role, val in (("subject", r[r_subj]), ("object", r[r_obj]), ("qualifier", r[r_q])):
            if role == "qualifier" and not val:
                continue
            if norm(val) not in names:
                problems.append(f"Relations row {i} ({uid}): {role} '{val}' is not an annotated entity of this unit")
        rels[uid].append({"subject": r[r_subj], "predicate": rel, "object": r[r_obj], "qualifier": r[r_q]})

    for uid in units:
        if uid not in seen_units:
            problems.append(f"{uid}: no annotation row (add a row with type NONE if the unit has no entity)")
    return ents, rels, problems


# ---------------------------------------------------------------- agreement
def prf(a, b):
    """F1 of set/multiset b against reference a."""
    ca, cb = Counter(a), Counter(b)
    tp = sum((ca & cb).values())
    p = tp / max(1, sum(cb.values()))
    r = tp / max(1, sum(ca.values()))
    return tp, sum(ca.values()), sum(cb.values()), (2 * p * r / (p + r) if p + r else 0.0)


def token_labels(text, ents):
    labels = []
    for m in re.finditer(r"\w+|[^\w\s]", text):
        lab = "O"
        for e in ents:
            if e["start"] <= m.start() < e["end"]:
                lab = e["label"]
                break
        labels.append(lab)
    return labels


def cohen_kappa(x, y):
    n = len(x)
    po = sum(a == b for a, b in zip(x, y)) / n
    cx, cy = Counter(x), Counter(y)
    pe = sum(cx[k] * cy[k] for k in set(cx) | set(cy)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def agreement(units, e1, r1, e2, r2, ids):
    lines = [f"Double-annotated units: {len(ids)}"]
    s1 = [(u, e["start"], e["end"], e["label"]) for u in ids for e in e1[u]]
    s2 = [(u, e["start"], e["end"], e["label"]) for u in ids for e in e2[u]]
    tp, n1, n2, f = prf(s1, s2)
    lines.append(f"Entities strict (span+type): A1={n1} A2={n2} agreed={tp} F1={f:.3f}")
    tp, n1, n2, f = prf([x[:3] for x in s1], [x[:3] for x in s2])
    lines.append(f"Entities untyped (span only): agreed={tp} F1={f:.3f}")
    t1, t2 = [], []
    for u in ids:
        t1 += token_labels(units[u]["text"], e1[u])
        t2 += token_labels(units[u]["text"], e2[u])
    lines.append(f"Cohen's kappa (token level, {len(t1)} tokens): {cohen_kappa(t1, t2):.3f}")
    key = lambda r: (norm(r["subject"]), r["predicate"], norm(r["object"]), norm(r["qualifier"]))
    q1 = [(u,) + key(r) for u in ids for r in r1[u]]
    q2 = [(u,) + key(r) for u in ids for r in r2[u]]
    tp, n1, n2, f = prf(q1, q2)
    lines.append(f"Relations strict: A1={n1} A2={n2} agreed={tp} F1={f:.3f}")
    return "\n".join(lines)


def main(units_csv, a1_path, *rest):
    a2_path = rest[0] if len(rest) == 2 else None
    out_dir = rest[-1]
    os.makedirs(out_dir, exist_ok=True)
    rows = list(csv.DictReader(open(units_csv, encoding="utf-8")))
    units = {r["unit_id"]: r for r in rows}

    e1, r1, p1 = load_annotations(a1_path, units)
    print(f"A1: {sum(map(len, e1.values()))} entities, {sum(map(len, r1.values()))} relations, {len(p1)} problems")
    for p in p1:
        print("  A1 -", p)

    for split in ("dev", "test"):
        with open(os.path.join(out_dir, f"gold_{split}.jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                if r["split"] == split:
                    f.write(json.dumps({"unit_id": r["unit_id"], "sentence": r["text"],
                                        "entities": e1[r["unit_id"]], "relations": r1[r["unit_id"]]},
                                       ensure_ascii=False) + "\n")
    labels = Counter(e["label"] for u in e1 for e in e1[u] if units[u]["split"] == "test")
    rels = Counter(r["predicate"] for u in r1 for r in r1[u] if units[u]["split"] == "test")
    print("Test entities per type:", dict(labels.most_common()))
    print("Test relations per type:", dict(rels.most_common()))

    if a2_path:
        a2_units = {u: units[u] for u in units if units[u]["double_annotation"] == "Y"}
        e2, r2, p2 = load_annotations(a2_path, a2_units)
        print(f"A2: {sum(map(len, e2.values()))} entities, {sum(map(len, r2.values()))} relations, {len(p2)} problems")
        for p in p2:
            print("  A2 -", p)
        rep = agreement(units, e1, r1, e2, r2, sorted(a2_units))
        open(os.path.join(out_dir, "agreement.txt"), "w").write(rep + "\n")
        print(rep)


if __name__ == "__main__":
    main(*sys.argv[1:])
