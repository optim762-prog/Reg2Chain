"""
Section 3 - Evaluation of entity and relation extraction against the gold standard (new Table 1).

Entities (micro-averaged over units, one-to-one matching):
  strict   : same start/end offsets and same type
  relaxed  : overlapping spans and same type
  untyped  : overlapping spans, type ignored (fair to systems with another label set)
Relations:
  strict   : same subject, relation type and object (normalised text); LIMIT also needs the qualifier
  relaxed  : same relation type, subject and object overlap (>= 50 % of tokens or containment)
95 % confidence intervals for F1 by bootstrap over units (1,000 resamples, fixed seed).

  python evaluate_extraction.py gold_test.jsonl OUT_DIR name=pred.jsonl [name=pred.jsonl ...]
"""
import csv
import os
import random
import re
import sys
from collections import Counter

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_common import load_jsonl, norm

TOK = re.compile(r"\w+|[^\w\s]")


def toks(s):
    return set(TOK.findall(norm(s)))


def text_overlap(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    if na == nb or na in nb or nb in na:
        return True
    ta, tb = toks(a), toks(b)
    return len(ta & tb) / max(1, min(len(ta), len(tb))) >= 0.5


def span_overlap(a, b):
    return a["start"] < b["end"] and b["start"] < a["end"]


ENT = {
    "strict": lambda g, p: g["start"] == p["start"] and g["end"] == p["end"] and g["label"] == p["label"],
    "relaxed": lambda g, p: span_overlap(g, p) and g["label"] == p["label"],
    "untyped": lambda g, p: span_overlap(g, p),
}
REL = {
    "strict": lambda g, p: (norm(g["subject"]), g["predicate"], norm(g["object"])) ==
                           (norm(p["subject"]), p["predicate"], norm(p["object"])) and
                           (g["predicate"] != "LIMIT" or norm(g.get("qualifier")) == norm(p.get("qualifier"))),
    "relaxed": lambda g, p: g["predicate"] == p["predicate"] and text_overlap(g["subject"], p["subject"])
                            and text_overlap(g["object"], p["object"]),
}


def match(gold, pred, same):
    used, tp = [False] * len(pred), 0
    for g in gold:
        for j, p in enumerate(pred):
            if not used[j] and same(g, p):
                used[j] = True
                tp += 1
                break
    return tp


def per_unit(gold, preds, key, same):
    out = []
    for g in gold:
        p = preds.get(g["unit_id"], {}).get(key, [])
        out.append((match(g[key], p, same), len(g[key]), len(p)))
    return out


def prf(counts):
    tp = sum(c[0] for c in counts); ng = sum(c[1] for c in counts); np_ = sum(c[2] for c in counts)
    p = tp / np_ if np_ else 0.0
    r = tp / ng if ng else 0.0
    return tp, np_ - tp, ng - tp, p, r, (2 * p * r / (p + r) if p + r else 0.0)


def bootstrap_ci(counts, n=1000, seed=2104):
    rnd = random.Random(seed)
    f1s = sorted(prf([counts[rnd.randrange(len(counts))] for _ in counts])[5] for _ in range(n))
    return f1s[int(0.025 * n)], f1s[int(0.975 * n) - 1]


def main(gold_path, out_dir, *specs):
    os.makedirs(out_dir, exist_ok=True)
    gold = load_jsonl(gold_path)
    print(f"Gold: {len(gold)} units, {sum(len(g['entities']) for g in gold)} entities, "
          f"{sum(len(g['relations']) for g in gold)} relations")
    rows = []
    for spec in specs:
        name, path = spec.split("=", 1)
        preds = {p["unit_id"]: p for p in load_jsonl(path)}
        missing = [g["unit_id"] for g in gold if g["unit_id"] not in preds]
        if missing:
            print(f"{name}: {len(missing)} units without prediction (counted as FN)")
        for task, key, settings in (("NER", "entities", ENT), ("RE", "relations", REL)):
            if task == "NER" and name.endswith("+gold-ents"):
                continue
            for s, fn in settings.items():
                c = per_unit(gold, preds, key, fn)
                tp, fp, fn_, p, r, f = prf(c)
                lo, hi = bootstrap_ci(c)
                rows.append([name, task, s, tp, fp, fn_, round(p, 3), round(r, 3), round(f, 3),
                             f"[{lo:.2f}, {hi:.2f}]"])
    hdr = ["system", "task", "setting", "TP", "FP", "FN", "P", "R", "F1", "F1 95% CI"]
    with open(os.path.join(out_dir, "table1_extraction.csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([hdr] + rows)
    print(f"\n{'system':<22}{'task':<5}{'setting':<9}{'TP':>5}{'FP':>5}{'FN':>5}{'P':>7}{'R':>7}{'F1':>7}  CI")
    for r in rows:
        print(f"{r[0]:<22}{r[1]:<5}{r[2]:<9}{r[3]:>5}{r[4]:>5}{r[5]:>5}{r[6]:>7.3f}{r[7]:>7.3f}{r[8]:>7.3f}  {r[9]}")
    with open(os.path.join(out_dir, "table1_extraction.tex"), "w", encoding="utf-8") as f:
        f.write("% system & task & setting & TP & FP & FN & P & R & F1 & 95% CI\n")
        for r in rows:
            f.write(" & ".join(str(x) for x in r).replace("_", "\\_") + " \\\\\n")

    # per-type F1 (strict entities) for each system
    types = sorted({e["label"] for g in gold for e in g["entities"]})
    per_type = []
    for spec in specs:
        name, path = spec.split("=", 1)
        if name.endswith("+gold-ents"):
            continue
        preds = {p["unit_id"]: p for p in load_jsonl(path)}
        row = [name]
        for t in types:
            c = [(match([e for e in g["entities"] if e["label"] == t],
                        [e for e in preds.get(g["unit_id"], {}).get("entities", []) if e["label"] == t],
                        ENT["relaxed"]),
                  sum(e["label"] == t for e in g["entities"]),
                  sum(e["label"] == t for e in preds.get(g["unit_id"], {}).get("entities", [])))
                 for g in gold]
            row.append(round(prf(c)[5], 3))
        per_type.append(row)
    with open(os.path.join(out_dir, "ner_f1_per_type_relaxed.csv"), "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["system"] + types] + per_type)
    print("\nRelaxed NER F1 per type:")
    print(f"{'system':<22}" + "".join(f"{t[:9]:>11}" for t in types))
    for row in per_type:
        print(f"{row[0]:<22}" + "".join(f"{v:>11.3f}" for v in row[1:]))


if __name__ == "__main__":
    main(*sys.argv[1:])
