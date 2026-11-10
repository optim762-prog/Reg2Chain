"""
Section 4 - Ontology Agent.

Follows the Text2Onto approach (Cimiano & Völker, 2005), re-implemented in Python on top of the
outputs of the Entity Extraction Agent on all provision units:
  1. Term extraction   : entity mentions -> terms (lemmatised, lower-cased), with frequency and
                         TF-IDF-style relevance (number of units mentioning the term).
  2. Concept formation : terms with the same lemma are merged into one concept; each concept is
                         placed under the top class of its entity type.
  3. Taxonomy          : 'vertical relations' by modifier stripping (e.g. 'refined olive oil'
                         -> 'olive oil'): the parent is the longest concept that is a head-suffix.
  4. Instances         : legal references become individuals of LegalReference; each normative
                         relation becomes a ComplianceRule individual linked to its subject, object,
                         threshold value / parameter and source provision (traceability).
  5. Non-taxonomic relations : one object property per relation type, domain/range from arguments.
The ontology is exported to OWL (Turtle) and to a review workbook for expert refinement.

  python ontology_agent.py extraction_all.jsonl units.csv OUT_DIR
"""
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import spacy
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_common import load_jsonl, norm  # noqa: E402

TOP = {"PRODUCT": "Product", "PARAMETER": "QualityParameter", "LABEL_ITEM": "LabelItem", "ACTOR": "Actor",
       "PROCESS": "Process", "LEGAL_REF": "LegalReference"}
PROPS = {"OBLIGATION": "hasObligation", "PERMISSION": "hasPermission", "PROHIBITION": "hasProhibition",
         "LIMIT": "hasLimit", "CONDITION": "hasCondition", "REFERS_TO": "refersTo"}
NORMATIVE = {"OBLIGATION", "PERMISSION", "PROHIBITION", "LIMIT", "CONDITION"}
NS = "http://example.org/reg2chain/olive-oil#"

_NLP = None


def lemma_key(text):
    global _NLP
    if _NLP is None:                       # loaded only when terms are lemmatised (not needed for 4.4)
        _NLP = spacy.load("en_core_web_sm", disable=["ner", "parser"])
    nlp = _NLP
    return " ".join(t.lemma_.lower() for t in nlp(norm(text)) if not t.is_punct or t.text in "()%/")


def camel(label):
    words = re.findall(r"[A-Za-z0-9ΔΣ]+", label)
    return "".join(w[:1].upper() + w[1:] for w in words) or "Concept"


def source_of(unit_id):
    m = re.match(r"ART(\d+)(?:\.(\d+))?(?:\.([a-h]|lead))?", unit_id)
    if m:
        s = f"Article {m.group(1)}" + (f"({m.group(2)})" if m.group(2) else "")
        return s + (f", point ({m.group(3)})" if m.group(3) and m.group(3) != "lead" else "")
    m = re.match(r"ANX1\.A\.(\d)", unit_id)
    return f"Annex I, Table A, row {m.group(1)}" if m else unit_id


def build(extraction, units):
    texts = {u["unit_id"]: u["text"] for u in units}
    n_units = len(texts)
    # 1-2. terms and concepts
    concepts, mention2concept = {}, {}
    for p in extraction:
        for e in p["entities"]:
            if e["label"] not in TOP:
                continue
            key = (e["label"], lemma_key(e["text"]))
            c = concepts.setdefault(key, {"type": e["label"], "variants": Counter(), "units": set()})
            c["variants"][e["text"]] += 1
            c["units"].add(p["unit_id"])
            mention2concept[(p["unit_id"], norm(e["text"]))] = key
    for key, c in concepts.items():
        c["label"] = c["variants"].most_common(1)[0][0]
        c["frequency"] = sum(c["variants"].values())
        c["relevance"] = round(c["frequency"] * math.log(1 + n_units / len(c["units"])), 3)
    names, ids = set(), {}
    for key, c in sorted(concepts.items(), key=lambda kv: (-kv[1]["frequency"], kv[1]["label"])):
        base = camel(c["label"]) if c["type"] != "LEGAL_REF" else "Ref_" + camel(c["label"])[:40]
        name, k = base, 2
        while name in names:
            name, k = f"{base}{k}", k + 1
        names.add(name)
        ids[key] = name
        c["id"] = name
    # 3. taxonomy by modifier stripping (head-suffix), within the same top class
    for key, c in concepts.items():
        c["parent"] = TOP[c["type"]]
        if c["type"] == "LEGAL_REF":
            continue
        words = key[1].split()
        for i in range(1, len(words)):
            cand = (c["type"], " ".join(words[i:]))
            if cand in concepts:
                c["parent"] = ids[cand]
                break
    # 4-5. rules and properties
    rules, refs, prop_use = [], [], defaultdict(lambda: [Counter(), Counter()])
    for p in extraction:
        for r in p["relations"]:
            s = mention2concept.get((p["unit_id"], norm(r["subject"])))
            o = mention2concept.get((p["unit_id"], norm(r["object"])))
            if r["predicate"] == "REFERS_TO":
                if s and o:
                    refs.append({"subject": ids[s], "reference": ids[o], "source": source_of(p["unit_id"])})
                    prop_use["REFERS_TO"][0][concepts[s]["type"]] += 1
                    prop_use["REFERS_TO"][1][concepts[o]["type"]] += 1
                continue
            if r["predicate"] not in NORMATIVE or not s:
                continue
            value = r["object"] if (o is None) else ""
            rules.append({"rule_id": f"R{len(rules) + 1:03d}", "type": r["predicate"], "subject": ids[s],
                          "object": ids[o] if o else "", "value": value, "qualifier": r.get("qualifier", ""),
                          "unit_id": p["unit_id"], "source": source_of(p["unit_id"]),
                          "provision": texts.get(p["unit_id"], "")})
            prop_use[r["predicate"]][0][concepts[s]["type"]] += 1
            prop_use[r["predicate"]][1][concepts[o]["type"] if o else "VALUE"] += 1
    props = [{"property": PROPS[t], "relation_type": t,
              "domain": TOP.get(prop_use[t][0].most_common(1)[0][0], "Product") if prop_use[t][0] else "Product",
              "range": (TOP.get(prop_use[t][1].most_common(1)[0][0], "xsd:string") if prop_use[t][1] else "")
              if t != "LIMIT" else "Threshold (value + parameter)",
              "uses": sum(prop_use[t][0].values())} for t in PROPS]
    return {"concepts": sorted(concepts.values(), key=lambda c: (c["type"], c["parent"], c["label"])),
            "properties": props, "rules": rules, "references": refs}


def to_owl(onto, path):
    from rdflib import RDF, RDFS, OWL, XSD, Graph, Literal, Namespace
    ex = Namespace(NS)
    g = Graph()
    g.bind("r2c", ex)
    g.bind("owl", OWL)
    for top in list(TOP.values()) + ["ComplianceRule", "Threshold"]:
        g.add((ex[top], RDF.type, OWL.Class))
    for t, cls in (("OBLIGATION", "Obligation"), ("PERMISSION", "Permission"), ("PROHIBITION", "Prohibition"),
                   ("LIMIT", "QualityLimit"), ("CONDITION", "Condition")):
        g.add((ex[cls], RDF.type, OWL.Class))
        g.add((ex[cls], RDFS.subClassOf, ex.ComplianceRule))
    for c in onto["concepts"]:
        node = ex[c["id"]]
        if c["type"] == "LEGAL_REF":
            g.add((node, RDF.type, ex.LegalReference))
        else:
            g.add((node, RDF.type, OWL.Class))
            g.add((node, RDFS.subClassOf, ex[c["parent"]]))
        g.add((node, RDFS.label, Literal(c["label"], lang="en")))
    for p in onto["properties"]:
        g.add((ex[p["property"]], RDF.type, OWL.ObjectProperty))
    for dp in ("thresholdValue", "onParameter", "sourceProvision", "provisionText", "appliesTo", "concerns"):
        g.add((ex[dp], RDF.type, OWL.DatatypeProperty if dp in ("thresholdValue", "sourceProvision",
                                                                  "provisionText") else OWL.ObjectProperty))
    cls_of = {"OBLIGATION": "Obligation", "PERMISSION": "Permission", "PROHIBITION": "Prohibition",
              "LIMIT": "QualityLimit", "CONDITION": "Condition"}
    for r in onto["rules"]:
        node = ex[r["rule_id"]]
        g.add((node, RDF.type, ex[cls_of[r["type"]]]))
        for subj in r["subject"].split(" OR "):
            g.add((node, ex.appliesTo, ex[subj.strip()]))
        if r["object"]:
            g.add((node, ex.concerns, ex[r["object"]]))
        if r.get("threshold"):
            t = r["threshold"]
            g.add((node, ex.thresholdOperator, Literal(t.get("operator", ""))))
            g.add((node, ex.thresholdNumeric, Literal(t.get("numeric_value", ""))))
            g.add((node, ex.thresholdUnit, Literal(t.get("unit", ""))))
        if r.get("condition"):
            g.add((node, ex.conditionExpression, Literal(r["condition"].get("expression", ""))))
        if r["value"]:
            g.add((node, ex.thresholdValue, Literal(r["value"], datatype=XSD.string)))
        if r["qualifier"]:
            g.add((node, ex.onParameter, Literal(r["qualifier"])))
        g.add((node, ex.sourceProvision, Literal(r["source"])))
    for ref in onto["references"]:
        g.add((ex[ref["subject"]], ex.refersTo, ex[ref["reference"]]))
    g.serialize(path, format="turtle")
    return len(g)


HEAD = Font(bold=True, color="FFFFFF")
FILL = PatternFill("solid", fgColor="2F5496")
WRAP = Alignment(wrap_text=True, vertical="top")


def sheet(wb, title, header, rows, widths, decision_col, choices):
    ws = wb.create_sheet(title)
    ws.append(header)
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    for c in ws[1]:
        c.font, c.fill, c.alignment = HEAD, FILL, WRAP
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = WRAP
            if isinstance(c.value, str) and c.value.startswith("="):   # e.g. '= 0,0' must stay text
                c.data_type = "s"
    dv = DataValidation(type="list", formula1='"' + ",".join(choices) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{decision_col}2:{decision_col}{len(rows) + 200}")
    ws.freeze_panes = "A2"


def review_workbook(onto, path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Instructions"
    for i, line in enumerate([
        "Reg2Chain - expert refinement of the automatically learned ontology",
        "The ontology was learned automatically (Text2Onto approach) from the Entity Extraction Agent output on all 63 provision units.",
        "For each row, choose a decision. Concepts: KEEP / EDIT (new label and/or new parent) / MERGE (give the concept id to merge into) / DELETE.",
        "Rules: KEEP / EDIT (corrected type, subject, object or value) / DELETE. Add missing concepts or rules at the bottom with decision ADD.",
        "Parent = the superclass of the concept (top classes: Product, QualityParameter, LabelItem, Actor, Process, LegalReference).",
        "Record your total time in the 'Log' sheet. The number of corrections and the time are reported in the paper (expert effort).",
    ], 1):
        c = ws.cell(row=i, column=1, value=line)
        c.alignment = WRAP
        if i == 1:
            c.font = Font(bold=True, size=13, color="2F5496")
    ws.column_dimensions["A"].width = 140
    sheet(wb, "Concepts",
          ["concept_id", "label", "top_class", "parent", "frequency", "n_units", "variants", "decision",
           "new_label", "new_parent", "merge_into", "comment"],
          [[c["id"], c["label"], TOP[c["type"]], c["parent"], c["frequency"], len(c["units"]),
            "; ".join(v for v in c["variants"] if v != c["label"]), "", "", "", "", ""] for c in onto["concepts"]],
          [28, 40, 16, 26, 10, 9, 30, 12, 30, 24, 20, 30], "H", ["KEEP", "EDIT", "MERGE", "DELETE", "ADD"])
    sheet(wb, "Properties",
          ["property", "relation_type", "domain", "range", "uses", "decision", "new_domain", "new_range", "comment"],
          [[p["property"], p["relation_type"], p["domain"], p["range"], p["uses"], "", "", "", ""]
           for p in onto["properties"]],
          [20, 16, 18, 26, 8, 12, 18, 18, 30], "F", ["KEEP", "EDIT", "DELETE", "ADD"])
    sheet(wb, "Rules",
          ["rule_id", "type", "subject", "object", "value", "qualifier", "source", "provision", "decision",
           "corrected_type", "corrected_subject", "corrected_object", "corrected_value", "comment"],
          [[r["rule_id"], r["type"], r["subject"], r["object"], r["value"], r["qualifier"], r["source"],
            r["provision"], "", "", "", "", "", ""] for r in onto["rules"]],
          [8, 13, 26, 26, 12, 22, 22, 70, 12, 14, 22, 22, 14, 28], "I", ["KEEP", "EDIT", "DELETE", "ADD"])
    log = wb.create_sheet("Log")
    log.append(["field", "value"])
    for k in ["expert name", "expertise", "date(s)", "total time (minutes)", "comments"]:
        log.append([k, ""])
    log.column_dimensions["A"].width = 26
    log.column_dimensions["B"].width = 80
    for c in log[1]:
        c.font, c.fill = HEAD, FILL
    wb.save(path)


def main(extraction_path, units_csv, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    units = list(csv.DictReader(open(units_csv, encoding="utf-8")))
    onto = build(load_jsonl(extraction_path), units)
    serial = json.loads(json.dumps(onto, default=lambda o: sorted(o) if isinstance(o, set) else dict(o)))
    json.dump(serial, open(os.path.join(out_dir, "ontology_learned.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    n = to_owl(onto, os.path.join(out_dir, "ontology_learned.ttl"))
    review_workbook(onto, os.path.join(out_dir, "Reg2Chain_ontology_review.xlsx"))
    by_type = Counter(TOP[c["type"]] for c in onto["concepts"])
    print(f"Ontology Agent: {len(onto['concepts'])} concepts {dict(by_type)}, "
          f"{sum(c['parent'] not in TOP.values() for c in onto['concepts'])} learned subclass links, "
          f"{len(onto['properties'])} properties, {len(onto['rules'])} rules, "
          f"{len(onto['references'])} refersTo links, {n} OWL triples -> {out_dir}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
