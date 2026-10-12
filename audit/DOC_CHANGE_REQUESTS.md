# Document change requests arising from the audit remediation

Written 7 October 2026 at the wind-up of the Wave 4R work. **This file is the input to a later document-change session. It is not an amendment.** No file under `docs/mvp-1-r1` was edited.

**Every entry must go through the repository's document-change protocol** (skill `anthropic-skills:kentender-document-change`, protocol copy at `docs/mvp-1-r1/98_work_progress/kentender-document-change_SKILL.md`): a full-replacement next version made by anchored edits from the exact previous file, preservation check, change report listing every changed or deleted original line, register update (`KenTender_Baseline_Register.yaml`, KT-DOC-CTRL-001), cross-references, and "Proposed" status until the Project Owner approves. Wording below is a proposal and is labelled as new content for the owner to review. Nothing here is a legal proposition; none was checked against primary legal sources.

**How the section and line references were checked.** Each reference below was found by `grep -n` / `sed -n` in the file named on 7 October 2026. The latest version of each document was confirmed with `ls | sort -V` in its module folder. The baseline register (`as_of` 2026-10-03) lags the library (for example it names BDS v0.8 while the library holds BDS v0_11), so the library listing, not the register, decided "latest". Every latest file below carries "Status: Approved — 3 October 2026" except the two SEED documents, which are Proposed.

## Index

| ID | Document (latest file) | Becomes | Blocked on an owner decision? |
|---|---|---|---|
| DCR-01 | PLN-CHG-001 v1_29 | v1_30 | Partly: items 9 to 11 need the owner; items 1 to 8 follow decisions already given (D4, D5) |
| DCR-02 | AUTH-ADR-001 v1_11 | v1_12 | Yes for items 3 to 4 (RG-39, XC-013); item 1 and 2 are clarifications |
| DCR-03 | AWD-CHG-001 v0_5 | v0_6 | No for items 1 to 3 (D2, D7 given); item 4 needs the owner (Q3, AWD-003 residual) |
| DCR-04 | EVL-CHG-001 v0_5 | v0_6 | No for item 1 (D7); item 2 needs the owner (EVL-016) |
| DCR-05 | BUD-CHG-001 v1_12 | v1_13 | Items 5 and 6 need the owner (RG-28: storage type, KES scale 2); the rest follow D3 and the built code |
| DCR-06 | REQ-CHG-001 v1_14 | v1_15 | Item 3 needs the owner (RG-28); item 1 needs confirmation (RG-14 reading) |
| DCR-07 | TPR-CHG-001 v0_17 | v0_18 | Yes for item 1 (TND-002), item 3 (TND-001 F-2), item 5 (RG-38) |
| DCR-08 | BDS-CHG-001 v0_11, BOP-CHG-001 v0_11, PRC-CHG-001 v0_11 | next versions | Yes (Wave 7 items, no code yet) |
| DCR-09 | The 12 working documents that still describe the retired Tender Configurations module | edited or closed | Yes: owner says whether history is edited (RG-35 and D6) |
| DCR-10 | STR-CHG-001 v1_9 | v1_10 | Item 1 needs the owner (STR-006) |
| DCR-11 | NDS-CHG-001 v1_16 | v1_17 | Item 3 needs the owner (wire contract version) |
| DCR-12 | SEED-OPS-001 v1_25 (Proposed) and SEED-002 v0_1 (Proposed) | fold in before approval | No |
| DCR-13 | Documents that still name Tender Management v2 (26 files under `docs/mvp-1-r1`) | edited or left as history | Yes (RG-35, D1) |
| DCR-14 | Supplier registry (KTSM): no approved document exists | new document or none | Yes |

Decisions referred to: D1 (Tender Management v2 retired), D2 (Award chain: Head of Procurement Function prepares and signs the opinion and handles correspondence and restrictions, Accounting Officer records the decision), D3 (Budget callers), D4 (Annual Plan publication is manual), D5 (the publisher is the Head of Procurement Function), D6 (legacy Tender Configurations retired completely), D7 (evaluation separation). Full text in `audit/REMEDIATION_TRACKER.md`.

---

## DCR-01 — PLN-CHG-001 Clean Procurement Planning v1_29 → v1_30

**File:** `docs/mvp-1-r1/04_planning/KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_29.md` (3,180 lines; Approved — 3 October 2026; latest in the folder). Tracker document item D-2.
**Drivers:** D4 and D5 (7 Oct 2026); findings AUD-XC-106, AUD-XC-121, AUD-PLN-020, AUD-PLN-021, AUD-XC-132, AUD-XC-134, AUD-XC-117, AUD-XC-131/-120; Wave 4R rows RG-01, RG-02, RG-03, RG-31. Built behaviour: `audit/progress/WP4R-L1.md`.

1. **§5.2.3 transition table, line 454.**
   Current: `| Awaiting statutory approval | Approve Annual Procurement Plan | Configured statutory authority | Record approval and Strategy snapshot; enqueue publication of exact approved content |`
   Change to (new content, owner to review): `... | Record approval and Strategy snapshot; hold the exact approved content as **Approved — publication pending** until the Head of Procurement Function presses **Publish annual plan** |`
   Why: the document made publication an automatic follow-on; D4 made it a manual act and D5 named who.

2. **Same table, line 457.**
   Current: `| Approved — publication pending; prerequisites met and no hold | Transmit and reconcile acknowledgement | System | Record authoritative publication evidence; activate only if activation checks also pass |`
   Change to two rows (new content): (a) `| Approved — publication pending; prerequisites met and no hold | Publish annual plan | Head of Procurement Function | PublishApprovedPlan: record the press once, then start transmission of the exact immutable manifest |` and (b) the existing row, kept, with "after the press" in the first column.

3. **Next-step table, lines 809 to 811.**
   Current line 810: `| Approved — publication pending; prerequisites met, no hold | Publication | System | — | Waiting for website publication |`
   Change to (new content): `... | Head of Procurement Function: Your turn — Publish the annual plan | — | Waiting |` and add a row for the state after the press ("sending", System). Line 809 (Treasury evidence missing, Accounting Officer) and line 811 (failed or indeterminate, technical operator) stay.

4. **Command catalogue §7.2, line 989.**
   Current: `| PublishAnnualPlan — system worker | Durable publication ID | Post-commit only; Treasury/hold checks; send exact immutable manifest under stable deduplication identity; record attempt |`
   Change: add the command row `PublishApprovedPlan — Head of Procurement Function | Approved Version, expected version, idempotency key | Session actor only; registered Head of Procurement Function responsibility required; Administrator and System Manager refused; refused unless Approved — publication pending, Treasury evidence recorded and no hold; refused with PLN_PUBLICATION_UNKNOWN while an earlier result is unknown; journalled with actor-bound replay; then runs PublishAnnualPlan once`. Reword the existing row's first column to "PublishAnnualPlan — system worker, started by PublishApprovedPlan" and keep its content. `RetryPublication` and `ReconcilePublication` (lines 991 and 990) are unchanged.

5. **§10 presentation rule, line 1244.**
   Current: `There is no new Author handover approval, HoD return stage, HOPF approval or business Publish button.`
   Change to: `There is no new Author handover approval, HoD return stage or HOPF approval. The Head of Procurement Function's **Publish annual plan** on an approved plan is the one business Publish button (Project Owner decision, 7 October 2026).` The rest of the paragraph is kept.

6. **Actor journeys §6.5 (table around lines 905 to 917), U13 route and variants (lines 1158, 1223 to 1235, 1293, 1921 to 1966).** Add a Head of Procurement Function row to the §6.5 table: heading `Head of Procurement Function — Publish the approved plan`, content `U13. **Publish annual plan** once the Treasury submission is recorded and nothing holds the plan`, consequence `Publication starts once; the press is not an approval; a second press while a result is pending or unknown is refused`. Add a U13 variant for the ready-to-publish state and its guidance-table row (`Your turn | Publish the annual plan`). Line 1293 stage 6 `Publication | Record Treasury submission; transmit and reconcile acknowledgement | As stated per U13 variant` gains `; Publish annual plan`. **A new variant needs a static design artboard, so this item needs a design step as well as a text step.** Built as `pub-publish` on the Publication screen (`WP4R-L1.md`).

7. **Double-press and replay rule (new text, §7.1 envelope or a §7.2 note).** Proposed wording: "A second press of **Publish annual plan** with a different idempotency key while the first is running or recorded is refused with `PLN_REVIEW_STALE` and sends nothing. A repeat with the same key by the same actor returns the first result. An idempotency key belongs to the actor, the command and the payload; the same key from anyone else, for another command or with another payload is `PLN_IDEMPOTENCY_CONFLICT`." Also (from `WP3.6-needs-planning.md`): a replay is answered only to an actor who still holds the standing recorded with the key; `PLN_STALE_WRITE` (line 1129) is no longer used for key reuse, `PLN_IDEMPOTENCY_CONFLICT` (line 1130) is. Verified codes: `PLN_REVIEW_STALE` line 1105, `PLN_PUBLICATION_UNKNOWN` line 1123.

8. **Acceptance row PLN18-AC-043, line 2405.**
   Current: `Publication is an idempotent system action; any technical retry reuses the exact approved payload.`
   Change to (new content): `Publication starts only when the Head of Procurement Function presses Publish (PublishApprovedPlan) and is then an idempotent system action; any technical retry reuses the exact approved payload.` Add acceptance rows for: Planner, Accounting Officer, System Manager and Administrator are refused; a second press sends once; the press is refused while an earlier result is unknown. Proposed ids are new content.

9. **§4.1 Money and Quantity rows (lines 141 and 142).** Clarification only: say that a departmental plan entry's amount is read at the Budget currency's decimal places and its quantity at the governed unit precision (whole numbers for a whole-number unit), and is refused, never rounded, with `PLN_MONEY_PRECISION_INVALID` (line 1115) or `PLN_ENTRY_INCOMPLETE` (line 1080). Built in RG-03. Note the stored precision of Plan Entry and Plan Source Allocation quantity changed from 2 to 3 (`WP4R-L1.md` follow-up 4): the owner confirms "3".

10. **Read and write scope (new sentences).** (a) §7.2 or §6: the approval evidence, task, snapshot, publication, finance, treasury, drawdown and journal records change only inside Planning commands (RG-02). (b) §6 or §4.8 around line 568: a Plan Item Correction Request is read site-wide by the Planner, Head of Procurement Function and Auditor and by the Head of a department with an allocation on the item (RG-31). Built; text follows code.

11. **Items needing an owner decision before drafting.**
    - **Signing Head may also publish?** The owner named the Head of Procurement Function as publisher. The same person may have signed the plan (Plan Preparation Signature, §6.2 line 861). §6.4 (line 888) lists no rule for publishing, so none was built. Options: (a) allow it (current build); (b) bar the signer from publishing, adding one row to the §6.4 table; (c) bar only if the same person also authored. Recommended default: (a), because the press is not a decision and the plan has already been through Finance, the Accounting Officer and the statutory authority.
    - **AUD-PLN-021** (line 888 table and §11 lines 461, 720, 847): is "Withdraw for correction" a statutory decision for the segregation chain, and does `CancelPlanUpdate` count as authoring? Recommended: option (c) in `WP4.6-planning-needs.md` (only the Accounting Officer who requested the withdrawal may not also decide it) if any rule is wanted.
    - **AUD-XC-132** (§5.5.3.1, line 733): state the rounding rule of the required allocation. Recommended: compare exactly and round only for display.
    - **AUD-PLN-020 / AUD-XC-121**: line 917 gives the System Manager the row `System Manager / authorised technical operator — Recover publication`, and lines 1959 to 1962 give a technical operator "Your turn", while PLN27-AC-009 (line 2717) says `Administrator and System Manager never receive Your turn or a fix from any Planning next-step answer.` Decide which wins; recommended: keep the operator's recovery rows, remove "System Manager" from line 917.

---

## DCR-02 — AUTH-ADR-001 Role-Bound Business Responsibility and Organisational Scope v1_11 → v1_12

**File:** `docs/mvp-1-r1/00_common/KenTender_AUTH-ADR-001_Role-Bound_Business_Responsibility_and_Organisational_Scope_v1_11.md` (1,008 lines; Approved — 3 October 2026). Tracker item D-9.
**Drivers:** AUD-XC-013, AUD-XC-136, AUD-XC-026, AUD-XC-028; RG-32, RG-39; D7.

**What the progress files asked for versus what v1_11 allows.** The Wave 4R workers asked for an AUTH "capability table" entry for the Head of Procurement Function's `PublishApprovedPlan`, for the Budget service-principal table (D3), and for the Award role matrix (D2). Reading v1_11 shows it has no such tables: §4.4 line 175 states "The registry does not enumerate commands. Each module names the business role its commands require." Those three items therefore belong in the module documents (PLN item 4 in DCR-01, BUD item 1 in DCR-05, AWD item 1 in DCR-03), and **no AUTH change is recommended for them**. The remaining AUTH items are:

1. **§5.8 Segregation of duties, line 320 to 324.** Current text ends: "Segregation is evaluated against actual actions using the registry's `sod_tags` and the owning module's rules." Clarification (new content): "Incompatibilities that are specific to one evidence chain are stated in the owning module (Evaluation and Award for the same-tender separation of the evaluation panel from the professional opinion and the decision; Planning §6.4 for the plan chain). `sod_tags` are a registry attribute; a module may consume them but none is required to." Reason: the code has no consumer of `sod_tags` (RG-39, Blocked); the document says they are "consumed by domain segregation checks" (line 173). Either the code consumes them or the document stops saying so; **owner decision (RG-39 option a, b or c)**.
2. **§8 Administrator and System Manager (line 359 onward).** Add two sentences (new content): "Technical accounts are denied business commands in the authorisation helper as well as on the record; an assignment of a business role to an account that also holds System Manager does not make that account a business actor." Needs the RG-39 decision first. Also line 359: add the registry attribute `technical_holder` (Technical Operator, Release Operator, Evaluation Technical Support may be held by a technical account) — the WP2.6-2.8 progress file records that the code uses this flag but AUTH does not state it.
3. **§9.2 `AssignResponsibility` and §10 (lines 405 to 423, 424 to 439).** AUD-XC-136 owner decision still open: the code now refuses (a) granting a business role to yourself and (b) granting to a technical account, using `AUTH_SEGREGATION_BLOCKED` and `AUTH_CONFIGURATION_INVALID`, both already in §10 (lines 432 and 438). Proposed wording (new content): "The administrator may not assign a responsibility to themselves or to Administrator or a System Manager account. A person granted a business role who later receives System Manager is reported by the diagnostics." Needs the owner (the later-grant half is RG-39).
4. **Legacy authority rows.** Lines 36, 482, 945 and 982 already say `User Scope Assignment` is not an authority source. Add (new content): "`User Scope Assignment` and `Strategy Scope Assignment` are command-only legacy rows (Legacy Authorization write family) that feed no entity or unit offer" — built in RG-32. The WP4R-L2 file cited "AUTH section 19"; v1_11 has no section 19 (the highest is §15), so the correct home is §11.3 step 11 and §8.
5. **XC-013, command-only enforcement (new citation, no new rule).** §8 (around line 363, "Administrator and System Manager hold technical read access") and §15 can cite `CommandWriteGuardMixin` as the mechanism that keeps Administrator and System Manager from writing business records over REST (the code is in `kentender_core/services/command_write_guard.py`). The open owner question is whether Administrator or System Manager may hold write on any business doctype at all (the older D-9); the built position is no.
6. **§5.5 line 285 to 296.** Optional sentence: no whitelisted function takes an acting-user parameter (now enforced by the repository guard test, extended in RG-41).
7. **OVS v0_6 §4.2 versus BOP v0_11 §6 (AUD-XC-028).** Listed under DCR-08.

---

## DCR-03 — AWD-CHG-001 Award v0_5 → v0_6

**File:** `docs/mvp-1-r1/16_award/KenTender_AWD-CHG-001_Award_v0_5.md` (585 lines; Approved — 3 October 2026). Tracker item D-1.
**Drivers:** D2 and D7; AUD-AWD-001, -002, -003, -011, -015, -017, -018; RG-15, RG-37.

1. **§6 Responsibilities and access, line 275.**
   Current: "HOP prepares/signs the opinion, deals with returned matters, resolves correspondence and records evidenced restrictions. HOP records evidence and proposes next actions. AO decides changes to the award or procurement outcome."
   Proposed addition (new content): "Only the Head of Procurement prepares and signs the opinion and handles supplier correspondence and restrictions; only the Accounting Officer records the Award, No award or Return decision; no other role does either (Project Owner decision D2, 6 October 2026). Separation within one tender (Project Owner decision D7, 7 October 2026): the Accounting Officer is not a member, chair or secretary of that tender's evaluation panel and signs nothing of its report; the Head of Procurement may be the evaluation secretary but not a member or chair; Award compares the deciding Accounting Officer with the delivered report's panel and signers, and the opinion's Head with its members and chair. Refusal: `AWD_AUTHORITY_REQUIRED`, reason `segregation_of_duties`." The code is in commit c4170950; reports delivered before the change carry no panel and only their signers are compared.
2. **§8 error contract, line 315.** `AWD_AUTHORITY_REQUIRED | You are not authorised to take this action. | Current holder shown where disclosure is allowed.` Add the `segregation_of_duties` reason to the recovery text.
3. **Role matrix (D2).** The document has no role-by-command table. Proposed new content: a table of the §7 commands against the roles permitted (the code's matrix is in `award/tests/test_awd_role_matrix.py`; one row per command). `RetryOperation` is run by the technical operator (line 232 and 248 name "Technical operator / Restore notice delivery" and "Restore Contracting delivery"). **Owner question RG-37:** is redelivery by a Technical Operator "correspondence" under D2? Recommended default: no, redelivery re-sends already-decided content and records only a technical outcome (§12 line 425: "Recovery records its own technical outcome without replacing business evidence"); state that in §6.
4. **Items that need the owner.** (a) **Q3**: may one person hold both the Head of Procurement and Accounting Officer offices? Built default: the person who prepared or signed the opinion for a case cannot record its decision, and the person who recorded a decision cannot prepare or sign an opinion, so a single-person site dead-ends. (b) **AUD-AWD-003 residual**: what counts as "operative authority evidence" for a manually recorded external order (§5.10, lines 255 to 271); recommended default: leave free text and rely on the audit trail until the owner defines "verifiable".
5. **Other corrections.**
   - **Funding fail-closed (AWD-002, EVL-014).** §5.1 line 91 and §8 line 325: state that an unavailable funding read refuses a positive award, issue and delivery with `AWD_STATUS_UNAVAILABLE` and that a shortfall holds with `AWD_ON_HOLD` (line 320). The closed set of codes was kept (no funding-specific code).
   - **§5.4 cancellation guard (AUD-XC-108).** State that the guard reads as last committed after the case lock (`WP3.2-4.3.md`).
   - **AWD-017.** Remove the leftover "Proposed"/"would establish" wording after approval: line 471 `AWD-AC-027 ... Registers, traceability and owner contracts agree on Proposed status and module boundaries` and lines 9 and 485 ("proposed technical-reader rule", "A test receiver demonstrates the proposed contract only") need reading in context before editing.
   - **AWD-018.** Line 479, current: "Persist timestamps in UTC and display the site timezone." The project rule and the code store site time (owner decision of 26 September 2026, Frappe's rule; UTC only in serialised payloads). Proposed: "Persist timestamps in site time, as Frappe does; serialise UTC only in event and file payloads, and display the site timezone." Needs the owner to confirm the wording.
   - **Idempotency envelope.** The order of the envelope (authorise, lock, claim the key, run) and, for Evaluation, the standing rule for replays, belong in §7 (`WP3.6-residual.md`).

---

## DCR-04 — EVL-CHG-001 Bid Evaluation v0_5 → v0_6

**File:** `docs/mvp-1-r1/15_bid_evaluation/KenTender_EVL-CHG-001_Bid_Evaluation_v0_5.md` (760 lines; Approved — 3 October 2026). Tracker item D-6.
**Drivers:** D7; AUD-EVL-001, -002, -003, -004, -010, -013, -016, -022, -023; RG-15.

1. **§3 People and access (lines 53 to 74): panel composition and the secretary (D7).**
   Current line 57: "Accounting Officer | Appoint or formally replace the committee; deal with declared conflicts and inability to serve. Appointment access contains no automatic right to read bids or alter findings."
   Current line 60: "Secretary | The Head of Procurement or a procurement officer appointed in writing by that head. Organise records, record discussion, send the authorised clarification and prepare the generated report. Secretary status alone gives no member vote, finding authority or signature."
   Proposed additions (new content): to line 57, "The Accounting Officer is not appointed to the committee in any capacity and signs nothing of its report." To line 60, "The Head of Procurement may be the secretary but may not be an appointed member or chair of the same tender's committee." After line 67 ("The committee has 3–5 appointed members...") add: "Evaluators assess and recommend; the secretary manages the proceedings; the Head of Procurement issues the professional opinion (Award); the Accounting Officer decides (Award)." Refusal: `EVL_MEMBER_INELIGIBLE` (line 308) with reason `accounting_officer` or `head_of_procurement`; applied at appointment, replacement and secretary assignment (line 249 `AssignEvaluationSecretary`), and by the command envelope for a member or secretary who now holds the other office (Appoint, Replace and AssignSecretary exempt as the remedy). Built in c4170950.
2. **Secretary declaration (AUD-EVL-016, owner decision).** §3 says nothing about the secretary declaring conflicts or confidentiality although the secretary reads every bid. Options: (a) leave; (b) the secretary makes the same declaration and acceptance before any bid read, a conflicted secretary is replaced by the Head of Procurement; (c) (b) plus the replacement is a reasoned, recorded re-assignment. Recommended default: (b) or (c). A member-secretary who is ineligible still keeps secretary write commands (`save_narrative`, `send_for_signing`, `retry_delivery`, clarification send); recommended: block them for an ineligible member-secretary (`WP4.2-eval.md` follow-up 2).
3. **Line 65 and BOP.** "Under BOP v0.10's retained product policy, the independent opening member cannot be appointed to evaluate the same tender." The exclusion is now symmetric in code (an evaluation member cannot be named independent opening member and vice versa, AUD-EVL-013); the document should say so, and BOP v0_11 should match (DCR-08).
4. **§4.4 and §5.5.** Say explicitly that a member finding or committee conclusion cannot resolve a price-arithmetic discrepancy or a missing rule, that a qualified outcome is the only record, and that delivery retry rechecks suspension, roster and validity like the last signature (AUD-EVL-002/-003/-004). Lines 106 to 116 and 156 to 166 are the places.
5. **Control table, history and task titles (AUD-EVL-022/-023).** The control table reads "0.4 · 30 September 2026"; "return clears the Head's item" needs a source event on `ReturnEvaluationReport` (line 264); reconcile the control-table, history and task-title claims. The findings give the lines.
6. **Idempotency envelope (§7.2 line 243).** Add the order authorise, lock, claim, run and the standing rule for replays.

---

## DCR-05 — BUD-CHG-001 Clean Budget and Funding v1_12 → v1_13

**File:** `docs/mvp-1-r1/03_budget/KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_12.md` (1,692 lines; Approved — 3 October 2026). Tracker item D-5.
**Drivers:** D3; AUD-XC-002, -012, -101 to -105, -117, -119, -129, -133, BUD-003, -004, -012, -013, -016, -017; RG-16, RG-20, RG-22, RG-26, RG-27, RG-28, RG-29.

1. **§7 Roles and permissions, lines 354 to 358 (D3 callers table).** The REQ and contract principals are already described. Missing, to add (new content): (a) a closed caller-by-action table: Requisitions principal: `check_funding`, `reserve_funding`, and release of the exact reservations its own requisition created, whole reservation only, before the handoff is consumed and only while nothing was converted; Contract principal: convert, release an unused amount, `adjust_commitment`, each with an authenticated owner event, an idempotency key and the contract's own lineage; Planning, Tenders, Evaluation and Award can release, convert or adjust nothing; no business user has a general "Release funds" permission; "release" means freeing a reserved budget amount, not cash. (b) the mechanism (a minted service caller checked against an allow-list of principal and action; refusal `BUDGET_DOWNSTREAM_FORBIDDEN`, line 1224; none of the functions is a web endpoint). (c) **`revalidate_reservations` is Budget-internal** in the build (Q1 default), while line 358 lists it among the contract principal's calls: **owner to confirm** the build or the text.
2. **Contract lineage rule (RG-26).** Add: a contract may convert only a reservation that belongs to its own tender. Must be written before a real Contract Management caller is built. Recommended default: add now.
3. **Idempotency (RG-16, RG-27).** Line 217 says "Replay the original result for the same key and payload; conflict for the same key with a different payload." Add: the key is bound to the actor, the command and the payload; it is claimed by a unique insert after authorisation (Budget Command Journal); a replay of a reservation under a changed source set is a conflict even after the check token expired. State whether a governance command may run without a key: the build allows it (docstring of `budget_idempotency.py`: "Commands without a key run as before"), the Vue editor always sends one, and line 494 says only "Every write requires the expected record version." **Owner question:** require a key on every governance command (needs the editor to always send one) or keep it optional.
4. **§13 error vocabulary (lines 1217 to 1232).** Add `BUDGET_RELEASE_EXCEEDS_REMAINDER` (a release larger than the remainder is refused, no longer clamped), `BUDGET_CURRENCY_PRECISION_UNSUPPORTED`, and name the code used for a missing downstream event or key (the build uses `BUDGET_DOWNSTREAM_FORBIDDEN`). Add `BUDGET_CLOSED` and `BUDGET_SOURCE_OU_REQUIRED` as approval outcomes (lines 1222 and 1228 exist; the approval paths are new). Add a missing expected record version as `BUDGET_STALE_WRITE`.
5. **Float JSON deviation (RG-28).** Line 234 and BUD18-AC-051 (line 1420): "Excess scale, float JSON, malformed and overflow values fail before effects." The build accepts a JSON float only when its shortest text is a plain decimal of at most 15 significant digits, because the editor sends numbers. Owner decides: record the deviation (recommended until the editor sends strings), or make the editor send strings and refuse every float.
6. **Storage digits and scale (AUD-XC-129, -133, RG-28).** Line 235: "At least 18 integral digits plus supported fractional digits." Frappe Currency is decimal(21,9), so the build enforces 12 integral digits with a typed refusal. Owner decides: (a) keep 12 and amend the text, (b) widen the Currency fields, (c) store money as decimal text (recommended if 18 digits are truly required, planned with Planning, Requisitions and Needs). Also decide whether scale 2 and KES are a deliberate site constraint (see DCR-06 item 3).
7. **Records and rules built.** §4.6 and §6: the Budget Submission Attempt record, the `BUDGET_CLOSED` refusal when approving a successor of a Closed Budget, the (contract, reservation) commitment key, and the Close-with-open-successor rule (owner decision, `WP3.1-3.3.md` follow-up 2). §4.1 and §4.8: the CurrencyBasis retained on the Budget root (line 124 `currency_basis_reference`) is described but not stored; either add the field or reword. §9.2: whether successor creation needs `expected_modified`. §4.5: the database-level uniqueness guards are ensured by `after_install` and `after_migrate`, not only by patches (RG-20).
8. **Wave 7 items on this document:** BUD-016 (`/app/budget` route collides with ERPNext Budget; line 543), BUD-017 (BUD-BR-027 "no ledger event" against §14 request events in the same ledger), BUD-008, BUD-009 (CurrencyBasis contract and `get_budget_currency_contract`, line 459), BUD-005, AUD-XC-137 (BUD21-XD-002, line 1673).

---

## DCR-06 — REQ-CHG-001 Structured Procurement Requisitions v1_14 → v1_15

**File:** `docs/mvp-1-r1/06_requisitions/KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_14.md` (2,098 lines; Approved — 3 October 2026; its control table and line 2086 still describe v1.13 as pending, AUD-HND-011). Tracker item D-4.
**Drivers:** AUD-REQ-002, -003, -004, -005, -006, AUD-HND-009, -011, AUD-XC-129, -133; RG-14, RG-28.

1. **§7.3 Maker-checker rules, lines 586 to 591, and the §7.1 table, lines 549 to 553.**
   Current line 586: "A Departmental Author cannot complete the Head of User Department decision on the same Version unless the actor is independently assigned the Head of User Department role and prepared the Requisition directly in that capacity."
   Current line 551: `| Draft | Submit to Procurement | Head of User Department preparing directly | ...`
   Proposed (new content): replace "prepared" by "prepared or edited": "...cannot complete the Head of User Department decision on, or authorise, a Version that they prepared or edited as an Author, in any contributing department; a Head may submit a Draft directly only if they prepared it in the Head capacity." The edited set is the actors of the Version's editing commands in the immutable Requisition Command Journal (Tender precedent AUD-TND-008). After a change of lead department the new lead Head certifies through the department approval task unless they prepared directly: **owner to confirm** (RG-14 follow-up 1). Also state whether the sender (who pressed Send for approval, recorded as `sent_for_approval_by`/`sent_for_approval_at`) may authorise (F2 in `WP3.2-4.3.md`; recommended: block the sender too, REQ19-AC-045).
2. **§5.2 RequisitionVersion (line 179 onward).** List the "sent for approval by / at" evidence; §7.2 (lines 566 to 583): say whether a correction hold blocks routing (the build lets existing Draft work continue, line 580 already says so); §6.3 (line 460): how brand wording is excused where a row has no reason column (build: brand-free wording only for rows without a reason column) and how `All items` applies in mixed-category packages (build: judged against every item category).
3. **§5.14 Shared precision, line 397.** Current: "Plain JSON decimal string in currency units, KES scale 2 from BUD v1.10 CurrencyBasis ... At least 18 integral digits plus supported fractional digits in storage/calculation." The Budget check/reserve contract carries scale 2 as a constant and Requisitions holds `CURRENCY = "KES"`. **Owner decision (RG-28):** (a) record KES, scale 2 as a deliberate site constraint in BUD and REQ (recommended: the site is KES only); (b) make Requisitions, check/reserve and the Tenders snapshot currency-driven, which changes approved contracts. The 12-versus-18-digit storage question is the same as DCR-05 item 6.
4. **§7.4 Corrections, line 608.**
   Current: "after handoff consumption, Requisitions cannot revoke or edit the authorised package; Tender Preparation uses its own upstream-correction route, per TPR-CHG-001 §10.4"
   Change: "§10.14" for "§10.4" (TPR v0_17 line 1067 is `### 10.4 TPR-DES-03 — Draft: Tender details`; line 1325 is `### 10.14 TPR-DES-13 — Returned and requisition-correction states`). Also reconcile with E2E-REQ-001 v0.2 §12 (AUD-HND-001).
5. **Handoff version (AUD-HND-009).** Lines 361 (`### 5.12 AuthorisedRequisitionHandoff v1.3`), 404 (§5.14 last row), 754 (§9.2), 786 (§9.1): the code produces handoff v1.4 and event `ProcurementRequisitionAuthorised.v1.4` (renamed fields; owner decision D4 of 24 September 2026 recorded only in code and the implementation plan). State v1.4, the field renames, and that stored v1.3 handoffs are history (an accepted owner decision that was never carried into an approved version). TPR v0_17 lines 32, 1823, 2024 and 2143 must change in step (DCR-07).
6. **§9.2 and §10.2, RecordHandoffConsumption (line 389 and §10.2 from line 791).** State that `RecordHandoffConsumption` is an in-process owner call inside Tenders' start commands with no public endpoint (the whitelisted endpoint was removed, AUD-REQ-001), the published lock order (Requisition root, then handoff), and that the order of the command envelope is authorise, claim the key, check the version under the row lock, run, with a key bound to actor, command and payload (`REQ_IDEMPOTENCY_CONFLICT`).
7. **Version status inconsistency (AUD-HND-011).** The control table says v1.14 Approved while supersession text and line 2086 describe v1.13 as pending; reconcile.

---

## DCR-07 — TPR-CHG-001 Tenders v0_17 → v0_18

**File:** `docs/mvp-1-r1/11_tenders/KenTender_TPR-CHG-001_Tenders_v0_17.md` (2,257 lines; Approved — 3 October 2026). Tracker item D-3.
**Drivers:** D1; AUD-TND-001, -002, -007, -008, -012; AUD-HND-001, -009; RG-38.

1. **§5.5(6) and §7.3, line 548 (owner decision AUD-TND-002).**
   Current: "If the applicable minimum period would be breached, the Tender cannot become Published until a lawful revised deadline is issued in the same immutable publication package."
   No command in §7.3 (lines 752 to 763) issues a revised deadline and the package digest covers the deadline. Options: (A) a governed command by the Head of Procurement Function that issues a revised deadline inside the same publication (new digest; previously confirmed channels must re-confirm; recommended default, keeps the publication record and never asks the Head to attest a false availability time); (B) the Accounting Officer withdraws authorisation even after confirmations (changes TPR09-AC-055, line 1772: "withdrawn only while confirmed unpublished and before any channel confirmation"); (C) refuse and keep current behaviour. Draft the command, its effect on the digest and prior confirmations.
2. **Handoff version, lines 32, 1823, 2024, 2143.** `AuthorisedRequisitionHandoff v1.3` becomes v1.4 in step with DCR-06 item 5 (AUD-HND-009).
3. **§4.8 / §5.6 (lines 347 to 372, 589 to 599).** State what happens to an addendum still awaiting channel confirmation when the submission period ends (build: refused, stays Awaiting, screen offers no action; proposed new status "Lapsed", recommended), and that issue and effectiveness are possible only before the submission deadline (AUD-TND-001). State that a clarification-deadline row's revised value is a date before the submission deadline.
4. **§6 Roles, line after the table (AUD-TND-008).**
   Current: "The person who prepared or submitted a Version cannot approve it as HOPF. The person who prepared, submitted or HOPF-approved a Version cannot authorise its publication as Accounting Officer. Checks use the immutable Version audit, not role labels alone."
   Define "prepared": the build means everyone who saved a value or an evidence requirement on any Version of the Tender. **Owner confirms or narrows.** Also AUD-XC-135: the `processing_actors` handed to Bid Opening still lists only prepared_by, submitted_by, approved_by, authorised_by.
5. **Addendum maker-checker (RG-38, owner decision).** §5.6 line 595 "Issue authority is HOPF" and §6: a Procurement Officer or the Head can draft, submit and issue an addendum alone. Options: add a maker-checker (the issuer is not the drafter or submitter), or keep. Recommended default: add, mirroring the package rule.
6. **Line 312 and AUD-TND-012.** "One publication authorisation per approved Version" against the code allowing several after withdrawal: pick one.
7. **Envelope (§11.1).** State the order authorise, claim the key, check the version under the row lock, run, and that a key is bound to actor, command and payload (`TND_IDEMPOTENCY_CONFLICT`); TPR09-AC-007 and AC-025 can cite the real two-connection tests.
8. **No Tender Management v2 or Tender Configurations text exists in v0_17** (grep `tender management|TM2|tender configuration` returns nothing): no change for D1 or D6.

---

## DCR-08 — BDS-CHG-001 v0_11, BOP-CHG-001 v0_11, PRC-CHG-001 v0_11

**Files:** `12_bid_submission/KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_11.md` (2,583 lines), `14_bid_opening/KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_11.md` (485 lines), `13_proceedings/KenTender_PRC-CHG-001_Minimal_Procurement_Proceedings_v0_11.md` (334 lines); all Approved — 3 October 2026. The lead's task note named "v0_5"; the latest files are v0_11 in all three folders.
**Retirement text (D6): none.** A grep of these three versioned documents for `tender_configurations`, `Tender Configuration`, `bwmf`, `bidder_workspace_manifest`, `IT Tender Publication Record` finds nothing. The 12 documents that name the retired module are working files, listed in DCR-09. **No change to BDS, BOP or PRC is needed for D6.**
Wave 7 items on these documents (no code exists for them; included so the later session has them):
1. **AUD-XC-028:** BOP v0_11 §6 table (line 146) against OVS v0_6 §4.2 (lines 104 to 106) and OVS-P05 (line 362; FU-OVS-18): what Administrator and System Manager read in Bid Opening. Owner decision.
2. **AUD-XC-135:** BOP v0_11 `AppointOpeningCommittee` (line 158) and BOP-A02: "independent of direct processing" covers only Tender Version actors and the publishing Accounting Officer. Decide whether it should include Tender draft editors (see DCR-07 item 4).
3. **AUD-XC-027:** BDS v0_11 BDS01-AC-080 (line 2012) "Technical and administrator views expose only authorised service/custody metadata" against Administrator reading the bid working-copy doctypes by name; BDS records the bypass as a production-gate residual. Owner decides how it is closed.
4. **AUD-XC-137:** BDS01-IMP-008 (line 2349) open segregation question (BDS signatory).
5. **Reference numbers and journals (RG-17, RG-18):** where BDS, BOP or PRC describe reference generation or command idempotency, state that references are allocated under a per-table allocation lock and the key is claimed by unique insert bound to the actor (build detail; only if the documents already speak to it).

---

## DCR-09 — The 12 working documents that still describe the retired Tender Configurations module

**Owner decision D6 (7 Oct 2026): the module is deleted.** None of the 12 is a versioned requirements document; they are follow-up registers, implementation plans, trackers and an inventory. The RG-04 worker named them in `audit/progress/WP4R-RG04.md` ("Document follow-ups"); their existence and the module-specific hits were confirmed by `grep -rIl -i -E "tender_configurations|Tender Configurations|IT Tender Configuration|bidder_workspace_manifest|bwmf|IT Tender Publication Record|Confirmed Tender Document Package"` over `docs/mvp-1-r1` on 7 October 2026 (exactly these 12 files):

| # | File (under `docs/mvp-1-r1`) | What it says that is no longer true |
|---|---|---|
| 1 | `07_std_configuration/STD-TPL-IMP-001_v1_0_FOLLOW_UPS.md` | FU-08 (line 12): the empty `tabSTD *` tables are "Not dropped, on purpose: live Tender Configurations code still queries" them. Nothing does now; the tables could be dropped (RG-04 follow-up F2). |
| 2 | `07_std_configuration/STD-TPL-IMP-001_v1_0_Implementation_Plan.md` | Line 99: names `tender_configurations/bidder_workspace_manifest/compiler/jcs.py` (deleted) as the RFC 8785 implementation "that can be adapted"; adapt from git history if needed. |
| 3 | `12_bid_submission/BDS-CHG-001_v0_8_FOLLOW_UPS.md` | FU-05 (line 21): the wizard machinery is "Left untouched this cycle"; superseded by the retirement. FU-09 (line 25): cross-app import from `kentender_core/seeds/demo_platform_seed` into `tender_configurations`; both gone. |
| 4 | `12_bid_submission/BDS-CHG-001_v0_8_Implementation_Plan.md` | Decisions D4 and OQ-5 keep the module untouched. |
| 5 | `12_bid_submission/BDS-CHG-001_v0_8_IMPLEMENTATION_TRACKER.md` | Same. |
| 6 | `12_bid_submission/BDS-CHG-001_FOLLOW_UPS.md` | Earlier BDS register; same. |
| 7 | `12_bid_submission/BDS-CHG-001_IMPLEMENTATION_TRACKER.md` | Same. |
| 8 | `12_bid_submission/BDS-CHG-001_Implementation_Plan.md` | Same. |
| 9 | `12_bid_submission/reconciliation/legacy_inventory.md` | Header (line 7) and §1 (line 11 onward, 15 hits; the keep-list at lines 48 to 50): "BWMF/STD-wizard machinery untouched". |
| 10 | `11_tenders/retired/TPR-CHG-001_v0_6_IMPLEMENTATION_TRACKER.md` | Retired folder; references the module. |
| 11 | `11_tenders/retired/TPR-CHG-001_v0_6_Implementation_Plan.md` | Retired folder; same. |
| 12 | `11_tenders/retired/TPR-CHG-001_v0_8_Implementation_Plan.md` | Retired folder; same. |

**Proposed handling (owner decides):** files 10 to 12 are in `retired/` and are history: leave. Files 1 to 9: add a dated closing note ("superseded 7 October 2026 by Project Owner decision D6; the module was deleted in commits 541be82a and 9756d5f4") through the protocol rather than rewriting history. The worker's list also mentions CFG-CHG-002 v0_11 to v0_18; a case-insensitive search finds the words "tender configuration" there only in the generic sense ("KenTender configuration navigation", line 453 of v0_18), not the legacy module. Outside `docs/mvp-1-r1` (not covered by this protocol, candidates for `archive/`): `docs/std-prod-impl/IT-STD-Wizard*`, `docs/bidder-workspace`, `docs/tender-publications`, `docs/data/DEMO_PLATFORM_SEED.md`, `docs/test-contracts/civic-ledger-queue-rollout-matrix.md`. `IT-STD-Wizard-v3/B-Components/code.html` must stay until the Civic Ledger library decision (RG-04 follow-up F1).

---

## DCR-10 — STR-CHG-001 Clean Strategy Alignment v1_9 → v1_10

**File:** `docs/mvp-1-r1/02_strategy/KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_9.md` (944 lines; Approved — 3 October 2026). Tracker item D-8.
**Drivers:** AUD-STR-001 to -006, -008, -011, -012, -016, -017, -019; AUD-XC-005, -120, -131; RG-34, RG-40.

1. **Define "author" (AUD-STR-006, owner decision).** §5.1 line 203: "The author of a version cannot approve it, even when that user also holds Strategy Approver." STR-AC-010 (line 748) repeats it; §6 line 258 says "cannot approve a version they authored". The build means "submitter". Options: (a) submitter only (current); (b) the submitter and any user who saved a Draft edit of this version (events Draft saved, Draft structure saved, Successor Version Created); (c) only the creator. Recommended default: (b). A single-person Strategy office would be blocked after any edit. Also AUD-STR-012: §12.4 says Return remains available; the build blocks the submitter from Return.
2. **Command-only enforcement as the mechanism.** STR-BR-006 (line 218 "Active content is immutable"), STR-AC-010 and STR-AC-032 (line 770) can cite `CommandWriteGuardMixin` as the enforcement of "Active content is immutable" and "every Strategy write goes through the commands"; line 161 (§4.6 audit event "append-only") and line 636 ("Deleting lifecycle events, renumbering versions and reusing generated references are prohibited") can cite the same guard for the Audit Event.
3. **§4.2 and §12.4, applicability.** State that a blank "Use until" means open-ended for overlap and resolution, and that approval is refused once applicability has ended (`EFFECTIVE_DATE_EXPIRED` blocker, `STRATEGY_NOT_READY`); and that `effective_to` is bounded by the plan period on the server (AUD-STR-013).
4. **§8.2 line 330 idempotency.** Current: "a stable command idempotency identity under KT-STD §11". Add: a key is bound to the actor, the command and the payload; the conflict codes are `STRATEGY_IDEMPOTENCY_CONFLICT`, `STRATEGY_IDEMPOTENCY_REQUIRED` and `STRATEGY_VERSION_REQUIRED` (add to §9 around line 349 to 369).
5. **§8 table line 296 `create_strategy_snapshot` (RG-34).** It is now an in-process service, not an endpoint. If §8 or §12.6 requires an HTTP contract, either the document or a capability-gated endpoint must say so. Recommended: state "in-process service called by Planning".
6. **§9 error vocabulary (AUD-STR-016, -017).** `STRATEGY_DOWNSTREAM_FORBIDDEN` (line 364) is now a PermissionError title; hierarchy and target validation should raise typed codes; the §9 vocabulary contradicts the closed vocabulary of AUTH-ADR-001 §10 (lines 424 to 439) that Strategy is bound to. Decide which wins.
7. **Seed title (AUD-STR-019) and workspace label (AUD-STR-021).** Seed plan title lacks "(Demo)"; the workspace shortcut is still labelled "Strategy Portfolio".

---

## DCR-11 — NDS-CHG-001 Clean Departmental Needs v1_16 → v1_17

**File:** `docs/mvp-1-r1/01_departmental_needs/KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_16.md` (2,000 lines; Approved — 3 October 2026). Tracker item D-7.
**Drivers:** AUD-XC-001, -016, -008, -015, -118, NDS-007, NDS-009, NDS-017, NDS-019; RG-08, RG-09.

1. **§8.2 command table, lines 635 to 637.** The three `project_need_planning_*` commands are in-process service seams called by the registered Planning producer, not endpoints. Line 637 reads "Procurement Planner or administrative principal only": drop "or administrative principal" (AUTH §8) and say "registered Planning producer only" (the wording of §7.5 line 573).
2. **§9 error contract (line 677 onward).** NDS §9 is a closed list with no invalid-request code; the build uses `NDS_FIELD_REQUIRED` for an unknown field and `NDS_SCOPE_DENIED` for a field naming the acting principal. Add `NDS_INVALID_REQUEST` or state which code is used. Also `NDS_IDEMPOTENCY_CONFLICT` (exists): add that the key is bound to actor, command and payload, and that a replay is answered only after authorisation. `NDS_UNIT_INELIGIBLE`, `NDS_QUANTITY_PRECISION_INVALID` and `NDS_STATE_CONFLICT` exist; §4.9 and §8.2 should say acceptance rechecks the unit, the quantity and the stored content hash (`NDS-007`).
3. **Wire contract (§4.9, §7.1; owner decision).** `indicative_quantity` on `DepartmentalNeedAccepted.v2` (and `DepartmentalNeedSuperseded.v1.successor_accepted_payload` and the §8.1 read) now travels as an exact decimal string, still named v2; replay normalises older numeric rows; the content hash is unchanged. NDS §4.9 asks for a documented coordinated cutover or an approved new event version. Options: keep and record the cutover evidence (recommended unless an external consumer exists; none found in the repository), or introduce v3 with v2 as a numeric compatibility shape. The 12-integral-digit column limit (NDS asks 18) is the same storage decision as DCR-05 item 6.
4. **§6 and §4.5 (lines 475 to 492, 260 to 272).** State that a Decision row is read inside the Need's department scope and never by the Planner (RG-09); NDS §6 line 482 and line 481 already give the Auditor and the Planner their reads; the Decision rows were the gap. Cite `need_authorization` as the single read predicate and the command-write guard as the enforcement of "no writable DocType endpoints" and "projection written only by the projection command" (§8.2, §16.1). The outbox (Need Event) is command-only (RG-08).
5. **§7.1 PE id (AUD-NDS-017).** §7.1 lists a PE id in the accepted payload while §3, §4.2 and §1.1 say the PE is implicit.
6. **§7.4 and §7.5 (AUD-NDS-009, -010).** The disposition event enum and sequence, and the consumer's versioning, conflict, ownership and ordering rules (Wave 5; code not yet changed).
7. **Seed (AUD-NDS-019).** NDS §14 seed fixture differs from the executable two-year seed world.

---

## DCR-12 — SEED-OPS-001 Canonical Site Seed Runbook v1_25 (Proposed) and SEED-002 Canonical Seed World v0_1 (Proposed)

**Files:** `docs/mvp-1-r1/00_common/KenTender_SEED-OPS-001_Canonical_Site_Seed_Runbook_v1_25.md` (584 lines; "Proposed — v1.24 was Approved; re-approval required") and `docs/mvp-1-r1/20_seed_data/KenTender_SEED-002_Canonical_Seed_World_v0_1.md` (472 lines; "Proposed — Project Owner approval required"; replaces SEED-OPS-001 and SEED-001 on approval). Both are unapproved, so these changes fold into the proposals before approval rather than being a separate successor.
**Retired seeds:** a grep of both documents for `tender configuration`, `demo platform`, `stable_platform`, `seed-demo`, `wizard`, `TM2` finds nothing (the one hit for "Tender Management", runbook line 380, is the live sidebar label over the Tenders module, see RG-35 and DCR-13). **Neither document mentions the retired demo-platform seed pack or the Tender Configuration demo, so D6 requires no change here** unless the owner wants the retirement recorded. SEED-002 line 307 already says "`make seed-kentender-mvp-v1` (the multi-PE-era pack) still creates a second Procuring Entity and legacy personas; do not run it on a canonical site."
Possible additions (all optional; new content):
1. **D7 as a roster rule** in the evaluation stage (runbook line 163, SEED-002 evaluation stage): the canonical evaluation roster has the Accounting Officer (Amina Hassan) appointing, Grace Wambui (chair), Peter Mugo and Ruth Achieng as members, and Charles Mutiso (Head of Procurement) assigning Brian Wafula as secretary; this already complies with D7, and the Evaluation canonical seed test passes. State the rule so a later seed edit cannot break it.
2. **Maintenance windows.** The canonical clear paths open each doctype family's maintenance window (Planning, Needs, Strategy, Budget, Requisitions, Tenders), allowed only on a development or test site and only from a shell, not from a web request. The runbook's section on guards (line 224 area, `force` parameter) can say so.
3. **Seed edits that follow the guards.** The Strategy canonical seed stamps `fixture_namespace` after the command rather than through it (commit a1747084).
4. **SEED-OPS version.** The repository's CLAUDE.md names v1_24 as the approved runbook; the library also holds the unapproved v1_25. Keep the statement consistent when the owner decides.

---

## DCR-13 — Documents that still name Tender Management v2

**Decision D1 (6 Oct 2026): "no reference to it".** The code is clean; `docs/` and `archive/` still name it (RG-35: 65 files in `docs/`, 237 in `archive/`; REG-AUTHORIZATION-14). Under `docs/mvp-1-r1` the WP1.3 worker counted 26 files, notably `11_tenders/TPR-CHG-001_FOLLOW_UPS.md` (FU-08, "inverted Administrator authority" debt now closed by deletion), `12_bid_submission/reconciliation/legacy_inventory.md` §4, the `BDS-CHG-001*` trackers and plans, `18_home_page/reconciliation/hook_inventory.md`, `17_oversight_visibility/reconciliation/baseline_audit.md`, and the plans for EVL, AWD, ANL and PLN. Outside `docs/mvp-1-r1` the worker deleted the wholly-TM2 documents and listed 49 other superseded prompt packs and audits that mention it in passing (`audit/REMEDIATION_DOC_FOLLOW_UPS.md`).
**Owner decision first (RG-35, Blocked):** does D1 cover history in `docs/` and `archive/` and the sidebar label "Tender Management" (the live label of the Tenders module, SEED-OPS-001 line 380)? Recommended default: history stays as history; the label is the module's name and stays. If the owner says yes, the edits go through the protocol (and the older files move to `archive/` rather than being edited).

---

## DCR-14 — Supplier registry (KTSM): no approved document

**Finding:** the registry has no approved module document (BDS v0_8 follow-up FU-06, `12_bid_submission/BDS-CHG-001_v0_8_FOLLOW_UPS.md` line 22). The only statement of who may do what is the capability list in `kentender_suppliers/services/registry_access.py` (now including `prepare_registration`: Registry Officer, Procurement Officer, Procurement Planner). The prompt packs under `docs/prompts/supplier management` name "Admin" as an actor, which AUTH-ADR-001 §8 contradicts.
**Options:** (a) write a short registry document (roles, capabilities, command-only status fields, the Q5 decision on guest registration, no technical roles on mutation capabilities); (b) state the rules inside AUTH-ADR-001 §4.4's registry and leave the module undocumented. Recommended: (a). Needs the owner: guest `ktsm_register` stays or is retired (RG-12, AUD-XC-020), and whether an Approving Authority or Compliance Officer may submit a profile for review (RG-11 removed that).
Also: **CFG-CHG-002 v0_18 conflict.** CFG10-AC-020 (line 885) says "No `Reference Data Manager` role, `reference_data.*` capability string or configuration approval chain exists" while the code still ships the Reference Data Manager role and surface (WP1.4-1.6 F3; RG-07 removed its create right). That is a code-versus-document conflict: owner decides whether to retire the surface (recommended) or amend CFG.
