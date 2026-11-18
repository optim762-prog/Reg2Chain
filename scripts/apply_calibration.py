"""
Step 1 - Apply the calibration decisions and build the FINAL gold standard.

  python apply_calibration.py units.csv A1.xlsx A2.xlsx calibration.xlsx OUT_DIR

Calibration decisions (sheet 'Rule'):
  Rule 1 = A2 : a PRODUCT mention of the form '<product> referred to in <reference>' is split into
                PRODUCT '<product>' + LEGAL_REF '<reference>' + relation REFERS_TO(product, reference).
                Relations that used the long span now use the product span.
                (Applied to PRODUCT entities only: the legal expert kept label items whole.)
  Rule 2 = A1 : the header of Annex units is not annotated.

Double-annotated units: final = A1 items not marked DROP + A2-only items marked KEEP
(sheet 'Disagreements'). Other units: A1 + automatic application of Rule 1.

Outputs: gold_dev.jsonl, gold_test.jsonl, calibration_report.txt
"""
import csv
import json
import os
import re
import sys
from collections import Counter

from openpyxl import load_workbook

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_and_build_gold import load_annotations, norm  # noqa: E402

SEP = " referred to in "


def apply_rule1(text, ents, rels):
    ents, rels = [dict(e) for e in ents], [dict(r) for r in rels]
    new_e, renamed = [], {}
    for e in ents:
        i = e["text"].find(SEP)
        if e["label"] == "PRODUCT" and i > 0:
            head, ref = e["text"][:i], e["text"][i + len(SEP):]
            hs, rs = e["start"], e["start"] + i + len(SEP)
            assert text[hs:hs + len(head)] == head and text[rs:rs + len(ref)] == ref
            new_e.append({"text": head, "label": "PRODUCT", "start": hs, "end": hs + len(head)})
            new_e.append({"text": ref, "label": "LEGAL_REF", "start": rs, "end": rs + len(ref)})
            renamed[norm(e["text"])] = head
            rels.append({"subject": head, "predicate": "REFERS_TO", "object": ref, "qualifier": ""})
        else:
            new_e.append(e)
    for r in rels:
        for k in ("subject", "object"):
            if norm(r[k]) in renamed:
                r[k] = renamed[norm(r[k])]
    return sorted(new_e, key=lambda e: e["start"]), rels


def parse_item(cell):
    """'text  [LABEL]' -> (text, LABEL) ; 'subj —REL→ obj  (qualifier: q)' -> tuple."""
    m = re.match(r"^(.*)  \[([A-Z_]+)\]$", cell)
    if m:
        return ("E", m.group(1), m.group(2))
    m = re.match(r"^(.*) —([A-Z_]+)→ (.*?)(?:  \(qualifier: (.*)\))?$", cell)
    return ("R", m.group(1), m.group(2), m.group(3), m.group(4) or "")


def main(units_csv, a1, a2, calib, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    rows = list(csv.DictReader(open(units_csv, encoding="utf-8")))
    units = {r["unit_id"]: r for r in rows}
    dbl = {u: units[u] for u in units if units[u]["double_annotation"] == "Y"}
    e1, r1, p1 = load_annotations(a1, units)
    e2, r2, p2 = load_annotations(a2, dbl)
    assert not p1 and not p2, (p1, p2)

    wb = load_workbook(calib, data_only=True)
    rules = {i: (row[3] or "").strip().upper()
             for i, row in enumerate(wb["Rule"].iter_rows(min_row=2, values_only=True), start=1) if row[0]}
    assert rules.get(1) == "A2" and rules.get(2) == "A1", rules
    decisions = []
    for row in wb["Disagreements"].iter_rows(min_row=2, values_only=True):
        if row[0]:
            src = "A1" if row[2] else "A2"
            decisions.append((row[0], src, parse_item(row[2] or row[3]), (row[4] or "").strip().upper()))
    undecided = [d for d in decisions if d[3] not in ("KEEP", "DROP")]
    assert not undecided, undecided

    final_e, final_r, report = {}, {}, []
    for u in units:
        if u in dbl:
            ents = [dict(e) for e in e1[u]]
            rels = [dict(r) for r in r1[u]]
            for uid, src, item, dec in decisions:
                if uid != u:
                    continue
                if src == "A1" and dec == "DROP":
                    if item[0] == "E":
                        ents = [e for e in ents if not (e["text"] == item[1] and e["label"] == item[2])]
                    else:
                        rels = [r for r in rels if not (r["subject"] == item[1] and r["predicate"] == item[2]
                                                         and r["object"] == item[3])]
                if src == "A2" and dec == "KEEP":
                    if item[0] == "E":
                        ents += [e for e in e2[u] if e["text"] == item[1] and e["label"] == item[2]][:1]
                    else:
                        rels.append({"subject": item[1], "predicate": item[2], "object": item[3],
                                     "qualifier": item[4]})
            # consistency check: Rule 1 applied to A1 must give the same product/reference entities
            auto_e, _ = apply_rule1(units[u]["text"], e1[u], r1[u])
            if {(e["text"], e["label"]) for e in auto_e if e["label"] in ("PRODUCT", "LEGAL_REF")} - \
               {(e["text"], e["label"]) for e in ents}:
                report.append(f"note {u}: rule-1 output differs from the joint decisions (decisions kept)")
            final_e[u], final_r[u] = sorted(ents, key=lambda e: e["start"]), rels
        else:
            final_e[u], final_r[u] = apply_rule1(units[u]["text"], e1[u], r1[u])

    # validate: no overlap, relations refer to entities
    for u in units:
        names = {norm(e["text"]) for e in final_e[u]}
        for a, b in zip(final_e[u], final_e[u][1:]):
            assert b["start"] >= a["end"], (u, a, b)
        for r in final_r[u]:
            assert norm(r["subject"]) in names and norm(r["object"]) in names, (u, r)

    for split in ("dev", "test"):
        with open(os.path.join(out_dir, f"gold_{split}.jsonl"), "w", encoding="utf-8") as f:
            for r in rows:
                if r["split"] == split:
                    f.write(json.dumps({"unit_id": r["unit_id"], "sentence": r["text"],
                                        "entities": final_e[r["unit_id"]], "relations": final_r[r["unit_id"]]},
                                       ensure_ascii=False) + "\n")
    lines = [f"Rules: {rules}", f"Decisions applied: {len(decisions)}"] + report
    for split in ("dev", "test"):
        ids = [r["unit_id"] for r in rows if r["split"] == split]
        E = Counter(e["label"] for u in ids for e in final_e[u])
        R = Counter(r["predicate"] for u in ids for r in final_r[u])
        lines.append(f"{split}: {len(ids)} units, {sum(E.values())} entities {dict(E.most_common())}, "
                     f"{sum(R.values())} relations {dict(R.most_common())}")
    open(os.path.join(out_dir, "calibration_report.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:6])
