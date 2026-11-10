"""
Section 3 - Statistical significance (paired bootstrap) and LLM error analysis.

1. Paired bootstrap over test units (10,000 resamples, fixed seed): for each comparison
   (hybrid vs rules, hybrid vs llm, hybrid vs baseline) and each setting, the F1 difference,
   its 95 % CI and a two-sided p-value (share of resamples where the difference changes sign).
2. LLM log analysis: entities/relations proposed by the model, kept, and discarded
   (span not found in the text = hallucinated span, invalid type, invalid relation),
   and the number of responses that were not valid JSON.

  python significance_and_errors.py gold_test.jsonl OUT_DIR preds_dir logs_dir
"""
import csv
import json
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evaluate_extraction import ENT, REL, per_unit, prf  # noqa: E402
from extraction_common import load_jsonl  # noqa: E402

N_BOOT, SEED = 10000, 2104
SETTINGS = [("NER", "entities", "strict", ENT["strict"]), ("NER", "entities", "relaxed", ENT["relaxed"]),
            ("RE", "relations", "strict", REL["strict"]), ("RE", "relations", "relaxed", REL["relaxed"])]
COMPARISONS = [("hybrid", "rules"), ("hybrid", "llm"), ("hybrid", "baseline"), ("llm", "rules")]


def paired_bootstrap(ca, cb):
    rnd, n = random.Random(SEED), len(ca)
    obs = prf(ca)[5] - prf(cb)[5]
    diffs = []
    for _ in range(N_BOOT):
        idx = [rnd.randrange(n) for _ in range(n)]
        diffs.append(prf([ca[i] for i in idx])[5] - prf([cb[i] for i in idx])[5])
    diffs.sort()
    lo, hi = diffs[int(0.025 * N_BOOT)], diffs[int(0.975 * N_BOOT) - 1]
    p = 2 * min(sum(d <= 0 for d in diffs), sum(d >= 0 for d in diffs)) / N_BOOT
    return obs, lo, hi, min(1.0, p)


def main(gold_path, out_dir, preds_dir, logs_dir):
    os.makedirs(out_dir, exist_ok=True)
    gold = load_jsonl(gold_path)
    files = {"baseline": "baseline_test.jsonl", "rules": "rules_test.jsonl", "llm": "llm_test.jsonl",
             "hybrid": "hybrid_test.jsonl"}
    preds = {k: {p["unit_id"]: p for p in load_jsonl(os.path.join(preds_dir, v))} for k, v in files.items()}
    rows = []
    print(f"Paired bootstrap ({N_BOOT} resamples over {len(gold)} test units)")
    print(f"{'comparison':<22}{'task':<5}{'setting':<9}{'ΔF1':>8}{'95% CI':>18}{'p':>8}")
    for a, b in COMPARISONS:
        for task, key, setting, fn in SETTINGS:
            d, lo, hi, p = paired_bootstrap(per_unit(gold, preds[a], key, fn), per_unit(gold, preds[b], key, fn))
            rows.append([f"{a} vs {b}", task, setting, round(d, 3), round(lo, 3), round(hi, 3), round(p, 4)])
            print(f"{a + ' vs ' + b:<22}{task:<5}{setting:<9}{d:>8.3f}   [{lo:6.3f}, {hi:6.3f}]{p:>8.4f}")
    with open(os.path.join(out_dir, "significance_paired_bootstrap.csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["comparison", "task", "setting", "delta_F1", "CI_low", "CI_high", "p_value"]] + rows)

    print("\nLLM output analysis (prompt/response logs)")
    report = []
    for name in ("llm_test_log.jsonl", "llm_test_gold_ents_log.jsonl"):
        path = os.path.join(logs_dir, name)
        if not os.path.exists(path):
            continue
        logs = load_jsonl(path)
        reasons = Counter(d[0] for l in logs for d in l["dropped"])
        proposed_e = kept_e = 0
        for l in logs:
            try:
                obj = json.loads(l["response"][l["response"].index("{"):l["response"].rindex("}") + 1])
                proposed_e += len(obj.get("entities", []))
            except (ValueError, json.JSONDecodeError):
                pass
        if "gold_ents" not in name:
            p = {x["unit_id"]: x for x in load_jsonl(os.path.join(preds_dir, "llm_test.jsonl"))}
            kept_e = sum(len(x["entities"]) for x in p.values())
        line = (f"{name}: {len(logs)} responses, {sum(not l['parsed'] for l in logs)} not valid JSON; "
                f"entities proposed {proposed_e}, kept {kept_e}, span not found in text (hallucinated) "
                f"{reasons.get('not_in_text', 0)}, invalid type {reasons.get('bad_type', 0)}; "
                f"relations discarded (argument not an entity / invalid type) {reasons.get('bad_relation', 0)}")
        report.append(line)
        print(line)
        if reasons.get("not_in_text"):
            ex = [d[1] for l in logs for d in l["dropped"] if d[0] == "not_in_text"][:8]
            print("   examples of discarded spans:", ex)
    open(os.path.join(out_dir, "llm_error_analysis.txt"), "w", encoding="utf-8").write("\n".join(report) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:5])
