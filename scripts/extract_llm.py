"""
Section 3 - LLM component of the Entity Extraction Agent (open model, runs on a Colab GPU).

Model: Qwen2.5-7B-Instruct, 4-bit (bitsandbytes), greedy decoding (deterministic).
Prompt: the annotation guidelines (types, relations, conventions) + few-shot examples taken
from the DEVELOPMENT units only + the unit to annotate. The model answers in JSON; spans are
aligned to the unit text (exact, then case-insensitive); spans not found in the text are
discarded and logged. Every prompt and raw response is saved (prompt/response log).

  python extract_llm.py gold_test.jsonl gold_dev.jsonl pred_llm.jsonl log.jsonl [--gold-entities]

--gold-entities : the gold entities are given in the prompt and only relations are asked
                  (relation extraction evaluated independently of entity errors).
--pipeline      : production run on all units (used to build the ontology / knowledge graph; not evaluated).
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_common import (ENTITY_TYPES, RELATION_TYPES, dedup_relations, load_jsonl, locate,  # noqa: E402
                               norm, save_jsonl, select_non_overlapping)

MODEL_ID = os.environ.get("REG2CHAIN_LLM", "Qwen/Qwen2.5-7B-Instruct")
MAX_NEW_TOKENS = 1200
FEW_SHOT_IDS = ["ART3.1", "ART8.2", "ART7", "ART11.3", "ART10.d", "ANX1.A.8"]   # development units only

GUIDELINES = """You annotate provisions of Regulation (EU) 2022/2104 on olive oil marketing standards.

ENTITY TYPES (copy each entity EXACTLY as it appears in the text; no overlap; longest span with one type;
no leading 'the/a/an'; no final punctuation):
- PRODUCT: oil categories and other products (extra virgin olive oil, oils, blends, foodstuffs...). If a product
  is followed by 'referred to in <reference>', annotate the product alone and the reference as LEGAL_REF.
- PARAMETER: a measurable characteristic (acidity, peroxide value, K232, temperature, maximum capacity...).
- VALUE: a numeric limit or quantity with its operator/unit ('≤ 0,80', 'below 27 °C', 'more than 50 %').
- LABEL_ITEM: something that must/may/must not appear on the label (place of origin, harvesting year, legal name,
  a quoted mandatory wording kept with its quotes...).
- ACTOR: an organisation or role (Member States, Commission, final consumer, mill...).
- LEGAL_REF: a reference to a legal act or provision (Article 6(1), Annex I, Regulation (EU) No 1308/2013...).
- PROCESS: a production, extraction or packaging method or feature (percolation, centrifugation...).
Do not annotate the words 'label' or 'container', nor the header 'Annex I, Table A, quality characteristics of'.

RELATION TYPES (between two annotated entities of the same provision):
- OBLIGATION: subject must have/do/show object ('shall', 'must').
- PERMISSION: subject may have/do/show object, including restricted permissions ('may', 'may only').
- PROHIBITION: subject must not have/show object ('shall not', 'no ... shall').
- LIMIT: a PRODUCT has a limit VALUE for a PARAMETER (put the PARAMETER text in "qualifier").
- CONDITION: a permission/obligation on the subject applies only if the object (VALUE or PROCESS) holds
  (PARAMETER in "qualifier" if any).
- REFERS_TO: an entity is defined by / referred to in / determined in accordance with a LEGAL_REF.
If several products share a rule, write one relation per product.

Answer with JSON only:
{"entities": [{"text": "...", "type": "..."}],
 "relations": [{"subject": "...", "relation": "...", "object": "...", "qualifier": ""}]}"""

GOLD_ENT_INSTR = ("The entities of the provision are given below. Use ONLY these entities as subjects and objects "
                  "and return the relations (copy the entity texts exactly). Return {\"relations\": [...]}.")


def example_answer(g, relations_only=False):
    rels = [{"subject": r["subject"], "relation": r["predicate"], "object": r["object"],
             "qualifier": r.get("qualifier", "")} for r in g["relations"]]
    if relations_only:
        return json.dumps({"relations": rels}, ensure_ascii=False)
    ents = [{"text": e["text"], "type": e["label"]} for e in g["entities"]]
    return json.dumps({"entities": ents, "relations": rels}, ensure_ascii=False)


def user_msg(g, relations_only):
    msg = f"Provision:\n{g['sentence']}"
    if relations_only:
        ents = json.dumps([{"text": e["text"], "type": e["label"]} for e in g["entities"]], ensure_ascii=False)
        msg += f"\n\n{GOLD_ENT_INSTR}\nEntities: {ents}"
    return msg


def build_messages(g, shots, relations_only):
    msgs = [{"role": "system", "content": GUIDELINES}]
    for s in shots:
        msgs.append({"role": "user", "content": user_msg(s, relations_only)})
        msgs.append({"role": "assistant", "content": example_answer(s, relations_only)})
    msgs.append({"role": "user", "content": user_msg(g, relations_only)})
    return msgs


def parse_json(raw):
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def to_prediction(g, obj, relations_only):
    text, dropped = g["sentence"], []
    if relations_only:
        ents = g["entities"]
    else:
        cands = []
        for e in (obj or {}).get("entities", []):
            t, ty = str(e.get("text", "")).strip(), str(e.get("type", "")).upper()
            if ty not in ENTITY_TYPES or not t:
                dropped.append(("bad_type", t, ty))
                continue
            loc = locate(text, t, [(c["start"], c["end"]) for c in cands if c["text"] == t])
            if loc is None:
                dropped.append(("not_in_text", t, ty))
                continue
            cands.append({"text": text[loc[0]:loc[1]], "label": ty, "start": loc[0], "end": loc[1]})
        ents = select_non_overlapping(cands)
    names = {norm(e["text"]) for e in ents}
    rels = []
    for r in (obj or {}).get("relations", []):
        rel = str(r.get("relation", r.get("predicate", ""))).upper()
        s, o = str(r.get("subject", "")), str(r.get("object", ""))
        if rel in RELATION_TYPES and norm(s) in names and norm(o) in names:
            rels.append({"subject": s, "predicate": rel, "object": o, "qualifier": str(r.get("qualifier", "") or "")})
        else:
            dropped.append(("bad_relation", s, rel, o))
    return {"unit_id": g["unit_id"], "entities": ents, "relations": dedup_relations(rels)}, dropped


def load_model():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, device_map="auto",
        quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
                                               bnb_4bit_quant_type="nf4"))
    model.eval()
    return tok, model


def generate(tok, model, messages):
    import torch
    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS, do_sample=False, temperature=None,
                             top_p=None, top_k=None, pad_token_id=tok.eos_token_id)
    return prompt, tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def main(gold_path, dev_path, out_path, log_path, *flags):
    relations_only = "--gold-entities" in flags
    dev = {g["unit_id"]: g for g in load_jsonl(dev_path)}
    shots = [dev[i] for i in FEW_SHOT_IDS]
    gold = load_jsonl(gold_path)
    if "--pipeline" not in flags:   # evaluation runs: the few-shot units must never be evaluated
        assert not set(FEW_SHOT_IDS) & {g["unit_id"] for g in gold}, "few-shot examples must not be evaluated"
    preds = load_jsonl(out_path) if os.path.exists(out_path) else []      # resume after a disconnection
    logs = load_jsonl(log_path) if os.path.exists(log_path) else []
    done = {p["unit_id"] for p in preds}
    if done:
        print(f"Resuming: {len(done)} units already done")
    if len(done) == len(gold):
        print(f"all units already done -> {out_path}")
        return
    tok, model = load_model()
    t0 = time.time()
    for k, g in enumerate(gold, 1):
        if g["unit_id"] in done:
            continue
        prompt, raw = generate(tok, model, build_messages(g, shots, relations_only))
        obj = parse_json(raw)
        pred, dropped = to_prediction(g, obj, relations_only)
        preds.append(pred)
        logs.append({"unit_id": g["unit_id"], "model": MODEL_ID, "decoding": "greedy",
                     "max_new_tokens": MAX_NEW_TOKENS, "relations_only": relations_only,
                     "prompt": prompt, "response": raw, "parsed": obj is not None, "dropped": dropped})
        print(f"[{k}/{len(gold)}] {g['unit_id']}: {len(pred['entities'])} ent, {len(pred['relations'])} rel, "
              f"{len(dropped)} dropped, {time.time() - t0:.0f}s", flush=True)
        save_jsonl(preds, out_path)          # saved after every unit (safe if the session stops)
        save_jsonl(logs, log_path)
    print(f"LLM ({MODEL_ID}) -> {out_path}; log -> {log_path}")


if __name__ == "__main__":
    main(*sys.argv[1:])
