"""
Section 7 - Prompt Engineering Agent + smart contract generation (open LLM, Colab T4).

Ablation of the input given to the LLM (what does the knowledge layer contribute?):
  A_text      : the regulation text only (all provisions, with their article numbers)
  B_json      : the compliance specification of the category (Regulatory Query Agent, section 6)
  C_json_onto : the compliance specification + an ontology excerpt (class hierarchy of the category
                and of its label items, properties, condition definitions)
  D_json_solidity : the compliance specification + the smart-contract ontology (Solidity ontology,
                Cano-Benito et al. 2021: classes and properties of the language), used to represent the
                rules as Solidity constructs; B vs D isolates the contribution of this ontology

The same fixed interface is required in every condition, so that all contracts can be tested by
the same oracle in section 8:
  checkLimit(string parameter, int256 value)      value = measured value x 1000 (0.80 -> 800)
  (all public pure; identifiers are ASCII, e.g. 'DeltaK' for ΔK; one '// source:' comment per check)
  checkLabelling(string[] items)                  identifiers of the label items present
  isCompliant(string[] parameters, int256[] values, string[] items)
The identifiers of the parameters and label items are the same list for every category and
condition (the union over all categories): the model must decide from its input which ones apply.

Several runs per (condition, category) with low-temperature sampling and a fixed seed per run;
every prompt and raw answer is logged (step6_contracts/logs/generation_log.jsonl), and the run
resumes where it stopped.

Model comparison: the main model (qwen7b) runs the full ablation; the other models run the
same prompts (--model=deepseek6.7b / --model=qwen14b), by default on the best condition.

  python contract_generator.py QUERY_DIR ONTOLOGY_JSON UNITS_CSV OUT_DIR [--model=qwen7b] [--runs=3]
                               [--conditions=A_text,B_json,C_json_onto,D_json_solidity]
                               [--solidity-ontology=data/solidity_ontology.ttl]
                               [--categories=ExtraVirginOliveOil,...] [--dry-run]
"""
import csv
import json
import os
import re
import sys
import time



def source_of(unit_id):
    """Same provision labels as the Ontology Agent (e.g. 'Article 8(1)', 'Annex I, Table A, row 1')."""
    m = re.match(r"ART(\d+)(?:\.(\d+))?(?:\.([a-h]|lead))?", unit_id)
    if m:
        s = f"Article {m.group(1)}" + (f"({m.group(2)})" if m.group(2) else "")
        return s + (f", point ({m.group(3)})" if m.group(3) and m.group(3) != "lead" else "")
    m = re.match(r"ANX1\.A\.(\d)", unit_id)
    return f"Annex I, Table A, row {m.group(1)}" if m else unit_id

MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"   # main model (full ablation)
# models compared (open weights, ungated, 4-bit on one GPU, T4 or L4); short name = output folder
MODELS = {"qwen7b": "Qwen/Qwen2.5-Coder-7B-Instruct",
          "deepseek6.7b": "deepseek-ai/deepseek-coder-6.7b-instruct",
          "qwen14b": "Qwen/Qwen2.5-Coder-14B-Instruct"}
MAX_NEW_TOKENS = 3000
TEMPERATURE, TOP_P = 0.2, 0.95
SEEDS = [11, 22, 33, 44, 55]
CONDITIONS = ["A_text", "B_json", "C_json_onto", "D_json_solidity"]
# Solidity ontology (Cano-Benito, Cimmino and Garcia-Castro, IEEE Access 2021), CC BY 4.0:
# https://github.com/oeg-upm/Solidity-ontology (ontology.ttl)
SOLIDITY_ONTOLOGY = "data/solidity_ontology.ttl"
# categories with at least one quality limit in the knowledge graph (lampante: classification
# condition only; crude olive-pomace oil: no rule) - see section 6
CATEGORIES = ["ExtraVirginOliveOil", "VirginOliveOil", "RefinedOliveOil",
              "OliveOilComposedOfRefinedOliveOilsAndVirginOliveOils", "RefinedOlivePomaceOil", "OlivePomaceOil"]

SYSTEM = ("You are an expert Solidity developer who writes regulatory-compliance smart contracts. "
          "You implement exactly the rules given in the input, nothing invented, and you answer with one "
          "Solidity code block only.")

INTERFACE = """Write ONE Solidity contract named `{name}Compliance` (pragma solidity ^0.8.20; SPDX MIT; no imports)
that checks the compliance of a batch of **{label}** with Commission Delegated Regulation (EU) 2022/2104.

The contract MUST expose exactly these functions (all `public pure`, so that `isCompliant` can call the other two):
```solidity
// Quality: `value` is the measured value multiplied by 1000 (e.g. 0.80 -> 800, 20.0 -> 20000).
// Returns true if the value satisfies the limit of this category for that parameter,
// and true if this category has no limit for that parameter.
function checkLimit(string memory parameter, int256 value) public pure returns (bool);
// Labelling: `items` are the identifiers of the label items present on the label.
// Returns false if a mandatory item is missing or a prohibited item is present.
function checkLabelling(string[] memory items) public pure returns (bool);
// Both checks together (parameters[i] measured as values[i]).
function isCompliant(string[] memory parameters, int256[] memory values, string[] memory items)
    public pure returns (bool);
```
Use only these identifiers (exact ASCII strings):
- quality parameters: {params}
- label items: {items}

Requirements:
1. Implement every limit, obligation and prohibition that applies to {label} according to the input, and only those.
2. Traceability: write a comment `// source: <provision>` on the line immediately above EACH individual check
   (one comment per limit, per obligation, per prohibition), with the provision the rule comes from, e.g.:
```solidity
        // source: <provision of this rule>
        if (keccak256(bytes(parameter)) == keccak256(bytes("<ParameterId>"))) return value <= <limit x 1000>;
```
3. Permissions and conditions that cannot be checked from these inputs must be documented in comments (with their source), not invented as checks.
4. The file must start with `// SPDX-License-Identifier: MIT` and `pragma solidity ^0.8.20;` and compile with solc 0.8.20 without errors.

INPUT:
{input}
"""


# ------------------------------------------------------------------ inputs of the four settings (A, B, C, D)
def regulation_text(units_csv):
    units = list(csv.DictReader(open(units_csv, encoding="utf-8")))
    return "\n".join(f"[{source_of(u['unit_id'])}] {u['text']}" for u in units)


def ontology_excerpt(onto, spec):
    concepts = {c["id"]: c for c in onto["concepts"]}

    def chain(cid):
        out, seen = [], set()
        while cid and cid not in seen:
            seen.add(cid)
            out.append(cid)
            cid = concepts.get(cid, {}).get("parent")
        return " ⊑ ".join(out)

    items = sorted({e["label_item_id"] for k in spec["labelling"].values() for e in k if e.get("label_item_id")})
    lines = ["Class hierarchy (⊑ = subClassOf):", f"- {chain(spec['category'])}"]
    lines += [f"- {chain(i)}" for i in items if i in concepts]
    lines.append("Object properties (domain -> range):")
    lines += [f"- {p['property']} ({p['relation_type']}): {p['domain']} -> {p['range']}" for p in onto["properties"]]
    used = {c["condition_id"] for k in spec["labelling"].values() for e in k for c in e.get("conditions", [])}
    used |= {c.get("condition_id") for c in spec.get("conditions", [])}
    conds = [c for c in onto.get("conditions", []) if c["condition_id"] in used]
    if conds:
        lines.append("Conditions (hasCondition):")
        lines += [f"- {c['condition_id']}: {c.get('condition_expression', '')}" for c in conds]
    return "\n".join(lines)


def ascii_id(x):
    """Solidity string literals must be ASCII (unless unicode"..."): ΔK -> DeltaK."""
    return (x or "").replace("Δ", "Delta").replace("δ", "delta")


def identifiers(query_dir):
    params, items = set(), set()
    for f in os.listdir(query_dir):
        if f.endswith(".json") and f != "compliance_all.json":
            s = json.load(open(os.path.join(query_dir, f), encoding="utf-8"))
            params |= {ascii_id(x["parameter"]) for x in s["quality_limits"] if x.get("parameter")}
            items |= {e["label_item_id"] for k in s["labelling"].values() for e in k if e.get("label_item_id")}
    return sorted(params), sorted(items)


def solidity_excerpt(ttl_path):
    """Compact text rendering of the Solidity ontology: classes (with superclasses), object properties
    and datatype properties (domain -> range)."""
    from rdflib import OWL, RDF, RDFS, Graph
    g = Graph()
    g.parse(ttl_path, format="turtle")

    def name(x):
        return str(x).rsplit("#", 1)[-1].rsplit("/", 1)[-1]

    lines = ["Classes (Class < superclasses):"]
    for c in sorted(set(g.subjects(RDF.type, OWL.Class)), key=name):
        if "#" not in str(c) and "/" not in str(c):
            continue
        sup = [name(x) for x in g.objects(c, RDFS.subClassOf) if ("#" in str(x) or "/" in str(x))]
        lines.append(f"- {name(c)}" + (f" < {', '.join(sorted(sup))}" if sup else ""))
    for title, kind in (("Object properties (domain -> range):", OWL.ObjectProperty),
                        ("Datatype properties (domain -> range):", OWL.DatatypeProperty)):
        lines.append(title)
        for p in sorted(set(g.subjects(RDF.type, kind)), key=name):
            dom = ",".join(sorted(name(x) for x in g.objects(p, RDFS.domain))) or "-"
            rng = ",".join(sorted(name(x) for x in g.objects(p, RDFS.range))) or "-"
            lines.append(f"- {name(p)}: {dom} -> {rng}")
    return "\n".join(lines)


def build_messages(condition, spec, reg_text, onto, params, items, solidity=None):
    compact = {k: v for k, v in spec.items() if k != "traceability"}
    compact["quality_limits"] = [dict(x, parameter=ascii_id(x.get("parameter", ""))) for x in compact["quality_limits"]]
    if condition == "A_text":
        inp = "Regulation text (provisions with their article numbers):\n" + reg_text
    elif condition == "B_json":
        inp = "Compliance specification (JSON):\n" + json.dumps(compact, ensure_ascii=False, indent=1)
    elif condition == "D_json_solidity":
        inp = ("Compliance specification (JSON):\n" + json.dumps(compact, ensure_ascii=False, indent=1) +
               "\n\nSmart-contract ontology (Solidity ontology): use it to determine how the compliance rules "
               "are represented as Solidity constructs.\n" + solidity)
    else:
        inp = ("Compliance specification (JSON):\n" + json.dumps(compact, ensure_ascii=False, indent=1) +
               "\n\nOntology excerpt:\n" + ontology_excerpt(onto, spec))
    user = INTERFACE.format(name=spec["category"], label=spec["label"], params=", ".join(params),
                            items=", ".join(items), input=inp)
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def extract_code(raw):
    blocks = re.findall(r"```(?:solidity|sol)?\s*\n(.*?)```", raw, flags=re.S)
    if blocks:
        return max(blocks, key=len).strip() + "\n"
    i = raw.find("// SPDX")
    return (raw[i:] if i >= 0 else raw).strip() + "\n"


# ------------------------------------------------------------------ model
def load_model(model_id):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, device_map="auto",
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                                               bnb_4bit_quant_type="nf4"))
    model.eval()
    return tok, model


def generate(tok, model, messages, seed):
    import torch
    torch.manual_seed(seed)
    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=True, temperature=TEMPERATURE,
                             top_p=TOP_P, pad_token_id=tok.eos_token_id)
    gen = out[0][inputs["input_ids"].shape[1]:]
    return tok.decode(gen, skip_special_tokens=True), int(inputs["input_ids"].shape[1]), int(gen.shape[0])


# ------------------------------------------------------------------ main
def main(query_dir, onto_path, units_csv, out_dir, *flags):
    opts = dict(f[2:].split("=", 1) for f in flags if f.startswith("--") and "=" in f)
    runs = int(opts.get("runs", 3))
    conditions = opts.get("conditions", ",".join(CONDITIONS)).split(",")
    categories = opts.get("categories", ",".join(CATEGORIES)).split(",")
    dry = "--dry-run" in flags
    short = opts.get("model", "qwen7b")
    model_id = MODELS[short]
    onto = json.load(open(onto_path, encoding="utf-8"))
    reg = regulation_text(units_csv)
    params, items = identifiers(query_dir)
    solidity = solidity_excerpt(opts.get("solidity-ontology", SOLIDITY_ONTOLOGY)) \
        if "D_json_solidity" in conditions else None
    os.makedirs(os.path.join(out_dir, "logs"), exist_ok=True)
    log_path = os.path.join(out_dir, "logs", "generation_log.jsonl")
    done = set()
    if os.path.exists(log_path):
        # a logged generation counts as done only if its prompt is the current one; generations made
        # with an earlier version of the prompt are moved to logs/stale_generations.jsonl and redone
        keep, stale = [], []
        for line in open(log_path, encoding="utf-8"):
            x = json.loads(line)
            spec_path = os.path.join(query_dir, x["category"] + ".json")
            same = x["condition"] != "D_json_solidity" or solidity is not None
            if same and os.path.exists(spec_path):
                cur = build_messages(x["condition"], json.load(open(spec_path, encoding="utf-8")), reg, onto,
                                     params, items, solidity)
                same = cur == x["messages"]
            (keep if same else stale).append(line)
        if stale and not dry:
            with open(os.path.join(out_dir, "logs", "stale_generations.jsonl"), "a", encoding="utf-8") as f:
                f.writelines(stale)
            with open(log_path, "w", encoding="utf-8") as f:
                f.writelines(keep)
            print(f"{len(stale)} generation(s) made with an earlier prompt moved to logs/stale_generations.jsonl")
        elif stale:
            print(f"{len(stale)} generation(s) made with an earlier prompt will be redone")
        for line in keep:
            x = json.loads(line)
            done.add((x["model"], x["condition"], x["category"], x["run"]))
    todo = [(c, k, r) for c in conditions for k in categories for r in range(1, runs + 1)
            if (model_id, c, k, r) not in done]
    print(f"{len(todo)} generations to do for {model_id} ({len(done)} generations already in the log)")
    if dry:
        spec = json.load(open(os.path.join(query_dir, categories[0] + ".json"), encoding="utf-8"))
        for c in conditions:
            m = build_messages(c, spec, reg, onto, params, items, solidity)
            open(os.path.join(out_dir, "logs", f"prompt_example_{c}.txt"), "w", encoding="utf-8").write(
                m[0]["content"] + "\n\n" + m[1]["content"])
            print(f"  {c}: prompt of {len(m[1]['content'])} characters -> logs/prompt_example_{c}.txt")
        return
    if not todo:
        return
    tok, model = load_model(model_id)
    for c, k, r in todo:
        spec = json.load(open(os.path.join(query_dir, k + ".json"), encoding="utf-8"))
        messages = build_messages(c, spec, reg, onto, params, items, solidity)
        t0 = time.time()
        raw, n_in, n_out = generate(tok, model, messages, SEEDS[r - 1])
        code = extract_code(raw)
        path = os.path.join(out_dir, short, c, k, f"run{r}.sol")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(code)
        rec = {"condition": c, "category": k, "run": r, "seed": SEEDS[r - 1], "model": model_id, "model_short": short,
               "temperature": TEMPERATURE, "top_p": TOP_P, "prompt_tokens": n_in, "output_tokens": n_out,
               "truncated": n_out >= MAX_NEW_TOKENS, "seconds": round(time.time() - t0, 1),
               "messages": messages, "raw": raw, "contract": path}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"{short} {c:12s} {k:55s} run{r}: {n_in} prompt tokens, {n_out} output tokens, {rec['seconds']} s"
              + (" (TRUNCATED)" if rec["truncated"] else ""))


if __name__ == "__main__":
    main(*sys.argv[1:])
