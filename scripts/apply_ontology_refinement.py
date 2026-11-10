"""
Section 4 - Apply the expert refinement to the learned ontology and measure the expert effort.

Reads the reviewed workbook and the learned ontology and applies the expert decisions:
  Concepts   : KEEP / EDIT (new label, new parent) / MERGE (merge_into) / DELETE / ADD
  Properties : KEEP / EDIT (new_label = new property name, new_domain, new_range) / DELETE
  Rules      : KEEP / EDIT (corrected type / subject / object / value) / DELETE / ADD
               - a subject written 'A OR B OR C' means that the rule applies to each category
               - an object 'Condition_x' / 'Threshold_x' refers to the Conditions / Thresholds sheets
Optional sheets added by the experts are integrated:
  Thresholds  : structured limits (parameter, operator, numeric value, unit, product scope) per rule
  Conditions  : condition expressions per rule
  Schema gaps : provisions the schema cannot express (reported, kept in the output)
Concepts referenced in rules but absent from the Concepts sheet are created and counted as
implicit additions. Rules added by the experts are linked to their provision via units.csv.

Outputs: ontology_refined.json, ontology_refined.ttl, refinement_report.txt / .csv

  python apply_ontology_refinement.py ontology_learned.json review.xlsx OUT_DIR [units.csv]
"""
import csv
import json
import os
import re
import sys
from collections import Counter

from openpyxl import load_workbook

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ontology_agent import TOP, camel, source_of, to_owl  # noqa: E402
from extraction_common import norm  # noqa: E402

TYPE_OF_TOP = {v: k for k, v in TOP.items()}
IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _clean(v):
    """Cells such as '= 0,0' may come back as '#ERROR!' or empty after editing in a spreadsheet tool."""
    return "" if (not v or v.startswith("#")) else v


def canon_source(s):
    """Experts sometimes wrote 'Article 6(2)(a)', 'Article 10(a)' or added ', first sentence'; map to the
    source format used by the pipeline ('Article 6(2), point (a)') so the rule is linked to its provision."""
    s = re.sub(r",\s*(read with|first|second|third|last)\b.*$", "", (s or "").strip())
    s = re.sub(r"^(Article \d+(?:\(\d+\))?)\(([a-h])\)$", r"\1, point (\2)", s)
    return s


def rows(wb, name):
    if name not in wb.sheetnames:
        return []
    data = list(wb[name].iter_rows(values_only=True))
    if not data:
        return []
    hdr = [str(h).strip() if h is not None else f"col{i}" for i, h in enumerate(data[0])]
    return [dict(zip(hdr, [("" if v is None else str(v).strip()) for v in r])) for r in data[1:]
            if any(v not in (None, "") for v in r)]


def minutes(text):
    t = (text or "").lower().replace(",", ".")
    h = re.search(r"(\d+(?:\.\d+)?)\s*h", t)
    m = re.search(r"(\d+)\s*(?:min|m\b)", t)
    if h or m:
        return round(float(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0)
    return int(float(t)) if re.fullmatch(r"\d+(?:\.\d+)?", t) else None


def parts(v):
    return [p.strip() for p in (v or "").split(" OR ") if p.strip()]


def main(learned_path, review_path, out_dir, units_csv=None):
    os.makedirs(out_dir, exist_ok=True)
    onto = json.load(open(learned_path, encoding="utf-8"))
    wb = load_workbook(review_path, data_only=True)
    stats = {s: Counter() for s in ("Concepts", "Properties", "Rules")}
    unit_of_source = {}
    if units_csv:
        for u in csv.DictReader(open(units_csv, encoding="utf-8")):
            unit_of_source.setdefault(source_of(u["unit_id"]), u["unit_id"])

    # ---------------- concepts
    by_id = {c["id"]: c for c in onto["concepts"]}
    merged, deleted, concepts = {}, set(), {}
    for r in rows(wb, "Concepts"):
        d = (r.get("decision") or "").upper() or "UNDECIDED"
        stats["Concepts"][d] += 1
        cid = r.get("concept_id") or camel(r.get("new_label") or r.get("label", ""))
        if d == "DELETE":
            deleted.add(cid)
            continue
        if d == "MERGE" and r.get("merge_into"):
            merged[cid] = r["merge_into"]
            continue
        c = dict(by_id.get(cid, {"id": cid, "type": TYPE_OF_TOP.get(r.get("top_class"), "PRODUCT"),
                                  "frequency": 0, "units": [], "variants": {}}))
        c["id"] = cid
        c["label"] = r.get("new_label") or r.get("label") or c.get("label", cid)
        c["parent"] = r.get("new_parent") or r.get("parent") or c.get("parent") or TOP[c["type"]]
        c["origin"] = "expert" if d == "ADD" else "learned"
        concepts[cid] = c

    def resolve(cid):
        seen = set()
        while cid in merged and cid not in seen:
            seen.add(cid)
            cid = merged[cid]
        return None if cid in deleted else cid

    # ---------------- thresholds, conditions, schema gaps (sheets added by the experts)
    thresholds = {t["rule_id"]: t for t in rows(wb, "Thresholds") if t.get("rule_id")}
    threshold_ids = {t.get("threshold_id"): t for t in rows(wb, "Thresholds") if t.get("threshold_id")}
    conditions = {c["condition_id"]: c for c in rows(wb, "Conditions") if c.get("condition_id")}
    cond_by_rule = {c["rule_id"]: c for c in conditions.values() if c.get("rule_id")}
    gaps_rows = list(wb["Schema gaps"].iter_rows(values_only=True)) if "Schema gaps" in wb.sheetnames else []
    gaps = [[("" if v is None else str(v)) for v in r] for r in gaps_rows if any(v not in (None, "") for v in r)]

    # ---------------- properties
    props = []
    for r in rows(wb, "Properties"):
        d = (r.get("decision") or "").upper() or "UNDECIDED"
        stats["Properties"][d] += 1
        if d == "DELETE":
            continue
        name = r.get("new_label") if IDENT.match(r.get("new_label") or "") else r["property"]
        props.append({"property": name, "relation_type": r["relation_type"],
                      "domain": r.get("new_domain") or r["domain"], "range": r.get("new_range") or r["range"],
                      "learned_name": r["property"]})

    # ---------------- rules
    by_rule = {x["rule_id"]: x for x in onto["rules"]}
    rules, implicit = [], Counter()

    def ensure(cid, role):
        """Concept referenced by a rule: resolve merges, create it if the experts introduced it."""
        if not cid or cid.startswith(("Condition_", "Threshold_")):
            return cid
        rid = resolve(cid)
        if rid is None:
            return None
        if rid not in concepts:
            concepts[rid] = {"id": rid, "type": "PRODUCT" if role == "subject" else "LABEL_ITEM",
                             "label": re.sub(r"(?<!^)(?=[A-Z])", " ", rid).lower(), "frequency": 0,
                             "units": [], "variants": {}, "origin": "expert (implicit)",
                             "parent": TOP["PRODUCT" if role == "subject" else "LABEL_ITEM"]}
            implicit[role] += 1
        return rid

    edit_kind = Counter()
    renumbered = 0
    restored_values = 0
    for r in rows(wb, "Rules"):
        d = (r.get("decision") or "").upper() or "UNDECIDED"
        stats["Rules"][d] += 1
        if d == "EDIT":
            changed_fields = [k for k in ("corrected_type", "corrected_subject", "corrected_object", "corrected_value")
                              if r.get(k)]
            edit_kind["content corrected" if changed_fields else "enriched only (threshold / condition / comment)"] += 1
        if d == "DELETE":
            continue
        # The review row is self-contained (source + provision). The learned rule with the same id is
        # reused only if it comes from the same provision: if the learned ontology was regenerated after
        # the review, rule ids may have been renumbered, and the row's own source must win.
        learned = by_rule.get(r["rule_id"])
        if learned and r.get("source") and learned.get("source") != r.get("source"):
            learned = None
            renumbered += 1
        base = dict(learned or {"rule_id": r["rule_id"] or f"X{len(rules) + 1:03d}",
                                "unit_id": "", "provision": r.get("provision", "")})
        subj = [s for s in (ensure(p, "subject") for p in parts(r.get("corrected_subject") or r.get("subject")))
                if s]
        obj = ensure(r.get("corrected_object") or r.get("object", ""), "object") or ""
        base.update({"type": r.get("corrected_type") or r["type"], "subject": " OR ".join(subj), "object": obj,
                     "value": r.get("corrected_value") or _clean(r.get("value", "")) or base.get("value", ""),
                     "qualifier": r.get("qualifier", "") or base.get("qualifier", ""),
                     "source": r.get("source") or base.get("source", ""), "decision": d})
        src = canon_source(base["source"])
        if src in unit_of_source:
            base["unit_id"] = unit_of_source[src]
        t = thresholds.get(base["rule_id"]) or threshold_ids.get(obj)
        if base["type"] == "LIMIT" and not base.get("value"):
            # a cell typed '= 0,0' is read as a formula and becomes '#ERROR!': take the value of the learned
            # rule of the same provision and parameter, or rebuild '= <numeric value>' from the Thresholds sheet
            same = [x.get("value", "") for x in onto["rules"] if x.get("source") == base["source"]
                    and norm(x.get("qualifier", "")) == norm(base.get("qualifier", "")) and x.get("value")]
            if same:
                base["value"] = same[0]
            elif t and t.get("numeric_value"):
                base["value"] = "= " + str(t["numeric_value"])
            restored_values += 1 if base.get("value") else 0
        if t and _clean(str(t.get("operator") or "")) == "" and base.get("value", "").startswith("="):
            t = dict(t, operator="=")
        if t:
            base["threshold"] = {k: t.get(k, "") for k in ("parameter", "operator", "numeric_value", "unit",
                                                             "product_scope")}
        c = conditions.get(obj) or cond_by_rule.get(base["rule_id"])
        if c:
            base["condition"] = {"id": c["condition_id"], "expression": c.get("condition_expression", "")}
        if subj:
            rules.append(base)

    for c in concepts.values():
        if c["parent"] not in TOP.values():
            c["parent"] = resolve(c["parent"]) or TOP[c["type"]]
            if c["parent"] not in concepts and c["parent"] not in TOP.values():
                c["parent"] = TOP[c["type"]]

    refs = [{"subject": resolve(x["subject"]), "reference": resolve(x["reference"]), "source": x["source"]}
            for x in onto["references"]]
    refs = [x for x in refs if x["subject"] in concepts and x["reference"] in concepts]
    refined = {"concepts": list(concepts.values()), "properties": props, "rules": rules, "references": refs,
               "conditions": list(conditions.values()), "thresholds": list(threshold_ids.values()),
               "schema_gaps": gaps}
    json.dump(refined, open(os.path.join(out_dir, "ontology_refined.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    n = to_owl(refined, os.path.join(out_dir, "ontology_refined.ttl"))

    log = {r["field"]: r.get("value", "") for r in rows(wb, "Log")}
    lines, table = [], []
    for s, cnt in stats.items():
        total = sum(cnt.values())
        learned = total - cnt.get("ADD", 0)
        changed = sum(v for k, v in cnt.items() if k in ("EDIT", "MERGE", "DELETE"))
        lines.append(f"{s}: {learned} learned items | " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items())) +
                     f" | learned items corrected: {changed}/{learned} ({100 * changed / max(1, learned):.1f} %), "
                     f"items added by the experts: {cnt.get('ADD', 0)}")
        for k, v in sorted(cnt.items()):
            table.append([s, k, v])
    lines.append(f"Rules marked EDIT: {dict(edit_kind)}")
    lines.append(f"Rules linked to their provision: {sum(1 for r in rules if r.get('unit_id'))}/{len(rules)} "
                 f"(review rows re-aligned on their own source: {renumbered}); "
                 f"limit values restored after a spreadsheet formula error: {restored_values}")
    lines.append(f"Concepts introduced implicitly in rules: {sum(implicit.values())} {dict(implicit)}")
    lines.append(f"Structured thresholds: {len(threshold_ids)}, conditions: {len(conditions)}, "
                 f"schema gaps identified: {max(0, len(gaps))}")
    t_min = minutes(log.get("total time (minutes)", ""))
    lines.append(f"Experts: {log.get('expert name', '')} ({log.get('expertise', '')}); "
                 f"time: {log.get('total time (minutes)', '')}" + (f" = {t_min} min" if t_min else ""))
    lines.append(f"Refined ontology: {len(concepts)} concepts, {len(props)} properties, {len(rules)} rules "
                 f"({sum(1 for r in rules if ' OR ' in r['subject'])} with several product categories), "
                 f"{len(refs)} refersTo links, {n} OWL triples")
    open(os.path.join(out_dir, "refinement_report.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    with open(os.path.join(out_dir, "refinement_report.csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["sheet", "decision", "count"]] + table)
    if gaps:
        with open(os.path.join(out_dir, "schema_gaps.csv"), "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(gaps)
    print("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:5])
