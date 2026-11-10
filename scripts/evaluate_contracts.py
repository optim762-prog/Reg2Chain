"""
Section 8 - Evaluation of the generated smart contracts (compilation, correctness, traceability, gas).

For every contract of step6_contracts/<model>/<condition>/<category>/run<k>.sol:
  1. raw compilation (solc 0.8.20, solc-js), no change to the code;
  2. documented, mechanical normalisation, then recompilation; every rule applied is logged:
       N1 missing SPDX line added             N2 missing pragma added
       N3 'external' -> 'public' when a function is called internally
       N4 'Stack too deep' -> compile with the IR pipeline (viaIR), code unchanged
     (no change to any rule, value, operator or identifier);
  3. functional tests on a local EVM (eth-tester / py-evm), with an oracle that does NOT come from
     the knowledge graph for the quality limits:
       - quality limits: the GOLD LIMIT relations of Annex I (manual annotation), two boundary tests
         per limit (value at the limit -> compliant, first value beyond -> non-compliant);
       - no invented limit: parameters without a gold limit for the category accept any value;
       - labelling: the expert-validated specification (refined KG, section 6): all mandatory items
         -> compliant, each mandatory item missing -> non-compliant, each prohibited item present ->
         non-compliant, optional (permitted) items present -> still compliant;
       - isCompliant: compliant batch -> true, one violated limit -> false;
  4. traceability: for each gold limit, the '// source:' (or @custom:source) comment closest above
     the line that tests the parameter must cite the right provision (Annex I, Table A, row k);
  5. gas: deployment gas and gas of isCompliant on the compliant batch (eth_estimateGas);
  6. Slither (static analysis) when the 'slither' command is available: findings by impact.

  python evaluate_contracts.py CONTRACTS_DIR QUERY_DIR GOLD_DEV GOLD_TEST OUT_DIR
Outputs: contract_results.csv (one line per contract), table3_contracts.csv/.tex (by model x
condition), normalisation_log.csv, slither_findings.csv.
"""
import csv
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_common import load_jsonl, norm  # noqa: E402

SOLC_VERSION = "0.8.20"
SCALE = 1000
COMPILE_JS = r"""
const solc = require('solc'); const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8'); const viaIR = process.argv[3] === '1';
const input = {language: 'Solidity', sources: {'c.sol': {content: src}},
  settings: {viaIR: viaIR, optimizer: {enabled: viaIR, runs: 200},
             outputSelection: {'*': {'*': ['abi', 'evm.bytecode.object']}}}};
console.log(JSON.stringify(JSON.parse(solc.compile(JSON.stringify(input)))));
"""
CONTRACT_PATH = re.compile(r"(?P<model>[^/]+)/(?P<condition>[^/]+)/(?P<category>[^/]+)/run(?P<run>\d+)\.sol$")


def ascii_id(x):
    return (x or "").replace("Δ", "Delta").replace("δ", "delta")


def compact(s):
    return re.sub(r"[^0-9a-z]", "", ascii_id(s or "").lower())


# ------------------------------------------------------------------ compilation
class Compiler:
    def __init__(self, workdir):
        self.dir = workdir
        if not os.path.exists(os.path.join(workdir, "node_modules", "solc")):
            subprocess.run(["npm", "install", "--silent", f"solc@{SOLC_VERSION}"], cwd=workdir, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.js = os.path.join(workdir, "compile.js")
        open(self.js, "w").write(COMPILE_JS)

    def compile(self, src, via_ir=False):
        with tempfile.NamedTemporaryFile("w", suffix=".sol", delete=False, dir=self.dir) as f:
            f.write(src)
        out = json.loads(subprocess.run(["node", self.js, f.name, "1" if via_ir else "0"], cwd=self.dir,
                                        capture_output=True, text=True, check=True).stdout)
        os.unlink(f.name)
        errors = [e for e in out.get("errors", []) if e["severity"] == "error"]
        warnings = [e for e in out.get("errors", []) if e["severity"] == "warning"]
        contracts = out.get("contracts", {}).get("c.sol", {})
        return {"ok": not errors and bool(contracts), "errors": [e["formattedMessage"] for e in errors],
                "warnings": len(warnings), "contracts": contracts}


def main_contract(contracts):
    """The contract exposing checkLimit (the generated code may contain helpers or libraries)."""
    for name, c in contracts.items():
        if any(x.get("name") == "checkLimit" for x in c["abi"]):
            return name, c
    return (next(iter(contracts.items())) if contracts else (None, None))


def normalise(src, compiler):
    """Mechanical fixes only; returns (src, via_ir, result, rules applied)."""
    rules = []
    if "SPDX-License-Identifier" not in src:
        src = "// SPDX-License-Identifier: MIT\n" + src
        rules.append("N1")
    if not re.search(r"pragma\s+solidity", src):
        src = re.sub(r"^(// SPDX[^\n]*\n)", r"\1pragma solidity ^0.8.20;\n", src, count=1)
        rules.append("N2")
    res = compiler.compile(src)
    if not res["ok"] and any("Undeclared identifier" in e or "external" in e for e in res["errors"]):
        src2 = re.sub(r"\)\s*external\b", ") public", src)
        src2 = src2.replace("calldata", "memory")
        res2 = compiler.compile(src2)
        if res2["ok"] or len(res2["errors"]) < len(res["errors"]):
            src, res = src2, res2
            rules.append("N3")
    via_ir = False
    if not res["ok"] and any("Stack too deep" in e for e in res["errors"]):
        res2 = compiler.compile(src, via_ir=True)
        if res2["ok"]:
            res, via_ir = res2, True
            rules.append("N4")
    return src, via_ir, res, rules


# ------------------------------------------------------------------ oracle
def split_value(v):
    m = re.match(r"\s*([<>≤≥=]+)\s*([0-9]+(?:[.,][0-9]+)?)", v or "")
    return (m.group(1), float(m.group(2).replace(",", "."))) if m else (None, None)


def singular(s):
    return " ".join(w[:-1] if w.endswith("s") and len(w) > 3 else w for w in norm(s).split())


def build_oracle(query_dir, gold_paths):
    specs = {s["category"]: s for s in json.load(open(os.path.join(query_dir, "compliance_all.json"),
                                                       encoding="utf-8"))}
    by_label = {singular(s["label"]): c for c, s in specs.items()}
    params = sorted({ascii_id(x["parameter"]) for s in specs.values() for x in s["quality_limits"]})
    oracle = {c: {"limits": [], "obligations": [], "prohibitions": [], "permissions": []} for c in specs}
    for g in [x for p in gold_paths for x in load_jsonl(p)]:
        if not g["unit_id"].startswith("ANX1.A."):
            continue
        row = g["unit_id"].split(".")[-1]
        for r in g["relations"]:
            cat = by_label.get(singular(r["subject"]))
            if r["predicate"] != "LIMIT" or not cat:
                continue
            op, val = split_value(r["object"])
            pid = [p for p in params if compact(p) == compact(r.get("qualifier", "")) or
                   (compact(r.get("qualifier", "")) and compact(r.get("qualifier", "")) in compact(p))]
            if op and pid:
                oracle[cat]["limits"].append({"parameter": pid[0], "op": op, "value": val,
                                              "source": f"Annex I, Table A, row {row}", "gold": r})
    for c, s in specs.items():
        lab = s["labelling"]
        oracle[c]["obligations"] = sorted({e["label_item_id"] for e in lab["obligations"] if e.get("label_item_id")})
        oracle[c]["prohibitions"] = sorted({e["label_item_id"] for e in lab["prohibitions"] if e.get("label_item_id")})
        oracle[c]["permissions"] = sorted({e["label_item_id"] for e in lab["permissions"] if e.get("label_item_id")}
                                          - set(oracle[c]["obligations"]) - set(oracle[c]["prohibitions"]))
    return oracle, params


def boundary_cases(lim):
    v = round(lim["value"] * SCALE)
    return {"≤": [(v, True), (v + 1, False)], "<": [(v - 1, True), (v, False)], "≥": [(v, True), (v - 1, False)],
            ">": [(v + 1, True), (v, False)], "=": [(v, True), (v + 1, False)]}[lim["op"]]


# ------------------------------------------------------------------ EVM tests
class EVM:
    def __init__(self):
        from web3 import EthereumTesterProvider, Web3
        self.w3 = Web3(EthereumTesterProvider())
        self.acct = self.w3.eth.accounts[0]

    def deploy(self, compiled):
        c = self.w3.eth.contract(abi=compiled["abi"], bytecode=compiled["evm"]["bytecode"]["object"])
        tx = c.constructor().transact({"from": self.acct, "gas": 29_000_000})
        rec = self.w3.eth.wait_for_transaction_receipt(tx)
        return self.w3.eth.contract(address=rec.contractAddress, abi=compiled["abi"]), rec.gasUsed


def call(fn):
    try:
        return bool(fn.call())
    except Exception:  # noqa: BLE001 - a revert is a failed test
        return None


def run_tests(contract, oracle, params):
    tests = []
    f = contract.functions
    names = {x["name"] for x in contract.abi if x.get("type") == "function"}
    if not {"checkLimit", "checkLabelling", "isCompliant"} <= names:
        return tests, None, sorted({"checkLimit", "checkLabelling", "isCompliant"} - names)
    for lim in oracle["limits"]:
        for value, expected in boundary_cases(lim):
            tests.append(("limit", f"{lim['parameter']} {lim['op']} {lim['value']} @ {value}", expected,
                          call(f.checkLimit(lim["parameter"], value))))
    limited = {lim["parameter"] for lim in oracle["limits"]}
    for p in params:
        if p not in limited and p != "PackagingCapacity":
            tests.append(("no_invented_limit", f"{p} @ 10^9", True, call(f.checkLimit(p, 10 ** 9))))
    full = list(oracle["obligations"])
    tests.append(("labelling", "all mandatory items", True, call(f.checkLabelling(full))))
    for item in oracle["obligations"]:
        tests.append(("labelling", f"missing {item}", False, call(f.checkLabelling([x for x in full if x != item]))))
    for item in oracle["prohibitions"]:
        tests.append(("labelling", f"prohibited {item}", False, call(f.checkLabelling(full + [item]))))
    if oracle["permissions"]:
        tests.append(("labelling", "optional items added", True, call(f.checkLabelling(full + oracle["permissions"]))))
    ok_p = [lim["parameter"] for lim in oracle["limits"]]
    ok_v = [boundary_cases(lim)[0][0] for lim in oracle["limits"]]
    tests.append(("isCompliant", "compliant batch", True, call(f.isCompliant(ok_p, ok_v, full))))
    if oracle["limits"]:
        bad_v = list(ok_v)
        bad_v[0] = boundary_cases(oracle["limits"][0])[1][0]
        tests.append(("isCompliant", "one limit violated", False, call(f.isCompliant(ok_p, bad_v, full))))
    gas = None
    try:
        gas = f.isCompliant(ok_p, ok_v, full).estimate_gas()
    except Exception:  # noqa: BLE001
        pass
    return tests, gas, []


# ------------------------------------------------------------------ traceability
SOURCE_RE = re.compile(r"(?://|\*|///)\s*(?:@custom:)?source\s*:?\s*(.+)", re.I)


def traceability(src, oracle):
    lines = src.splitlines()
    any_src, right = 0, 0
    for lim in oracle["limits"]:
        idx = [i for i, l in enumerate(lines) if f'"{lim["parameter"]}"' in l]
        cited = None
        for i in idx:
            for j in range(i, max(-1, i - 6), -1):
                m = SOURCE_RE.search(lines[j])
                if m:
                    cited = m.group(1)
                    break
            if cited:
                break
        if cited:
            any_src += 1
            row = lim["source"].rsplit(" ", 1)[-1]
            if re.search(r"Annex\s*I\b", cited) and re.search(rf"row\s*{row}\b", cited):
                right += 1
    n = len(oracle["limits"])
    return (any_src / n if n else None), (right / n if n else None)


# ------------------------------------------------------------------ slither
def slither(src, via_ir):
    if not shutil.which("slither"):
        return None
    d = tempfile.mkdtemp()
    p = os.path.join(d, "c.sol")
    with open(p, "w") as fh:
        fh.write(src)
    args = ["slither", p, "--json", "-"] + (["--solc-args", "--via-ir"] if via_ir else [])
    r = subprocess.run(args, capture_output=True, text=True, env=dict(os.environ, SOLC_VERSION=SOLC_VERSION))
    try:
        dets = json.loads(r.stdout)["results"].get("detectors", [])
    except Exception:  # noqa: BLE001
        return None
    shutil.rmtree(d, ignore_errors=True)
    return [(x["check"], x["impact"], x["confidence"]) for x in dets]


# ------------------------------------------------------------------ main
def paired_tests(rows, out_dir):
    """Wilcoxon signed-rank tests on the share of passed tests, paired by (category, run)."""
    try:
        from scipy.stats import wilcoxon
    except ImportError:
        return
    score = {(r["model"], r["condition"], r["category"], r["run"]):
             (r["tests_passed"] / r["tests_total"] if r["tests_total"] else 0.0) for r in rows}
    pairs = [(("qwen7b", "C_json_onto"), ("qwen7b", "A_text")), (("qwen7b", "B_json"), ("qwen7b", "A_text")),
             (("qwen7b", "C_json_onto"), ("qwen7b", "B_json")),
             (("qwen14b", "C_json_onto"), ("qwen14b", "A_text")), (("qwen14b", "B_json"), ("qwen14b", "A_text")),
             (("qwen14b", "C_json_onto"), ("qwen14b", "B_json")),
             (("qwen7b", "D_json_solidity"), ("qwen7b", "B_json")), (("qwen7b", "D_json_solidity"), ("qwen7b", "A_text")),
             (("qwen14b", "D_json_solidity"), ("qwen14b", "B_json")),
             (("qwen14b", "D_json_solidity"), ("qwen14b", "A_text")),
             (("qwen14b", "C_json_onto"), ("qwen7b", "C_json_onto")),
             (("qwen14b", "C_json_onto"), ("deepseek6.7b", "C_json_onto")),
             (("deepseek6.7b", "C_json_onto"), ("qwen7b", "C_json_onto"))]
    lines = []
    for a, b in pairs:
        keys = sorted({(k[2], k[3]) for k in score if k[:2] == a} & {(k[2], k[3]) for k in score if k[:2] == b})
        if not keys:
            continue
        xa = [score[a + k] for k in keys]
        xb = [score[b + k] for k in keys]
        diff = statistics.mean(xa) - statistics.mean(xb)
        try:
            p = wilcoxon(xa, xb).pvalue if any(x != y for x, y in zip(xa, xb)) else 1.0
        except ValueError:
            p = 1.0
        lines.append(f"{a[0]}/{a[1]} vs {b[0]}/{b[1]}: n={len(keys)} mean test pass {statistics.mean(xa):.3f} vs "
                     f"{statistics.mean(xb):.3f} (diff {diff:+.3f}), Wilcoxon p={p:.4f}")
    with open(os.path.join(out_dir, "contract_significance.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def mean_sd(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "–"
    return f"{statistics.mean(xs):.3f}" + (f" ± {statistics.stdev(xs):.3f}" if len(xs) > 1 else "")


def main(contracts_dir, query_dir, gold_dev, gold_test, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    work = os.path.join(tempfile.gettempdir(), "reg2chain_solc")   # node_modules outside Drive (faster)
    os.makedirs(work, exist_ok=True)
    compiler = Compiler(work)
    oracle, params = build_oracle(query_dir, [gold_dev, gold_test])
    print("Oracle: " + ", ".join(f"{c}: {len(o['limits'])} gold limits / {len(o['obligations'])} mandatory / "
                                 f"{len(o['prohibitions'])} prohibited" for c, o in oracle.items() if o["limits"]))
    evm = EVM()
    rows, norm_log, sl_rows, failures = [], [], [], []
    files = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(contracts_dir) for f in fs if f.endswith(".sol"))
    for path in files:
        m = CONTRACT_PATH.search(path.replace(os.sep, "/"))
        if not m:
            continue
        meta = m.groupdict()
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        raw = compiler.compile(src)
        nsrc, via_ir, res, rules = (src, False, raw, []) if raw["ok"] else normalise(src, compiler)
        if not raw["ok"]:
            norm_log.append({**meta, "rules": "+".join(rules) or "none", "compiles_after": res["ok"],
                             "first_error": (raw["errors"] or [""])[0].splitlines()[0][:200]})
        row = {**meta, "compile_raw": raw["ok"], "compile_normalised": res["ok"], "normalisation": "+".join(rules),
               "warnings": res["warnings"], "lines": len(src.splitlines())}
        tests, gas_call, missing = [], None, []
        if res["ok"]:
            name, comp = main_contract(res["contracts"])
            try:
                contract, gas_deploy = evm.deploy(comp)
                row["deploy"] = True
                row["gas_deploy"] = gas_deploy
                tests, gas_call, missing = run_tests(contract, oracle[meta["category"]], params)
            except Exception as ex:  # noqa: BLE001
                row["deploy"] = False
                row["deploy_error"] = str(ex)[:200]
        row["missing_functions"] = ",".join(missing)
        row["gas_isCompliant"] = gas_call
        for kind in ("limit", "no_invented_limit", "labelling", "isCompliant"):
            t = [x for x in tests if x[0] == kind]
            row[f"{kind}_pass"] = (sum(1 for x in t if x[3] == x[2]) / len(t)) if t else None
        row["tests_total"] = len(tests)
        row["tests_passed"] = sum(1 for x in tests if x[3] == x[2])
        row["all_tests_pass"] = bool(tests) and row["tests_passed"] == len(tests)
        row["trace_any"], row["trace_correct"] = traceability(src, oracle[meta["category"]])
        failures += [{**meta, "kind": k, "test": d, "expected": e, "got": g} for k, d, e, g in tests if g != e]
        sl = slither(nsrc, via_ir) if res["ok"] else None
        if sl is not None:
            row["slither_high_medium"] = sum(1 for _, imp, _ in sl if imp in ("High", "Medium"))
            row["slither_low_info"] = sum(1 for _, imp, _ in sl if imp not in ("High", "Medium"))
            sl_rows += [{**meta, "check": c, "impact": i, "confidence": cf} for c, i, cf in sl]
        rows.append(row)
        print(f"{meta['model']:13s} {meta['condition']:12s} {meta['category'][:30]:30s} run{meta['run']}: "
              f"raw={'OK' if raw['ok'] else 'ERR'} norm={'OK' if res['ok'] else 'ERR'} "
              f"tests={row['tests_passed']}/{row['tests_total']} trace={row['trace_correct']}")

    def dump(name, data):
        if not data:
            return
        keys = list(dict.fromkeys(k for d in data for k in d))
        with open(os.path.join(out_dir, name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(data)

    dump("contract_results.csv", rows)
    dump("normalisation_log.csv", norm_log)
    dump("test_failures.csv", failures)
    dump("slither_findings.csv", sl_rows)

    # Table 3: model x condition
    groups = list(dict.fromkeys((r["model"], r["condition"]) for r in rows))
    table = []
    for g in groups:
        rs = [r for r in rows if (r["model"], r["condition"]) == g]
        n = len(rs)
        table.append({
            "model": g[0], "condition": g[1], "contracts": n,
            "compile_raw": f"{sum(r['compile_raw'] for r in rs) / n:.3f}",
            "compile_normalised": f"{sum(r['compile_normalised'] for r in rs) / n:.3f}",
            "limit_tests": mean_sd([r["limit_pass"] for r in rs]),
            "no_invented_limit": mean_sd([r["no_invented_limit_pass"] for r in rs]),
            "labelling_tests": mean_sd([r["labelling_pass"] for r in rs]),
            "isCompliant_tests": mean_sd([r["isCompliant_pass"] for r in rs]),
            "all_tests_pass": f"{sum(r['all_tests_pass'] for r in rs) / n:.3f}",
            "traceability_correct": mean_sd([r["trace_correct"] for r in rs]),
            "gas_deploy": mean_sd([r.get("gas_deploy") for r in rs]).split(".")[0],
            "gas_isCompliant": mean_sd([r.get("gas_isCompliant") for r in rs]).split(".")[0],
            "slither_high_medium": mean_sd([r.get("slither_high_medium") for r in rs]),
        })
    dump("table3_contracts.csv", table)
    cols = ["model", "condition", "compile_raw", "compile_normalised", "limit_tests", "labelling_tests",
            "all_tests_pass", "traceability_correct", "gas_isCompliant"]
    tex = ["\\begin{tabular}{llrrrrrrr}", "\\toprule",
           "Model & Input & Comp. raw & Comp. norm. & Limit tests & Label tests & All pass & Trace. & Gas \\\\",
           "\\midrule"]
    tex += [" & ".join(str(t[c]).replace("_", "\\_").replace("±", "$\\pm$") for c in cols) + " \\\\" for t in table]
    tex += ["\\bottomrule", "\\end{tabular}"]
    with open(os.path.join(out_dir, "table3_contracts.tex"), "w") as fh:
        fh.write("\n".join(tex) + "\n")
    paired_tests(rows, out_dir)
    print()
    for t in table:
        print(" | ".join(f"{k}={v}" for k, v in t.items()))


if __name__ == "__main__":
    main(*sys.argv[1:])
