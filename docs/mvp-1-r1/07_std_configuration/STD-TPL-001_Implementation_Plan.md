# STD-TPL-001 v0.2 — IT Equipment Tender Template Curation — Implementation Plan

**Authority:** STD-TPL-001 v0.3 - Proposed for curation review (supersedes v0.2; adds the two-output Invitation/issued-Tender boundary per ITT 5.2)
**Companion:** TPR-CHG-001 v0.2 - Proposed (downstream consumer once this template is approved)
**Owning app:** kentender_procurement (future implementation pack only; not touched by this curation)
**Status:** Curation not started — Pass 1 not yet authorized to begin

## 1. Why this plan exists

STD-TPL-001 v0.2 defines the first KenTender tender template, `IT-EQUIPMENT-OPEN-V1`, produced by a six-pass, gate-controlled curation procedure (its own §14 / Appendix A). Each pass stops for human review before the next may begin. The work spans multiple sessions and produces a folder of interdependent evidence files (registers, a Jinja HTML master, a rendered fixture, a review record). This plan and its companion tracker exist so that:

- gate approvals and open issues survive context resets between sessions;
- no pass is started, or treated as complete, without the specific human confirmation STD-TPL-001 requires at its gate; and
- scope stays exactly what STD-TPL-001 v0.2 authorizes — curation only, no Frappe runtime work.

## 2. What this is not

This is document curation, not software implementation. Per STD-TPL-001 §14 and Appendix A, no DocType, hook, route, service, permission, patch, seed, or runtime template code may be created or modified under this work. `render_fixture.py` is curation-only tooling; it is never imported by KenTender. A later, separately authorized implementation pack will state how the reviewed master and registers are encoded into `kentender_procurement`.

## 3. Controlling decisions (do not relitigate)

From STD-TPL-001 §2, binding for Version 1.0 of this template:

| Decision | First release |
|---|---|
| Procurement category | Goods - IT equipment |
| Procurement method | Open Tender only |
| Award package | One |
| Tender currency | One |
| Technical assessment | Pass/fail compliance |
| Financial assessment | Lowest evaluated responsive Tender |
| Standard text | Fixed and read-only |
| Tender-specific data | Five plain-language officer tasks |
| Template maintenance | Code-owned release; no Desk editor |

The template must reject: software implementation/integration/data-migration projects, construction/WORKS, consulting/non-consulting services, multiple award packages or lots, weighted technical scoring, multiple Tender currencies, any procurement method not covered by this release, and a Requisition whose technical package is missing or not approved.

## 4. Phase overview

Six phases map 1:1 to STD-TPL-001's six passes. Each phase ends at a gate (A–F) where curation must stop for human review; a pass is not treated as complete merely because its files exist.

| Phase | Scope | Depends on |
|---|---|---|
| 1. Establish the source | Copy the official PDF byte-for-byte into the curation workspace; run `pdfinfo`, `sha256sum`, `pdftotext -layout`, `pdftoppm`; complete `source_record.md` | Official PDF confirmed (done: `STD-FOR-PROCUREMENT-OF-GOODS.pdf`, poppler-utils confirmed installed) |
| 2. Complete source coverage | `coverage_register.csv` — one row per official heading, table, form and insertion instruction, each assigned one of the eight treatments in §5.1 | Phase 1 passes Gate A |
| 3. Define every permitted insertion | `insertion_points.csv` and `forms_register.csv`, built only from §7/§13 of STD-TPL-001 | Phase 2 passes Gate B |
| 4. Build the complete working master | `02_master/complete_tender.html` + `print.css`, official wording copied (not paraphrased), only approved Jinja keys/loops used | Phase 3 passes Gate C |
| 5. Build the KEBS fixture | `kebs_input.json`, `render_fixture.py`, `kebs_expected.html`/`.pdf`, `package_index.md`; unresolved-content grep must return nothing | Phase 4 passes Gate D |
| 6. Record the decision | `05_review/review_record.md` with one of APPROVE FOR IMPLEMENTATION PACK / CORRECT AND RE-REVIEW / REJECT THE PRODUCT PATTERN | Phase 5 passes Gate E |

## 5. Key risks per phase

- **Phase 1** — the supplied PDF must still be confirmed by the product owner as the exact official file at Gate A; possessing the file is not the same as confirming it.
- **Phase 2** — an incomplete coverage register can silently hide an unresolved prompt. `Not used by this released pattern` rows require both a reason and proof the official source permits that treatment; it must never be used to bury an open question.
- **Phase 3** — adding an officer-facing field that STD-TPL-001 §7/§13 does not authorize. Proposed additions go to `open_issues.md`, never straight into the register.
- **Phase 4** — paraphrasing fixed official wording instead of copying it verbatim; introducing inline styles outside `print.css`; embedding JavaScript, calculations, DB calls or permission checks in Jinja.
- **Phase 5** — replacing `StrictUndefined` or inserting blank defaults to force the fixture render to pass, which would mask a real coverage or insertion-point gap instead of surfacing it.

## 6. Decisions confirmed by the user

- 2026-08-28 — Official source PDF supplied at `docs/mvp-1-r1/07_std_configuration/STD-FOR-PROCUREMENT-OF-GOODS.pdf`.
- 2026-08-28 — `poppler-utils` (`pdfinfo`, `pdftotext`, `pdftoppm`) confirmed installed, unblocking Pass 1's mandated commands.
- 2026-08-28 — This plan and its companion tracker are documentation-only; no curation pass has been authorized to execute yet.

## 7. Out of scope for this plan/tracker task

- Creating or populating `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/` (the actual curation workspace) — created only when Pass 1 execution is explicitly authorized.
- Executing any of the six passes.
- Any change to `kentender_procurement` or any other Frappe app.

## 8. Version 1.2 delta (proposed) — a bid-response-definition register, not yet authorized

**Origin**: while planning BDS-CHG-001 v0.4 ("Supplier and Electronic Bid Submission"), that module's Phase 3 was found to need a machine-readable response/evaluation/contract-mapping register for `IT-EQUIPMENT-OPEN-V1` that does not exist in any approved STD-TPL-001 version to date. §9 ("Evaluation and supplier response") and §10 ("Contract treatment") of the current approved v0.6 describe this at a policy/prose level only ("no weighted scoring screen and no criterion builder," a table of applicable forms) — there is no structured, per-row register a downstream module's runtime could consume to render/validate a bidder-facing workspace. This is genuinely new scope, independent of the still-open `TPL-G07` gate (the Version 1.1 delta below, a different, already-complete piece of work awaiting only the sign-off).

**What exists so far**: `STD-TPL-001_Bid_Response_Definition_Proposal_IT-EQUIPMENT-OPEN-V1.md`, in this same folder — draft content authored directly from the approved bundle's own source (every file in `insertion_points.csv`/`forms_register.csv`/`fixtures/moh_input.json`/the rendered `complete_tender.html` read in full), proposing 9 declaration units, 11 technical response rows, warranty/comparable-experience/evidence content, tender security and a simplified price schedule, each with its evaluation and contract mapping, plus three flagged decisions that need the document owner's confirmation.

**What this plan/tracker task does not do, per the same discipline as §2 above**: this document is analysis and a proposal, not a STD-TPL-001 spec revision. Per this document's own established pattern (Pass 2's Gate-B pause: "Claude will not draft or amend STD-TPL-001 — a revision will be authored separately by the document owner"), no curation work on this delta begins, and no register file is created, until the document owner authors or approves a spec revision (the next version — v0.7 or later) that explicitly authorizes this new register, its response-type vocabulary, and the three flagged decisions. This mirrors exactly how the Version 1.1 delta below could not begin until v0.5 was approved.

**Relationship to BDS-CHG-001**: BDS-CHG-001's own plan treats this as an external dependency, not work it owns — see that module's plan D7/D20 and tracker row BDS-301, which point back here rather than duplicating this content.
