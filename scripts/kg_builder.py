"""
Section 5 - Graph Construction Agent.

Builds the regulatory knowledge graph from an ontology (learned or expert-refined):
  (:Concept {id, label, top_class})            one node per concept (Product, LabelItem, ...)
  (:LegalReference {id, label})                legal references
  (:Rule {id, type, value, parameter, source}) one node per compliance rule
  (:Provision {id, source, text})              the provision unit each rule comes from
  edges: SUBCLASS_OF, APPLIES_TO (rule -> subject concept), CONCERNS (rule -> object concept),
         DERIVED_FROM (rule -> provision), REFERS_TO (concept -> legal reference)
Each threshold is attached to the rule of the product category it applies to, and each rule is
traceable to its source provision.

The graph is written as JSON (nodes/edges) and, if Neo4j credentials are available
(environment variables NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD - in Colab from the Secrets panel),
loaded into Neo4j (the database is cleared first).

  python kg_builder.py ontology.json units.csv kg.json [--neo4j]
"""
import csv
import json
import os
import sys

TOPS = {"Product", "QualityParameter", "LabelItem", "Actor", "Process", "LegalReference"}


def build_graph(onto, units):
    texts = {u["unit_id"]: u["text"] for u in units}
    nodes, edges = {}, []
    for t in TOPS - {"LegalReference"}:
        nodes[t] = {"id": t, "kind": "Concept", "label": t, "top_class": t}
    for c in onto["concepts"]:
        top = {"PRODUCT": "Product", "PARAMETER": "QualityParameter", "LABEL_ITEM": "LabelItem",
               "ACTOR": "Actor", "PROCESS": "Process", "LEGAL_REF": "LegalReference"}.get(c["type"], "Product")
        kind = "LegalReference" if top == "LegalReference" else "Concept"
        nodes[c["id"]] = {"id": c["id"], "kind": kind, "label": c["label"], "top_class": top}
        if kind == "Concept" and c.get("parent") and c["parent"] != c["id"]:
            edges.append((c["id"], "SUBCLASS_OF", c["parent"]))
    for r in onto["rules"]:
        rid = r["rule_id"]
        t = r.get("threshold") or {}
        nodes[rid] = {"id": rid, "kind": "Rule", "type": r["type"], "value": r.get("value", ""),
                      "parameter": t.get("parameter") or r.get("qualifier", ""), "source": r.get("source", ""),
                      "operator": t.get("operator", ""), "numeric_value": t.get("numeric_value", ""),
                      "unit": t.get("unit", ""), "condition": (r.get("condition") or {}).get("expression", "")}
        for subj in (r.get("subject") or "").split(" OR "):
            if subj.strip():
                edges.append((rid, "APPLIES_TO", subj.strip()))
        obj = r.get("object") or ""
        if obj.startswith("Condition_"):
            nodes.setdefault(obj, {"id": obj, "kind": "Condition", "label": obj,
                                   "expression": (r.get("condition") or {}).get("expression", "")})
        elif obj.startswith("Threshold_"):
            nodes.setdefault(obj, {"id": obj, "kind": "Threshold", "label": obj, **{k: str(v) for k, v in t.items()}})
        if obj:
            edges.append((rid, "CONCERNS", obj))
        uid = r.get("unit_id") or ""
        if uid:
            pid = "P_" + uid
            nodes.setdefault(pid, {"id": pid, "kind": "Provision", "source": r.get("source", ""),
                                   "text": texts.get(uid, r.get("provision", ""))})
            edges.append((rid, "DERIVED_FROM", pid))
    for x in onto.get("references", []):
        edges.append((x["subject"], "REFERS_TO", x["reference"]))
    edges = [e for e in dict.fromkeys(edges) if e[0] in nodes and e[2] in nodes]
    return {"nodes": list(nodes.values()), "edges": [{"source": a, "type": t, "target": b} for a, t, b in edges]}


def load_neo4j(graph):
    from neo4j import GraphDatabase
    uri, pwd = os.environ.get("NEO4J_URI"), os.environ.get("NEO4J_PASSWORD")
    user = os.environ.get("NEO4J_USER") or os.environ.get("NEO4J_USERNAME")
    if not (uri and user and pwd):
        print("Neo4j credentials not set (NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD): Neo4j loading skipped")
        return
    with GraphDatabase.driver(uri, auth=(user, pwd)) as driver, driver.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
        for kind in ("Concept", "LegalReference", "Rule", "Provision", "Condition", "Threshold"):
            batch = [n for n in graph["nodes"] if n["kind"] == kind]
            s.run(f"UNWIND $rows AS r MERGE (n:{kind} {{id: r.id}}) SET n += r", rows=batch)
        for et in sorted({e["type"] for e in graph["edges"]}):
            batch = [e for e in graph["edges"] if e["type"] == et]
            s.run(f"UNWIND $rows AS r MATCH (a {{id: r.source}}), (b {{id: r.target}}) MERGE (a)-[:{et}]->(b)",
                  rows=batch)
        n = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        m = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    print(f"loaded into Neo4j: {n} nodes, {m} relationships")


def main(onto_path, units_csv, out_path, *flags):
    onto = json.load(open(onto_path, encoding="utf-8"))
    units = list(csv.DictReader(open(units_csv, encoding="utf-8")))
    graph = build_graph(onto, units)
    json.dump(graph, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    kinds = {}
    for n in graph["nodes"]:
        kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1
    print(f"Graph Construction Agent: {len(graph['nodes'])} nodes {kinds}, {len(graph['edges'])} edges -> {out_path}")
    if "--neo4j" in flags:
        load_neo4j(graph)


if __name__ == "__main__":
    main(*sys.argv[1:])
