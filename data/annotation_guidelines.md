# Reg2Chain annotation guidelines (v1.0)

**Purpose.** Build an independent gold standard for entity and relation extraction from Regulation (EU) 2022/2104. Annotate from the text only. Do not look at any system output.

**Unit.** One provision unit = one numbered paragraph (or one lettered point of a long paragraph) of Articles 1-14, or one linearised row of Annex I, Table A. Annotate each unit on its own.

**How to annotate an entity.** In sheet 'Entities', add one row per entity: unit_id, the entity text COPIED EXACTLY from the unit (same spelling, spaces, quotes), and its type. Leave 'occurrence' at 1. Use 2, 3... only if the same entity text appears several times as separate entities (text inside a longer entity, e.g. 'virgin olive oil' inside 'extra virgin olive oil', is not counted).

**No overlap.** Entities never overlap or nest. Take the longest span that still has a single type. Example: 'oils referred to in Article 1, point (b)' is ONE PRODUCT (do not also mark 'Article 1, point (b)' as LEGAL_REF).

**Spans.** Exclude leading articles (the, a, an) and final punctuation. Keep quotes for quoted label texts.

## Entity types

**PRODUCT.** Olive-oil categories and other products: extra virgin olive oil; virgin olive oil; lampante olive oil; refined olive oil; olive oil composed of refined olive oils and virgin olive oils; crude olive-pomace oil; refined olive-pomace oil; olive-pomace oil; blends of olive oil and other vegetable oils; foodstuffs; groups such as 'oils referred to in Article 1, point (b)'.

**PARAMETER.** A measurable characteristic: acidity, peroxide value, K232, K268 or K270, ΔK, median of defect, fruity median, fatty acid ethyl esters, wax content, ultraviolet absorption, temperature, maximum capacity, percentage of oil.

**VALUE.** A numeric limit or quantity, with its operator and unit: '≤ 0,80', 'five litres', '27 °C' (write 'below 27 °C' if 'below' is part of the condition), 'more than 50 %', '100 %'.

**LABEL_ITEM.** Something that must / may / must not appear on the label or container: legal name, category information, place of origin, harvesting year, storage conditions information, alphanumeric identification of the packaging plant, 'first cold pressing', 'cold extraction', organoleptic characteristics, trade description, a quoted mandatory wording.

**ACTOR.** An organisation or role: Member States, Commission, final consumer, packaging plant, mill, restaurants/hospitals/canteens (collective establishments), panel leader.

**LEGAL_REF.** A reference to a legal act or provision when it is not part of a PRODUCT span: 'Regulation (EU) No 1308/2013', 'Commission Implementing Regulation (EU) 2022/2105', 'Article 6(1)', 'Annex I'. Take the maximal reference ('Part VIII, point 1(a), of Annex VII to Regulation (EU) No 1308/2013').

**PROCESS.** A production, extraction or packaging method or feature: mechanical means, refining, first mechanical pressing, percolation, centrifugation, hydraulic presses, opening system that can no longer be sealed.

## Relation types (between two entities already annotated in the same unit)

**OBLIGATION.** subject must have / do / show object ('shall', 'must', 'mandatory'). Ex.: (extra virgin olive oil, OBLIGATION, place of origin) in Art. 8(1).

**PERMISSION.** subject may have / do / show object, including restricted permissions ('may only', 'may appear only for'). Ex.: (extra virgin olive oil, PERMISSION, harvesting year) in Art. 11(1).

**PROHIBITION.** subject must not have / show object ('shall not', 'no ... shall'). Ex.: (olive-pomace oil ..., PROHIBITION, place of origin) in Art. 8(2).

**LIMIT.** a PRODUCT has a limit VALUE for a PARAMETER. Subject = PRODUCT, object = VALUE, and write the PARAMETER text in the 'qualifier' column. Ex.: (extra virgin olive oil, LIMIT, ≤ 0,80, qualifier: Acidity (%)).

**CONDITION.** a permission/obligation on the subject applies only if the object holds. Subject = LABEL_ITEM or PRODUCT, object = VALUE or PROCESS; PARAMETER in 'qualifier' if any. Ex.: ('first cold pressing', CONDITION, below 27 °C, qualifier: temperature).

**REFERS_TO.** an entity is defined by / determined in accordance with a LEGAL_REF. Ex.: (characteristics of olive oils, REFERS_TO, Commission Implementing Regulation (EU) 2022/2105).

**Several subjects.** If the provision lists several products ('extra virgin olive oil and virgin olive oil'), annotate one entity per product and one relation per product.

**Unsure?.** Write your doubt in 'notes' and annotate your best choice. Do not leave a unit unannotated: if a unit has no entity, add one row with unit_id and type 'NONE'.

**Time.** About 4-5 minutes per unit. Please record your total time in the 'Log' sheet.
