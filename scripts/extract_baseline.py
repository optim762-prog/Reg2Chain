"""
Section 3 - Baseline: spaCy NER (labels mapped to the annotation scheme) + dependency-based RE.

spaCy's generic labels are mapped to the closest types of our scheme so that the comparison
is fair (the 'untyped' score in the evaluation additionally ignores types altogether).
Relations: for each verb with a subject and an object, the deontic type is derived from the
modal verb (shall/must -> OBLIGATION, may -> PERMISSION, negation -> PROHIBITION).

  python extract_baseline.py gold_test.jsonl pred_baseline.jsonl
"""
import sys

import spacy

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extraction_common import dedup_relations, load_jsonl, save_jsonl

LABEL_MAP = {"ORG": "ACTOR", "GPE": "ACTOR", "NORP": "ACTOR", "PERSON": "ACTOR",
             "LAW": "LEGAL_REF", "PRODUCT": "PRODUCT",
             "PERCENT": "VALUE", "QUANTITY": "VALUE", "CARDINAL": "VALUE", "MONEY": "VALUE"}


def chunk_of(tok, doc):
    for nc in doc.noun_chunks:
        if nc.start <= tok.i < nc.end:
            return nc
    return doc[tok.i:tok.i + 1]


def deontic(verb):
    kids = list(verb.children)
    neg = any(k.dep_ == "neg" for k in kids) or any(t.lower_ == "no" for t in verb.subtree if t.i < verb.i)
    modal = {k.lower_ for k in kids if k.dep_ == "aux"}
    if neg and modal & {"shall", "must", "may"}:
        return "PROHIBITION"
    if modal & {"shall", "must"}:
        return "OBLIGATION"
    if "may" in modal:
        return "PERMISSION"
    return None


def relations(doc):
    out = []
    for v in doc:
        if v.pos_ not in ("VERB", "AUX"):
            continue
        rel = deontic(v)
        if not rel:
            continue
        subj = [c for c in v.children if c.dep_ in ("nsubj", "nsubjpass")]
        objs = [c for c in v.children if c.dep_ in ("dobj", "attr")]
        objs += [p for c in v.children if c.dep_ == "prep" for p in c.children if p.dep_ == "pobj"]
        for s in subj:
            for o in objs:
                out.append({"subject": chunk_of(s, doc).text, "predicate": rel,
                            "object": chunk_of(o, doc).text, "qualifier": ""})
    return dedup_relations(out)


def main(gold_path, out_path):
    nlp = spacy.load("en_core_web_sm")
    preds = []
    for g in load_jsonl(gold_path):
        doc = nlp(g["sentence"])
        ents = [{"text": e.text, "label": LABEL_MAP[e.label_], "start": e.start_char, "end": e.end_char}
                for e in doc.ents if e.label_ in LABEL_MAP]
        preds.append({"unit_id": g["unit_id"], "entities": ents, "relations": relations(doc)})
    save_jsonl(preds, out_path)
    print(f"baseline: {sum(len(p['entities']) for p in preds)} entities, "
          f"{sum(len(p['relations']) for p in preds)} relations -> {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
