"""
Collect the artefacts of the study into one folder (and a zip) for the public GitHub repository.

  python export_repository.py NOTEBOOK.ipynb OUT_DIR

- scripts/      : every %%writefile cell of the notebook, so the code in the repository is
                  exactly the code that was run
- data/         : regulation text, provision units, gold standard (dev/test), annotation guidelines,
                  agreement and calibration reports, requirements checklist, Solidity ontology
- results/      : evaluation outputs (Tables 3 to 6 of the paper), extraction predictions and LLM logs
- artefacts/    : ontologies (OWL + JSON), knowledge graphs, compliance specifications,
                  generated contracts and the generation log (every prompt and raw answer)
- README.md, LICENSE, requirements.txt, SUMMARY.md (main numbers)
Annotator and review workbooks and credentials are not exported.
"""
import glob
import importlib
import json
import os
import re
import shutil
import sys

COPY = {
    "data": ["data/regulation_text.txt", "data/solidity_ontology.ttl",
             "step1_gold/units.csv", "step1_gold/gold/gold_dev.jsonl", "step1_gold/gold/gold_test.jsonl",
             "step1_gold/gold/agreement.txt", "step1_gold/gold/calibration_report.txt",
             "step1_gold/gold/correction_report.txt", "step1_gold/Reg2Chain_requirements_checklist.xlsx"],
    "results/extraction": ["step2_extraction/results/*", "step2_extraction/hybrid_strategy.txt"],
    "results/extraction/predictions": ["step2_extraction/preds/*"],
    "results/extraction/llm_logs": ["step2_extraction/logs/*"],
    "results/ontology": ["step3_ontology/refined/refinement_report.*", "step3_ontology/refined/schema_gaps.csv"],
    "results/kg": ["step4_kg/table2_kg_quality.csv", "step4_kg/coverage/coverage_report.txt"],
    "results/query": ["step5_query/query_evaluation.txt", "step5_query/algorithm1_cypher.txt"],
    "results/contracts": ["step7_evaluation/*.csv", "step7_evaluation/*.tex", "step7_evaluation/*.txt",
                          "step7_evaluation/expert_review/expert_review_summary.*",
                          "step7_evaluation/expert_review/review_key*.csv"],
    "artefacts/ontology": ["step3_ontology/learned/ontology_learned.*", "step3_ontology/refined/ontology_refined.*"],
    "artefacts/kg": ["step4_kg/kg_*.json"],
    "artefacts/compliance_specifications": ["step5_query/*.json"],
    "artefacts/contracts": ["step6_contracts"],
}
EXCLUDE = {"stale_generations.jsonl"}  # contract generated with an earlier prompt, replaced before evaluation

README = """# Reg2Chain: Bridging Regulations to Blockchain through Automated Smart Contract Generation

Code, data and results of the paper *Reg2Chain: Bridging Regulations to Blockchain through Automated
Smart Contract Generation* (Kohail, De Luzi, Grati, Boukadi and Mecella).

Reg2Chain turns a regulation into a knowledge graph and uses it to guide the generation of smart
contracts by open LLMs. The case study is Commission Delegated Regulation (EU) 2022/2104 on olive
oil marketing standards.

Pipeline: provision units -> entity and relation extraction (rules + Qwen2.5-7B-Instruct) ->
ontology learning (Text2Onto approach) and expert refinement -> knowledge graph (Neo4j) ->
regulatory query agent (Cypher) -> smart contract generation (Qwen2.5-Coder-7B/14B-Instruct,
deepseek-coder-6.7b-instruct) -> evaluation.

## Contents

| Folder | Content |
|---|---|
| `Reg2Chain_pipeline.ipynb` | the notebook that runs the whole pipeline and all evaluations, with its outputs |
| `scripts/` | every script of the notebook (written by its `%%writefile` cells) |
| `data/` | regulation text, the 63 provision units, the gold standard (16 development / 47 test units) and its annotation guidelines, the agreement and calibration reports, the requirements checklist (55 requirements), the Solidity ontology |
| `results/extraction/` | Table 3 (`table1_extraction.*`), relation extraction with gold entities, significance tests, predictions of every system and LLM logs |
| `results/ontology/` | expert refinement of the ontology (decisions, effort, schema gaps) |
| `results/kg/` | Table 4 (`table2_kg_quality.csv`) and coverage of the requirements checklist |
| `results/query/` | evaluation of the Regulatory Query Agent and its Cypher queries |
| `results/contracts/` | Table 5 (`table3_contracts.*`), per-contract results, normalisation log, Slither findings, significance tests, blind expert review (Table 6) and its key |
| `artefacts/` | learned and refined ontologies (OWL), knowledge graphs, compliance specifications, the 162 generated contracts (`contracts/<model>/<input>/<category>/run<k>.sol`) and `contracts/logs/generation_log.jsonl` (every prompt and raw model answer) |

File names follow the numbering of the notebook (Table 1 = extraction, Table 2 = knowledge graph,
Table 3 = contracts); in the paper these are Tables 3, 4 and 5.

## Running the pipeline

The notebook was run on Google Colab with one GPU (NVIDIA T4 or L4). Open `Reg2Chain_pipeline.ipynb`
in Colab, copy the repository to a Google Drive folder named `Reg2Chain_revision` and run the
sections in order; each section starts with a setup cell and can be resumed after a disconnection.
All models are open-weight models downloaded from Hugging Face and run locally in 4-bit.
Section 5 needs a Neo4j instance: its URI, user and password are read from the Colab Secrets
(`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`) and are not part of the repository.

## Licence

Code: MIT licence (see `LICENSE`). Data, annotations and results: CC BY 4.0.
The regulation text is reused under the EUR-Lex reuse policy; the Solidity ontology is from
Cano-Benito et al. (2021), *Toward the ontological modeling of smart contracts: a Solidity use case*.
"""

LICENSE = """MIT License

Copyright (c) 2026 The authors of Reg2Chain

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

REQUIREMENTS = """spacy==3.8.*
en_core_web_sm==3.8.0
transformers
accelerate
bitsandbytes
torch
rdflib
networkx
neo4j
openpyxl
pymupdf
scipy
web3[tester]
slither-analyzer
solc-select
# solc-js 0.8.20 (npm install solc@0.8.20) for compilation
"""


def scripts_from_notebook(nb_path, out):
    nb = json.load(open(nb_path, encoding="utf-8"))
    os.makedirs(out, exist_ok=True)
    n = 0
    for c in nb["cells"]:
        src = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
        m = re.match(r"%%writefile\s+(\S+)\n", src)
        if c["cell_type"] == "code" and m:
            with open(os.path.join(out, os.path.basename(m.group(1))), "w", encoding="utf-8") as f:
                f.write(src[m.end():])
            n += 1
    return n


def write_guidelines(path):
    """The annotation guidelines are defined in build_annotation_workbooks.py (sheet 'Guidelines')."""
    sys.path.insert(0, "scripts")
    try:
        rows = importlib.import_module("build_annotation_workbooks").GUIDELINES
    except Exception as e:  # keep the export going, but say so
        print("annotation guidelines not exported:", e)
        return
    lines = []
    for title, text in rows:
        lines.append(f"## {title}" if text is None else f"**{title}.** {text}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).replace("## Reg2Chain", "# Reg2Chain", 1))


def first_lines(path, n=12):
    if not os.path.exists(path):
        return f"(missing: {path})"
    with open(path, encoding="utf-8") as f:
        return "".join(f.readlines()[:n]).rstrip()


def main(nb_path, out_dir):
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    n = scripts_from_notebook(nb_path, os.path.join(out_dir, "scripts"))
    shutil.copy(nb_path, os.path.join(out_dir, os.path.basename(nb_path)))
    copied, missing = 0, []
    ignore = shutil.ignore_patterns(*EXCLUDE, "__pycache__")
    for dest, patterns in COPY.items():
        os.makedirs(os.path.join(out_dir, dest), exist_ok=True)
        for p in patterns:
            hits = [h for h in glob.glob(p) if os.path.basename(h) not in EXCLUDE]
            if not hits:
                missing.append(p)
            for h in hits:
                if os.path.isdir(h):
                    shutil.copytree(h, os.path.join(out_dir, dest), dirs_exist_ok=True, ignore=ignore)
                else:
                    shutil.copy(h, os.path.join(out_dir, dest))
                copied += 1
    write_guidelines(os.path.join(out_dir, "data", "annotation_guidelines.md"))
    for name, text in (("README.md", README), ("LICENSE", LICENSE), ("requirements.txt", REQUIREMENTS)):
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(text)
    summary = ["# Main results", "",
               "## Inter-annotator agreement", "```", first_lines("step1_gold/gold/agreement.txt"), "```",
               "## Table 3 of the paper - extraction (test units)", "```", first_lines("step2_extraction/results/table1_extraction.csv"), "```",
               "```", first_lines("step2_extraction/results/re_gold_entities.csv", 20), "```",
               "## Table 4 of the paper - knowledge graph", "```", first_lines("step4_kg/table2_kg_quality.csv", 20), "```",
               "## Coverage of the requirements", "```", first_lines("step4_kg/coverage/coverage_report.txt", 3), "```",
               "## Regulatory query agent", "```", first_lines("step5_query/query_evaluation.txt", 10), "```",
               "## Table 5 of the paper - contracts", "```", first_lines("step7_evaluation/table3_contracts.csv", 10), "```",
               "```", first_lines("step7_evaluation/contract_significance.txt", 12), "```",
               "## Table 6 of the paper - blind expert review", "```",
               first_lines("step7_evaluation/expert_review/expert_review_summary.txt", 12), "```"]
    with open(os.path.join(out_dir, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary) + "\n")
    n_sol = len(glob.glob(os.path.join(out_dir, "artefacts", "contracts", "**", "*.sol"), recursive=True))
    zip_path = shutil.make_archive(out_dir.rstrip("/"), "zip", out_dir)
    print(f"{n} scripts, {copied} files/folders copied, {n_sol} contracts -> {out_dir} ({zip_path})")
    if missing:
        print("not found (skipped):", ", ".join(missing))


if __name__ == "__main__":
    main(*sys.argv[1:3])
