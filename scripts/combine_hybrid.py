"""
Section 3 - Hybrid Entity Extraction Agent (Reg2Chain) = rules + LLM.

Entities: the precise pattern-based types (LEGAL_REF, VALUE, quoted LABEL_ITEM) and the
domain-gazetteer PARAMETERs come from the rules; every other type comes from the LLM;
rule entities are then added wherever they do not overlap an LLM entity.
Relations: union of the LLM relations and of the rule relations recomputed on the merged
entities (deduplicated); relations whose arguments are not merged entities are discarded.

  python combine_hybrid.py gold.jsonl pred_rules.jsonl pred_llm.jsonl pred_hybrid.jsonl --strategy=patterns-first|llm-first

The strategy is selected on the development units (never on the test units).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_common import dedup_relations, load_jsonl, norm, save_jsonl, select_non_overlapping  # noqa: E402
from extract_rules import extract_relations  # noqa: E402

RULE_FIRST = {"LEGAL_REF", "VALUE", "PARAMETER"}
QUOTED = re.compile(r"^‘.*’$")


def merge(rule_ents, llm_ents, strategy):
    """patterns-first: rule LEGAL_REF/VALUE/PARAMETER/quoted spans win over the LLM, the LLM wins elsewhere.
    llm-first: LLM spans win everywhere; rule spans only fill the gaps."""
    cands = []
    for e in rule_ents:
        strong = e["label"] in RULE_FIRST or QUOTED.match(e["text"])
        prio = 3 if (strategy == "patterns-first" and strong) else 1
        cands.append(dict(e, prio=prio))
    for e in llm_ents:
        cands.append(dict(e, prio=2))
    return select_non_overlapping(cands)


def main(gold_path, rules_path, llm_path, out_path, *flags):
    strategy = next((f.split("=", 1)[1] for f in flags if f.startswith("--strategy=")), "patterns-first")
    assert strategy in ("patterns-first", "llm-first"), strategy
    rules = {p["unit_id"]: p for p in load_jsonl(rules_path)}
    llm = {p["unit_id"]: p for p in load_jsonl(llm_path)}
    out = []
    for g in load_jsonl(gold_path):
        u = g["unit_id"]
        r, l = rules.get(u, {"entities": [], "relations": []}), llm.get(u, {"entities": [], "relations": []})
        ents = merge(r["entities"], l["entities"], strategy)
        names = {norm(e["text"]) for e in ents}
        rels = [x for x in l["relations"] + extract_relations(g["sentence"], ents)
                if norm(x["subject"]) in names and norm(x["object"]) in names]
        out.append({"unit_id": u, "entities": ents, "relations": dedup_relations(rels)})
    save_jsonl(out, out_path)
    print(f"hybrid ({strategy}): {sum(len(p['entities']) for p in out)} entities, "
          f"{sum(len(p['relations']) for p in out)} relations -> {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:])
