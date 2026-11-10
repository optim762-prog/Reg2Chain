"""
Section 5 - Evaluation 2: quality of the knowledge graph (replaces the former Table 2).

Structure, semantic quality against the gold standard, and coverage of the requirements:

  metrics       structural metrics of each graph (nodes, edges, average degree, isolated nodes,
                connected components, traceable rules) AND semantic quality against the gold
                standard, on the TEST units only: precision / recall of the rules (relaxed match
                with the gold normative relations of the same provision) and of the concepts.
  coverage-sheet  coverage workbook: for each requirement of the validated checklist, candidate
                rules of the graph (same provision; same product + parameter + value for limits);
                the expert marks COVERED / PARTIAL / NOT_COVERED.
  coverage-score  coverage of the regulation's requirements (overall and by on-chain class).

  python kg_evaluation.py metrics gold_test.jsonl OUT_DIR name=kg.json [name=kg.json ...]
  python kg_evaluation.py coverage-sheet checklist.xlsx kg.json coverage.xlsx
  python kg_evaluation.py coverage-score coverage_reviewed.xlsx OUT_DIR
"""
import csv
import json
import os
import re
import sys
from collections import Counter

import networkx as nx
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evaluate_extraction import text_overlap  # noqa: E402
from extraction_common import load_jsonl, norm  # noqa: E402

NORMATIVE = {"OBLIGATION", "PERMISSION", "PROHIBITION", "LIMIT", "CONDITION"}
TOP2TYPE = {"Product": "PRODUCT", "QualityParameter": "PARAMETER", "LabelItem": "LABEL_ITEM", "Actor": "ACTOR",
            "Process": "PROCESS", "LegalReference": "LEGAL_REF"}


# ------------------------------------------------------------------ metrics
def structure(graph):
    g = nx.Graph()
    g.add_nodes_from(n["id"] for n in graph["nodes"])
    g.add_edges_from((e["source"], e["target"]) for e in graph["edges"])
    comps = list(nx.connected_components(g))
    rules = [n for n in graph["nodes"] if n["kind"] == "Rule"]
    traced = {e["source"] for e in graph["edges"] if e["type"] == "DERIVED_FROM"}
    return {"nodes": g.number_of_nodes(), "edges": g.number_of_edges(),
            "avg_degree": round(2 * g.number_of_edges() / max(1, g.number_of_nodes()), 2),
            "isolated_nodes": sum(1 for _, d in g.degree() if d == 0),
            "components": len(comps),
            "largest_component_share": round(max((len(c) for c in comps), default=0) / max(1, g.number_of_nodes()), 3),
            "concepts": sum(n["kind"] == "Concept" for n in graph["nodes"]),
            "rules": len(rules),
            "traceable_rules_share": round(sum(r["id"] in traced for r in rules) / max(1, len(rules)), 3)}


def rule_views(graph):
    label = {n["id"]: n.get("label", n["id"]) for n in graph["nodes"]}
    cond = {n["id"]: n.get("expression", "") for n in graph["nodes"] if n["kind"] == "Condition"}
    out_e = {}
    for e in graph["edges"]:
        out_e.setdefault(e["source"], {}).setdefault(e["type"], []).append(e["target"])
    rules = []
    for n in graph["nodes"]:
        if n["kind"] != "Rule":
            continue
        ed = out_e.get(n["id"], {})
        prov = ed.get("DERIVED_FROM", [""])[0]
        rules.append({"id": n["id"], "type": n["type"], "unit_id": prov[2:] if prov.startswith("P_") else "",
                      "subject": " | ".join(label.get(x, x) for x in (ed.get("APPLIES_TO") or [""])),
                      "subjects": [label.get(x, x) for x in (ed.get("APPLIES_TO") or [])],
                      "object": label.get((ed.get("CONCERNS") or [""])[0], "") or n.get("value", ""),
                      "value": n.get("value", ""), "parameter": n.get("parameter", ""),
                      "condition": n.get("condition", "") or cond.get((ed.get("CONCERNS") or [""])[0], "")})
    return rules


def compact(s):
    """'PeroxideValueMEqO2Kg' and 'Peroxide value (mEq O2/kg)' -> 'peroxidevaluemeqo2kg' (identifier vs text form)."""
    return re.sub(r"[^0-9a-zδ]", "", (s or "").lower())


def same_param(a, b):
    ca, cb = compact(a), compact(b)
    return text_overlap(a, b) or (bool(ca) and bool(cb) and (ca == cb or ca in cb or cb in ca))


def same_value(a, b):
    """'≤ 0,80' == '≤ 0.8'; '= 0,0' == '= 0,00' (operator and number must both agree)."""
    pa, pb = (re.match(r"\s*([<>≤≥=]*)\s*([0-9]+(?:[.,][0-9]+)?)", x or "") for x in (a, b))
    if pa and pb:
        return pa.group(1) == pb.group(1) and float(pa.group(2).replace(",", ".")) == float(pb.group(2).replace(",", "."))
    return norm(a) == norm(b)


def same_rule(g, r):
    if g["predicate"] != r["type"] or not any(text_overlap(g["subject"], s) for s in (r.get("subjects") or [r["subject"]])):
        return False
    if g["predicate"] == "LIMIT":
        return same_value(g["object"], r["value"]) and same_param(g.get("qualifier", ""), r["parameter"])
    # a CONDITION may point to a Condition node: compare with its expression as well
    return any(text_overlap(g["object"], x) for x in (r["object"], r.get("condition", "")) if x)


def semantic(graph, gold):
    test_units = {g["unit_id"] for g in gold}
    gold_rules = [dict(r, unit_id=g["unit_id"]) for g in gold for r in g["relations"] if r["predicate"] in NORMATIVE]
    rules = [r for r in rule_views(graph) if r["unit_id"] in test_units]
    used, tp = set(), 0
    for g in gold_rules:
        for r in rules:
            if r["id"] not in used and r["unit_id"] == g["unit_id"] and same_rule(g, r):
                used.add(r["id"])
                tp += 1
                break
    p = tp / len(rules) if rules else 0.0
    rc = tp / len(gold_rules) if gold_rules else 0.0
    gold_concepts = {(e["label"], norm(e["text"])) for g in gold for e in g["entities"] if e["label"] != "VALUE"}
    concepts = [n for n in graph["nodes"] if n["kind"] in ("Concept", "LegalReference") and n["id"] not in TOP2TYPE]
    ok = sum(1 for n in concepts if any(t == TOP2TYPE.get(n.get("top_class")) and text_overlap(x, n["label"])
                                         for t, x in gold_concepts))
    return {"rules_test": len(rules), "gold_rules_test": len(gold_rules), "rule_TP": tp,
            "rule_precision": round(p, 3), "rule_recall": round(rc, 3),
            "rule_F1": round(2 * p * rc / (p + rc), 3) if p + rc else 0.0,
            "concept_precision": round(ok / max(1, len(concepts)), 3)}


def cmd_metrics(gold_path, out_dir, *specs):
    os.makedirs(out_dir, exist_ok=True)
    gold = load_jsonl(gold_path)
    rows = []
    for spec in specs:
        name, path = spec.split("=", 1)
        graph = json.load(open(path, encoding="utf-8"))
        rows.append({"graph": name, **structure(graph), **semantic(graph, gold)})
    keys = list(rows[0])
    with open(os.path.join(out_dir, "table2_kg_quality.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    for k in keys:
        print(f"{k:<26}" + "".join(f"{str(r[k]):>22}" for r in rows))


# ------------------------------------------------------------------ coverage
def prov_key(s):
    """'Art. 8(1)' / 'Article 8(1)' -> ('8','1');  'Art. 10(a)' / 'Article 10, point (a)' -> ('10','a');
    anything with 'Annex I' -> ('ANNEX',)"""
    s = s or ""
    if re.search(r"Annex I\b", s) and not re.search(r"Art", s):
        return ("ANNEX",)
    m = re.search(r"Art(?:icle|\.)?\s*(\d+)\s*(?:\((\w+)\))?(?:,\s*point\s*\((\w)\))?", s)
    if not m:
        return ("?",)
    return tuple(x for x in (m.group(1), m.group(2) or m.group(3)) if x)


def requirements(checklist_path):
    ws = load_workbook(checklist_path, data_only=True)["Checklist"]
    data = list(ws.iter_rows(values_only=True))
    hdr = [str(h).strip() if h else "" for h in data[0]]
    reqs = []
    for row in data[1:]:
        r = dict(zip(hdr, ["" if v is None else str(v).strip() for v in row]))
        if not r.get("req_id") or r.get("expert_decision", "").upper() == "DELETE":
            continue
        r["final_requirement"] = r.get("corrected_requirement") or r.get("requirement")
        r["final_on_chain"] = r.get("corrected_on_chain") or r.get("on_chain")
        reqs.append(r)
    return reqs


def product_eq(a, b):
    """Same product category name, up to singular/plural (no partial overlap: 'virgin' != 'extra virgin')."""
    f = lambda x: " ".join(w[:-1] if w.endswith("s") and len(w) > 3 else w for w in norm(x).replace("-", " ").split())
    return f(a) == f(b)


def candidates(req, rules):
    key = prov_key(req["provision"])
    out = []
    for r in rules:
        rk = ("ANNEX",) if r["source"].startswith("Annex") else prov_key(r["source"])
        if key == ("ANNEX",) and rk == ("ANNEX",) and req["type"].upper() == "LIMIT":
            prod_ok = any(product_eq(req["applies_to"], s) for s in (r.get("subjects") or [r["subject"]]))
            val = re.search(r"(?:≤|≥|<|>|=)\s?\d+(?:,\d+)?", req["final_requirement"])
            val_ok = bool(val) and norm(val.group(0)).replace(" ", "") == norm(r["value"]).replace(" ", "")
            par_ok = text_overlap(req["final_requirement"].split("≤")[0].split(">")[0].split("=")[0], r["parameter"])
            if prod_ok and val_ok and par_ok:
                out.append((3, r))
            elif prod_ok and (val_ok or par_ok):
                out.append((1, r))
        elif key[0] != "ANNEX" and rk[:len(key)] == key:
            out.append((2 if len(key) > 1 or len(rk) == 1 else 1, r))
    out = sorted(out, key=lambda x: -x[0])
    return [r for _, r in out[:4]], (bool(out) and out[0][0] == 3)


def rule_text(r):
    obj = r["object"] or r["value"]
    q = f" [{r['parameter']}]" if r["parameter"] else ""
    return f"{r['id']}: {r['subject']} —{r['type']}→ {obj}{q} ({r['source']})"


def cmd_coverage_sheet(checklist_path, kg_path, out_path):
    graph = json.load(open(kg_path, encoding="utf-8"))
    rules = rule_views(graph)
    src = {n["id"]: n.get("source", "") for n in graph["nodes"] if n["kind"] == "Rule"}
    for r in rules:
        r["source"] = src.get(r["id"], "")
    wb = Workbook()
    ws = wb.active
    ws.title = "Instructions"
    for i, line in enumerate([
        "Reg2Chain - coverage of the regulation's requirements by the knowledge graph",
        "For each requirement of the validated checklist, the candidate rules of the knowledge graph are listed "
        "(same provision; for quality limits, same product, parameter and value).",
        "Choose in 'decision': COVERED (the graph contains the requirement), PARTIAL (only part of it), "
        "NOT_COVERED (absent). 'suggestion' is an automatic hint only (exact limit match).",
        "Record your time in the 'Log' sheet.",
    ], 1):
        c = ws.cell(row=i, column=1, value=line)
        c.alignment = Alignment(wrap_text=True)
        if i == 1:
            c.font = Font(bold=True, size=13, color="2F5496")
    ws.column_dimensions["A"].width = 140
    s = wb.create_sheet("Coverage")
    s.append(["req_id", "provision", "applies_to", "type", "requirement", "on_chain", "candidate_rules",
              "suggestion", "decision", "comment"])
    for req in requirements(checklist_path):
        cands, exact = candidates(req, rules)
        s.append([req["req_id"], req["provision"], req["applies_to"], req["type"], req["final_requirement"],
                  req["final_on_chain"], "\n".join(rule_text(r) for r in cands) or "(no candidate)",
                  "COVERED (exact limit match)" if exact else "", "", ""])
    for i, w in enumerate([8, 16, 26, 18, 60, 10, 70, 18, 14, 30], 1):
        s.column_dimensions[s.cell(row=1, column=i).column_letter].width = w
    for c in s[1]:
        c.font, c.fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="2F5496")
    for row in s.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    dv = DataValidation(type="list", formula1='"COVERED,PARTIAL,NOT_COVERED"', allow_blank=True)
    s.add_data_validation(dv)
    dv.add(f"I2:I{s.max_row + 50}")
    s.freeze_panes = "A2"
    log = wb.create_sheet("Log")
    log.append(["field", "value"])
    for k in ["expert name", "expertise", "date(s)", "total time (minutes)", "comments"]:
        log.append([k, ""])
    wb.save(out_path)
    print(f"coverage workbook: {s.max_row - 1} requirements -> {out_path}")


def cmd_coverage_score(review_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ws = load_workbook(review_path, data_only=True)["Coverage"]
    data = list(ws.iter_rows(values_only=True))
    hdr = [str(h) for h in data[0]]
    rows = [dict(zip(hdr, ["" if v is None else str(v).strip() for v in r])) for r in data[1:] if r[0]]
    by = {}
    for r in rows:
        d = (r["decision"] or "UNDECIDED").upper()
        for group in ("ALL", f"on_chain={r['on_chain'] or '?'}", f"type={r['type'] or '?'}"):
            by.setdefault(group, Counter())[d] += 1
    lines = []
    for group, c in by.items():
        n = sum(c.values())
        cov = c["COVERED"] + 0.5 * c["PARTIAL"]
        lines.append(f"{group:<32} n={n:<3} covered={c['COVERED']:<3} partial={c['PARTIAL']:<3} "
                     f"not_covered={c['NOT_COVERED']:<3} undecided={c['UNDECIDED']:<3} "
                     f"coverage={100 * c['COVERED'] / n:.1f} % (with partial as 1/2: {100 * cov / n:.1f} %)")
    open(os.path.join(out_dir, "coverage_report.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    {"metrics": cmd_metrics, "coverage-sheet": cmd_coverage_sheet,
     "coverage-score": cmd_coverage_score}[sys.argv[1]](*sys.argv[2:])
