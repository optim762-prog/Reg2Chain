"""
Comparison of inputs and models for the generated contracts, with the product category as the
independent unit (the three runs of a category are not independent).

  python contract_mixed_effects.py step7_evaluation/contract_results.csv step7_evaluation

For each comparison, a linear mixed-effects model is fitted on the share of passed tests of each
contract (36 contracts: 2 settings x 6 categories x 3 runs):
    share ~ setting + (1 + setting | category)
so that the effect of the setting is tested against its variation between categories.
The p-values of the seven comparisons are corrected with the Holm method. As a sensitivity check,
the model with a random intercept only is also reported, together with the number of categories
in which the effect goes in each direction (category means over the three runs).

Outputs: contract_mixed_effects.csv and contract_mixed_effects.txt
"""
import os
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")

LABEL = {"A_text": "A", "B_json": "B", "C_json_onto": "C", "D_json_solidity": "D"}
COMPARISONS = [  # (model, input) of the first setting, then of the second one
    ("qwen7b", "B_json", "qwen7b", "A_text"),
    ("qwen14b", "B_json", "qwen14b", "A_text"),
    ("qwen7b", "C_json_onto", "qwen7b", "B_json"),
    ("qwen7b", "D_json_solidity", "qwen7b", "B_json"),
    ("qwen14b", "C_json_onto", "qwen7b", "C_json_onto"),
    ("qwen14b", "C_json_onto", "deepseek6.7b", "C_json_onto"),
    ("deepseek6.7b", "C_json_onto", "qwen7b", "C_json_onto"),
]


def share_of_passed_tests(df):
    total = df["tests_total"].fillna(0)
    passed = df["tests_passed"].fillna(0)
    return np.where(total > 0, passed / total.where(total > 0, 1), 0.0)  # a contract without tests counts 0


def fit(data, re_formula):
    m = smf.mixedlm("share ~ x", data, groups=data["category"], re_formula=re_formula)
    r = m.fit(reml=True, method=["lbfgs", "powell"])
    return r.params["x"], r.bse["x"], r.pvalues["x"]


def main(results_csv, out_dir):
    df = pd.read_csv(results_csv)
    df["share"] = share_of_passed_tests(df)
    rows = []
    for m1, c1, m2, c2 in COMPARISONS:
        a = df[(df.model == m1) & (df.condition == c1)].assign(x=1)
        b = df[(df.model == m2) & (df.condition == c2)].assign(x=0)
        data = pd.concat([a, b], ignore_index=True)
        diff = a.groupby("category").share.mean() - b.groupby("category").share.mean()
        est, se, p = fit(data, "~x")
        _, _, p_int = fit(data, "1")
        rows.append({"comparison": f"{m1} {LABEL[c1]} vs {m2} {LABEL[c2]}",
                     "mean_1": round(a.share.mean(), 3), "mean_2": round(b.share.mean(), 3),
                     "effect": round(est, 3), "se": round(se, 3),
                     "categories_up": int((diff > 0).sum()), "categories_down": int((diff < 0).sum()),
                     "categories_equal": int((diff == 0).sum()),
                     "p": p, "p_random_intercept_only": p_int})
    t = pd.DataFrame(rows)
    t["p_holm"] = multipletests(t["p"], method="holm")[1]
    t["p_holm_random_intercept_only"] = multipletests(t["p_random_intercept_only"], method="holm")[1]
    for c in ("p", "p_random_intercept_only", "p_holm", "p_holm_random_intercept_only"):
        t[c] = t[c].round(4)
    os.makedirs(out_dir, exist_ok=True)
    t.to_csv(os.path.join(out_dir, "contract_mixed_effects.csv"), index=False)
    lines = ["Share of passed tests: linear mixed-effects model share ~ setting + (1 + setting | category),",
             "7 comparisons, Holm correction (sensitivity: random intercept only).", ""]
    for r in t.itertuples():
        lines.append(f"{r.comparison:<32} {r.mean_1:.2f} vs {r.mean_2:.2f}  effect {r.effect:+.3f} (se {r.se:.3f})  "
                     f"categories +{r.categories_up}/-{r.categories_down}/={r.categories_equal}  "
                     f"p_holm {r.p_holm:.4f}  (random intercept only: {r.p_holm_random_intercept_only:.4f})")
    text = "\n".join(lines)
    with open(os.path.join(out_dir, "contract_mixed_effects.txt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main(*sys.argv[1:3])