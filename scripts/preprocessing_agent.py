"""
Section 2 - Preprocessing Agent.

Cleans and normalises each provision unit and adds linguistic annotations (sentences,
tokens, lemmas, POS, stop-word flags) while keeping the ORIGINAL text and character
offsets, so that every downstream extraction can be aligned with the gold standard.
Legal references (e.g. 'Article 8(1)', 'Annex I') are kept intact: no token is removed
from the text itself; stop-word removal is only a flag.

  python preprocessing_agent.py units.csv preprocessed_units.json
"""
import csv
import json
import re
import sys
import unicodedata

import spacy

MODALS = {"shall", "must", "may"}


def normalise(text):
    t = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", t).strip()


def main(units_csv, out_path):
    nlp = spacy.load("en_core_web_sm")
    units = list(csv.DictReader(open(units_csv, encoding="utf-8")))
    out = []
    for u in units:
        doc = nlp(u["text"])
        out.append({
            "unit_id": u["unit_id"], "article": u["article"], "split": u["split"],
            "original": u["text"], "normalised": normalise(u["text"]),
            "sentences": [{"text": s.text, "start": s.start_char, "end": s.end_char} for s in doc.sents],
            "tokens": [{"text": t.text, "lemma": t.lemma_, "pos": t.pos_, "dep": t.dep_,
                        "start": t.idx, "end": t.idx + len(t.text),
                        # obligation / condition words are never treated as stop words
                        "is_stop": bool(t.is_stop and t.lower_ not in MODALS | {"not", "no", "only"})}
                       for t in doc],
        })
    json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n_tok = sum(len(u["tokens"]) for u in out)
    print(f"Preprocessing Agent: {len(out)} units, {n_tok} tokens -> {out_path}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
