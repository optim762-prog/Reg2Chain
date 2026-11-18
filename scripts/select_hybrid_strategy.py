"""
Section 3 - Select the hybrid fusion strategy on the DEVELOPMENT units (never on the test units).

Score = mean of relaxed NER F1 and relaxed RE F1 on the dev units that are not few-shot examples.

  python select_hybrid_strategy.py gold_dev_eval.jsonl pred_rules_dev.jsonl pred_llm_dev.jsonl OUT_DIR
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evaluate_extraction import ENT, REL, per_unit, prf  # noqa: E402
from extraction_common import load_jsonl  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main(gold_path, rules_path, llm_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    gold, scores = load_jsonl(gold_path), {}
    for st in ("patterns-first", "llm-first"):
        out = os.path.join(out_dir, f"pred_hybrid_dev_{st}.jsonl")
        subprocess.run([sys.executable, os.path.join(HERE, "combine_hybrid.py"), gold_path, rules_path, llm_path,
                        out, f"--strategy={st}"], check=True)
        preds = {p["unit_id"]: p for p in load_jsonl(out)}
        ner = prf(per_unit(gold, preds, "entities", ENT["relaxed"]))[5]
        re_ = prf(per_unit(gold, preds, "relations", REL["relaxed"]))[5]
        scores[st] = (ner + re_) / 2
        print(f"dev {st}: NER relaxed F1 = {ner:.3f}, RE relaxed F1 = {re_:.3f}, score = {scores[st]:.3f}")
    best = max(scores, key=scores.get)
    open(os.path.join(out_dir, "hybrid_strategy.txt"), "w").write(best + "\n")
    print(f"selected strategy (on dev): {best}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
