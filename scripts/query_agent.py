"""
Section 6 - Regulatory Query Agent.

For each legal category of olive oil, queries the Reg2Chain knowledge graph and produces a
compliance specification (JSON) that is the input of contract generation (section 7):
  quality_limits  : LIMIT rules (parameter, operator, value, unit) with their source provision
  labelling       : obligations / permissions / prohibitions on label items, each with the
                    conditions attached to that label item and its source provision
  conditions      : conditions that apply to the category itself (e.g. classification conditions)
Rules stated for a broader concept (e.g. 'olive oils') are inherited through SUBCLASS_OF
(the top concept 'Product' is excluded); each inherited rule records the concept it comes from.

Two back-ends run the same query:
  neo4j : Cypher on the Neo4j database (credentials NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD)
  json  : the same traversal on kg.json (used when Neo4j is not available, and as a cross-check)

  python query_agent.py kg.json OUT_DIR [--neo4j]
  python query_agent.py evaluate OUT_DIR gold_dev.jsonl gold_test.jsonl
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_common import load_jsonl, norm  # noqa: E402

REGULATION = "Commission Delegated Regulation (EU) 2022/2104"
CATEGORIES = ["ExtraVirginOliveOil", "VirginOliveOil", "LampanteOliveOil", "RefinedOliveOil",
              "OliveOilComposedOfRefinedOliveOilsAndVirginOliveOils", "CrudeOlivePomaceOil",
              "RefinedOlivePomaceOil", "OlivePomaceOil"]

# Algorithm 1 (paper): rules of a category, including rules inherited from its super-concepts
CYPHER_RULES = """
MATCH (c:Concept {id: $category})-[:SUBCLASS_OF*0..]->(a:Concept)
WHERE a.id <> 'Product'
MATCH (r:Rule)-[:APPLIES_TO]->(a)
OPTIONAL MATCH (r)-[:CONCERNS]->(o)
OPTIONAL MATCH (r)-[:DERIVED_FROM]->(p:Provision)
RETURN DISTINCT r {.*} AS rule, a.id AS via, o.id AS object_id,
       coalesce(o.label, o.id) AS object_label, o.expression AS object_expression,
       p.source AS source, p.text AS provision
"""
# conditions attached to a label item (CONDITION rules whose subject is that item)
CYPHER_CONDITIONS = """
MATCH (r:Rule {type: 'CONDITION'})-[:APPLIES_TO]->(x {id: $item})
OPTIONAL MATCH (r)-[:CONCERNS]->(o)
OPTIONAL MATCH (r)-[:DERIVED_FROM]->(p:Provision)
RETURN DISTINCT r {.*} AS rule, $item AS via, o.id AS object_id,
       coalesce(o.label, o.id) AS object_label, o.expression AS object_expression,
       p.source AS source, p.text AS provision
"""
CYPHER_LABEL = "MATCH (c {id: $id}) RETURN coalesce(c.label, c.id) AS label"


# ------------------------------------------------------------------ back-ends
class JsonBackend:
    name = "json"

    def __init__(self, graph):
        self.nodes = {n["id"]: n for n in graph["nodes"]}
        self.out = {}
        for e in graph["edges"]:
            self.out.setdefault(e["source"], {}).setdefault(e["type"], []).append(e["target"])
        self.applies = {}
        for e in graph["edges"]:
            if e["type"] == "APPLIES_TO":
                self.applies.setdefault(e["target"], []).append(e["source"])

    def ancestors(self, cid):
        seen, todo = [], [cid]
        while todo:
            x = todo.pop(0)
            if x in seen or x not in self.nodes:
                continue
            seen.append(x)
            todo += self.out.get(x, {}).get("SUBCLASS_OF", [])
        return [x for x in seen if x != "Product"]

    def _row(self, rid, via):
        r = self.nodes[rid]
        o = (self.out.get(rid, {}).get("CONCERNS") or [None])[0]
        p = (self.out.get(rid, {}).get("DERIVED_FROM") or [None])[0]
        on, pn = self.nodes.get(o, {}), self.nodes.get(p, {})
        return {"rule": {k: v for k, v in r.items() if k != "kind"}, "via": via, "object_id": o,
                "object_label": on.get("label", o), "object_expression": on.get("expression"),
                "source": pn.get("source"), "provision": pn.get("text")}

    def rules(self, category):
        rows = []
        for a in self.ancestors(category):
            rows += [self._row(rid, a) for rid in self.applies.get(a, []) if self.nodes[rid]["kind"] == "Rule"]
        return rows

    def conditions(self, item):
        return [self._row(rid, item) for rid in self.applies.get(item, [])
                if self.nodes[rid]["kind"] == "Rule" and self.nodes[rid]["type"] == "CONDITION"]

    def label(self, cid):
        return self.nodes.get(cid, {}).get("label", cid)

    def close(self):
        pass


class Neo4jBackend:
    name = "neo4j"

    def __init__(self):
        from neo4j import GraphDatabase
        uri, pwd = os.environ.get("NEO4J_URI"), os.environ.get("NEO4J_PASSWORD")
        user = os.environ.get("NEO4J_USER") or os.environ.get("NEO4J_USERNAME")
        if not (uri and user and pwd):
            raise RuntimeError("Neo4j credentials not set")
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd))

    def _q(self, query, **kw):
        with self.driver.session() as s:
            return [dict(r) for r in s.run(query, **kw)]

    def rules(self, category):
        return self._q(CYPHER_RULES, category=category)

    def conditions(self, item):
        return self._q(CYPHER_CONDITIONS, item=item)

    def label(self, cid):
        r = self._q(CYPHER_LABEL, id=cid)
        return r[0]["label"] if r else cid

    def close(self):
        self.driver.close()


# ------------------------------------------------------------------ compliance JSON
def split_value(v):
    m = re.match(r"\s*([<>≤≥=]+)\s*([0-9]+(?:[.,][0-9]+)?)\s*(.*)$", v or "")
    return (m.group(1), m.group(2).replace(",", "."), m.group(3).strip()) if m else ("", "", (v or "").strip())


def entry(row):
    r = row["rule"]
    e = {"rule_id": r["id"], "type": r["type"], "source": row["source"] or r.get("source", "")}
    if row["via"]:
        e["applies_via"] = row["via"]
    return e


def specification(backend, category):
    # a rule stated both for the category and for a super-concept is kept once (the most specific link)
    best = {}
    for row in backend.rules(category):
        rid = row["rule"]["id"]
        key = (row["via"] != category, row["via"] or "")
        if rid not in best or key < best[rid][0]:
            best[rid] = (key, row)
    rows = [v[1] for v in best.values()]
    spec = {"category": category, "label": backend.label(category), "regulation": REGULATION,
            "quality_limits": [], "labelling": {"obligations": [], "permissions": [], "prohibitions": []},
            "conditions": []}
    for row in sorted(rows, key=lambda x: x["rule"]["id"]):
        r, e = row["rule"], entry(row)
        if row["via"] == category:
            e.pop("applies_via")
        if r["type"] == "LIMIT":
            op, num, unit = split_value(r.get("value", ""))
            e.update({"parameter": r.get("parameter", ""), "operator": r.get("operator") or op,
                      "value": float(num) if num else None, "value_text": r.get("value", ""),
                      "unit": r.get("unit") or unit})
            spec["quality_limits"].append(e)
        elif r["type"] == "CONDITION":
            e.update({"condition": row["object_expression"] or r.get("condition") or r.get("value", ""),
                      "condition_id": row["object_id"]})
            spec["conditions"].append(e)
        else:
            item = row["object_id"]
            conds = []
            if item:
                for c in sorted(backend.conditions(item), key=lambda x: x["rule"]["id"]):
                    conds.append({"rule_id": c["rule"]["id"], "condition_id": c["object_id"],
                                  "condition": c["object_expression"] or c["rule"].get("condition") or
                                  c["rule"].get("value", ""), "source": c["source"] or c["rule"].get("source", "")})
            e.update({"label_item": row["object_label"] or r.get("value", ""), "label_item_id": item})
            if r.get("value"):
                e["value"] = r["value"]
            if conds:
                e["conditions"] = conds
            key = {"OBLIGATION": "obligations", "PERMISSION": "permissions", "PROHIBITION": "prohibitions"}[r["type"]]
            spec["labelling"][key].append(e)
    spec["traceability"] = {"rules": len(rows), "with_source_provision": sum(1 for x in rows if x["source"])}
    return spec


def run(kg_path, out_dir, *flags):
    os.makedirs(out_dir, exist_ok=True)
    backends = [JsonBackend(json.load(open(kg_path, encoding="utf-8")))]
    if "--neo4j" in flags:
        try:
            backends.insert(0, Neo4jBackend())
        except Exception as ex:  # noqa: BLE001
            print(f"Neo4j not available ({ex}): JSON back-end only")
    results = {b.name: {c: specification(b, c) for c in CATEGORIES} for b in backends}
    main = results[backends[0].name]
    for c, spec in main.items():
        json.dump(spec, open(os.path.join(out_dir, f"{c}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(list(main.values()), open(os.path.join(out_dir, "compliance_all.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(out_dir, "algorithm1_cypher.txt"), "w").write(CYPHER_RULES.strip() + "\n\n" +
                                                                    CYPHER_CONDITIONS.strip() + "\n")
    print(f"Regulatory Query Agent ({backends[0].name}): compliance JSON for {len(main)} categories -> {out_dir}")
    print(f"{'category':55s} {'limits':>6s} {'oblig.':>6s} {'perm.':>6s} {'prohib.':>7s} {'cond.':>5s} {'traceable':>9s}")
    for c, s in main.items():
        lab = s["labelling"]
        print(f"{c:55s} {len(s['quality_limits']):6d} {len(lab['obligations']):6d} {len(lab['permissions']):6d} "
              f"{len(lab['prohibitions']):7d} {len(s['conditions']):5d} "
              f"{s['traceability']['with_source_provision']:>4d}/{s['traceability']['rules']:<4d}")
    if len(backends) == 2:
        same = all(json.dumps(results["neo4j"][c], sort_keys=True) == json.dumps(results["json"][c], sort_keys=True)
                   for c in CATEGORIES)
        diff = [c for c in CATEGORIES if json.dumps(results["neo4j"][c], sort_keys=True) !=
                json.dumps(results["json"][c], sort_keys=True)]
        print("Cypher (Neo4j) and JSON back-ends return identical specifications" if same else
              f"back-ends differ for: {diff}")
    for b in backends:
        b.close()


# ------------------------------------------------------------------ evaluation of the quality limits
def singular(s):
    return " ".join(w[:-1] if w.endswith("s") and len(w) > 3 else w for w in norm(s).split())


def cmd_evaluate(out_dir, *gold_paths):
    """Quality limits returned per category vs the gold LIMIT relations of Annex I (all gold units)."""
    specs = json.load(open(os.path.join(out_dir, "compliance_all.json"), encoding="utf-8"))
    by_label = {singular(s["label"]): s for s in specs}
    gold = [g for p in gold_paths for g in load_jsonl(p)]
    lines, tp_all, n_gold, n_pred = [], 0, 0, 0
    per_cat = {s["category"]: [] for s in specs}
    for g in gold:
        for r in g["relations"]:
            if r["predicate"] == "LIMIT" and singular(r["subject"]) in by_label:
                per_cat[by_label[singular(r["subject"])]["category"]].append(r)
    for s in specs:
        gl = per_cat[s["category"]]
        preds = [x for x in s["quality_limits"] if x.get("value") is not None]
        used, tp = set(), 0
        for r in gl:
            op, num, _ = split_value(r["object"])
            pc = re.sub(r"[^0-9a-zδ]", "", r.get("qualifier", "").lower())
            for i, x in enumerate(preds):
                xc = re.sub(r"[^0-9a-zδ]", "", x["parameter"].lower())
                if i not in used and num and x["operator"] == op and abs(x["value"] - float(num)) < 1e-9 and \
                        pc and xc and (pc in xc or xc in pc):
                    used.add(i)
                    tp += 1
                    break
        tp_all, n_gold, n_pred = tp_all + tp, n_gold + len(gl), n_pred + len(preds)
        lines.append(f"{s['category']:55s} gold={len(gl):2d} returned={len(preds):2d} correct={tp:2d}")
    p, r = tp_all / max(1, n_pred), tp_all / max(1, n_gold)
    lines.append(f"ALL quality limits: gold={n_gold} returned={n_pred} correct={tp_all} precision={p:.3f} "
                 f"recall={r:.3f} F1={2 * p * r / max(1e-9, p + r):.3f}")
    open(os.path.join(out_dir, "query_evaluation.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if sys.argv[1] == "evaluate":
        cmd_evaluate(*sys.argv[2:])
    else:
        run(*sys.argv[1:])
