"""
Step 1 - Measure how much the annotator corrected the LLM pre-annotation (reported in the paper).

  python compare_with_preannotation.py units.csv preannotation_claude_A1.xlsx Reg2Chain_annotation_A1.xlsx OUT_DIR

Counts, for entities (span + type) and relations (subject, relation, object, qualifier):
  kept      : present in both
  deleted   : in the pre-annotation, removed by the annotator
  added     : added by the annotator
  retyped   : same entity span, different type (entities only)
Writes correction_report.txt and a per-unit CSV of changes.
"""
import csv
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_and_build_gold import load_annotations, norm  # noqa: E402


def main(units_csv, pre_path, final_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    units = {r["unit_id"]: r for r in csv.DictReader(open(units_csv, encoding="utf-8"))}
    pe, pr, _ = load_annotations(pre_path, units)
    fe, fr, probs = load_annotations(final_path, units)
    if probs:
        print(f"{len(probs)} problems in the final workbook: fix them first (run check_and_build_gold.py)")

    rows, tot = [], Counter()
    for u in units:
        P = Counter((e["start"], e["end"], e["label"]) for e in pe[u])
        F = Counter((e["start"], e["end"], e["label"]) for e in fe[u])
        kept, dele, add = P & F, P - F, F - P
        spans_d = Counter((s, e) for s, e, _ in dele.elements())
        spans_a = Counter((s, e) for s, e, _ in add.elements())
        retyped = sum((spans_d & spans_a).values())
        tot["ent_pre"] += sum(P.values()); tot["ent_final"] += sum(F.values())
        tot["ent_kept"] += sum(kept.values()); tot["ent_retyped"] += retyped
        tot["ent_deleted"] += sum(dele.values()) - retyped; tot["ent_added"] += sum(add.values()) - retyped
        key = lambda r: (norm(r["subject"]), r["predicate"], norm(r["object"]), norm(r["qualifier"]))
        RP, RF = Counter(map(key, pr[u])), Counter(map(key, fr[u]))
        tot["rel_pre"] += sum(RP.values()); tot["rel_final"] += sum(RF.values())
        tot["rel_kept"] += sum((RP & RF).values())
        tot["rel_deleted"] += sum((RP - RF).values()); tot["rel_added"] += sum((RF - RP).values())
        changed = (P != F) or (RP != RF)
        tot["units_changed"] += changed
        rows.append([u, units[u]["split"], sum(P.values()), sum(F.values()), retyped,
                     sum((RP - RF).values()), sum((RF - RP).values()), "Y" if changed else "N"])

    with open(os.path.join(out_dir, "corrections_per_unit.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["unit_id", "split", "entities_pre", "entities_final", "entities_retyped",
                    "relations_deleted", "relations_added", "changed"])
        w.writerows(rows)

    pct = lambda a, b: f"{100 * a / b:.1f} %" if b else "n/a"
    ent_changes = tot["ent_deleted"] + tot["ent_added"] + tot["ent_retyped"]
    rel_changes = tot["rel_deleted"] + tot["rel_added"]
    rep = "\n".join([
        f"Units changed by the annotator: {tot['units_changed']}/{len(units)} ({pct(tot['units_changed'], len(units))})",
        f"Entities: pre-annotated {tot['ent_pre']}, final {tot['ent_final']}",
        f"  kept {tot['ent_kept']} | retyped {tot['ent_retyped']} | deleted {tot['ent_deleted']} | added {tot['ent_added']}",
        f"  correction rate = (retyped + deleted + added) / final = {pct(ent_changes, tot['ent_final'])}",
        f"Relations: pre-annotated {tot['rel_pre']}, final {tot['rel_final']}",
        f"  kept {tot['rel_kept']} | deleted {tot['rel_deleted']} | added {tot['rel_added']}",
        f"  correction rate = (deleted + added) / final = {pct(rel_changes, tot['rel_final'])}",
    ])
    open(os.path.join(out_dir, "correction_report.txt"), "w").write(rep + "\n")
    print(rep)


if __name__ == "__main__":
    main(*sys.argv[1:5])
