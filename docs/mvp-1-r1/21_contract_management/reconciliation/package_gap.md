# CM-CHG-001 v0.8: source handoff gap

| Control | Value |
|---|---|
| Version | 0.8-package-gap.3 (.2 read: Form No. 4 "Unknown" and "no contract destination" for payment and security terms; .1 read: "package gap", framed the eight-category package as something Award should carry) |
| Date | 14 October 2026 |
| Source | CM v0.8 §19.4, §19.5, §5.14, §3, §17.10 and §19.8; Award `award/services/eligibility.py::_content`; Award v0.5 §5.8; STD-TPL release 1.5 `06_runtime/downstream_rules.json` and `release_manifest.json`; read 14 Oct 2026 (tracker CM8-008) |
| Direction | Owner, 14 Oct 2026: "Award supplies the authoritative source material; CM generates the agreement. Award should not be expected to hold a completed eight-category agreement package before CM prepares it." The gap is "a required integration dependency already identified in approved v0.8 §19.8". |

## What this file is

**Who produces what (CM v0.8 §19.4).** The owning modules (Tenders, the template release, Bid Submission and Evaluation, Award, Budget, site configuration, supplier accounts) supply **source material** through an explicit, versioned interface. **Contract Management generates the agreement** from the issued Form No. 4 and its bindings, **assembles the complete signing package** (the eight manifest categories plus addenda and any incorporated document) and **freezes it** with its source versions and hashes. Award is not expected to hold an assembled package, and no user re-uploads what KenTender already holds (CM §9.2, §9.1: "Enter each business fact once").

**Method.** For each source CM needs: who owns it, what the Award handoff and the owning module give CM **today**, and the interface change the owner must make. Immutable document references are acceptable "if their exact contents remain retrievable and verifiable" (owner direction). This is reading of source, not a test. Phase 2 (S8) and Phase 5 verify against running code. CM never fills a gap by reading tender, bid, evaluation or award tables (plan D2).

**Status of the gaps.** They are **required work inside Package B (formation)**, specified in plan D20 and tracker rows CM8-513…CM8-521: verify the handoff, implement the missing owner-interface changes, update the affected current documentation, and prove that every required source is available. They are not a future follow-up, and they block formation acceptance until closed.

## What Award hands over today

The keys of the dictionary `_content` freezes into `Award Contracting Package.content_json`: `award_case`, `tender`, `tender_reference`, `lot`, `cycle`; `report` {id, version, digest, source}; `opinion` {id, version, digest, proof}; `decision` {id, version, outcome, supplier, organisation, bid, submitted_amount, evaluated_amount, currency}; `notice_batch` {id, version, notices[id, digest, given_at, evidence]}; `response` {id, response, by, received_at, authority}; `contract_terms` {quantity, warranty, and four fixed descriptive sentences: `delivery_and_warranty` = "As issued in the tender and the supplier's response", `reservation_treatment` = "As recorded in the tender's reservation lineage", `performance_security` = "As published in the tender (Contracting verifies before signature)", `tender_security` = "As recorded at submission"}; `restrictions[]`; `legal_profile`; `fixture_namespace`. Award v0.5 §5.8 says the package "includes the issued requirement and supplier response mappings needed for the contract, delivery/warranty commitments, applicable reservation treatment, published performance-security terms, tender-security references, and all current restrictions". **The built package carries references to its own records and descriptive sentences; the mappings and terms §5.8 names are not in it.**

## Source material CM needs, and the interface change each owner must make

Status: **Absent** (nothing usable reaches CM), **Partial**, **Unknown** (not established by reading; Phase 2 S8), **Present**.

| # | Source CM needs (CM v0.8) | Owner | Reaches CM today | Status | Required owner-interface change (versioned; contents retrievable and verifiable) |
|---|---|---|---|---|---|
| S1 | Issued tender instance, template release (`IT-EQUIPMENT-OPEN-V1`, release id) and **addenda** (list explicit even when empty) (§19.4 Source selection) | Tenders, STD-TPL | `tender`, `tender_reference`, `lot` only | Absent | Reference per issued item: identity, version, digest, retrieval. Addenda list with identities |
| S2 | **Accepted tender** and clarifications: the accepted offer (`tender_form`), incorporated acceptance and clarification letters | Bid Submission, Evaluation, Award | `decision.bid`, `submitted_amount`, `response` (the acceptance) | Partial | References to the accepted bid version and clarifications, with digests |
| S3 | **Price schedule** with original offered and awarded line ids, rates, quantities, UOM, tax and reconciled arithmetic (§19.4 Amount row) | Tenders, Award | totals and currency | Partial | Awarded lines and allocations as a versioned structure, or a reference to the price schedule document with digest |
| S4 | **Requirements schedule** and **technical specifications** (goods and delivery schedule, technical obligations, related services) | Tenders, template release | `contract_terms.quantity`, `warranty` strings | Partial | Release 1.5 maps these to destinations `CD-GOODS-DELIVERY-SCHEDULE`, `CD-TECHNICAL-OBLIGATION-SCHEDULE`, `CD-RELATED-SERVICES-SCHEDULE`; the values are not in the handoff. References with digests |
| S5 | **GCC and SCC** with exact clause ids, values and precedence wording; **payment, invoice period, advance and recovery, performance security, remedies, termination and change terms** (§19.4 commercial row; CM-R-07, 08, 12) | Template release, Tenders | fixed sentences ("As published in the tender") | **Absent from the handoff.** In the release: six response-rule destinations (delivery, technical, SCC warranty/support, related services, inspection/acceptance, price) **plus typed contract parameters** in `insertion_points.csv` — `contract.payment_terms`, `payment_days`, `performance_security.required` / `percentage` / `form_variant`, `delay_damages.rate_per_week` / `cap_percent`, `inspection_acceptance_office`, `contact_office` ("Contract projection parameter (Section VII)"). **No advance, invoice-process, change, termination or warranty-discharge parameters**; those exist only as GCC prose, which has no clause anchors | Carry the typed parameters and the GCC/SCC text with clause locators as retrievable references; add the missing parameters or a stated "not provided" in a compatible future release (never an edit to an issued tender) |
| S6 | **Inspection and acceptance criteria**, frozen for inspection (§5.5) | Tenders, template release | none | Absent (destination `CD-INSPECTION-ACCEPTANCE-SCHEDULE` exists in release 1.5) | References with digests; criteria typed per CM §5.5 |
| S7 | **Form No. 4** Contract Agreement source: body, declared placeholders, versioned anchors (§19.4 table, §19.2 extraction locators) | Template release (STD-TPL) | **Spike S8 (executed):** the installed release asset `02_master/complete_tender.html` is retrievable through the database and its SHA-256 recomputes to the recorded digest; Form No. 4 is a 3,170-byte fragment found by its heading text, with 15 blanks, 4 template placeholders (entity name and address, tender title and reference), the 8 incorporated documents a)–h), 2 witness lines and the "To be completed by the successful Tenderer" instruction. **The master has 25 element ids and none for Form No. 4, the GCC or the SCC.** Compared with the official PPRA DOCX (hash `ee081f60…f81` reproduced; paragraphs 2647–2667 are Form No. 4): normalised similarity 94.5% (typo fixed, lettered list, signing block laid out differently) | **Partial:** text present and verifiable; no stable anchor | Stable ids (`form-n4-agreement`, `gcc`, `scc` with clause ids) in a compatible release, or an owner provider that serves the Form No. 4, GCC and SCC fragments as separate digest-bound documents; the issued release text, not the PPRA file, governs conformance |
| S8 | **Award notification** meeting §134–135 content; **signing-window result with counting basis** (CM-R-02) | Award | each notice has `digest`, `given_at`, evidence | Partial: notice present; the window result is absent | Window result and counting basis as an Award fact; notification identity and digest |
| S9 | **Funding lineage**: REQ source allocation and reservation identities, exact awarded price allocation, tax and rounding (§5.14) | Award, Budget | fixed sentence `reservation_treatment` | Absent | Allocation identities and amounts (Budget's `get_funding_lineage` is the existing reader); a missing mapping is a funding issue, never a contract-officer allocation |
| S10 | **Entity** legal name and principal address (§19.4) | Site configuration (CFG) | none | Absent | Read once from the entity's site configuration (CFG) if it is held there — whether CFG holds a principal address was **not established** in Phase 0 — and never typed again |
| S11 | **Supplier** legal identity and form of entity (§19.4: a sole proprietor is not "incorporated"); signatories and representatives with authority evidence | Supplier accounts (existing core seam), Award | `decision.supplier`, `organisation`; `response.by`, `authority` | Present (identity and authority through `kt_supplier_account_provider`); acceptance evidence Present | none beyond the existing seam |
| S12 | Restrictions, later updates, `AwardDecisionRecorded v1` (§5.2, CM-R-13) | Award | `restrictions[]`, `receive_update`, `receive_decision_event` | Present (event payload content not re-read) | none |

**Count:** 12 sources: 5 absent (S1, S5, S6, S9, S10), 5 partial (S2, S3, S4, S7, S8), 0 unknown, 2 present (S11, S12). (Version .2 counted S7 unknown; spike S8 settled it.)

## What CM produces (not Award's duty)

| Output | Source (CM v0.8) |
|---|---|
| Generated agreement (Form No. 4 with bindings: date, entity, supplier, goods description, incorporated documents, amount, terms, signatories, witness fields) | §19.4 table |
| The eight-category manifest (`agreement`, `tender_form`, `price_schedule`, `requirements_schedule`, `technical_specifications`, `gcc`, `scc`, `award_notification`) plus addenda and every incorporated document, each entry with document id and version, file digest, category, release/instance, locator, inclusion basis and access projection | §19.4 |
| The frozen signing package: every signature binds the complete manifest and immutable bytes | §19.4, TRUST v0.6 §1 |
| Coverage result before **Send for signature**: all categories resolved, bindings complete, no unresolved placeholder, unchanged award, scope and price | §19.4 "Coverage result", CM-R-04 |

## Required handling (owner direction, 14 October 2026)

> Verify the current Award/source handoff against CM §19.4. Identify and implement any missing owner-interface changes, updating the affected current documentation. CM generates the agreement and freezes the complete incorporated package. Formation acceptance requires proof that every required source is available; unresolved gaps block that acceptance.

1. **Check** the current handoff against §19.4 — this file, rows S1–S12 (Phase 0 done).
2. **Supply the missing material** through an explicit, versioned interface from each owning module; immutable document references are acceptable where the exact contents stay retrievable and verifiable (plan D20).
3. **CM assembles** the generated agreement and freezes the complete package, preserving source versions and hashes.
4. **Close each gap inside Package B's implementation.** Formation is not declared complete while a required source is unavailable.

## Notes

- **Release identity.** The test site holds template release 1.5 (11 Oct 2026, manifest status `Candidate`); the dev site's latest is 1.4. CM v0.8 §17.4 names STD-TPL v0.15; the register has v0.17 approved. The release the canonical tender TND-MOH-2027-002 used was not established in Phase 0 (FU-CM-45).
- **What stays outside this gap.** Existing-contract registration supplies its executed package itself (the registrant uploads it; that is the intake). The handoff gap concerns the KenTender-award route only.
