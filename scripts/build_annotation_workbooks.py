"""
Step 1 - Build the annotation workbooks and the requirements checklist.

Outputs (in the output folder):
  Reg2Chain_annotation_A1.xlsx      annotator 1, all 63 units (dev + test)
  Reg2Chain_annotation_A2.xlsx      annotator 2, only the double-annotated test units
  Reg2Chain_requirements_checklist.xlsx   legal expert: validate / edit / delete / add

Usage: python build_annotation_workbooks.py units.csv OUT_DIR
"""
import csv
import os
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ENTITY_TYPES = ["PRODUCT", "PARAMETER", "VALUE", "LABEL_ITEM", "ACTOR", "LEGAL_REF", "PROCESS"]
RELATION_TYPES = ["OBLIGATION", "PERMISSION", "PROHIBITION", "LIMIT", "CONDITION", "REFERS_TO"]

HEAD = Font(bold=True, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="2F5496")
WRAP = Alignment(wrap_text=True, vertical="top")

GUIDELINES = [
    ("Reg2Chain annotation guidelines (v1.0)", None),
    ("Purpose", "Build an independent gold standard for entity and relation extraction from "
                "Regulation (EU) 2022/2104. Annotate from the text only. Do not look at any system output."),
    ("Unit", "One provision unit = one numbered paragraph (or one lettered point of a long paragraph) "
             "of Articles 1-14, or one linearised row of Annex I, Table A. Annotate each unit on its own."),
    ("How to annotate an entity", "In sheet 'Entities', add one row per entity: unit_id, the entity text COPIED EXACTLY "
                                  "from the unit (same spelling, spaces, quotes), and its type. Leave 'occurrence' at 1. "
                                  "Use 2, 3... only if the same entity text appears several times as separate entities "
                                  "(text inside a longer entity, e.g. 'virgin olive oil' inside 'extra virgin olive oil', "
                                  "is not counted)."),
    ("No overlap", "Entities never overlap or nest. Take the longest span that still has a single type. "
                   "Example: 'oils referred to in Article 1, point (b)' is ONE PRODUCT (do not also mark "
                   "'Article 1, point (b)' as LEGAL_REF)."),
    ("Spans", "Exclude leading articles (the, a, an) and final punctuation. Keep quotes for quoted label texts."),
    ("Entity types", None),
    ("PRODUCT", "Olive-oil categories and other products: extra virgin olive oil; virgin olive oil; lampante olive oil; "
                "refined olive oil; olive oil composed of refined olive oils and virgin olive oils; crude olive-pomace oil; "
                "refined olive-pomace oil; olive-pomace oil; blends of olive oil and other vegetable oils; foodstuffs; "
                "groups such as 'oils referred to in Article 1, point (b)'."),
    ("PARAMETER", "A measurable characteristic: acidity, peroxide value, K232, K268 or K270, ΔK, median of defect, "
                  "fruity median, fatty acid ethyl esters, wax content, ultraviolet absorption, temperature, "
                  "maximum capacity, percentage of oil."),
    ("VALUE", "A numeric limit or quantity, with its operator and unit: '≤ 0,80', 'five litres', '27 °C' "
              "(write 'below 27 °C' if 'below' is part of the condition), 'more than 50 %', '100 %'."),
    ("LABEL_ITEM", "Something that must / may / must not appear on the label or container: legal name, category "
                   "information, place of origin, harvesting year, storage conditions information, alphanumeric "
                   "identification of the packaging plant, 'first cold pressing', 'cold extraction', organoleptic "
                   "characteristics, trade description, a quoted mandatory wording."),
    ("ACTOR", "An organisation or role: Member States, Commission, final consumer, packaging plant, mill, "
              "restaurants/hospitals/canteens (collective establishments), panel leader."),
    ("LEGAL_REF", "A reference to a legal act or provision when it is not part of a PRODUCT span: "
                  "'Regulation (EU) No 1308/2013', 'Commission Implementing Regulation (EU) 2022/2105', 'Article 6(1)', "
                  "'Annex I'. Take the maximal reference ('Part VIII, point 1(a), of Annex VII to Regulation (EU) No 1308/2013')."),
    ("PROCESS", "A production, extraction or packaging method or feature: mechanical means, refining, first mechanical "
                "pressing, percolation, centrifugation, hydraulic presses, opening system that can no longer be sealed."),
    ("Relation types (between two entities already annotated in the same unit)", None),
    ("OBLIGATION", "subject must have / do / show object ('shall', 'must', 'mandatory'). "
                   "Ex.: (extra virgin olive oil, OBLIGATION, place of origin) in Art. 8(1)."),
    ("PERMISSION", "subject may have / do / show object, including restricted permissions ('may only', 'may appear "
                   "only for'). Ex.: (extra virgin olive oil, PERMISSION, harvesting year) in Art. 11(1)."),
    ("PROHIBITION", "subject must not have / show object ('shall not', 'no ... shall'). "
                    "Ex.: (olive-pomace oil ..., PROHIBITION, place of origin) in Art. 8(2)."),
    ("LIMIT", "a PRODUCT has a limit VALUE for a PARAMETER. Subject = PRODUCT, object = VALUE, and write the "
              "PARAMETER text in the 'qualifier' column. Ex.: (extra virgin olive oil, LIMIT, ≤ 0,80, qualifier: Acidity (%))."),
    ("CONDITION", "a permission/obligation on the subject applies only if the object holds. Subject = LABEL_ITEM or "
                  "PRODUCT, object = VALUE or PROCESS; PARAMETER in 'qualifier' if any. "
                  "Ex.: ('first cold pressing', CONDITION, below 27 °C, qualifier: temperature)."),
    ("REFERS_TO", "an entity is defined by / determined in accordance with a LEGAL_REF. "
                  "Ex.: (characteristics of olive oils, REFERS_TO, Commission Implementing Regulation (EU) 2022/2105)."),
    ("Several subjects", "If the provision lists several products ('extra virgin olive oil and virgin olive oil'), "
                         "annotate one entity per product and one relation per product."),
    ("Unsure?", "Write your doubt in 'notes' and annotate your best choice. Do not leave a unit unannotated: "
                "if a unit has no entity, add one row with unit_id and type 'NONE'."),
    ("Time", "About 4-5 minutes per unit. Please record your total time in the 'Log' sheet."),
]


def style_header(ws, widths):
    for i, w in enumerate(widths, start=1):
        c = ws.cell(row=1, column=i)
        c.font, c.fill, c.alignment = HEAD, HEAD_FILL, WRAP
        ws.column_dimensions[c.column_letter].width = w
    ws.freeze_panes = "A2"


def add_list_validation(ws, col, values, rows=2000):
    dv = DataValidation(type="list", formula1='"' + ",".join(values) + '"', allow_blank=True,
                        showErrorMessage=True, errorTitle="Invalid value",
                        error="Choose a value from the list.")
    ws.add_data_validation(dv)
    dv.add(f"{col}2:{col}{rows}")


def add_ref_validation(ws, col, ref, rows=2000):
    dv = DataValidation(type="list", formula1=ref, allow_blank=True, showErrorMessage=True,
                        errorTitle="Unknown unit", error="Choose a unit_id from the 'Units' sheet.")
    ws.add_data_validation(dv)
    dv.add(f"{col}2:{col}{rows}")


def guidelines_sheet(wb):
    ws = wb.active
    ws.title = "Guidelines"
    ws.column_dimensions["A"].width = 28
    ws.column_dimensions["B"].width = 120
    for r, (k, v) in enumerate(GUIDELINES, start=1):
        a = ws.cell(row=r, column=1, value=k)
        a.alignment = WRAP
        if v is None:
            a.font = Font(bold=True, size=12 if r > 1 else 14, color="2F5496")
        else:
            a.font = Font(bold=True)
            ws.cell(row=r, column=2, value=v).alignment = WRAP


def annotation_workbook(units, path, annotator):
    wb = Workbook()
    guidelines_sheet(wb)

    ws = wb.create_sheet("Units")
    ws.append(["unit_id", "article", "title", "text"])
    for u in units:
        ws.append([u["unit_id"], u["article"], u["title"], u["text"]])
    style_header(ws, [14, 10, 34, 130])
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = WRAP
    n = len(units) + 1
    unit_ref = f"=Units!$A$2:$A${n}"

    ents = wb.create_sheet("Entities")
    ents.append(["unit_id", "entity_text (copy exactly)", "type", "occurrence", "notes"])
    style_header(ents, [14, 70, 16, 12, 50])
    add_ref_validation(ents, "A", unit_ref)
    add_list_validation(ents, "C", ENTITY_TYPES + ["NONE"])

    rels = wb.create_sheet("Relations")
    rels.append(["unit_id", "subject_text", "relation", "object_text", "qualifier (PARAMETER, optional)", "notes"])
    style_header(rels, [14, 50, 16, 50, 30, 40])
    add_ref_validation(rels, "A", unit_ref)
    add_list_validation(rels, "C", RELATION_TYPES)

    log = wb.create_sheet("Log")
    log.append(["field", "value"])
    for k in ["annotator name", "role / expertise", "date(s)", "total time (minutes)", "comments"]:
        log.append([k, ""])
    style_header(log, [28, 80])
    if annotator == "A1":
        log.append(["", ""])
        log.append(["note", "A1 annotates ALL units (dev + test)."])
    else:
        log.append(["", ""])
        log.append(["note", "A2 annotates only these units, independently of A1."])

    wb.save(path)


# --------------------------------------------------------------------------
# Requirements checklist (drafted from the text; to be validated by the legal expert)
# Columns: id, provision, applies_to, type, requirement, on-chain
#   on-chain: DATA   = checkable from data submitted to the contract
#             ORACLE = needs certified off-chain input (lab, panel, sensor, inspector)
#             OFF    = not meaningfully enforceable on-chain (physical / visual / legal)
# --------------------------------------------------------------------------
CONSUMER = "consumer oils (EVOO, virgin, composed oil, olive-pomace oil)"
LIMITS = {
    "extra virgin olive oil": [("acidity (%)", "≤ 0,80"), ("peroxide value (mEq O2/kg)", "≤ 20,0"),
                               ("K232", "≤ 2,50"), ("K268 or K270", "≤ 0,22"), ("ΔK", "≤ 0,01"),
                               ("median of defect (Md)", "= 0,0"), ("fruity median (Mf)", "> 0,0"),
                               ("fatty acid ethyl esters (mg/kg)", "≤ 35")],
    "virgin olive oil": [("acidity (%)", "≤ 2,0"), ("peroxide value (mEq O2/kg)", "≤ 20,0"),
                         ("K232", "≤ 2,60"), ("K268 or K270", "≤ 0,25"), ("ΔK", "≤ 0,01"),
                         ("median of defect (Md)", "≤ 3,5"), ("fruity median (Mf)", "> 0,0")],
    "olive oil composed of refined olive oils and virgin olive oils": [
        ("acidity (%)", "≤ 1,00"), ("peroxide value (mEq O2/kg)", "≤ 15,0"),
        ("K268 or K270", "≤ 1,15"), ("ΔK", "≤ 0,15")],
    "olive-pomace oil": [("acidity (%)", "≤ 1,00"), ("peroxide value (mEq O2/kg)", "≤ 15,0"),
                         ("K268 or K270", "≤ 1,70"), ("ΔK", "≤ 0,18")],
}

OTHER_REQS = [
    ("Art. 2(1), Annex I", "all 8 categories", "DEFINITION",
     "An oil belongs to a category only if it meets the characteristics of that category in Annex I, Tables A and B.", "ORACLE"),
    ("Art. 3(1)", CONSUMER, "CONSTRAINT",
     "Only consumer oils may be part of blends of olive oil and other vegetable oils.", "DATA"),
    ("Art. 3(2)", CONSUMER, "CONSTRAINT", "Only consumer oils may be incorporated in other foodstuffs.", "DATA"),
    ("Art. 4(1)", CONSUMER, "OBLIGATION",
     "Packaging presented to the final consumer has a maximum capacity of five litres.", "DATA"),
    ("Art. 4(1)", CONSUMER, "OBLIGATION",
     "Packaging is fitted with an opening system that can no longer be sealed after first opening.", "OFF"),
    ("Art. 4(2)", CONSUMER, "PERMISSION",
     "For restaurants, hospitals, canteens and similar establishments, Member States may allow packaging above five litres.", "DATA"),
    ("Art. 5(1)", CONSUMER, "OBLIGATION",
     "The particulars of Articles 6 to 9 (legal name/category, storage, origin, packaging plant) are mandatory on the label.", "DATA"),
    ("Art. 5(2)", CONSUMER, "OBLIGATION",
     "Legal name and place of origin are grouped in the principal field of vision, in full and in a homogeneous body of text.", "OFF"),
    ("Art. 6(2)", CONSUMER, "OBLIGATION",
     "The label bears the category information text prescribed for the category (e.g. EVOO: 'superior category olive oil "
     "obtained directly from olives and solely by mechanical means').", "DATA"),
    ("Art. 7", CONSUMER, "OBLIGATION",
     "The container or label states that the oil must be stored away from light and heat.", "DATA"),
    ("Art. 8(1)", "extra virgin olive oil, virgin olive oil", "OBLIGATION", "The place of origin appears on the label.", "DATA"),
    ("Art. 8(2)", "composed oil, olive-pomace oil", "PROHIBITION", "No place of origin is displayed on the label.", "DATA"),
    ("Art. 8(3)", "extra virgin olive oil, virgin olive oil", "CONSTRAINT",
     "Place of origin is only: a Member State / the Union / a third country; one of the three prescribed blend indications; "
     "or a PDO/PGI.", "DATA"),
    ("Art. 8(6)", "extra virgin olive oil, virgin olive oil", "OBLIGATION",
     "An origin naming a Member State or the Union corresponds to where olives were harvested and where the mill is.", "ORACLE"),
    ("Art. 8(7)", "extra virgin olive oil, virgin olive oil", "OBLIGATION",
     "If harvest country differs from mill country, the origin uses the prescribed wording "
     "('... obtained in X from olives harvested in Y').", "DATA"),
    ("Art. 8(5)", "imported oils", "OBLIGATION",
     "For imports, origin is determined under Articles 59-63 of Regulation (EU) No 952/2013.", "OFF"),
    ("Art. 9", CONSUMER, "OBLIGATION",
     "Where applicable, the label bears the alphanumeric identification of the approved packaging plant.", "DATA"),
    ("Art. 10(a)", "extra virgin olive oil, virgin olive oil", "CONDITIONAL PERMISSION",
     "'First cold pressing' only if obtained below 27 °C by a first mechanical pressing with hydraulic presses.", "ORACLE"),
    ("Art. 10(b)", "extra virgin olive oil, virgin olive oil", "CONDITIONAL PERMISSION",
     "'Cold extraction' only if obtained below 27 °C by percolation or centrifugation.", "ORACLE"),
    ("Art. 10(c)", "extra virgin olive oil, virgin olive oil", "CONDITIONAL PERMISSION",
     "Organoleptic indications only for EVOO/virgin and only if based on the official panel assessment (Annex II ranges).", "ORACLE"),
    ("Art. 10(d)", CONSUMER, "CONDITIONAL OBLIGATION",
     "If maximum acidity is indicated, maximum peroxide, wax content and UV absorption values are shown alongside.", "DATA"),
    ("Art. 11(1)", "extra virgin olive oil, virgin olive oil", "RESTRICTED PERMISSION",
     "Only EVOO and virgin olive oil may bear the harvesting year.", "DATA"),
    ("Art. 11(2)", "extra virgin olive oil, virgin olive oil", "CONDITIONAL PERMISSION",
     "Harvesting year only if 100 % of the contents come from that harvest; shown as marketing year or month + year.", "ORACLE"),
    ("Art. 11(3)", "Member States", "PERMISSION",
     "Member States may make the harvesting year mandatory for domestic production sold on their national market.", "DATA"),
    ("Art. 12(1)", "blends", "CONDITIONAL OBLIGATION",
     "If olive oil is highlighted outside the ingredients list, the blend bears the prescribed trade description and the percentage.", "DATA"),
    ("Art. 12(2)", "blends", "CONDITIONAL PERMISSION",
     "Images or graphics may highlight olive oil only if it is more than 50 % of the blend.", "DATA"),
    ("Art. 12(3)", "foodstuffs", "CONDITIONAL OBLIGATION",
     "If olive oil is highlighted outside the ingredients list, the food name is followed by the percentage of oil.", "DATA"),
    ("Art. 12(6)", "foodstuffs", "PROHIBITION",
     "Oils with other foodstuffs added do not bear any of the legal names of Article 6.", "DATA"),
]


def checklist_rows():
    rows, n = [], 1
    for cat, lims in LIMITS.items():
        for param, val in lims:
            rows.append([f"R{n:02d}", "Annex I, Table A", cat, "LIMIT", f"{param} {val}", "ORACLE"])
            n += 1
    for prov, applies, typ, req, chain in OTHER_REQS:
        rows.append([f"R{n:02d}", prov, applies, typ, req, chain])
        n += 1
    return rows


def checklist_workbook(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Instructions"
    ws.column_dimensions["A"].width = 140
    for r, line in enumerate([
        "Reg2Chain - requirements checklist (gold reference for KG coverage and contract coverage)",
        "Scope: the four categories sold to the final consumer (Art. 1(b)) and the labelling/marketing rules of Articles 2-12.",
        "This list is a DRAFT prepared from the regulation text. It does not come from the Reg2Chain system.",
        "For each row, choose in 'expert_decision': KEEP, EDIT (write the corrected text in 'corrected_requirement'), or DELETE.",
        "Check also the 'on_chain' column: DATA = checkable from submitted data; ORACLE = needs certified off-chain input "
        "(lab, panel, sensor, inspector); OFF = not meaningfully enforceable on-chain.",
        "Add any missing requirement at the bottom with expert_decision = ADD.",
        "Record your total time in the 'Log' sheet. These numbers are reported in the paper (expert effort).",
    ], start=1):
        c = ws.cell(row=r, column=1, value=line)
        c.alignment = WRAP
        if r == 1:
            c.font = Font(bold=True, size=14, color="2F5496")

    cl = wb.create_sheet("Checklist")
    cl.append(["req_id", "provision", "applies_to", "type", "requirement", "on_chain",
               "expert_decision", "corrected_requirement", "corrected_on_chain", "reason / comment"])
    for row in checklist_rows():
        cl.append(row + ["", "", "", ""])
    style_header(cl, [8, 18, 34, 22, 80, 10, 16, 60, 16, 40])
    for row in cl.iter_rows(min_row=2):
        for c in row:
            c.alignment = WRAP
    add_list_validation(cl, "G", ["KEEP", "EDIT", "DELETE", "ADD"], rows=300)
    add_list_validation(cl, "F", ["DATA", "ORACLE", "OFF"], rows=300)
    add_list_validation(cl, "I", ["DATA", "ORACLE", "OFF"], rows=300)

    log = wb.create_sheet("Log")
    log.append(["field", "value"])
    for k in ["expert name", "expertise", "date(s)", "total time (minutes)", "comments"]:
        log.append([k, ""])
    style_header(log, [28, 80])
    wb.save(path)
    return len(checklist_rows())


def main(units_csv, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    units = list(csv.DictReader(open(units_csv, encoding="utf-8")))
    a2 = [u for u in units if u["double_annotation"] == "Y"]
    annotation_workbook(units, os.path.join(out_dir, "Reg2Chain_annotation_A1.xlsx"), "A1")
    annotation_workbook(a2, os.path.join(out_dir, "Reg2Chain_annotation_A2.xlsx"), "A2")
    n = checklist_workbook(os.path.join(out_dir, "Reg2Chain_requirements_checklist.xlsx"))
    print(f"A1: {len(units)} units | A2: {len(a2)} units | checklist: {n} requirements -> {out_dir}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
