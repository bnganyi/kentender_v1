# KHSSP 2023-2027 — distilled Strategy Alignment records

**Source:** `KHSSP 2023-2027 signed copy.pdf` (Kenya Health Sector Strategic Plan, Ministry of Health, 149 pages), specifically Chapter 3.3 (Strategic Objectives, p.50) for objective titles and the "Indicators by Strategic Objectives" annex (p.104-109, PDF pages 124-129) for indicators and targets.
**Target schema:** STR-CHG-001 v1.6 §4 (`StrategicPlan` → `StrategicPlanVersion` → `StrategyNode` → `PerformanceIndicator` → `PerformanceTarget`).
**Scope decided with the module owner (2026-09-03):** full transcription of all 6 Strategic-Objective-indexed indicator tables only (not the separate "UHC Impact-level Indicators" set or the numbered disease-elimination annex at the back of the document — both excluded by explicit decision). One Pillar, one Programme, six Strategic Objectives (also decided with the owner).
**Distilled:** 2026-09-03

This is a **data distillation for review**, not a seed script. Every row was read from the source table (cross-checked against the rendered PDF page images, not text extraction alone) and transcribed as printed, including values that look like source-document errors — those are flagged in §2, not silently corrected. A Strategy Author should review §2's flags and the placeholder `definition` text (§6.1) before this becomes a real Draft plan.

---

## 1. What this does NOT include, and why

Per STR-CHG-001 v1.6, the following are **never** populated from this or any source, regardless of what the KHSSP PDF contains:

- **No `procuring_entity_id`, `owner_org_unit_id`, or any PE/OU scope field** (§1.1, §4.1) — this plan belongs to the site's single Procuring Entity by construction.
- **No baseline field.** The KHSSP tables' `2022/23` "Baseline" column is real, useful context — included below purely for review — but `PerformanceTarget` has no baseline field (§2 exclusions: "baseline or tolerance fields in MVP 1"; STR-AC-028 confirms no Strategy page/API accepts baseline data). Baselines here are **reference only**, not an importable record.
- **No source-reference, evidence, attachment, contact, or generic notes field** (§2 exclusions) — the "Data Source" column (KHIS, TIBU, STEPS, etc.) is carried below for traceability during authoring, but there is no field on `PerformanceIndicator` or `PerformanceTarget` to store it. If a future consumer needs it, that is a new data-purpose decision outside this document's scope, not a default inclusion.
- **No UHC Impact-level indicators, no disease-elimination annex content** — excluded by the scope decision above, not because they don't exist in the source.

## 2. Data-quality flags in the source document

Found while cross-checking the annex tables against the rendered PDF (not introduced by this distillation). Each is transcribed as printed below and flagged inline with a `⚠` marker; resolve with the KHSSP document owner before treating the affected target value as authoritative.

| # | Location | Issue |
|---|---|---|
| F1 | SO1, "TB Treatment Coverage" | 2026/27 target is `60`, a sharp dip between `78` (2025/26) and `80` (2027/28) that breaks the otherwise monotonic increase. Likely a source typo. |
| F2 | SO1, two "nutrition assessment, counselling and support" rows (people living with HIV; people on TB treatment) | 2027/28 target is printed `0.75` where every other value in the row is a whole number in the 50-70 range. Almost certainly a typo for `75`. |
| F3 | SO1, "Proportion of pregnant women in malaria-endemic areas who slept under LLIN" | Baseline `98` is higher than every target year (70-90) — the plan targets a *decrease* on a "proportion... slept under" indicator, which reads backwards. Transcribed as printed. |
| F4 | SO1, "Proportion of households with universal coverage of LLINs in malaria risk areas" | Target sequence `80, 70, 60, 80, 70` is non-monotonic (rises then falls then rises again). Transcribed as printed. |
| F5 | SO2, "Percentage of women aged 25-49 years screened for cervical cancer" | The source table splits this indicator's baseline (`30.9`) onto its own table row, separate from the indicator name and the 2023/24-2027/28 target row. Reassembled here as one record; reasonably confident but not certain the `30.9` belongs to this indicator rather than an adjacent one. |
| F6 | SO4, "Fresh stillbirth rate per 1,000 births in facilities" | The source cell is genuinely corrupted — the Baseline column contains `10.6` followed by run-on text from a *different* indicator ("Percentage of Low birth weight in health facilities"), and the row shows six numbers (`6,6,6,6,5,5`) where five target years are expected. Transcribed below with baseline `10.6` and targets `6, 6, 6, 5, 5` (dropping one duplicate `6`) as the best-effort reading — **do not treat this row as authoritative without checking the source PDF directly.** |
| F7 | SO3 table | Has no `2022/23` Baseline column at all (unlike every other SO table) — its first data column is already `2023/24`. No baseline is available for any SO3 indicator; not a defect, just a different table shape in the source. |
| F8 | SO4, three adolescent-health indicators ("adolescent and youth friendly services", "equipped with knowledge for decision making", "reached with key health messages") | Each is missing its 2025/26 target value (blank cell in the source table). Left blank below, not interpolated. |
| F9 | SO5, four indicators (tobacco use, harmful alcohol use, physical violence among women, intimate/sexual violence) | Each has only 3 of 5 target years populated (2023/24 and 2026/27 blank in the source). Left blank below. |
| F10 | SO6, "Percentage of women completed secondary education" | Only 2025/26 and 2027/28 are populated; 2023/24, 2024/25 and 2026/27 are blank in the source. |
| F11 | SO5 rows 11-12 and SO6 rows 1-2 | "Percentage of households using improved sanitation facilities" and "...improved safe water facilities" appear **verbatim, with identical values**, under both Strategic Objective 5 and Strategic Objective 6 in the source document. Real duplication in the source, not a distillation error — see §6.6/§6.7's note on how this is handled below. |
| F12 | Cover page vs. indicator tables | The document's own title states the plan period as **"July 2023 - June 2027"** (4 years), but every indicator table provides five target columns running through **2027/28** (i.e., ending June 2028). §5 below uses the 5-year span the tables actually populate (period_end `2028-06-30`), since that is the operationally meaningful boundary — flag the cover page's "June 2027" wording as an apparent inconsistency in the source, not a transcription choice. |

## 3. Fiscal Year prerequisite

Every `PerformanceTarget.fiscal_year` below references an ERPNext `Fiscal Year` named `2023-2024` through `2027-2028`. Per STR-CHG-001 v1.6 §14.2, Strategy creates no Fiscal Year and fails closed if one is missing (`STRATEGY_CONFIG_MISSING`) — **confirm all five years exist on the target site before attempting to import any target below.** Only `2026-2027` and `2027-2028` are confirmed seeded on the current dev site per prior work; `2023-2024` through `2025-2026` are historical years that may need to be added through Configuration & Governance's `add_fiscal_year` command first, or the corresponding already-elapsed target rows may be imported as historical record only (not as live targets a Strategy Author would edit).

## 4. `StrategicPlan` record

| Field | Value |
|---|---|
| `title` | Kenya Health Sector Strategic Plan (KHSSP) 2023-2027 |
| `plan_role` | Primary |
| `period_start` | 2023-07-01 |
| `period_end` | 2028-06-30 *(see F12 — the tables' actual 5-year span, not the cover page's stated "June 2027")* |

`plan_id` is server-generated on save; not set here.

## 5. `StrategicPlanVersion` record

| Field | Value |
|---|---|
| `version_number` | 1 |
| `based_on_plan_version_id` | *(empty — first version)* |
| `effective_from` | 2023-07-01 |
| `effective_to` | 2028-06-30 |
| `status` | Draft on creation. This document does not assert an Active status — the real plan must go through Submit → Approve by the actual Strategy Author/Approver holding the responsibility for the Ministry of Health's site, per §5.1. |

## 6. `StrategyNode` records

### 6.1 Pillar and Programme

| `node_type` | `title` | `parent_node_id` | `display_order` |
|---|---|---|---|
| Pillar | Universal Health Coverage | *(root)* | 1 |
| Programme | Kenya Health Sector Strategic Plan 2023-2027 | ↑ Pillar above | 1 |

Rationale (decided with the module owner): the source document has no explicit Pillar/Programme layer above its six Strategic Objectives — they sit as a flat list under one Goal/Theme. "Universal Health Coverage" is the document's own stated THEME (§3.2); "Kenya Health Sector Strategic Plan 2023-2027" is the document's own title, used as the single umbrella Programme so as not to invent a thematic grouping the source text doesn't state.

### 6.2 Strategic Objectives

All six are direct children of the Programme above (Sub-programme omitted, per STR-BR-007's "a Programme may parent an Objective when Sub-programme is omitted"). Titles are taken verbatim from the indicator-annex table headers (Chapter 3.3's own SO1-SO6 titles differ from these — see the note below the table).

| `display_order` | `node_type` | `title` |
|---|---|---|
| 1 | Strategic Objective | Accelerate Reduction of the Burden of Communicable Diseases |
| 2 | Strategic Objective | Halt and Reverse the Burden of Non-Communicable Conditions |
| 3 | Strategic Objective | Reduce the Burden of Violence and Injuries |
| 4 | Strategic Objective | Improve Persons Centred Essential Health Services |
| 5 | Strategic Objective | Minimize Exposure to Health Risk Factors |
| 6 | Strategic Objective | Strengthen Collaboration with Health-Related Sectors |

**Important naming note:** the KHSSP document uses the label "Strategic Objective 1-6" for **two different sets** of content — Chapter 3.3's forward-looking objectives ("Reinforce and improve access to people-centered essential primary health services," etc.) and the indicator annex's differently-titled SO1-6 above. Only the annex set carries indicators and targets, so it is the set used here — Chapter 3.3's objectives have no measurable content to attach and are not represented as `StrategyNode` records in this distillation. If the module owner wants Chapter 3.3's objectives captured too, that is a second, separate set of six Strategic Objective nodes (or Supporting Framework) with no indicators — flag before adding, since an Objective with zero indicators fails STR-BR-012's submission-readiness check.

---

## 7. `PerformanceIndicator` + `PerformanceTarget` records

One wide row per indicator: `2027/28`'s comparison direction (`≥`/`≤`) is inferred from the target trend (increasing → **At least**; decreasing → **At most**) and stated in the `Cmp` column. **`Definition`** is not present in the source table at all — every indicator below needs a real definition sentence from a Strategy Author before submission (STR-BR-008 requires it, and STR-AC-008 blocks submission on an incomplete Indicator); until then, treat the indicator name as a placeholder, not a definition. **Unit** is inferred from the indicator's own wording and value range, not stated explicitly in the source either.

`Baseline` (2022/23) is shown for review only — it is not an importable field (§1). Blank cells (`—`) reproduce a blank cell in the source (see flags F7-F10); do not invent a value.

### 7.1 Strategic Objective 1 — Accelerate Reduction of the Burden of Communicable Diseases (28 indicators)

| # | Indicator | Unit | Cmp | Baseline 22/23 | 23/24 | 24/25 | 25/26 | 26/27 | 27/28 | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Proportion of under 1 year receiving DPT/Hep+HiB1 | Percentage | ≥ | 87.8 | 90 | 92 | 93 | 94 | 95 | KHIS |
| 2 | Proportion of under 1 year receiving DPT/Hep+HiB3 | Percentage | ≥ | 84 | 87 | 90 | 91 | 92 | 93 | KHIS |
| 3 | Proportion of under 1 year receiving vaccine against Measles and Rubella 1 | Percentage | ≥ | 84.2 | 85 | 86 | 86 | 87 | 90 | KHIS |
| 4 | Proportion of under two years receiving vaccine against Measles and Rubella 2 | Percentage | ≥ | 59.7 | 65 | 74 | 78 | 80 | 82 | KHIS |
| 5 | Proportion of 10-year-old girls receiving dose one of HPV Vaccine | Percentage | ≥ | 33 | 40 | 55 | 60 | 70 | 80 | KHIS |
| 6 | Proportion of 10-year-old girls receiving dose two of HPV Vaccine | Percentage | ≥ | 27 | 35 | 40 | 45 | 50 | 60 | KHIS |
| 7 | Proportion of under 1 year receiving IPV | Percentage | ≥ | 84.7 | 90 | 90 | 90 | 90 | 90 | KHIS |
| 8 | TB treatment success rate (all forms of TB) | Percentage | ≥ | 85 | 88 | 90 | 92 | 94 | 95 | TIBU |
| 9 | TB Treatment Coverage ⚠F1 | Percentage | ≥ | 69 | 72 | 75 | 78 | 60 | 80 | TIBU |
| 10 | TB case notification rate | Rate per 100,000 population | ≤ | 179 | 185 | 185 | 179 | 168 | 156 | TIBU |
| 11 | Proportion of HIV positive pregnant women currently on ART | Percentage | ≥ | 90 | 95 | 97 | 98 | 100 | 100 | KHIS |
| 12 | Antiretroviral therapy coverage (Adults) | Percentage | ≥ | 97 | 99 | 99 | 99 | 99 | 99 | KHIS |
| 13 | Antiretroviral therapy coverage (Children) | Percentage | ≥ | 80 | 85 | 90 | 95 | 95 | 95 | KHIS |
| 14 | Viral load suppression (adults) | Percentage | ≥ | 91 | 92 | 98 | 98 | 99 | 100 | EID/Database |
| 15 | Viral load suppression (children) | Percentage | ≥ | 61 | 70 | 74 | 80 | 95 | 95 | EID/VL Database |
| 16 | Advanced HIV disease screening (newly initiated on ART/RTT/CTF) | Percentage | ≥ | 61 | 70 | 80 | 90 | 95 | 100 | NDWH |
| 17 | Children under five with diarrhoea treated with ORS & Zinc | Percentage | ≥ | 55.3 | 60 | 65 | 70 | 75 | 80 | KHIS/KDHS |
| 18 | Total confirmed malaria cases | Rate per 1,000 persons/year | ≤ | 105 | 73.8 | 58 | 42.2 | 31.6 | 21.1 | KHIS |
| 19 | Proportion of pregnant women in malaria-endemic areas who slept under LLIN ⚠F3 | Percentage | ≤ | 98 | 70 | 75 | 80 | 85 | 90 | KDHS/KMIS/PMLLIN |
| 20 | Proportion of children in malaria-endemic areas who slept under LLIN | Percentage | ≥ | 51 | 75 | 78 | 80 | 85 | 90 | KDHS/KMIS/PMLLIN |
| 21 | Proportion of households with universal coverage of LLINs in malaria risk areas ⚠F4 | Percentage | ≥ | 48 | 80 | 70 | 60 | 80 | 70 | KDHS/KMIS |
| 22 | Proportion of eligible women/adolescents receiving 3+ doses of IPTp-SP | Percentage | ≥ | 48 | 54 | 61 | 67 | 74 | 80 | KHIS/KMIS |
| 23 | Proportion of suspected malaria cases tested with mRDT or microscopy | Percentage | ≥ | 89 | 100 | 100 | 100 | 100 | 100 | KHIS |
| 24 | Proportion of people living with HIV receiving nutrition assessment, counselling and support ⚠F2 | Percentage | ≥ | 50 | 55 | 60 | 65 | 70 | 75 | KHIS |
| 25 | Proportion of people on TB treatment receiving nutrition assessment, counselling and support ⚠F2 | Percentage | ≥ | 50 | 55 | 60 | 65 | 70 | 75 | KHIS |
| 26 | Proportion of travellers screened for notifiable diseases at all points of entry | Percentage | ≥ | 77 | 79 | 81 | 83 | 85 | 100 | POES Monthly report |
| 27 | Proportion of conveyances disinfected and/or issued with certificates | Percentage | ≥ | 84 | 85 | 86 | 87 | 88 | 100 | POES Monthly report |
| 28 | Proportion of designated health facilities providing travel related vaccination services | Percentage | ≥ | 70 | 75 | 80 | 85 | 90 | 100 | POES Monthly report |

Row 24/25 use `75` (not the source's literal `0.75`) per flag F2 — recorded here as the corrected reading since it is not plausibly a real target value; verify against the source before final import.

### 7.2 Strategic Objective 2 — Halt and Reverse the Burden of Non-Communicable Conditions (15 indicators)

| # | Indicator | Unit | Cmp | Baseline 22/23 | 23/24 | 24/25 | 25/26 | 26/27 | 27/28 | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Incidence of hypertension | Rate per 100,000 OPD cases | ≤ | 2,784 | 2,645 | 2,513 | 2,387 | 2,268 | 2,154 | KHIS |
| 2 | Incidence of diabetes | Rate per 100,000 OPD cases | ≤ | 1,158 | 1,100 | 1,045 | 993 | 943 | 896 | KHIS |
| 3 | Proportion of persons living with hypertension achieving control (<140/90) | Percentage | ≥ | 59 | 62 | 66 | 70 | 75 | 80 | KHIS |
| 4 | Proportion of people screened for hypertension at community, successfully linked to care | Percentage | ≥ | 18 | 23 | 28 | 33 | 38 | 45 | KHIS and SPICE |
| 5 | Proportion of adults (18-69) with raised blood glucose currently on medication for diabetes | Percentage | ≤ | 1.9 | 1.9 | 1.85 | 1.8 | 1.75 | 1.7 | STEPS |
| 6 | Proportion of persons living with diabetes achieving control (HbA1c <7) | Percentage | ≥ | 53 | 58 | 65 | 70 | 75 | 80 | KHIS |
| 7 | Proportion of health facilities with capacity to offer cardiovascular disease services (readiness) | Percentage | ≥ | 55 | 73 | 75 | 85 | 90 | 95 | KHFA/QOC |
| 8 | Proportion of outpatient clients with mental health conditions ⚠F9-style gap (23/24 blank) | Percentage | ≤ | — | — | 25 | 23 | 21 | 19 | KHIS |
| 9 | Percentage of women aged 25-49 years screened for cervical cancer ⚠F5 | Percentage | ≥ | 30.9 | 30 | 45 | 50 | 55 | 60 | KHIS |
| 10 | Proportion of cancers diagnosed in early stages | Percentage | ≥ | — | 35 | 40 | 45 | 50 | 60 | National Cancer Registry |
| 11 | Number of days from diagnosis to initiation of cancer treatment | Days | ≤ | — | 100 | 90 | 80 | 70 | 60 | National Cancer Registry |
| 12 | Proportion of women 25-74 years undergoing clinical breast examination | Percentage | ≥ | — | 10 | 15 | 30 | 50 | 70 | KHIS |
| 13 | Age-standardized prevalence of raised blood pressure among adults 18+ | Percentage | ≤ | — | 30 | 28 | 26 | 24 | 22 | STEPS and WHO |
| 14 | Prevalence of dental caries in adults | Ratio (0-1 scale, as reported) | ≤ | 0.343 | — | — | 0.2575 | — | 0.193 | Kenya Oral Health Survey |
| 15 | Prevalence of dental fluorosis among children | Ratio (0-1 scale, as reported) | ≤ | 0.414 | — | — | 0.3105 | — | 0.233 | Kenya Oral Health Survey |

Row 14-15's unit is deliberately not "Percentage" — the source values (0.343, 0.2575, etc.) are on a 0-1 scale, and STR-BR-011 requires Percentage values to fall between 0 and 100; forcing these into "Percentage" would fail that rule. Flag for the Strategy Author to confirm the intended scale before import.

### 7.3 Strategic Objective 3 — Reduce the Burden of Violence and Injuries (6 indicators)

No baseline column exists in the source table for this Strategic Objective (⚠F7) — all values below are targets only.

| # | Indicator | Unit | Cmp | 23/24 | 24/25 | 25/26 | 26/27 | 27/28 | Source |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Road traffic injuries | Rate per 1,000 OPD visits | ≤ | 2.2 | 2.1 | 2.0 | 1.9 | 1.8 | KHIS |
| 2 | Number of SGBV survivors seen | Count | ≤ | 3,833 | 3,200 | 2,700 | 2,500 | 2,300 | KHIS |
| 3 | Proportion of SGBV survivors presenting to facility within 72 hours | Percentage | ≥ | 59 | 64 | 69 | 75 | 80 | KHIS |
| 4 | Percentage of women aged 15-49 years who experienced gender-based violence | Percentage | ≤ | 32 | 27 | 22 | 17 | 12 | KHIS |
| 5 | Number of snake bites cases seen in OPD | Count | ≤ | 17,567 | 15,810 | 14,229 | 12,806 | 11,526 | KHIS |
| 6 | Number of dog bites cases seen in OPD | Count | ≤ | 66,439 | 59,795 | 53,816 | 48,434 | 43,591 | KHIS |

### 7.4 Strategic Objective 4 — Improve Persons Centred Essential Health Services (32 indicators)

| # | Indicator | Unit | Cmp | Baseline 22/23 | 23/24 | 24/25 | 25/26 | 26/27 | 27/28 | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Proportion of hospitals providing CEmONC services | Percentage | ≥ | 16.2 | 23 | 30 | 37 | 44 | 50 | HHFA/QOC |
| 2 | Percentage of Pregnant women who completed 8 ANC contacts | Percentage | ≥ | 4 | 8 | 12 | 16 | 20 | 24 | KHIS |
| 3 | Percentage of Low birth weight in health facilities | Percentage | ≤ | 6 | 6 | 5 | 4 | 4 | 4 | KHIS |
| 4 | Proportion of children under five whose developmental milestones are on track | Percentage | ≥ | 78 | 79 | 80 | 81 | 82 | 83 | KHIS |
| 5 | Proportion of children under five with diarrhoea treated with Zinc/ORS combined (facility) | Percentage | ≥ | 32 | 35 | 40 | 45 | 50 | 55 | KHIS |
| 6 | Proportion of children under five with diarrhoea treated with Zinc/ORS Copack (community) | Percentage | ≥ | 85 | 87 | 88 | 90 | 91 | 91 | KHIS |
| 7 | Proportion of children under 5 with pneumonia treated with amoxicillin DT (facility) | Percentage | ≥ | 58 | 60 | 65 | 70 | 75 | 80 | KHIS/KDHS |
| 8 | Proportion of low birth weight/preterm babies put on Kangaroo Mother Care | Percentage | ≥ | 60 | 65 | 68 | 70 | 73 | 75 | KHIS/KDHS |
| 9 | Proportion of newborns applied chlorhexidine for umbilical cord care at birth | Percentage | ≥ | 72 | 73 | 74 | 75 | 76 | 80 | KHIS |
| 10 | Proportion of skilled deliveries conducted in health facilities | Percentage | ≥ | 73 | 74 | 75 | 76 | 77 | 78 | KHIS |
| 11 | Modern Contraceptives prevalence rate (mCPR, all women) | Percentage | ≥ | 57 | 58 | 59 | 60 | 61 | 62 | KDHS |
| 12 | % of women of reproductive age with unmet needs for family planning | Percentage | ≤ | 14 | 13.5 | 13 | 12.5 | 12 | 11.5 | KDHS |
| 13 | Fresh stillbirth rate per 1,000 births in facilities ⚠F6 | Rate per 1,000 births | ≤ | 10.6 | 6 | 6 | 6 | 5 | 5 | *(garbled in source — verify)* |
| 14 | Number of maternal deaths in health facilities per 100,000 deliveries | Rate per 100,000 deliveries | ≤ | 90 | 87 | 84 | 81 | 78 | 75 | KHIS |
| 15 | Maternal deaths audited | Percentage | ≥ | 93 | 94.4 | 95.8 | 97.2 | 98.6 | 100 | KHIS |
| 16 | Caesarean Birth rate | Percentage | ≤ | 17 | 17 | 15 | 14 | 13 | 12 | KHIS |
| 17 | Proportion of facilities providing oral health services | Percentage | ≥ | 13 | 13 | 18 | 25 | 35 | 50 | Health Facility Census report, KHIS |
| 18 | Discharges from Outpatient Therapeutic Program (OTP) who recovered (SAM cure rate) | Percentage | ≥ | 82 | 82 | 82 | 83 | 83 | 84 | KHIS |
| 19 | Proportion of facilities complying with inpatient feeding guidelines | Percentage | ≥ | — (ND) | — (ND) | — (ND) | 60 | 80 | 100 | MOH/Clinical nutrition program reports |
| 20 | Proportion of pregnant women attending ANC who received combined iron and folate supplements | Percentage | ≥ | 75 | 75 | 78 | 80 | 82 | 82 | KHIS |
| 21 | Proportion of new ANC clients with low Hb <11mg/dl | Percentage | ≤ | 25 | 23 | 22 | 20 | 18 | 15 | KHIS |
| 22 | Proportion of brands of maize flour compliant to fortification standards | Percentage | ≥ | 46 | 48 | 50 | 52 | 53 | 55 | MoH-DND Industrial Survey reports |
| 23 | Proportion of facilities offering adolescent and youth friendly services ⚠F8 | Percentage | ≥ | 62 | 70 | 78 | — | 85 | 90 | KAHS/KDHS |
| 24 | Proportion of adolescents 10-19 equipped with knowledge for decision making ⚠F8 | Percentage | ≥ | 30 | 45 | 60 | — | 70 | 80 | KAHS |
| 25 | Proportion of adolescents 10-19 reached with key health messages ⚠F8 | Percentage | ≥ | 30 | 45 | 55 | — | 65 | 80 | KAHS |
| 26 | Proportion of facilities providing Ear and Hearing care services | Percentage | ≥ | — | — | 20 | 30 | 40 | 50 | Health Facility Census reports, KHIS |
| 27 | Schistosomiasis MDA Treatment coverage in endemic sub-counties | Percentage | ≥ | 60 | 75 | 85 | 100 | 100 | 100 | Programme reports |
| 28 | Soil Transmitted Helminths MDA Treatment coverage in endemic sub-counties | Percentage | ≥ | 75 | 90 | 95 | 100 | 100 | 100 | Survey Reports |
| 29 | Trachoma MDA Treatment coverage in endemic sub-counties | Percentage | ≥ | 80 | 85 | 90 | 100 | 100 | 100 | Survey Reports |
| 30 | Proportion of villages certified as open defecation free | Percentage | ≥ | 30 | 37 | 49 | 55 | 60 | 65 | KRTMS-CLTS |
| 31 | Proportion of health facilities implementing occupational health and safety standards | Percentage | ≥ | 25 | 30 | 40 | 50 | 60 | 80 | Program reports/surveys/KHIS |
| 32 | Number of hospitals with waste treatment equipment compliant to climate/health requirements | Count | ≥ | 16 | 20 | 40 | 55 | 60 | 65 | Program report/Surveys/KHIS |

### 7.5 Strategic Objective 5 — Minimize Exposure to Health Risk Factors (12 indicators)

| # | Indicator | Unit | Cmp | Baseline 22/23 | 23/24 | 24/25 | 25/26 | 26/27 | 27/28 | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Proportion of children 6-59 months supplemented with two doses of Vitamin A | Percentage | ≥ | 83.7 | 84 | 84 | 84 | 84 | 85 | KDHS/KHIS |
| 2 | Proportion of children 6-23 months achieving Minimum Dietary Diversity | Percentage | ≥ | 39 | 40 | 42 | 43 | 45 | 50 | KDHS/KHIS |
| 3 | Proportion of adult population consuming 5 servings of fruit/vegetable per day | Percentage | ≥ | 6 | 10 | 15 | 20 | 25 | 35 | STEPS survey |
| 4 | Prevalence of raised total cholesterol in adults | Percentage | ≤ | 13.3 | 13.3 | 11 | 9 | 7 | 5 | STEPS |
| 5 | Prevalence of overweight and obesity among adults 18+ | Percentage | ≥ | 27.9 | 28 | 28.2 | 28.4 | 28.6 | 28.8 | STEPS |
| 6 | Percentage of population with low level of total physical activity | Percentage | ≤ | 6.5 | 6.5 | 6.3 | 6.1 | 5.9 | 5.8 | STEPS |
| 7 | Prevalence of current tobacco use among adults ⚠F9 | Percentage | ≤ | 13.3 | — | — | 11 | — | 9.7 | STEPS |
| 8 | Prevalence of harmful use of alcohol ⚠F9 | Percentage | ≤ | 12.7 | — | — | 11.5 | — | 10.5 | STEPS |
| 9 | Prevalence of physical violence among women ⚠F9 | Percentage | ≤ | 16 | — | — | 14 | — | 10 | KDHS |
| 10 | Percentage of women who have experienced intimate or sexual violence ⚠F9 | Percentage | ≤ | 7 | — | — | 5 | — | 2 | KDHS |
| 11 | Percentage of households using improved sanitation facilities ⚠F11 | Percentage | ≥ | 41 | 48 | 55 | 62 | 69 | 76 | KDHS |
| 12 | Percentage of households using improved safe water facilities ⚠F11 | Percentage | ≥ | 68 | 71 | 74 | 77 | 80 | 83 | KDHS |

### 7.6 Strategic Objective 6 — Strengthen Collaboration with Health-Related Sectors (14 indicators, 2 duplicated from SO5)

| # | Indicator | Unit | Cmp | Baseline 22/23 | 23/24 | 24/25 | 25/26 | 26/27 | 27/28 | Source |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Percentage of households using improved sanitation facilities ⚠F11 | Percentage | ≥ | 41 | 48 | 55 | 62 | 69 | 76 | KDHS |
| 2 | Percentage of households using improved safe water facilities ⚠F11 | Percentage | ≥ | 68 | 71 | 74 | 77 | 80 | 83 | KDHS |
| 3 | Percentage of Health facilities with access to a reliable power source | Percentage | ≥ | 89 | 93 | 94 | 96 | 98 | 100 | Health facility Census |
| 4 | Percentage of Health facilities with access to reliable water source | Percentage | ≥ | — (ND) | 83 | 88 | 93 | 97 | 100 | Health facility Census |
| 5 | Percentage of facilities with an electronic health information system (any form) | Percentage | ≥ | — (ND) | 31 | 70 | 80 | 90 | 100 | Health facility Census |
| 6 | Percentage of women completed secondary education ⚠F10 | Percentage | ≥ | 12.9 | — | — | 20 | — | 40 | KDHS |
| 7 | Proportion of health facilities with access to a road all year round | Percentage | ≥ | 84 | 87 | 94 | 96 | 98 | 100 | Health facility Census |
| 8 | Number of workplaces/organizations established with lactation spaces | Count | ≥ | 10 | 10 | 15 | 30 | 40 | 300 | MoH/DND program reports |
| 9 | Proportion of school going children dewormed | Percentage | ≥ | 84.7 | — | 100 | 100 | 100 | 100 | KHIS |
| 10 | Number of community health promoters trained on Household Air Pollution | Count | — | 2,668 | 20,000 | 20,000 | 20,000 | 30,000 | 18,000 | Program report/KHIS |
| 11 | Proportion of households using clean fuels/technologies for heating/cooking | Percentage | ≥ | 21 | 23 | 25 | 27 | 29 | 30 | KDHS |
| 12 | Reduction of ambient concentration of air pollutants (PM 2.5) | Concentration (µg/m³) | ≤ | 13 | 12 | 11 | 10 | 9 | 8 | WHO air quality database |
| 13 | Total number of dialogue days held | Count | ≥ | 43,237 | 43,500 | 44,000 | 45,000 | 46,000 | 47,000 | KHIS |
| 14 | Total number of community action days conducted | Count | ≥ | 50,864 | 53,400 | 60,000 | 65,000 | 70,000 | 80,000 | KHIS |

Row 10's `Cmp` is intentionally blank — the 27/28 target (`18,000`) is *lower* than 24/25-26/27 (`20,000`/`20,000`/`30,000`), a genuinely non-monotonic trend in the source (not flagged separately above only because it doesn't affect data integrity the way F1-F12 do — noted here for completeness).

**On the SO5/SO6 duplication (F11):** both copies are transcribed above rather than collapsed into one, because that is what the source document does. Whether the real Strategic Plan should attach these two indicators to SO5, to SO6, or to both is an authoring decision for the Strategy Author, not something this distillation should silently resolve — STR-BR-009 requires an indicator name to be unique **under its measured node**, which permits the same indicator name under two different Strategic Objectives, so both are schema-legal as written.

---

## 8. Totals

| Strategic Objective | Indicators | Targets (non-blank cells) |
|---|---|---|
| 1. Communicable Diseases | 28 | ~136 |
| 2. Non-Communicable Conditions | 15 | ~65 |
| 3. Violence and Injuries | 6 | 30 |
| 4. Essential Health Services | 32 | ~150 |
| 5. Health Risk Factors | 12 | ~48 |
| 6. Cross-Sectoral Collaboration | 14 | ~64 |
| **Total** | **107** | **~493** |

## 9. Suggested import path

This document is data, not a script. To turn it into real Strategy records:

1. Confirm the 5 Fiscal Year prerequisites (§3).
2. A Strategy Author uses `save_strategy_plan_draft` to create the plan and version 1 (§4-5 above), then `save_strategy_structure_draft` to build the hierarchy (§6) and attach each Indicator/Target (§7) — the same commands the UI calls, per this repo's seed convention ("seeds call the same commands the UI calls, never write governed DocTypes directly"). A bespoke one-off script driving these same service functions is preferable to a raw `frappe.get_doc(...).insert()` loop, for the same reason.
3. Resolve every `⚠`-flagged row in §2 before submission — STR-AC-007's target validation and STR-BR-011's percentage-range rule will reject some of these as written (e.g. F2's `0.75`, F14/15's 0-1-scale values under a "Percentage" unit) if not corrected first.
4. Write real `definition` text for all 107 indicators (§7's header note) — required by STR-BR-008, not optional.
5. Decide the SO5/SO6 duplication (F11) and the Chapter-3.3-vs-annex naming question (§6.2) before treating this as final.
