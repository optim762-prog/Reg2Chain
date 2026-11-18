"""
Section 8.2 - Blind expert review of a sample of generated contracts (blockchain developer).

  python expert_review.py build CONTRACTS_DIR UNITS_CSV OUT_DIR
      Stratified sample: 2 categories (extra virgin olive oil: richest set of limits and labelling
      obligations; olive-pomace oil: includes a prohibition) x run 1 x every (model, input) group.
      Contracts are shuffled (seed 2104) and renamed K01..Knn: the expert does not know the model
      or the input. The key is written to review_key.csv (not to be given to the expert).
      -> Reg2Chain_contract_review.xlsx (Instructions, Reference, Review, one sheet per contract)

  python expert_review.py build CONTRACTS_DIR UNITS_CSV OUT_DIR --batch=2 --start=15
                           --groups=qwen7b/D_json_solidity,qwen14b/D_json_solidity
                           [--add=qwen7b/B_json/ExtraVirginOliveOil] [--replaces=K04]
      Additional batch (same protocol, new ids). --add puts single contracts in the batch (e.g. a
      contract regenerated after the first review); --replaces marks the first-batch reviews that
      the new ones supersede (they are not scored).

  python expert_review.py score OUT_DIR [contract_results.csv]
      Reads every review_key*.csv and the matching *_reviewed.xlsx in OUT_DIR
      -> expert_review_summary.csv / .txt by (model, input), and the agreement between the expert's
         correctness scores and the automatic tests (Spearman correlation).
"""
import csv
import os
import random
import re
import statistics
import sys

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

SEED = 2104
CATEGORIES = ["ExtraVirginOliveOil", "OlivePomaceOil"]
RUN = "1"
HEAD, FILL = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="2F5496")
WRAP = Alignment(wrap_text=True, vertical="top")
MONO = Font(name="Consolas", size=10)

CRITERIA = [
    ("Q1_limits_correct", "1-5", "Quality limits (Annex I, Table A): values, operators and scaling (x1000) are correct for "
                                 "this category. 5 = all correct, 1 = mostly wrong."),
    ("Q2_labelling_correct", "1-5", "Labelling rules (Articles 4-12): mandatory items required, prohibited items rejected, "
                                    "permissions not turned into obligations. 5 = all correct."),
    ("Q3_missing_rules", "text", "Rules of the regulation for this category that are missing (list them, with article)."),
    ("Q4_invented_rules", "text", "Checks that are NOT in the regulation for this category (invented or wrong category)."),
    ("Q5_traceability", "1-5", "The '// source:' comments cite the right provision for each check. 5 = all right."),
    ("Q6_code_quality", "1-5", "Readability, structure, maintainability, gas-conscious code. 5 = production quality."),
    ("Q7_security_issue", "NONE/LOW/MEDIUM/HIGH", "Most severe security or design issue you see."),
    ("Q8_security_comment", "text", "Describe the issue(s), if any."),
    ("Q9_deployable", "YES/MINOR_CHANGES/NO", "Could this contract be deployed as it is for the stated purpose?"),
    ("Q10_minutes", "number", "Time spent on this contract (minutes)."),
]


def style_header(ws, widths):
    for i, w in enumerate(widths, start=1):
        c = ws.cell(row=1, column=i)
        c.font, c.fill, c.alignment = HEAD, FILL, WRAP
        ws.column_dimensions[c.column_letter].width = w
    ws.freeze_panes = "B2"


def build(contracts_dir, units_csv, out_dir, *flags):
    opts = dict(f[2:].split("=", 1) for f in flags if f.startswith("--") and "=" in f)
    batch = opts.get("batch", "1")
    suffix = "" if batch == "1" else f"_batch{batch}"
    os.makedirs(out_dir, exist_ok=True)
    if "groups" in opts:
        groups = [tuple(g.split("/")) for g in opts["groups"].split(",") if g]
    else:
        groups = sorted({(m, c) for m in os.listdir(contracts_dir) if os.path.isdir(os.path.join(contracts_dir, m))
                         and m != "logs" for c in os.listdir(os.path.join(contracts_dir, m))})
    sample = [(m, c, k) for m, c in groups for k in CATEGORIES
              if os.path.exists(os.path.join(contracts_dir, m, c, k, f"run{RUN}.sol"))]
    sample += [tuple(a.split("/")) for a in opts.get("add", "").split(",") if a]
    random.Random(SEED + int(batch) - 1).shuffle(sample)
    start = int(opts.get("start", 1))
    key = [{"review_id": f"K{i:02d}", "model": m, "condition": c, "category": k, "run": RUN,
            "replaces": opts.get("replaces", "") if (m, c, k) in [tuple(a.split("/")) for a in
                                                                   opts.get("add", "").split(",") if a] else ""}
           for i, (m, c, k) in enumerate(sample, start=start)]
    with open(os.path.join(out_dir, f"review_key{suffix}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(key[0]))
        w.writeheader()
        w.writerows(key)

    label = {"ExtraVirginOliveOil": "extra virgin olive oil", "OlivePomaceOil": "olive-pomace oil"}
    wb = Workbook()
    ws = wb.active
    ws.title = "Instructions"
    ws.column_dimensions["A"].width = 150
    lines = [
        "Reg2Chain - expert review of generated smart contracts (blind)",
        f"You review {len(key)} Solidity contracts (sheets {key[0]['review_id']}...{key[-1]['review_id']}). Each one checks the compliance of a batch "
        "of olive oil of ONE category with Commission Delegated Regulation (EU) 2022/2104.",
        "The contracts were generated automatically by different systems. You are not told which system produced which "
        "contract: please judge each one on its own, against the regulation (sheet 'Reference').",
        "Common interface: checkLimit(parameter, value) with value = measured value x 1000 (0.80 -> 800); "
        "checkLabelling(items) with the identifiers of the label items present; isCompliant(...) = both.",
        "Fill one row per contract in sheet 'Review' (columns Q1 to Q10). Scores 1-5: 1 = very poor, 3 = acceptable, "
        "5 = excellent. Use the drop-down lists where present.",
        "Work without AI tools. Please do not discuss the contracts with the other experts before you finish.",
        "Expected time: about 5 minutes per contract. Record your total time in the 'Log' sheet.",
        "",
        "Criteria:",
    ] + [f"  {n} ({t}): {d}" for n, t, d in CRITERIA]
    for r, line in enumerate(lines, start=1):
        c = ws.cell(row=r, column=1, value=line)
        c.alignment = WRAP
        if r == 1:
            c.font = Font(bold=True, size=14, color="2F5496")

    ref = wb.create_sheet("Reference")
    ref.append(["provision", "text"])
    style_header(ref, [26, 150])
    for u in csv.DictReader(open(units_csv, encoding="utf-8")):
        if re.match(r"ART(4|5|6|7|8|9|10|11|12)\b|ANX1\.A\.(1|8)$", u["unit_id"]):
            ref.append([u["unit_id"], u["text"]])
    for row in ref.iter_rows(min_row=2):
        for c in row:
            c.alignment = WRAP

    rv = wb.create_sheet("Review")
    rv.append(["review_id", "category"] + [n for n, _, _ in CRITERIA])
    style_header(rv, [10, 24] + [16, 16, 40, 40, 14, 14, 18, 40, 18, 10])
    for k in key:
        rv.append([k["review_id"], label[k["category"]]] + [""] * len(CRITERIA))
    n = len(key) + 1
    for col, vals in (("C", "1,2,3,4,5"), ("D", "1,2,3,4,5"), ("G", "1,2,3,4,5"), ("H", "1,2,3,4,5"),
                      ("I", "NONE,LOW,MEDIUM,HIGH"), ("K", "YES,MINOR_CHANGES,NO")):
        dv = DataValidation(type="list", formula1=f'"{vals}"', allow_blank=True)
        rv.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n}")
    for row in rv.iter_rows(min_row=2):
        for c in row:
            c.alignment = WRAP

    for k in key:
        src = open(os.path.join(contracts_dir, k["model"], k["condition"], k["category"], f"run{RUN}.sol"),
                   encoding="utf-8").read()
        s = wb.create_sheet(k["review_id"])
        s.append(["line", f"{k['review_id']} - contract for {label[k['category']]}"])
        style_header(s, [6, 160])
        for i, line in enumerate(src.splitlines(), start=1):
            s.append([i, line])
            c = s.cell(row=i + 1, column=2)
            c.font = MONO
            if line.startswith("="):
                c.data_type = "s"

    log = wb.create_sheet("Log")
    log.append(["field", "value"])
    for f_ in ["expert name", "expertise", "date", "total time (minutes)", "general comments"]:
        log.append([f_, ""])
    style_header(log, [26, 100])
    path = os.path.join(out_dir, f"Reg2Chain_contract_review{suffix}.xlsx")
    wb.save(path)
    print(f"{len(key)} contracts in the blind review workbook -> {path} (key: review_key{suffix}.csv, keep it private)")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def spearman(x, y):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def score(out_dir, results_csv=None, *rest):
    if out_dir.endswith(".xlsx"):                      # old call: score REVIEWED_XLSX OUT_DIR [results]
        out_dir, results_csv = results_csv, (rest[0] if rest else None)
    key, reviews = {}, []
    for kf in sorted(f for f in os.listdir(out_dir) if f.startswith("review_key") and f.endswith(".csv")):
        suffix = kf[len("review_key"):-len(".csv")]
        bkey = {k["review_id"]: k for k in csv.DictReader(open(os.path.join(out_dir, kf), encoding="utf-8"))}
        xlsx = os.path.join(out_dir, f"Reg2Chain_contract_review{suffix}_reviewed.xlsx")
        if not os.path.exists(xlsx):
            print(f"not reviewed yet: {xlsx}")
            continue
        key.update(bkey)
        rows = list(load_workbook(xlsx, data_only=True)["Review"].iter_rows(values_only=True))
        head = [str(h) for h in rows[0]]
        reviews += [dict(zip(head, r)) for r in rows[1:] if r and r[0] in bkey]
    replaced = {k.get("replaces") for k in key.values() if k.get("replaces")}
    reviews = [r for r in reviews if r["review_id"] not in replaced]
    auto = {}
    if results_csv and os.path.exists(results_csv):
        for r in csv.DictReader(open(results_csv, encoding="utf-8")):
            t = int(r["tests_total"] or 0)
            auto[(r["model"], r["condition"], r["category"], r["run"])] = int(r["tests_passed"] or 0) / t if t else 0.0
    groups = {}
    for r in reviews:
        k = key[r["review_id"]]
        groups.setdefault((k["model"], k["condition"]), []).append((r, k))
    out, lines = [], []
    for g, items in sorted(groups.items()):
        rr = [r for r, _ in items]
        row = {"model": g[0], "condition": g[1], "contracts": len(rr)}
        for n in ("Q1_limits_correct", "Q2_labelling_correct", "Q5_traceability", "Q6_code_quality"):
            v = [_num(r[n]) for r in rr if _num(r[n]) is not None]
            row[n] = f"{statistics.mean(v):.2f}" if v else "–"
        row["security_medium_high"] = sum(1 for r in rr if str(r["Q7_security_issue"]).upper() in ("MEDIUM", "HIGH"))
        row["deployable_yes_or_minor"] = sum(1 for r in rr if str(r["Q9_deployable"]).upper() in ("YES", "MINOR_CHANGES"))
        row["minutes"] = sum(_num(r["Q10_minutes"]) or 0 for r in rr)
        out.append(row)
        lines.append(" | ".join(f"{a}={b}" for a, b in row.items()))
    with open(os.path.join(out_dir, "expert_review_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    if auto:
        xs, ys = [], []
        for r in reviews:
            k = key[r["review_id"]]
            a = auto.get((k["model"], k["condition"], k["category"], k["run"]))
            q1, q2 = _num(r["Q1_limits_correct"]), _num(r["Q2_labelling_correct"])
            if a is not None and q1 is not None and q2 is not None:
                xs.append((q1 + q2) / 2)
                ys.append(a)
        if len(xs) > 2:
            lines.append(f"Agreement expert correctness (mean Q1,Q2) vs automatic test pass rate: "
                         f"Spearman rho = {spearman(xs, ys):.3f} (n={len(xs)})")
    lines.append(f"Total expert time: {sum(_num(r['Q10_minutes']) or 0 for r in reviews):.0f} min")
    with open(os.path.join(out_dir, "expert_review_summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    {"build": build, "score": score}[sys.argv[1]](*sys.argv[2:])
