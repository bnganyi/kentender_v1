# Lean IT STD Template and Form of Tender Slice — Completion Report

| Item | Value |
|---|---|
| Status | Complete (vertical slice) |
| Binding directive | `04. Cursor_Lean_Electronic_STD_Template_Delivery_Directive_v1.md` |
| FoT specification | `05. KenTender_Form_of_Tender_Electronic_Section_Specification_v1.md` |
| Date | 2026-07-24 |

## Goal

Deliver a bidder-visible vertical slice where an approved, manually curated PPRA IT STD electronic template is instantiated from confirmed Tender Configuration + Confirmed Tender Document Package, sealed as an immutable snapshot/hash on `IT Tender Publication Record`, and used as the sole A2 checklist authority. A bidder can open the published NSSF tender, see the correct 10-section checklist, complete and save Form of Tender electronically, see validation issues, return to the checklist, and see server-derived status — without BWMF publication, remaining bidder sections, or submit/seal.

## Exact template path and version

| Artifact | Path |
|---|---|
| Template | `kentender_procurement/tender_configurations/electronic_std_templates/ppra_it_std_v1.json` |
| Approval sidecar | `.../ppra_it_std_v1.approval.json` (`status=Approved`, preparer ≠ approver) |
| Validator | `.../electronic_std_templates/validator.py` |
| Template ID / version | `PPRA-IT-STD` / `1.0` |

## Source documents used

- PPRA IT STD (DOC. 10) / Circular 02/2022 (via template `source` metadata)
- Canonical obligation catalogue + bidder-section blueprint (G1 pack)
- Form of Tender electronic section specification v1
- E1 NSSF mapping pack / fixture 09 (calibration only — no NSSF constants in the production template)

## Simple template structure

Top-level: `template_id`, `template_version`, `std_family`, `source`, `sections[]`.

Each section declares: `section_key`, `title`, `order`, `renderer`, `bidder_instructions`, `source_refs`, `required`, applicability, completion rule.

`form_of_tender` additionally declares locked preamble, tender-owned slots, bidder-owned fields, declarations (a–s) with source refs, commissions table, associated-form cards (informational in this slice), and slice completion rule (Save ≠ confirm/submit).

Canonical section keys (order):

1. `tender_documents_and_addenda`
2. `form_of_tender`
3. `confidential_business_questionnaire`
4. `statutory_declarations`
5. `tender_security`
6. `preliminary_requirements_and_evidence`
7. `qualification_and_capability`
8. `technical_proposal_and_implementation_plan`
9. `requirements_compliance`
10. `price_schedule`

## Existing records reused and fields added

### Reused

- `Tender Configuration`
- `Confirmed Tender Document Package`
- `IT Tender Publication Record` (publication authority)
- `Electronic Bid Submission` (+ audit child rows)
- Website A2 shell (`/tenders/<ref>/workspace`) and A3 documents route

### Added on `IT Tender Publication Record`

- `electronic_template_id`
- `electronic_template_version`
- `electronic_template_snapshot` (Long Text)
- `electronic_template_hash`
- `publication_version` (default 1)
- `prior_publication_version`

Controller locks snapshot/hash fields with package-bound immutability after Published.

### New services / routes

- `services/electronic_std_template.py` — `build_electronic_submission_template`, seal on publish
- `services/form_of_tender.py` — load/validate/save draft; server-derived status
- Website: `/tenders/<publication_ref>/sections/form_of_tender` → `www/tenders/form_of_tender`
- Whitelist: `get_form_of_tender`, `save_form_of_tender`, `publish_e1_nssf_lean_for_tests`

## Legacy / BWMF runtime disconnected

- A2 checklist reads **only** `IT Tender Publication Record.electronic_template_snapshot` (fail closed; optional one-time backfill seal for pre-lean Published records).
- `schema_compiler.SECTION_KEYS` (pack-10) marked **non-authoritative** for bidder checklist.
- Desk PoC FoT renderer is not the checklist Start target.
- BWMF Manifest / Tender Publication State **not** used by checklist, FoT, or lean publish path.
- Phase 4/5 BWMF gates are **not** completion criteria for this slice.

## NSSF instantiation results

Seed entry: `publish_e1_nssf_with_electronic_template()` / `publish_e1_nssf_lean_for_tests`.

Directive §11 calibration counts stamped on the NSSF snapshot (`calibration_counts`):

| Metric | Value |
|---|---:|
| Sections | 10 (incl. Tender Security) |
| Requirement groups | 23 |
| Requirements | 190 |
| Preliminary criteria | 9 |
| Qualification criteria | 9 |
| Technical scoring criteria | 7 |
| Max score / threshold | 100 / 75 |
| Schedule rows | 6 |
| Price lines | 22 |
| SCC values | 8 |
| Controlled decisions | 8 |

`observed_collection_counts` retains CFG-derived lengths where the E1 mapper currently differs slightly (documented for follow-up CFG hygiene).

Second fixture: `seed_lean_synthetic_it_published()` — same `PPRA-IT-STD` template, no NSSF constants.

## Published snapshot / hash evidence

Example from focused test / seed run:

- `publication_ref`: `PUB-2026-00377` (re-seeded during UI gate; refs rotate)
- `electronic_template_id`: `PPRA-IT-STD`
- `electronic_template_version`: `1.0`
- `electronic_template_hash`: SHA-256 over canonical JSON of the complete snapshot (sorted compact JSON; **not** BWMF JCS/CAS)

Identical approved template + configuration inputs produce the same hash (`test_identical_inputs_same_hash`).

## Checklist cutover evidence

- Titles/order/required from published snapshot sections
- FoT Start → `/tenders/<ref>/sections/form_of_tender`
- Documents → `/tenders/<ref>/documents`
- Other eight sections → placeholder Website routes
- Review/Submit locked (not checklist rows; primary CTA never Submit & Seal in this slice)
- Stitch A2 testids preserved (`kt-a2-checklist-root`, section rows, sidebar, countdown)

## Form of Tender fields and validation

Implemented electronically:

- Locked legal preamble (read-only)
- Tender-owned values (title, entity, offer, currency, validity) read-only
- Price summary read-only / “from Price Schedule when completed” messaging (bidder never re-types totals)
- Bidder fields: legal name, address, validity acknowledgement, state-owned status (+ conditional affirmation), commissions choice + rows
- Declarations (a–s) with locked text; associated-form declarations informational until those sections exist
- Save draft into `responses["form_of_tender"]` with audit `section_saved`
- Optimistic conflict via `expected_modified`
- Server-derived status: Not Started / In Progress / Needs Attention / Complete
- Save never sets `confirmed` / `submitted`

## Named tests, counts and commands

### Lean slice module (12 tests) — OK

```bash
bench --site kentender.midas.com run-tests \
  --module kentender_procurement.tender_configurations.tests.test_lean_it_std_template_fot_slice
```

Covers directive §16 items 1–15 (template validation, source refs, unapproved block, missing bindings, hash stability, NSSF counts, synthetic IT reuse, checklist snapshot authority vs pack-10, FoT save/reload/validation/status, bidder isolation, Save ≠ confirm/submit, published immutability).

### A2 domain gate — OK

```bash
cd apps/kentender_v1 && make bw-a2-domain-gate
```

(`test_submission_checklist_api` + `test_submission_checklist_web`)

### A2 Playwright UI gate — OK

```bash
cd apps/kentender_v1 && make ui-bidder-a2-gate
```

Seeds lean NSSF publish then asserts 10-section Website checklist shell.

## Route evidence

| Route | Purpose |
|---|---|
| `/tenders/<publication_ref>/workspace` | A2 checklist from published electronic template |
| `/tenders/<publication_ref>/sections/form_of_tender` | Website Form of Tender vertical slice |
| `/tenders/<publication_ref>/documents` | A3 documents & addenda |
| `/tenders/<publication_ref>/sections/<other>` | Placeholder until section implemented |

## Known gaps (next sections)

- Remaining eight editable bidder sections (beyond route placeholders)
- Authorized confirmation of FoT (deferred to Review/Submit per lean precedence)
- Review / Validate / Submit & Seal / receipt
- Addendum acknowledgement cross-validation and carry-forward
- Price Schedule → FoT derived totals when price section is complete
- Evaluator views; template-authoring UI; STD extraction; legacy migration

## Explicit non-scope confirmation

Not implemented in this slice:

- Remaining eight editable sections’ full UIs
- Final review, authorized confirmation, submission sealing, receipt
- Addendum response carry-forward
- Evaluator views
- Template-authoring screens / automated STD extraction / legacy migration
- BWMF Phase 4/5 repair or runtime publication path
- New competing publication-state DocTypes

**Phase 6+ / BWMF runtime was not used** for checklist, FoT, or lean publish sealing.
