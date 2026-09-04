# LAW-REG-001 — Statutory Correction Register

| Control | Value |
|---|---|
| Document ID | LAW-REG-001 |
| Version | 1.0 |
| Date | 3 September 2026 |
| Status | **Approved** |
| Approved on | 3 September 2026 |
| Purpose | Maps every planning-relevant provision of the Act and Regulations to the KenTender document it affects and the exact change required |
| Primary sources read in full | Public Procurement and Asset Disposal Act, Cap. 412C (as revised to 31 Dec 2022), 79pp; Public Procurement and Asset Disposal Regulations, Legal Notice 69 of 2020 (as revised to 31 Dec 2022), 111pp including all sixteen Schedules |

Every statement below cites the provision it rests on. Nothing here is inferred from a secondary source.

---

## 1. The Third Schedule — the plan format, verbatim

Regulation 42 requires the annual procurement plan to follow the Third Schedule format. That format is a sixteen-column table with a header block and a signature block.

**Header:** Ministry/Parastatal · Procuring Entity's Name · **Project Name (if applicable)** · Financial Year

| Col | Column | Guidance note |
|---|---|---|
| 1 | No. | At the entity's discretion |
| 2 | Item description | Comprehensive but not to the level of specifications |
| 3 | Unit | Unit of purchase or issue |
| 4 | Qty | In universally acceptable terms |
| 5 | Procurement Method | Limited to the eleven methods in note 5 below |
| 6 | Source of Funds | Government of Kenya or a donor |
| 7 | Estimated Cost (Kshs '000) | **Established through market surveys** |
| 8 | Time Process | **Planned dates, planned days, actual days, and variance** (variance = planned − actual), filled after activities conclude |
| 9 | Invite/Advertise Tender | Date |
| 10 | Bid opening | Date |
| 11 | Bid evaluation | Not more than 30 calendar days |
| 12 | Tender award | Date the accounting officer awards |
| 13 | Notification of Award | Date the letter is sent |
| 14 | Contract Signing | Date |
| 15 | Total time to contract signature | Days between notification and signing |
| 16 | Date for completion of contract | Days to completion |
| 17 | Status | Named in the guidance notes |

**Signature block:** Prepared by **Head of the Procurement Function** · Countersigned by **Accounting Officer** · Approved by **Cabinet Secretary / CECM / Board / Council**

### 1.1 Consequences

**The plan records actuals and variance, not only plans.** Column 8 requires planned days, actual days and variance. PLN-CHG-001 §11 currently prohibits showing "actual milestones" on every artboard. That prohibition is contrary to the prescribed format and must be reversed. It also supplies the data for the quarterly implementation report under regulation 40(6).

**PLN's seven planned dates are correct and traceable.** `invitation_date`, `bid_opening_date`, `evaluation_completion_date`, `award_approval_date`, `award_notification_date`, `contract_signing_date` and `delivery_completion_date` map to columns 9–14 and 16. Column 15 is derived. My earlier suggestion that seven dates might be over-modelled was wrong.

**The approval routes are four, not three.** CFG-CHG-002 v0.7 §4.1 lists Cabinet Secretary, County Executive Committee Member and Board of Directors. The Schedule adds **Council**. Add it.

**Preparation and countersignature are split.** The Head of the Procurement Function prepares; the Accounting Officer countersigns; the statutory authority approves. This matches PLN's Procurement Planner → Accounting Officer adoption → statutory approval sequence exactly.

---

## 2. Procurement methods — the plan's list is eleven

Third Schedule guidance note 5 limits the plan's method column to: **open tender, direct, restricted, request for quotation, low value, community participation, design competition, electronic reverse auction, force account, competitive negotiations, request for proposals.**

Section 92(1) of the Act lists thirteen methods, adding two-stage tendering and framework agreements. **Those two are absent from the plan format's list.** The plan catalogue is the Schedule's eleven.

This replaces the three-method restriction in PLN v1.8. It also resolves the problem that force account (reg 95(a)), specially permitted procurement (reg 107(2)(b)) and community participation (reg 109(d)) must each be identified in the plan.

Section 91(1): **open tendering is the preferred method**; an alternative may be used only where allowed and its conditions are satisfied.

---

## 3. The Second Schedule threshold matrix — actual figures

The matrix is keyed on **goods / works / services**, and also sets segregation of duties per method.

| Method | Goods | Works | Services |
|---|---|---|---|
| International open tender (s.89) | No min. Max determined by funds allocated in the budget for the particular procurement | Same | Same |
| National open tender (s.96) | No min. Max determined by funds allocated | Same | Same |
| Restricted tender s.102(1)(a) | No min. Max determined by funds allocated | Same | Same |
| **Restricted tender s.102(1)(b)** | **Max KES 30,000,000** | **Max KES 30,000,000** | **Max KES 20,000,000** — above this use open tender |
| Restricted tender s.102(1)(c) | No min. Max determined by funds allocated | Same | Same |
| Request for proposals (s.116) | No min. Max determined by funds allocated | Same | Same |
| Direct procurement (s.103) | No min or max, provided the section's conditions are met | Same | Same |
| **Request for quotations (s.105)** | **Max KES 3,000,000 per request** | **Max KES 5,000,000 per request** | **Max KES 3,000,000 per request** |
| **Low value procurement (s.107)** | **Max KES 50,000 per item per financial year** | **Max KES 100,000 per item per financial year** | **Max KES 50,000 per item per financial year** |

### 3.1 Consequence — a missing classification

**Method admissibility is keyed on goods, works or services.** PLN's `requirement_type_id` seed values are Non-consulting services, Consulting services and Goods. **Works is absent.** Without it the threshold check cannot run, because works carries different limits from goods and services at both the RFQ and low-value bands.

The plan therefore needs the goods/works/services classification as a distinct field from the requirement type, or the requirement type must be restructured to carry it.

Note also that the low-value limit is **per item per financial year**, not per transaction — so the check is cumulative across the plan, not per line.

---

## 4. Preference and reservation — the correct current provisions

| Provision | Requirement |
|---|---|
| **Regulation 149** | The accounting officer shall allocate **at least 30% of its annual procurement budget** for procuring goods, works and services from **enterprises owned by youth, women and persons with disability** |
| **s.53(6)** | All procurement **and asset disposal** planning shall reserve a minimum of 30% of budgetary allocations for enterprises owned by women, youth, persons with disabilities **and other disadvantaged groups** |
| **s.157(5)** | Reserve a prescribed percentage of the procurement budget, not less than 30%, **to the disadvantaged group** |
| **s.157(10)** | At least 30% of **procurement value in every financial year** allocated to youth, women and persons with disability |
| **s.158(1)** | Procuring entities **shall integrate preferences and reservations in their procurement plans** |
| **Reg 40(5) / s.33(2)(g)** | A county procuring entity shall indicate a **minimum 20%** allocation for resident tenderers of the county |

Regulation 149 is the correct current citation. My earlier reference to "regulation 31" was to the repealed Preference and Reservations Regulations under the 2005 Act.

### 4.1 Categories are wider than four

**s.157(4)** applies preferences and reservations to: disadvantaged groups; **micro, small and medium enterprises**; works, services and goods; **identified regions**; and other prescribed categories.

**Reg 151**: the regions are **counties, sub-counties and constituencies**, applicable where citizen contractors are based and operate.

**Reg 152**: exclusive preference to citizen contractors offering goods, services and works assembled, manufactured, mined, extracted or grown in Kenya — including motor vehicles, motorcycles, bicycles, plant and equipment assembled in Kenya; furniture, textile, foodstuffs, oil and gas, ICT, steel, cement, leather, agro-processing and sanitary products made in Kenya; and hospitality, air travel and security services.

### 4.2 One scheme at a time, highest advantage

**s.156**: where a person is entitled to more than one preference scheme, the scheme with the **highest advantage** applies. **Reg 153**: a candidate is entitled to **one** scheme at a time in a proceeding.

So `reservation_category` is not a free choice — where several could apply, the highest-advantage one governs.

### 4.3 Exclusive preference thresholds

**Reg 163**, for s.157(8)(a): exclusive preference to citizen contractors where funding is 100% national or county and the amount is below —

- **KES 1,000,000,000** for works, construction materials and other materials made in Kenya
- **KES 500,000,000** for goods and services

This is a planning-time classification currently absent from every document.

### 4.4 Unbundling is the statutory basis for lotting

**Reg 154**: despite s.54(1), an entity may unbundle a category of goods, works and services in practicable quantities to ensure maximum participation of citizen contractors, disadvantaged groups and SMMEs — and **may lot** them in quantities affordable to specific target groups.

So the lotting indicator required by reg 41(e) is tied to the reservation purpose. PLN v1.8 added the indicator and reversed the prohibition; that is correct and now has its rationale.

---

## 5. Reporting and publication — six distinct obligations

| Provision | What | To whom | When |
|---|---|---|---|
| **s.44(2)(c)** | Procurement plans, in conformity with the medium term fiscal framework | National Treasury | On preparation. National security organs exempt under s.44(3) |
| **s.53(12)** | Publish the **approved** plan **as an invitation to treat** on the entity website | Public | On submission to Treasury |
| **s.53(13)** | Treasury publishes plans as invitation to treat on the state tender portal | Public | On receipt |
| **s.158(2) / s.44(2)(i)** | The part of the plan demonstrating preference and reservation application | The Authority | **Within 60 days after FY commencement** |
| **s.157(12)–(13)** | Compliance certification with data disaggregated by youth, women, PWD | The Authority | **Every six months** |
| **s.158(3)** | All awards where a preference or reservation applied, disaggregated | The Authority | **Quarterly** |
| **Reg 40(6)** | Report on **implementation** of the annual procurement plan | Cabinet Secretary / CECM / governing body | **Quarterly** |
| **Reg 150(4)** | Payment performance statistics against the 60-day invoice obligation | National Treasury and the Authority | Quarterly |

**Reg 161(2)**: reports under s.157(12) and s.158(3) go to the Authority **within fourteen days after the end of the reporting period**, copied to the National Treasury, in formats the Authority provides.

Publication is statutory and is characterised as an **invitation to treat** — not a discretionary transparency measure.

---

## 6. Asset disposal — a separate plan with its own format

**s.53(4)**: all asset disposals shall be planned through an **annual asset disposal plan** in a format set out in the Regulations. **Reg 176(2)**: that format is the **Thirteenth Schedule**.

This is a distinct statutory instrument, not a section of the procurement plan. PLN v1.8 §4.4A puts disposal items inside the procurement plan and is structurally wrong.

### 6.1 Thirteenth Schedule columns, verbatim

**Header:** Financial Year · Name of the Procuring Entity

No. · Item Description · Qty · Unit of Issue · Date of purchase · Purchase Price · Estimated current value · Justification for disposal · Item Life span · Ref No to the asset register · Disposal Method · Cost of managing disposal

**Dates for completing key disposal activities:** Disposal Initiation · Bid Documents Prepared · Invitation To Tender/Public Auction · Bid Opening/Registration of Bidders · Accounting officer Award/Fall of Auction Hammer · Notification of Award · Contract Signed · Disposal Completed · **Notice to PPRA (if Disposal to Employee)**

**Signature block:** Prepared by **Head of Procurement** · Approved by **Accounting Officer**

### 6.2 The disposal plan is approved by the Accounting Officer

The Thirteenth Schedule signature block names the Accounting Officer as approver. The Third Schedule names the Cabinet Secretary, CECM, Board or Council. **The two plans have different approval authorities.** Section 53(5) speaks of "procurement and asset disposal planning" being approved by CS or CECM for a State or County Department, so for those entities the position needs care; the Schedule is the prescribed format and names the Accounting Officer.

### 6.3 Reg 176(3) content list

Item description for boarding; quantity; unit of issue; date of purchase; purchase price; estimated current value; justification for disposal; lifespan of item for boarding; reference number to the assets register or stores records; envisaged disposal method; time schedule; **an indication whether the disposal is to be managed by the procuring entity or any special agency or hired expert**; and **the cost of managing the disposal process**.

The manager indication has no column in the Thirteenth Schedule — the same content-versus-format gap that exists between regulation 41 and the Third Schedule.

**Reg 176(4)**: the disposal plan **shall be flexible to accommodate emerging issues** in the disposal process. That is an express instruction against a rigid immutable-version model for this plan.

### 6.4 Disposal methods and reasons

**s.165(1)**: transfer to another public entity, with or without financial adjustment; sale by public tender; sale by public auction; trade-in; **waste disposal management**; or as prescribed. My §4.4A used "Destruction", which is not statutory.

**s.163(1) / reg 176(1)**: items declared **unserviceable, surplus, obsolete or obsolescent**. My §4.4A used "Expired", which is not statutory.

**s.165(2)**: radioactive or electronic waste may be disposed of only to persons licensed under the Environmental Management and Co-ordination Act.

**s.4(2)(b)** excludes transfer of assets between public entities **without financial consideration** from the Act entirely, while s.165(1)(a) lists transfer "with or without financial adjustment" as a disposal method. Recorded as a tension, not resolved here.

### 6.5 Disposal governance

**Reg 177**: the disposal committee comprises a chairperson who is a head of department; the head of the finance function; at least three heads of user departments, one of whom heads the disposing department; and the head of the procurement function as secretary. **Reg 178**: quorum is three including the chairperson.

**s.45(4)**: asset disposal processes shall be handled by **different persons** in respect of identification, consolidation, **preparation of a disposal plan**, pricing, and the disposal itself.

**s.164(3)**: a technical report sets a **reserve price** — the minimum acceptable price below real market value. **s.166**: no disposal to employees or board or committee members except as expressly allowed; disposal pursuant to artificial valuation is an offence.

---

## 7. Confirmed correct — no change needed

| Position | Authority |
|---|---|
| The Departmental Procurement Plan is statutory | Reg 34(i): user department prepares departmental procurement and asset disposal plans and submits to the procurement function. Reg 40(3): head of user department submits an annual departmental procurement plan **before the financial year commences** |
| Departmental Needs has no statutory standing and is internal consultation | No provision creates it; the DPP is the statutory instrument |
| Statutory approval above the accounting officer is mandatory for the procurement plan | Reg 40(4); Third Schedule signature block |
| Reservation belongs at requisition, not planning | s.53(8): no procurement proceeding until satisfied funds are in the approved budget estimates. Reg 71(1): the head of user department initiates through a requisition **as per the approved procurement plan** |
| One plan-level funding confirmation | s.53(2): the plan is prepared within the approved budget — an affordability test |
| The plan is part of budget preparation | s.53(2), reg 40(1) |
| Multi-year plans consistent with the MTEF | s.53(7), reg 40(2) |
| The estimate includes incidentals | Reg 41(i); Third Schedule note 7 adds "established through market surveys" |
| Anti-splitting control | s.54(1), reg 43(1) |
| Market price index as a benchmark | s.54(3), reg 43(2)–(4); s.54(2A)–(2B) add entity market surveys and a six-monthly cost handbook for infrastructure |
| Classified procurement is a separate channel | s.90; reg 84 — annual list to the Cabinet Secretary by 30 July, Tenth Schedule format, Cabinet approval |

---

## 8. Change register by document

### PLN-CHG-001 (currently v1.8)

| # | Change | Authority |
|---|---|---|
| P1 | Reverse the prohibition on actual milestones. Add actual dates and variance per Plan Item. | Third Schedule col 8 |
| P2 | Add the **Status** column and the optional **Project Name** header. | Third Schedule col 17, header |
| P3 | Replace the three-method catalogue with the Schedule's **eleven**. Open tender is the default. | Third Schedule note 5; s.91(1) |
| P4 | Add **goods / works / services** classification; key method admissibility on it. Add **Works** to the requirement-type seed. | Second Schedule |
| P5 | Load the real threshold figures in §3 above; make the low-value check **cumulative per item per financial year**. | Second Schedule |
| P6 | Expand reservation categories to disadvantaged groups, MSMEs, identified regions, and the national/citizen reservations; add the highest-advantage resolution rule. | s.157(4), s.156, reg 151–153 |
| P7 | Add exclusive-preference classification at KES 1bn works / KES 500m goods and services. | Reg 163 |
| P8 | Add the six reporting obligations in §5 as either implemented outputs or named non-goals with retained lineage. | s.44(2)(c), 53(12)–(13), 157(12), 158(2)–(3), reg 40(6), 150(4), 161(2) |
| P9 | Characterise publication as **invitation to treat** on the entity website. | s.53(12) |
| P10 | Remove §4.4A disposal items from the procurement plan. | s.53(4) |
| P11 | Correct the estimate basis note to add "established through market surveys". | Third Schedule note 7 |

### New: DSP-CHG-001 — Annual Asset Disposal Plan

A separate change unit built on the Thirteenth Schedule format, reg 176 contents, s.165 methods, s.163(1) reasons, reg 177–179 committee, and s.45(4) segregation. Approved by the Accounting Officer. Explicitly flexible per reg 176(4).

### CFG-CHG-002 (currently v0.7)

| # | Change | Authority |
|---|---|---|
| C1 | `statutory_approval_route` gains a fourth value: **Council**. | Third Schedule signature block |
| C2 | Regulator reference register carries the Second Schedule matrix keyed on goods/works/services with the figures in §3, the reg 163 exclusive-preference thresholds, the reg 164 margins of preference, the 30% reservation target and the county 20%. | Second Schedule, reg 163–164, reg 149, reg 40(5) |
| C3 | Add a disposal-plan intake flag if the disposal plan follows the same annual cycle. | Reg 176 |

### BUD-CHG-001 (currently v1.4)

No change. Section 53(8) confirms the funds test sits at procurement commencement, which is where reservation now lives.

### NDS-CHG-001 (currently v1.6)

No change. Its standing as non-statutory internal consultation is confirmed by the absence of any provision creating it.

---

## 9. Still outstanding

The **margin of preference** table in regulation 164 (20%, 15%, 10%, 8%, 6% by Kenyan shareholding and origin) applies at tender evaluation, not planning. It is recorded here so the Tender module inherits it rather than rediscovering it.

Nothing in the two instruments remains unread.
