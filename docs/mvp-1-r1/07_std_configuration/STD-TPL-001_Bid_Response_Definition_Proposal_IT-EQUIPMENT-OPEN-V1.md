# Proposed bid-response-definition content for `IT-EQUIPMENT-OPEN-V1` — input to a future STD-TPL-001 version

**Status: proposal, not an authorised curation deliverable.** This is analysis and draft content for the document owner's review — it is not a STD-TPL-001 spec revision and does not authorise any register or code change on its own, per this document's own established discipline (curation may add nothing beyond what an approved STD-TPL-001 version §7/§13-equivalent section explicitly authorises; a proposed addition is recorded, never built ahead of approval). See `STD-TPL-001_Implementation_Plan.md`'s "Version 1.2 delta (proposed)" section and `STD-TPL-001_IMPLEMENTATION_TRACKER.md`'s matching block for how this fits into STD-TPL-001's own tracked work, independent of and prerequisite to BDS-CHG-001's own Phase 3.

**Where this came from.** BDS-CHG-001 v0.4 ("Supplier and Electronic Bid Submission") needs `IT-EQUIPMENT-OPEN-V1` to expose a machine-readable response/evaluation/contract-mapping layer — stable response-row identity, a closed response-type vocabulary, applicability rules, and an explicit evaluation-gate and contract-clause reference per response — so a bidder-facing workspace can render and validate itself without any officer-facing template logic leaking into the portal. Checked directly against the approved template: **STD-TPL-001 v0.6 §9 ("Evaluation and supplier response") and §10 ("Contract treatment") describe this at a policy/prose level only** ("no weighted scoring screen and no criterion builder," a table of which forms exist) — no version of STD-TPL-001 to date defines a structured, per-row register of this kind. This is genuinely new scope for the template, not a gap in something already authorised, and it is independent of the still-open `TPL-G07` gate (the Version 1.1 delta, which is a different, already-complete piece of work awaiting only the owner's sign-off).

**How this document was built**: every file in the approved `IT-EQUIPMENT-OPEN-V1` release 1.1 runtime bundle was read directly (`kentender_procurement/kentender_procurement/tender_templates/it_equipment_open_v1/insertion_points.csv`, `forms_register.csv`, `fixtures/moh_input.json`, and the full rendered `templates/complete_tender.html` — every supplier-facing form and the Section III qualification/evaluation table). Everything below is a faithful transcription of that already-approved content into the shape a downstream consumer needs, **except three flagged `[DECISION]` items**, which are genuinely new judgment calls, not transcription, and need the document owner's confirmation before any future spec version adopts them.

**Response-type vocabulary used below** is BDS-CHG-001 spec §4.4.3's own closed set (confirmation, yes/no, controlled single choice, short text, long text, integer/decimal/money, date, evidence reference, reviewed table/schedule input) — quoted here only so this proposal is self-contained; STD-TPL-001 itself would need to adopt (or adapt) a vocabulary like this explicitly if a future version authorises this register.

---

## 0. Two unit types, not one

Reading the actual rendered forms settles something worth deciding explicitly in any future spec text: most of the "declaration" forms (Form of Tender, Certificate of Independent Tender Determination, SD1, SD2, Code of Ethics, Tenderer Information, Youth reservation) are **overwhelmingly fixed legal text with a small identity/signature block**, not itemised field-by-field wizards. This matches BDS-CHG-001's own fixture language exactly — "7 declaration rows... all Complete/Confirmed." A future register should model two kinds of unit, not one:

- **Declaration** (9 of these, see §3): one locked text block, auto-populated identity fields, a small number of genuinely bidder-entered sub-fields only where the source form actually asks for one, and one `Confirmed` acknowledgement — never a field-by-field replica of every blank on the printed page.
- **Response row** (the Technical Compliance, Warranty, Comparable Experience, and Evidence content): genuine per-item bidder input with its own identity, type, and mapping.

Price is its own thing — a schedule, not a declaration or a response row — see §4.

---

## 1. Declarations — Company/declarations/tender-security content

| # | Declaration | Locked text source | Auto-populated from | Bidder-entered sub-fields | Confirmation |
|---|---|---|---|---|---|
| DEC-01 | Tenderer information | Tenderer Information Form (source pp. 49) | Bidder legal name, registration number, country, registered address, official contact; Authorised Signatory as "Authorized Representative" | None for a single organisation. For a joint venture: each member org's registration/year/address/representative — `[reviewed table/schedule input]`, repeating, one row per member | `confirmation` |
| DEC-02 | Form of Tender | Form of Tender (pp. 40-42) | Tenderer name, Tender title/reference, PE name, the goods/services table, the Tender Price (from the Price total — never separately entered here) | **Discounts offered and methodology** — `long_text`, optional, default "None" (item f). **State-owned-enterprise declaration** — `yes/no` (item k). **Commissions, gratuities or fees paid/payable** — `long_text`, optional, default "None" (item l) | `confirmation` |
| DEC-03 | Certificate of Independent Tender Determination | pp. 43-44 | Tenderer name, Tender title/reference, PE name | **Disclosure choice** — `controlled single choice`: "Arrived at the Tender independently" / "Consulted with one or more competitors" (clause 5). If the second option is chosen: a required `long_text` disclosure of which competitor(s) and the nature of the consultation — the one declaration with real conditional content, not just a rubber stamp | `confirmation` |
| DEC-04 | Self-declaration — not debarred (SD1) | pp. 44 | Tenderer name/company, Tender reference/title, PE name | None — fixed statement only | `confirmation` |
| DEC-05 | Self-declaration — no corrupt/fraudulent practice (SD2) | pp. 44-45 | Same as SD1 | None | `confirmation` |
| DEC-06 | Code of Ethics commitment | pp. 45-46 | Signatory name/position, firm name, PE contact office (Code of Ethics reference URL) | None. `[DECISION]` witness name/signature/date fields dropped — no electronic equivalent; the licensed digital signature is the electronic seal | `confirmation` |
| DEC-07 | Youth/reservation declaration | The reservation-category paragraph (Section III, gated on category ≠ None) | Reservation category, PPADA/Regulation citation text | None — the evidentiary proof is the AGPO registration certificate, handled as an evidence item (EVI-06 below), not a declaration sub-field | `confirmation`, only when the reservation category is not "None". `[DECISION]` **the approved bundle's own fixture currently has this exact tender (`TND-MOH-2027-033`) set to reservation category "None," while BDS-CHG-001's own canonical fixture has it as "Youth" for the same tender** — recommend correcting the bundle's fixture to "Youth" since both describe the same real tender and BDS-CHG-001's is the newer, more complete source for it |
| DEC-08 | Confidential Business Questionnaire | Tenderer's Eligibility form | PE name, Tender reference, opening date/time | Business-structure detail (sole proprietor / partnership / registered company — `controlled single choice`, gating a sub-block of `short_text` fields) + the 9-item Disclosure of Interest table as 9 `yes/no` rows, each with a conditional `long_text` "if yes, details" field | `confirmation` |
| DEC-09 | JV Members Information | JV Members form | — | Only rendered when the bidder arrangement is a joint venture; effectively the same repeating content as DEC-01's JV rows (the bundle's own `forms_register.csv` notes the base Tenderer Information form's JV field is "not active" — this dedicated form is the real one) | `confirmation` |

(This is 9 distinct units, not the 7 BDS-CHG-001's own spec currently states — the CBQ and JV form are genuinely separate. Worth a wording note at BDS-CHG-001's next revision, not a blocker.)

**Tender security** (same task, not a declaration): `security_type` — `controlled single choice` (Demand Bank Guarantee / Insurance Guarantee — both published "at the Tenderer's option," directly per source, no judgment call); `issuer`, `reference` — `short_text`; `amount`/`currency` — pre-filled read-only from the Tender (not bidder-editable — the amount is fixed by the Tender, not offered by the bidder); `valid_until` — auto-computed (already a generated value in the approved bundle); `proof_evidence_id` — `evidence reference`, required.

---

## 2. Response rows — Requirements and supporting evidence

### 2.1 Technical Compliance Response — 11 rows, `[reviewed table/schedule input]`

One row per technical requirement, exactly as rendered in the approved bundle. Each row bundles four sub-values as one atomic unit — matching BDS-CHG-001's own design board's per-row "response drawer" dialog concept, not four separate response rows:

Published, read-only per row: ID, label, comparison rule, required value + unit, applies-to.
Bidder sub-fields: **Compliance** — `controlled single choice` (Comply / Do not comply). **Offered value** — `short_text` (a single numeric/text type can't cover all eleven rows uniformly — "16 GB" vs "Yes" vs "USB-C ×2, USB-A ×2, HDMI ×1" — and the source form itself uses one open text cell for every row). **Comment** — `long_text`, optional. **Evidence reference** — `evidence reference`, required only when the row's evidence-required flag is true.

**Evaluation mapping** (uniform across all 11, not a per-row distinct criterion — this is the direct resolution of STD-TPL-001 §9.1's own "no weighted scoring, no criterion builder"): *pass* if Compliance = "Comply", *fail* (non-responsive) if "Do not comply" or left blank — the same rule, applied per row, individually assessed.
**Contract mapping** (uniform, via the Contract Documents clause): the accepted Technical Compliance Response becomes part of the Contract by incorporation — no separate per-row contract clause exists to reference.

### 2.2 Warranty and support confirmation — 1 row, `yes/no`

Published fact (read-only): minimum warranty months, support obligations. Bidder field: single `Confirmed (Yes/No)`. **Evaluation mapping**: GO/NO-GO qualification requirement (§9.3, "warranty confirmation" — always required). **Contract mapping**: SCC warranty clause (§10 table, "Warranty and replacement period").

### 2.3 Comparable supply experience — repeating, `[reviewed table/schedule input]`, conditional

Rendered only when required by the officer's Task 4 selection. Per row: client/contract name — `short_text`; contract value — `money`; completion date — `date`; brief scope — `long_text`; evidence — `evidence reference`. Minimum row count = the officer-configured count. **Evaluation mapping**: GO/NO-GO qualification requirement, "at least N comparable contracts completed within P years" (§9.3). **Contract mapping**: none — qualification-only.

### 2.4 Evidence checklist — up to 6 items, `evidence reference` each, individually conditional on the officer's Task 4 selections

Manufacturer's Authorization; technical datasheet/brochure; after-sales support evidence (with its officer-stated requirement text); one additional evidence item (free description + the one published requirement it proves); tender security proof (always); the reservation/AGPO certificate (only when the reservation category is not "None" — see DEC-07's `[DECISION]`). Each maps directly to the matching §9.3 qualification-table row — no invented mapping needed, the source states it directly.

---

## 3. Task "Price" — `[DECISION]` a simplified electronic-response shape

**What should stay faithful to the official form**: the printed/reference Tender document keeps the full official Price Schedule table exactly as the approved bundle renders it (origin, import status, customs duties, local-content %, inland transport, taxes, line total) — no change proposed to that rendering.

**What the bidder's electronic response should actually collect** (simplified, matching BDS-CHG-001's own design and fixture numbers exactly: one unit price + tax + total, no origin/import breakdown): one row per goods line, `money` unit price + read-only quantity/unit/description, plus a `money` tax amount. Total = server-computed, deterministic. Origin/import-status/customs-duty/local-content columns are **not** proposed as bidder-collected fields for this product profile — they'd stay as the official form's own boilerplate in the printed document only.

**Evaluation mapping**: feeds the sole evaluation factor, lowest evaluated responsive Tender Price (§9.1 stage 3). **Contract mapping**: the fixed, non-adjustable Contract Price clause (§10 table, "Price adjustment").

---

## 4. What a future STD-TPL-001 version would need to add

If the document owner adopts this proposal (in whole, in part, or amended), a future spec revision would need to:

1. Add a new authorised register alongside `insertion_points.csv`/`forms_register.csv`/`coverage_register.csv` — e.g. `response_definition.csv` (technical/warranty/comparable-experience/evidence/price rows) and `declarations.csv` (the 9 declaration units) — with an explicit closed response-type vocabulary (§0 above) as a new binding decision, the same way §2/§6.1 already fix other Version-1.0-scope choices.
2. State explicitly that evaluation/contract mapping for this release is **uniform per content class, not per individual row** — a direct, honest statement of what §9.1's existing "no weighted scoring, no criterion builder" already implies, made explicit as a register-level rule rather than left to be inferred.
3. Resolve the three `[DECISION]` items above as binding release choices (§6.1-style), or override them.
4. Authorise a new curation pass (or an extension of the existing Version 1.1 delta's Pass 3 concept) to build the actual register files against this authorisation, with its own gate — see the tracker's "Version 1.2 delta (proposed)" block.

This document does not itself authorise that work — it is the input for the document owner to decide whether, when and how to do it.
