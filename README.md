# Reg2Chain: Bridging Regulations to Blockchain through Automated Smart Contract Generation

Code, data and results of the paper *Reg2Chain: Bridging Regulations to Blockchain through Automated
Smart Contract Generation*.

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
