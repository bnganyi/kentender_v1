# STD-TPL-001 — tracker

**Authority:** STD-TPL-001 v0.3 - Proposed for curation review (supersedes v0.2; adds the two-output Invitation/issued-Tender boundary)
**Status:** IT-EQUIPMENT-OPEN-V1 Version 1.0 LOCKED 2026-08-28. All six passes and Gates A-F complete; decision APPROVE FOR IMPLEMENTATION PACK (`05_review/review_record.md`). No further curation edits to the locked files — a future change is a new version with its own gate sequence. Implementation-pack authorization is a separate, not-yet-started step
**Started:** 2026-08-28

## Tracker rules

1. Status vocabulary: `Planned`, `In progress`, `Blocked`, `Done`, `Permanently paused`.
2. A pass stops at its gate for human review. It is not marked `Done` merely because its files exist — only when the named reviewer has confirmed the gate's exit condition.
3. No field, form, variant or policy choice may be added to any register or the working master beyond what STD-TPL-001 v0.2 §7/§13 authorizes. A proposed addition goes to `open_issues.md`, not directly into a register.
4. Every row requires evidence (a file path, a reviewer name and date, or a command output) before it moves to `Done`.
5. `render_fixture.py` is curation-only tooling and must never be imported by KenTender or any Frappe app.

## Decision log

| Date | Decision | Reasoning |
|---|---|---|
| 2026-08-28 | Official source PDF accepted as `docs/mvp-1-r1/07_std_configuration/STD-FOR-PROCUREMENT-OF-GOODS.pdf` | Supplied by user; Gate A confirmation of it as the exact official file is still owed |
| 2026-08-28 | `poppler-utils` confirmed installed (`pdfinfo`, `pdftotext`, `pdftoppm` on PATH, poppler 22.02.0) | Unblocks Pass 1's mandated commands; previously missing and blocked Gate A prerequisites |
| 2026-08-28 | Implementation plan and this tracker created; no curation pass executed | User asked for a plan and tracker only, as a verification/scoping step, not to begin Pass 1 |
| 2026-08-28 | User confirmed the supplied PDF as the source and authorized starting Phase 1 | Explicit instruction: "Start with Phase 1. STD-FOR-PROCUREMENT-OF-GOODS.pdf is confirmed as the source" |
| 2026-08-28 | Original download filename recorded as `DOC 4. STD FOR PROCUREMENT OF GOODS`, source URL as the PPRA register page, retrieved-on as 2026-08-28, reviewer as bnganyi | User-supplied answers to the four facts §3 of STD-TPL-001 requires and forbids guessing |
| 2026-08-28 | Gate A confirmed; Phase 2 (coverage register) executed and independently re-validated before presenting for Gate B | User: "Approved. Proceed" |
| 2026-08-28 | Gate B confirmed; 5 of 7 flagged Pass-2 items resolved: office-hours/signature blocks → Generated from governed data; e-Proc identity → Generated from governed platform config; Kenya registration clause → fixed Locked "not applicable" text; Tender-Securing Declaration form (COV-227/228/229) → Not used, since KEBS fixture confirms the paid Tender Security path | User: "Approved" + detailed per-item resolutions |
| 2026-08-28 | Surfaced a new open item (#10): Demand Bank Guarantee vs. Insurance Guarantee variant choice (COV-224/225/226) was defaulted by the Pass-2 agent citing §6 but never explicitly confirmed by the product owner, unlike the now-resolved Declaration-vs-Security choice | Consistency check while applying the user's resolutions — the same §6 "select the permitted variant" rule applies to both choices, so both need the same explicit sign-off |
| 2026-08-28 | Item 9 resolved: advance payment fixed at 0%, Form No. 7 excluded, SCC narrowed to the delivery/inspection/acceptance/invoice payment rule only | User's explicit resolution |
| 2026-08-28 | Item 10 resolved, reversing the Pass-2 agent's default: ITT 18.3 permits 5 Tender Security instruments at the **Tenderer's** option, not the Procuring Entity's — this was never a §6 release choice. Both Demand Bank Guarantee and Insurance Guarantee forms are retained as Locked, always-published | User's explicit resolution, corrected by source citation (ITT 18.3, source page 21) |
| 2026-08-28 | Item 8 escalated to **blocking**: STD-TPL-001 v0.2 §5/§11 render the Invitation to Tender, but the source itself (ITT 5.2 + Guideline 6) states it is not part of the issued Tender document. User: treat the source as authoritative, render the Invitation as a separate publication artifact, and **stop curating this item** — STD-TPL-001 v0.2 itself needs a revision, which is outside this curation pack's authority to make unilaterally | User: "Record this as a blocking document defect and stop this part of curation. Do not silently follow §5 or invent another file." No coverage-register rows changed for this item |
| 2026-08-28 | **Curation paused at Gate B.** Claude will not draft or amend STD-TPL-001 — v0.3 will be authored separately by the document owner. All resolved register changes (items 3–7, 9, 10) are preserved as-is. No further Invitation-related classification work, and Pass 3 does not begin. Resume condition: once v0.3 is supplied, reassess only the Invitation-affected coverage rows (COV-006 onward and any cross-references) against it, close open_issues.md item 8, and only then re-attempt Gate B → Pass 3 | User: "Stop at Gate B and preserve the completed register changes. Do not draft or amend STD-TPL-001 yourself... After v0.3 is supplied, reassess only the affected Invitation rows, close the blocker and resume from Gate B." |
| 2026-08-28 | STD-TPL-001 v0.3 supplied (product owner-authored, not by Claude). Adopted as governing document. Authority updated from v0.2 to v0.3 in this plan/tracker | User: "Check ...v0.3.md. Resume section 14 of STD-TPL-001 v0.3 from Gate B..." |
| 2026-08-28 | All 16 Invitation-related coverage rows (COV-006–COV-021) reclassified per v0.3 §5.1/§11.1/§14 Pass 2 step 11: `render_location` moved to `invitation_to_tender.html` or marked not used; none point to `complete_tender.html`. COV-018/019/020 (print-era obtaining-info/submission/opening addresses) additionally changed from Inherited to Not used, collapsed into the single governed electronic access channel per v0.3 §11.1 item 4 | Direct application of v0.3's own explicit instructions — not a new policy call |
| 2026-08-28 | open_issues.md item 8 closed as Resolved via STD-TPL-001 v0.3 | Blocker cleared by the document revision itself |
| 2026-08-28 | Gate C approved with exactly 6 new Generated keys added to `insertion_points.csv` (platform.name, platform.public_url, tender.approval.official_name/official_title/approved_date/reference — total 70 rows). `platform.public_url` reused for both e-Procurement address and Invitation electronic access (no separate publication-URL key); `procuring_entity.contact_office` reused for clarification channel | User's explicit Gate C decision |
| 2026-08-28 | Items 14/15 (Section VIII Award-derived values, "other Tenderers" table) resolved: no Jinja keys or new repeating structure added — these fields stay blank at issuance, populated later by Award and Contract Formation | User's explicit Gate C decision |
| 2026-08-28 | Item 16 resolved: COV-249 (shipping/delivery documents) and COV-256 (packing/marking) changed from Officer value to Locked fixed Version 1.0 wording; item-specific needs route through the technical specification or goods schedule instead | User's explicit Gate C decision, applied to coverage_register.csv |
| 2026-08-28 | Item 17 resolved: supplier-response scalars (unit prices, offered delivery date, form blanks) remain blank fields completed at bid submission, not Jinja-rendered by this curation pack | User's explicit Gate C decision |
| 2026-08-28 | Item 18 resolved: National Open Tender selected for Version 1.0 (§6 release choice never previously resolved); International wording rejected | Surfaced while drafting invitation_to_tender.html — a real unresolved release choice, not assumed |
| 2026-08-28 | Item 19 resolved: opening date/time (COV-017) folded into the submission-deadline paragraph, not rendered as a separate 9th item beyond §11.1's exact 8-item list | User's explicit decision, following §11.1 literally as the content boundary |
| 2026-08-28 | Gate E officer walkthrough found 7 defects; user's verdict: CORRECT AND RE-REVIEW, do not start Pass 6. All 7 corrected same day (see open_issues.md "Gate E — CORRECT AND RE-REVIEW" section, items 46-52): Tender Security expiry dates now computed via two new Generated insertion-point keys instead of reusing tender.validity_date; six internal KenTender process notes reworded to supplier-facing text and the technical-specification fixture PDF's baked-in curation disclaimer removed (regenerated, digest changed); ITT 23.3 rewritten for electronic (not physical) withdrawal; the excluded Advance Payment Security form dropped from the Section VIII intro sentence; the approved debriefing-period decision (item 32) explicitly re-cited rather than left implicit; 12 bracketed `[Not applicable ...]` drafting-note placeholders (9 full clauses + 3 lettered sub-items) rewritten as clean numbered prose; a Tender-reference/page-number footer added to the 41-(now 44-)page issued Tender via wkhtmltopdf --footer-center | User: "Mark Gate E CORRECT AND RE-REVIEW... Correct only the seven listed matters, regenerate the three PDFs, rerun the existing strict and consistency checks, and present the revised fixture." |
| 2026-08-28 | Footer correction (item 52) blocked mid-fix: the apt-packaged wkhtmltopdf (0.12.6-2) is Debian/Ubuntu's permanently footer-incapable "without patched Qt" build (confirmed via ldd — dynamically linked against system libQt5WebKit); apt has no newer/patched version to offer. Escalated to the user rather than silently faking a static footer or skipping the item | User installed the patched static wkhtmltopdf binary (confirmed `0.12.6.1 (with patched qt)`, statically linked); footer re-rendered and confirmed correct on pages 1, 20 and 44 of 44 |

## Gate register

| Gate | Exit condition | Status | Evidence / gap |
|---|---|---|---|
| TPL-G01 (Gate A) | Product owner confirms the official file and digest; if not confirmed, the master is not prepared | Done | User: "Approved. Proceed" (2026-08-28), confirming title, digest, and the two logged observations in `open_issues.md` |
| TPL-G02 (Gate B) | Procurement-domain reviewer confirms `coverage_register.csv` accounts for the complete source and applies the two-output boundary (v0.3 wording) | Done | User: "Approved" (2026-08-28), confirming the v0.3-reclassified register |
| TPL-G03 (Gate C) | Product owner confirms the insertion list (`insertion_points.csv`) and form list (`forms_register.csv`) | Done | User: "Gate C decision — approved with the following changes" (2026-08-28). Approved with exactly 6 additions (platform.name, platform.public_url, tender.approval.official_name/official_title/approved_date/reference) — insertion register now 70 rows. Items #11–17 all resolved; forms_register.csv approved unchanged |
| TPL-G04 (Gate D) | Reviewers compare both HTML masters with the official PDF and confirm the Invitation is absent from the issued Tender; every coverage row is `Reviewed` or a stated blocker | Done | User: "Aproved" (2026-08-28), after two remediation rounds. All 45 open_issues.md items resolved |
| TPL-G05 (Gate E) | A practising Procurement Officer walks through the five tasks using `kebs_input.json` and checks the separate Invitation notice, issued Tender and package index | Done | First walkthrough (2026-08-28) returned CORRECT AND RE-REVIEW: 7 defects found and corrected (see TPL-G06 evidence). Second walkthrough: user confirmed the revised fixture without further findings, proceeding directly to the Gate F decision |
| TPL-G06 (Gate F) | `05_review/review_record.md` completed with a named decision: APPROVE FOR IMPLEMENTATION PACK / CORRECT AND RE-REVIEW / REJECT THE PRODUCT PATTERN | Done | User: "Review result: APPROVE FOR IMPLEMENTATION PACK. Lock the reviewed masters, registers, KEBS fixture and file digests as Version 1.0." (2026-08-28). `05_review/review_record.md` completed with all required confirmations, zero unresolved blockers, and a 15-file SHA-256 release digest manifest. Before locking: caught and fixed a stale-status bookkeeping gap (open_issues.md item 34 said "Partially resolved" though the content had actually been completed in a later Gate D pass) and a CSV-quoting bug in COV-225 introduced during the Gate E edit (an unquoted field containing a comma had shifted every later column) — both independently found and corrected during the pre-lock review, not reported by the user |

## Work register — Phase 1: Establish the source

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| TPL-101 | Confirm exact official PPRA Goods STD selected by product owner | Done | User: "STD-FOR-PROCUREMENT-OF-GOODS.pdf is confirmed as the source" (2026-08-28) |
| TPL-102 | Create `docs/mvp-1-r1/07_tender_templates/it_equipment_open_v1/` folder structure per §4.1 | Done | `01_source/pages/`, `02_master/`, `03_registers/`, `04_fixture/`, `05_review/` created |
| TPL-103 | Copy source byte-for-byte to `01_source/ppra_goods_std_official.pdf` | Done | SHA-256 of copy matches SHA-256 of `docs/mvp-1-r1/07_std_configuration/STD-FOR-PROCUREMENT-OF-GOODS.pdf` exactly: `95726a88642730e85a212389b4257f26970ecf3f23de872578d11172063ae1ee` |
| TPL-104 | Run `pdfinfo` on the copied source | Done | 103 pages, A4, PDF 1.7, not encrypted — recorded in `source_record.md` |
| TPL-105 | Run `sha256sum` on the copied source | Done | Digest recorded in `source_record.md`, matches original |
| TPL-106 | Run `pdftotext -layout` to produce `ppra_goods_std_official.txt` | Done | 5,010 lines extracted |
| TPL-107 | Run `pdftoppm -png -r 150` to produce `pages/` images | Done | 103 PNG pages produced, matches `pdfinfo` page count |
| TPL-108 | Complete `source_record.md` (title, STD family, revision/issue date or "Not stated in source", filename, URL, retrieved-on date, digest, reviewer, review date) | Done | `01_source/source_record.md` — all facts filled from source text or user-supplied answers; no field guessed |
| TPL-109 | Record any damaged/blank/scanned/unreadable page in `open_issues.md` | Done | `05_review/open_issues.md` — page 103 confirmed blank (visual check); PDF metadata date anomaly also logged; both non-blocking |

**Checkpoint:** Phase 1 is `Done` only when Gate A (TPL-G01) is confirmed by the product owner — not when the files above merely exist.

## Work register — Phase 2: Complete source coverage

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| TPL-201 | Create `coverage_register.csv` with the exact required columns | Done | `03_registers/coverage_register.csv`, header verified exact match to §14 Pass 2 |
| TPL-202 | Read official source first page to last page; add one row per cover/invitation block, numbered heading/subheading, table, form, option/alternative instruction, blank, and preparer instruction | Done | 290 rows, source pages 1–103 covered, no duplicate coverage_id |
| TPL-203 | Assign each row one of the eight treatments (Locked, Inherited, Officer value, Generated, Supplier response, Award-derived, Governed document, Not used by this released pattern) | Done | Validated: only the 8 permitted values used. Counts — Locked 124, Not used 63, Officer value 31, Inherited 23, Generated 20, Supplier response 17, Award-derived 11, Governed document 1 |
| TPL-204 | For each treatment type, record the required target (heading, key, response area, or document) per §14 Pass 2 steps 5–9 | Done | Spot-checked rows carry keys/targets consistent with §7/§8/§9; 5 rows use `owner_key=PENDING-REVIEW` where §7/§13 name no key (see TPL-205) |
| TPL-205 | Route every unresolved choice to `open_issues.md`, not a new field | Done | `05_review/open_issues.md` — Pass 2 section appended (existing Pass 1 entries preserved), 8 entries (#3–10) raised across two rounds, all now resolved |
| TPL-206 | (v0.3 addition) Reclassify every Invitation row against §5.1; `render_location` must point to `invitation_to_tender.html`, never `complete_tender.html` | Done | COV-006–COV-021 (16 rows) updated; COV-018/019/020 changed to Not used (collapsed into the single governed electronic access channel). Verified: zero Invitation rows point to `complete_tender.html` |

**Checkpoint:** Phase 2 is `Done` only when Gate B (TPL-G02) is confirmed — zero unclassified rows.

## Work register — Phase 3: Define every permitted insertion

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| TPL-301 | Create `insertion_points.csv` with the exact required columns | Done | `03_registers/insertion_points.csv`, 64 rows, header verified exact match to §14 Pass 3 |
| TPL-302 | Populate only from §7 of STD-TPL-001; no key added merely because the source has a blank | Done | Verified — every row traces to §7.1/7.2/7.3; candidate keys not in §7 (platform identity, approval-record block, shipping/packing) were excluded and routed to open_issues.md instead of invented |
| TPL-303 | Resolve each blank as fixed / inherited / generated / supplier-entered / award-derived / genuinely officer-entered | Done | `source_treatment` column populated for all 64 rows using the same 8-value vocabulary as the coverage register |
| TPL-304 | Use stable lower-case dotted key names; one key per value even if it appears in several places | Done | Spot-checked — no duplicate keys, e.g. `tender.title` used once, referenced from multiple render locations via `downstream_use` |
| TPL-305 | Create `forms_register.csv` with the exact required columns | Done | `03_registers/forms_register.csv`, 25 rows (17 included, 8 excluded), header verified. Cross-checked exclusions (JV Members Form, Group C import price schedules) against coverage_register.csv — all trace to prior gate-approved decisions, not new unilateral calls |
| TPL-306 | Route proposed additional officer values to `open_issues.md` pending product-owner approval | Done | `05_review/open_issues.md` — Pass 3 section appended, 7 new entries (#11–17): 3 unresolved key-naming gaps (platform identity, approval-record block, shipping/packing docs), 2 scope questions (Award-derived Section VIII values, "other Tenderers" comparison table), 2 structural/scope notes (supplier-response scalars have no `kind`) |

**Checkpoint:** Phase 3 is `Done` only when Gate C (TPL-G03) is confirmed.

## Work register — Phase 4: Build the two working masters (v0.3)

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| TPL-401 | Build `02_master/invitation_to_tender.html` first, from only the rows assigned to the separate notice (COV-006–021) | Done | Built directly (not delegated). Strict-Jinja sanity render passed with realistic KEBS-style values, zero missing/misspelled keys. Resolved 2 new gaps found while drafting: §6 National-vs-International choice (open_issues #18) and opening-date/time placement (open_issues #19) |
| TPL-402 | Do not copy the Invitation notice into `complete_tender.html`; never include/import one file inside the other | Done | Verified — `invitation_to_tender.html` is a standalone file, no `{% include %}`/`{% import %}` used anywhere |
| TPL-403 | Copy the issued Tender wording into `02_master/complete_tender.html`, beginning with cover and contents, then Section I onward, working through the official PDF in order | Done | `02_master/complete_tender.html`, 1,595 lines, all 10 render-order sections present |
| TPL-404 | Copy fixed official wording verbatim into both masters; no paraphrase | Done (with disclosed exceptions) | Independently spot-checked ITT clause 1 and GCC clause 1 word-for-word against source — exact match apart from ligature normalization (ﬁ→fi). 4 disclosed deviations logged in open_issues.md #20–23 (Locked-clause edits to remove unused excluded-alternative wording, and near-verbatim condensation of Section VIII award forms and Section III instructional brackets) — all judgment calls, none inventing new fields |
| TPL-405 | Recreate tables as semantic HTML tables (not images); preserve section numbering and form titles | Done | Verified — no image-based tables |
| TPL-406 | Replace approved changing values with exact Jinja keys from `insertion_points.csv` (70 rows); insert only approved conditionals and the goods/related-services loops (`complete_tender.html` only — the Invitation master may not use the two repeated structures) | Done | Independently cross-checked: all 51 distinct Jinja references in the file trace to the 70 approved keys or documented loop variables — zero invented keys. Only `goods_rows`/`service_rows` loops used |
| TPL-407 | Remove document-preparer instructions from supplier-facing output only after their action is resolved; keep bidder-facing declarations/legal text | Done | `rg` scan for `[insert`, `insert here`, `delete if`, `select one`, `Manual Input`, `Auto Populate` returned zero matches (independently re-run, confirmed) |
| TPL-408 | Resolve the §6 Version 1.0 fixed alternatives; do not expose them as officer choices | Done | National Open Tender, Tender Security only, Demand Bank Guarantee performance security variant, no advance payment — all rendered as fixed/excluded, not officer fields |
| TPL-409 | For Section V, render the goods schedule, related-services schedule (if applicable), inspection/acceptance text, and the controlled technical-specification cover sheet | Done | Goods/service loops present with gating condition; technical_specification.* cover sheet present |
| TPL-410 | Preserve official supplier-form wording; leave supplier/award fields at their proper stage | Done | Supplier/award blanks rendered as static fields, not Jinja — consistent with open_issues.md items 14/17 |
| TPL-411 | Print rules only in `02_master/print.css` (shared by both masters); no inline styles unless a table cannot otherwise retain the reviewed layout | Done | `print.css` created directly; shared by both masters |
| TPL-412 | Visually compare both HTML outputs against `01_source/pages/` images; mark corresponding coverage rows `Draft checked` | Partial | Spot-checked (ITT 1, GCC 1, Form No. 3) by both the building agent and independently by the reviewing session; full row-by-row `Draft checked` marking not yet applied to coverage_register.csv — recommended before/at Gate D, not a blocker to presenting the draft |
| TPL-413 | Record any unreadable text in `open_issues.md` and stop that section rather than paraphrasing | Done | No unreadable text encountered; 4 judgment-call items logged instead (#20–23) |

**Checkpoint:** Phase 4 is `Done` only when Gate D (TPL-G04) is confirmed — reviewers compare both HTML masters with the official PDF, confirm the Invitation is absent from the issued Tender, and every coverage row is `Reviewed` or a stated blocker.

## Work register — Phase 5: Build the KEBS fixture

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| TPL-501 | Create `kebs_input.json` using exactly the §13 values and approved insertion keys | Done | `04_fixture/kebs_input.json`, all 72 keys populated with §13 fixture values plus Gate C/D/E additions (Gate E item 46 added the two Generated Tender Security expiry keys) |
| TPL-502 | Store `kebs_technical_specification.pdf`; add title/version/approval date/publication filename/SHA-256 to `kebs_input.json` | Done | Fixture spec PDF regenerated 2026-08-28 (Gate E item 47 removed an internal "KenTender product curation fixture document" disclaimer that had been baked into the document body); digest recomputed and recorded: `f3556acf...b8d5326` |
| TPL-503 | Create `render_fixture.py` with the exact specified content (StrictUndefined, no custom filters) | Done | `04_fixture/render_fixture.py`, exact content from §14 Pass 5 step 3, both output pairs declared; unchanged by the Gate E correction round |
| TPL-504 | Run the strict renderer via the bench Python environment; a missing/misspelled key must fail the run | Done | Re-ran 2026-08-28 after the Gate E corrections, exit code 0, both HTML outputs produced with zero missing/misspelled keys |
| TPL-505 | Render `kebs_expected.html` + `print.css` to `kebs_expected.pdf` via `wkhtmltopdf` (and the Invitation equivalent) | Done | Re-rendered 2026-08-28 (`kebs_expected.pdf` now 44 pages, with a Tender-reference/page-number footer added via `wkhtmltopdf --footer-center`; `kebs_invitation_expected.pdf` unchanged at 1 page); spot-checked expiry dates, ITT 23.3, and footer text on pages 1/20/44 |
| TPL-506 | Complete `package_index.md` (main Tender PDF, controlled technical-specification PDF + digest, nothing unreferenced) | Done | `04_fixture/package_index.md` updated 2026-08-28 with the new digest, 44-page count and footer note |
| TPL-507 | Run the unresolved-content grep against both fixture outputs; must return nothing except individually recorded/approved legitimate ellipses | Done | Re-run 2026-08-28 after corrections — zero matches in both `kebs_invitation_expected.html` and `kebs_expected.html`; additional re-grep for the 6 internal-note phrases also returns zero matches |
| TPL-508 | Any value `kebs_input.json` needs that §7/§13 doesn't authorize goes to `open_issues.md`; work stops, no fixture-only field invented | Done | Gate E item 46's two new Generated keys (bank/insurance guarantee expiry dates) added to `insertion_points.csv` and disclosed in `open_issues.md`, not invented silently as fixture-only values |

**Checkpoint:** Phase 5 is `Done` — Gate E (TPL-G05) confirmed 2026-08-28 after one CORRECT AND RE-REVIEW round.

## Work register — Phase 6: Record the decision

| ID | Item | Status | Evidence / gap |
|---|---|---|---|
| TPL-601 | Complete `05_review/review_record.md`: official source and digest confirmed by | Done | `05_review/review_record.md` — bnganyi, Gate A 2026-08-28, digest `95726a88...ae1ee` |
| TPL-602 | Coverage confirmed by | Done | bnganyi, Gate B + Gate D (both remediation rounds); 290/290 coverage rows `Reviewed` |
| TPL-603 | Legal text and fixed-alternative treatment confirmed by | Done | bnganyi, Gate D items 20-23/36-45 and Gate E items 46-52 |
| TPL-604 | Five-task usability confirmed by | Done | bnganyi, Gate E walkthrough using `kebs_input.json` — first pass CORRECT AND RE-REVIEW (7 defects), corrected, second pass APPROVE FOR IMPLEMENTATION PACK |
| TPL-605 | Technical-specification package treatment confirmed by | Done | bnganyi, via `package_index.md` — separate file within the package, not embedded |
| TPL-606 | Unresolved blockers listed; review date recorded | Done | None outstanding; review date 2026-08-28 recorded in `review_record.md` |
| TPL-607 | One final decision recorded: APPROVE FOR IMPLEMENTATION PACK / CORRECT AND RE-REVIEW / REJECT THE PRODUCT PATTERN | Done | User: "Review result: APPROVE FOR IMPLEMENTATION PACK. Lock the reviewed masters, registers, KEBS fixture and file digests as Version 1.0." Recorded in `review_record.md`, including a 15-file SHA-256 release digest manifest |

**Checkpoint:** Phase 6 is `Done` — Gate F (TPL-G06) confirmed 2026-08-28, decision APPROVE FOR IMPLEMENTATION PACK. IT-EQUIPMENT-OPEN-V1 Version 1.0 is locked; the 15-file release digest manifest in `review_record.md` is the authoritative record of its final content. Any further change is a new version with its own gate sequence, not an edit to these files. Only now does STD-TPL-001 authorize revising TPR-CHG-001 and preparing a separate, explicitly authorized implementation pack — this tracker does not extend into that work.
