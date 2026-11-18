"""
Pre-annotation of the 63 units (drafted by Claude, Anthropic) - to be reviewed and corrected by annotator A1.
NOT given to annotator A2 (independent annotation).

E(text, type, occurrence=1)      R(subject, relation, object, qualifier="")
"""

def E(t, ty, occ=1, note=""):
    return (t, ty, occ, note)


def R(s, r, o, q="", note=""):
    return (s, r, o, q, note)


P1B = "oils referred to in Article 1, point (b)"
REG1308 = "Regulation (EU) No 1308/2013"


def art2(point, product, part):
    ref1 = f"point {point} of Tables A and B of Annex I to this Regulation"
    ref2 = f"Part VIII, {part}, of Annex VII to {REG1308}"
    return ([E(ref1, "LEGAL_REF"), E(product, "PRODUCT"), E(ref2, "LEGAL_REF")],
            [R(product, "REFERS_TO", ref1), R(product, "REFERS_TO", ref2)])


def annex(product, pairs):
    ents = [E(product, "PRODUCT")]
    rels = []
    for param, val in pairs:
        ents += [E(param, "PARAMETER"), E(val, "VALUE")]
        rels.append(R(product, "LIMIT", val, param))
    return ents, rels


A = {}

A["ART1"] = ([
    E("characteristics", "PARAMETER"),
    E(f"olive oils referred to in Part VIII, points 1 to 6, of Annex VII to {REG1308}", "PRODUCT"),
    E(f"olive oils referred to in Part VIII, points 1(a) and (b) and points 3 and 6, of Annex VII to {REG1308}", "PRODUCT"),
    E("final consumer", "ACTOR"),
    E("foodstuff", "PRODUCT"),
], [], "scope provision: no deontic relation")

A["ART2.1.lead"] = ([E("Olive oils", "PRODUCT"), E("characteristics", "PARAMETER")], [], "")
for k, (pt, prod, part) in {
    "a": (1, "extra virgin olive oil", "point 1(a)"), "b": (2, "virgin olive oil", "point 1(b)"),
    "c": (3, "lampante olive oil", "point 1(c)"), "d": (4, "refined olive oil", "point 2"),
    "e": (5, "olive oil composed of refined olive oils and virgin olive oils", "point 3"),
    "f": (6, "crude olive-pomace oil", "point 4"), "g": (7, "refined olive-pomace oil", "point 5"),
    "h": (8, "olive-pomace oil", "point 6"),
}.items():
    e, r = art2(pt, prod, part)
    A[f"ART2.1.{k}"] = (e, r, "")

A["ART2.2"] = ([E("characteristics of olive oils laid down in Annex I", "PARAMETER"),
                E("Commission Implementing Regulation (EU) 2022/2105", "LEGAL_REF")],
               [R("characteristics of olive oils laid down in Annex I", "REFERS_TO",
                  "Commission Implementing Regulation (EU) 2022/2105")], "")

A["ART3.1"] = ([E(P1B, "PRODUCT"), E("blends of olive oil and other vegetable oils", "PRODUCT")],
               [R(P1B, "PERMISSION", "blends of olive oil and other vegetable oils")], "")
A["ART3.2"] = ([E(P1B, "PRODUCT"), E("other foodstuffs", "PRODUCT")],
               [R(P1B, "PERMISSION", "other foodstuffs")], "")
A["ART3.3"] = ([E("Member States", "ACTOR"),
                E("blends of olive oil and other vegetable oils referred to in paragraph 1", "PRODUCT"),
                E("production", "PROCESS", 1), E("marketing", "PROCESS", 1), E("production", "PROCESS", 2),
                E("such blends", "PRODUCT", 1), E("such blends", "PRODUCT", 2)],
               [], "rule on Member States' powers: no relation of the schema fits")

A["ART4.1"] = ([E("Oils referred to in Article 1, point (b)", "PRODUCT"), E("final consumer", "ACTOR"), E("maximum capacity", "PARAMETER"),
                E("five litres", "VALUE"),
                E("opening system that can no longer be sealed after the first time it is opened", "PROCESS")],
               [R("Oils referred to in Article 1, point (b)", "LIMIT", "five litres", "maximum capacity"),
                R("Oils referred to in Article 1, point (b)", "OBLIGATION",
                  "opening system that can no longer be sealed after the first time it is opened")], "")
A["ART4.2"] = ([E(P1B, "PRODUCT"),
                E("restaurants, hospitals, canteens and other similar collective establishments", "ACTOR"),
                E("Member States", "ACTOR"), E("maximum capacity", "PARAMETER"),
                E("exceeding five litres", "VALUE")],
               [R("Member States", "PERMISSION", "exceeding five litres", "maximum capacity")], "")

A["ART5.1"] = ([E("particulars referred to in Articles 6 to 9", "LABEL_ITEM")], [], "obligation without subject entity")
A["ART5.2"] = ([E("legal name referred to in Article 6(1)", "LABEL_ITEM"),
                E("place of origin referred to in Article 8(1)", "LABEL_ITEM"),
                E("Article 2(2), point (l), of Regulation (EU) No 1169/2011", "LEGAL_REF")], [], "")
A["ART5.3"] = ([E("particulars referred to in Articles 10, 11 and 12", "LABEL_ITEM")], [], "")
A["ART6.1"] = ([E(f"description of the {P1B}", "LABEL_ITEM"), E("legal name", "LABEL_ITEM"),
                E("Article 2(2), point (n), of Regulation (EU) No 1169/2011", "LEGAL_REF")],
               [R("legal name", "REFERS_TO", "Article 2(2), point (n), of Regulation (EU) No 1169/2011")], "")
A["ART6.2.lead"] = ([E("those oils", "PRODUCT"), E("description referred to in paragraph 1", "LABEL_ITEM"),
                     E("information on the category of oil", "LABEL_ITEM")],
                    [R("those oils", "OBLIGATION", "information on the category of oil")], "")
for k, prod, txt in [
    ("a", "extra virgin olive oil", "‘superior category olive oil obtained directly from olives and solely by mechanical means’"),
    ("b", "virgin olive oil", "‘olive oil obtained directly from olives and solely by mechanical means’"),
    ("c", "olive oil composed of refined olive oils and virgin olive oils",
     "‘oil comprising exclusively olive oils that have undergone refining and oils obtained directly from olives’"),
]:
    A[f"ART6.2.{k}"] = ([E(prod, "PRODUCT"), E(txt, "LABEL_ITEM")], [R(prod, "OBLIGATION", txt)], "")
T1 = "‘oil comprising exclusively oils obtained by treating the product obtained after the extraction of olive oil and oils obtained directly from olives’"
T2 = "‘oil comprising exclusively oils obtained by processing olive pomace and oils obtained directly from olives’"
A["ART6.2.d"] = ([E("olive-pomace oil", "PRODUCT"), E(T1, "LABEL_ITEM"), E(T2, "LABEL_ITEM")],
                 [R("olive-pomace oil", "OBLIGATION", T1, note="alternative (i)"),
                  R("olive-pomace oil", "OBLIGATION", T2, note="alternative (ii)")], "")
A["ART7"] = ([E("Information on the special storage conditions", "LABEL_ITEM"), E(P1B, "PRODUCT")],
             [R(P1B, "OBLIGATION", "Information on the special storage conditions")], "")

REF8 = f"Part VIII, points 1(a) and (b), of Annex VII to {REG1308}"
A["ART8.1"] = ([E("extra virgin olive oil", "PRODUCT"), E("virgin olive oil", "PRODUCT"), E(REF8, "LEGAL_REF"),
                E("place of origin", "LABEL_ITEM")],
               [R("extra virgin olive oil", "OBLIGATION", "place of origin"),
                R("virgin olive oil", "OBLIGATION", "place of origin"),
                R("extra virgin olive oil", "REFERS_TO", REF8), R("virgin olive oil", "REFERS_TO", REF8)], "")
P82 = f"oils referred to in Part VIII, points 3 and 6, of Annex VII to {REG1308}"
A["ART8.2"] = ([E(P82, "PRODUCT"), E("place of origin", "LABEL_ITEM")],
               [R(P82, "PROHIBITION", "place of origin")], "")
A["ART8.3.lead"] = ([E("place of origin referred to in paragraph 1", "LABEL_ITEM")], [], "")
L83a = "reference to that Member State, the Union or the third country"
A["ART8.3.a"] = ([E("olive oils", "PRODUCT"), E("paragraphs 6 and 7", "LEGAL_REF"), E(L83a, "LABEL_ITEM")],
                 [R("olive oils", "PERMISSION", L83a)], "'shall only consist of' = restricted permission")
B = ["‘blend of olive oils of European Union origin’", "reference to the Union",
     "‘blend of olive oils not of European Union origin’", "reference to origin outside the Union",
     "‘blend of olive oils of European Union origin and not of European Union origin’",
     "reference to origin within the Union and outside the Union"]
A["ART8.3.b"] = ([E("blends of olive oils", "PRODUCT"), E("paragraphs 6 and 7", "LEGAL_REF")]
                 + [E(b, "LABEL_ITEM") for b in B],
                 [R("blends of olive oils", "PERMISSION", b) for b in B], "")
A["ART8.3.c"] = ([E("protected designation of origin", "LABEL_ITEM"), E("protected geographical indication", "LABEL_ITEM"),
                  E("Regulation (EU) No 1151/2012", "LEGAL_REF")],
                 [R("protected designation of origin", "REFERS_TO", "Regulation (EU) No 1151/2012"),
                  R("protected geographical indication", "REFERS_TO", "Regulation (EU) No 1151/2012")], "")
A["ART8.4"] = ([E("names of brands or firms", "LABEL_ITEM"), E("Directive 89/104/EEC", "LEGAL_REF"),
                E("Council Regulation (EC) No 40/94", "LEGAL_REF"), E("place of origin", "LABEL_ITEM")],
               [R("names of brands or firms", "PROHIBITION", "place of origin", note="cannot count as place of origin"),
                R("names of brands or firms", "REFERS_TO", "Directive 89/104/EEC"),
                R("names of brands or firms", "REFERS_TO", "Council Regulation (EC) No 40/94")], "")
A["ART8.5"] = ([E("place of origin", "LABEL_ITEM"), E("Articles 59 to 63 of Regulation (EU) No 952/2013", "LEGAL_REF")],
               [R("place of origin", "REFERS_TO", "Articles 59 to 63 of Regulation (EU) No 952/2013")], "")
A["ART8.6"] = ([E("place of origin mentioning a Member State or the Union", "LABEL_ITEM"), E("mill", "ACTOR")], [], "")
W87 = ("‘(extra) virgin olive oil obtained in (the Union or the name of the Member State or third country concerned) "
       "from olives harvested in (the Union or the name of the Member State or third country concerned)’")
A["ART8.7"] = ([E("mill", "ACTOR"), E("place of origin", "LABEL_ITEM"), E(W87, "LABEL_ITEM")],
               [R("place of origin", "OBLIGATION", W87)], "")
A["ART9"] = ([E(P1B, "PRODUCT"), E("alphanumeric identification of the packaging plant", "LABEL_ITEM"),
              E("Article 6 of Commission Implementing Regulation (EU) 2022/2105", "LEGAL_REF")],
             [R(P1B, "OBLIGATION", "alphanumeric identification of the packaging plant"),
              R("alphanumeric identification of the packaging plant", "REFERS_TO",
                "Article 6 of Commission Implementing Regulation (EU) 2022/2105")], "")
P10 = f"{P1B}, of this Regulation"
A["ART10.lead"] = ([E("optional reserved terms", "LABEL_ITEM"), E(f"Annex IX to {REG1308}", "LEGAL_REF"),
                    E(P10, "PRODUCT")],
                   [R("optional reserved terms", "REFERS_TO", f"Annex IX to {REG1308}"),
                    R(P10, "PERMISSION", "optional reserved terms")], "")
EV = "extra virgin or virgin olive oils"
A["ART10.a"] = ([E("‘first cold pressing’", "LABEL_ITEM"), E(EV, "PRODUCT"), E("temperature", "PARAMETER"),
                 E("below 27 °C", "VALUE"), E("first mechanical pressing of the olive paste", "PROCESS"),
                 E("traditional extraction system using hydraulic presses", "PROCESS")],
                [R(EV, "PERMISSION", "‘first cold pressing’"),
                 R("‘first cold pressing’", "CONDITION", "below 27 °C", "temperature"),
                 R("‘first cold pressing’", "CONDITION", "first mechanical pressing of the olive paste"),
                 R("‘first cold pressing’", "CONDITION", "traditional extraction system using hydraulic presses")], "")
A["ART10.b"] = ([E("‘cold extraction’", "LABEL_ITEM"), E(EV, "PRODUCT"), E("temperature", "PARAMETER"),
                 E("below 27 ° C", "VALUE"), E("percolation", "PROCESS"), E("centrifugation", "PROCESS")],
                [R(EV, "PERMISSION", "‘cold extraction’"),
                 R("‘cold extraction’", "CONDITION", "below 27 ° C", "temperature"),
                 R("‘cold extraction’", "CONDITION", "percolation"),
                 R("‘cold extraction’", "CONDITION", "centrifugation")], "")
IND = "indications of organoleptic characteristics referring to taste or smell"
OC = f"organoleptic characteristics as defined in Annex IX to {REG1308}"
ASS = "assessment carried out following the method referred to in Annex I, point 5, of Commission Implementing Regulation (EU) 2022/2105"
A["ART10.c"] = ([E(IND, "LABEL_ITEM"), E("extra virgin and virgin olive oils", "PRODUCT"), E(OC, "LABEL_ITEM"),
                 E(ASS, "PROCESS"), E("Annex II to this Regulation", "LEGAL_REF")],
                [R("extra virgin and virgin olive oils", "PERMISSION", IND), R(OC, "CONDITION", ASS)], "")
MA = "indication of the maximum acidity expected by the date of minimum durability"
MV = "maximum values for peroxide, wax content and ultraviolet absorption"
A["ART10.d"] = ([E(MA, "LABEL_ITEM"), E("Article 9(1), point (f), of Regulation (EU) No 1169/2011", "LEGAL_REF"),
                 E(MV, "LABEL_ITEM"), E("Commission Implementing Regulation (EU) 2022/2105", "LEGAL_REF")],
                [R(MA, "CONDITION", MV), R(MV, "REFERS_TO", "Commission Implementing Regulation (EU) 2022/2105")], "")
A["ART11.1"] = ([E("extra virgin olive oil", "PRODUCT"), E("virgin olive oil", "PRODUCT"), E(REF8, "LEGAL_REF"),
                 E("indication of the harvesting year", "LABEL_ITEM")],
                [R("extra virgin olive oil", "PERMISSION", "indication of the harvesting year"),
                 R("virgin olive oil", "PERMISSION", "indication of the harvesting year"),
                 R("extra virgin olive oil", "REFERS_TO", REF8), R("virgin olive oil", "REFERS_TO", REF8)], "")
A["ART11.2"] = ([E("harvesting year", "LABEL_ITEM"), E("100 %", "VALUE"), E("contents of the container", "PARAMETER"),
                 E("relevant marketing year", "LABEL_ITEM"),
                 E(f"Article 6, point (f), of {REG1308}", "LEGAL_REF"),
                 E("month and the year of the harvest", "LABEL_ITEM")],
                [R("harvesting year", "CONDITION", "100 %", "contents of the container"),
                 R("relevant marketing year", "REFERS_TO", f"Article 6, point (f), of {REG1308}")], "")
A["ART11.3"] = ([E("Member States", "ACTOR"), E("harvesting year referred to in paragraph 1", "LABEL_ITEM"),
                 E("olive oils referred to in that paragraph", "PRODUCT")],
                [R("Member States", "PERMISSION", "harvesting year referred to in paragraph 1")], "")
A["ART11.4"] = ([E("olive oils labelled prior to the date on which that decision takes effect", "PRODUCT")], [], "")
A["ART11.5"] = ([E("Member States", "ACTOR"), E("Commission", "ACTOR"),
                 E("Delegated Regulation (EU) 2017/1183", "LEGAL_REF")],
                [R("Member States", "OBLIGATION", "Commission", note="obligation to notify the Commission")], "")
TD = "‘Blend of vegetable oils (or the specific names of the vegetable oils concerned) and olive oil’"
A["ART12.1"] = ([E(P1B, "PRODUCT"), E("blend with other vegetable oils", "PRODUCT"), E("blend concerned", "PRODUCT"),
                 E(TD, "LABEL_ITEM"), E("percentage of such oils in the blend", "LABEL_ITEM")],
                [R("blend concerned", "OBLIGATION", TD),
                 R("blend concerned", "OBLIGATION", "percentage of such oils in the blend")], "")
A["ART12.2"] = ([E(P1B, "PRODUCT"), E("images or graphics", "LABEL_ITEM"),
                 E("blend referred to in paragraph 1", "PRODUCT"), E("more than 50 %", "VALUE")],
                [R("blend referred to in paragraph 1", "PERMISSION", "images or graphics"),
                 R("images or graphics", "CONDITION", "more than 50 %")], "")
PO = "percentage of oil relative to the total net weight of the foodstuff"
A["ART12.3"] = ([E("solid foodstuffs preserved exclusively in olive oil", "PRODUCT"),
                 E("Council Regulations (EEC) No 2136/89 (12) and (EEC) No 1536/92 (13)", "LEGAL_REF"),
                 E(f"{P1B}, of this Regulation", "PRODUCT"), E("name of the food", "LABEL_ITEM"), E(PO, "LABEL_ITEM")],
                [R("name of the food", "OBLIGATION", PO)], "")
PA1 = "percentage of added oils referred to in Article 1, point (b), relative to the total net weight of the foodstuff referred to in paragraph 3 of this Article"
PA2 = "percentage of added oil relative to the total weight of fats"
A["ART12.4"] = ([E(PA1, "LABEL_ITEM"), E(PA2, "LABEL_ITEM"), E("‘percentage of fats’", "LABEL_ITEM")],
                [R(PA1, "PERMISSION", PA2, note="may be replaced by")], "")
A["ART12.5"] = ([E("descriptions referred to in Article 6(1)", "LABEL_ITEM"), E("‘olive oil’", "LABEL_ITEM", 1),
                 E("products referred to in paragraphs 1 and 3 of this Article", "PRODUCT"),
                 E("olive-pomace oil", "PRODUCT"), E("‘olive oil’", "LABEL_ITEM", 2),
                 E("‘olive-pomace oil’", "LABEL_ITEM")],
                [R("products referred to in paragraphs 1 and 3 of this Article", "PERMISSION", "‘olive oil’"),
                 R("olive-pomace oil", "OBLIGATION", "‘olive-pomace oil’")], "")
A["ART12.6"] = ([E("other foodstuffs", "PRODUCT"), E(P1B, "PRODUCT"), E("resulting foodstuff", "PRODUCT"),
                 E("legal names referred to in Article 6", "LABEL_ITEM")],
                [R("resulting foodstuff", "PROHIBITION", "legal names referred to in Article 6")], "")
A["ART13"] = ([E("Regulation (EEC) No 2568/91", "LEGAL_REF"), E("Implementing Regulation (EU) No 29/2012", "LEGAL_REF"),
               E("Commission Implementing Regulation (EU) 2022/2105", "LEGAL_REF"),
               E("correlation table in Annex III to this Regulation", "LEGAL_REF")], [],
              "repeal: no relation of the schema fits")
A["ART14"] = ([], [], "no entity")

ANX = {
    "1": ("extra virgin olive oil", [("Acidity (%)", "≤ 0,80"), ("Peroxide value (mEq O2/kg)", "≤ 20,0"),
                                     ("K232", "≤ 2,50"), ("K268 or K270", "≤ 0,22"), ("ΔK", "≤ 0,01"),
                                     ("Median of defect (Md)", "= 0,0"), ("Fruity median (Mf)", "> 0,0"),
                                     ("Fatty acid ethyl esters (mg/kg)", "≤ 35")]),
    "2": ("virgin olive oil", [("Acidity (%)", "≤ 2,0"), ("Peroxide value (mEq O2/kg)", "≤ 20,0"),
                               ("K232", "≤ 2,60"), ("K268 or K270", "≤ 0,25"), ("ΔK", "≤ 0,01"),
                               ("Median of defect (Md)", "≤ 3,5"), ("Fruity median (Mf)", "> 0,0")]),
    "3": ("lampante olive oil", [("Acidity (%)", "> 2,0"), ("Median of defect (Md)", "> 3,5")]),
    "4": ("refined olive oil", [("Acidity (%)", "≤ 0,30"), ("Peroxide value (mEq O2/kg)", "≤ 5,0"),
                                ("K268 or K270", "≤ 1,25"), ("ΔK", "≤ 0,16")]),
    "5": ("olive oil composed of refined olive oil and virgin olive oils",
          [("Acidity (%)", "≤ 1,00"), ("Peroxide value (mEq O2/kg)", "≤ 15,0"), ("K268 or K270", "≤ 1,15"), ("ΔK", "≤ 0,15")]),
    "6": ("crude olive-pomace oil", []),
    "7": ("refined olive-pomace oil", [("Acidity (%)", "≤ 0,30"), ("Peroxide value (mEq O2/kg)", "≤ 5,0"),
                                       ("K268 or K270", "≤ 2,00"), ("ΔK", "≤ 0,20")]),
    "8": ("olive-pomace oil", [("Acidity (%)", "≤ 1,00"), ("Peroxide value (mEq O2/kg)", "≤ 15,0"),
                               ("K268 or K270", "≤ 1,70"), ("ΔK", "≤ 0,18")]),
}
for k, (prod, pairs) in ANX.items():
    e, r = annex(prod, pairs)
    A[f"ANX1.A.{k}"] = (e, r, "")
