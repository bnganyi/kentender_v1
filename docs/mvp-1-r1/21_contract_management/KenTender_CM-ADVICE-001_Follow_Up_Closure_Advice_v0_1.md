# CM-ADVICE-001 — Closing the Contract Management implementation follow-ups

| Control | Value |
|---|---|
| Version | 0.1 |
| Date | 16 October 2026 |
| Status | Proposed advice; no source status, requirement, code or approval changed |
| Basis | Supplied CM-CHG-001_v0_8_FOLLOW_UPS.md, version 0.8-follow-ups.1; entries through 16 October 2026 |
| Coverage | All 129 rows reviewed: 111 marked Open; 18 built, closed, decided, done or recorded |
| Source SHA-256 | `f3e39dc1a5cc82c43cc3f99f4e52843df0cd08709d9e166be34fd85a48dfed1e` |

## 1. Recommended direction

Treat the implementation as completed work requiring a bounded closure pass. Do not restart Contract Management, build a second inventory/accounting system, or close rows solely because their implementation phase has finished. Much of the remaining work is reconciling owner requirements and proving real integration; some items expose actual missing controls or incomplete user paths.

The immediate priority is **formation from real source records**: exact issued agreement bindings, successful-offer bytes, real reservations and their award allocation, entity address, final-acceptance applicability, pre-signing funding checks and actual Award delivery. The 14 October OD-E direction already makes source completion required Package B work; it is not an optional future enhancement.

Keep three distinct acceptance statements:

| Statement | Sufficient basis |
|---|---|
| Internal demonstration | Isolated named scenarios, controlled test transports and clearly non-production proof; disclose incomplete behaviours. |
| Acceptance of an affected package | Approved requirements/interface reconciliation and passing installed-site evidence for every capability claimed in that package. |
| Production enablement | Package acceptance plus applicable legal/policy, real signing, official channels and deployment configuration clearance. |

A limited customer review can proceed with an honest scope. It must not be described as acceptance of formation, payment, official reporting or production execution while their specific gates remain open.

**Evidence boundary:** the supplied register and your report that implementation is done are the implementation basis. The repository, actual test receipts, current owner documents and installed sites were not supplied or executed here. References to CM clauses and implementation results below are reported by the register, not independently re-certified. The advice is self-contained; it is not a replacement CM requirements specification.

## 2. Decisions recommended now

These are recommendations for the Project Owner and the named policy owners, not decisions already taken.

| Decision | Recommendation | Principal rows |
|---|---|---|
| Issued sources | Complete deterministic source mappings without changing issued text or adding terms after award. | 05–07, 32, 45, 50, 70, 75, 80 |
| Funding split | Budget/Award applies a reviewed allocation derived from the frozen eligible source basis; CM consumes it read-only. No first-fit allocation based on arbitrary list order. | 71, 81, 118 |
| Acceptance authority | Reuse a valid, explicit written appointment/mandate; do not duplicate it in a second approval form. A generic appointment label is insufficient. | 01, 84, 87, 110 |
| Dissent | Preserve dissent and allow evidenced reconsideration; retest only where facts/measurements require it. | 90 |
| Finance workflow | CM supplies simple guided actions; ERPNext owns invoices, returns, credits, payments and their ledger. | 53, 93–96, 104, 119 |
| Settlement separation | Retain existing maker/approver capacities unless institutional policy expressly requires a separate reconciler. | 24 |
| Reopening | Reopen work, not money or stock. Reconcile funding again if the new outcome changes what Budget acknowledged. | 116 |
| Demonstration clocks | Implement the real-date anchoring decision already approved on 15 October; retain isolated later-stage CM scenarios within that clock. | 61, 122, 127, 129 |
| Alerts | Use the approved notification column; do not alert every derived turn or repeated read by default. | 123 |
| Publication | Keep the duty visible; route legal/channel uncertainty to a person who can resolve it. Do not infer a universal manual portal process or an eGP API. | 19, 28, 79, 107, 108 |
| List performance | Use scoped list projections and batching, not full contract reads or a permission-authoritative per-user copy. | 98 |
| Dev installation | Prepare one reviewed deployment covering installation, native guards and demo data; obtain the deployment authorisation already required by the register. | 37, 62, 124 |

Numbers in the last column are FU-CM suffixes; all individual closure tests appear in §5.

## 3. Matters that need explicit treatment

### 3.1 Complete formation without rewriting a tender

Use one source-availability matrix covering all twelve package sources and all applicable incorporated-document categories. Each entry identifies its owner, exact issued/accepted version, bytes or source reference, digest, binding, availability and conformance evidence. “Not applicable” needs a supported basis; absence is not that basis.

For an already-issued Form No. 4, the template owner may propose a reviewed metadata mapping over the **unchanged exact issued bytes**: each blank/token, insertion source, allowed value and output expectation. This is a proposed treatment, subject to the existing source-governance and legal review. It must not fill legal meaning by guesswork, change an obligation, replace the issued form with the latest release, or silently repair the supplier’s offer. If metadata completion cannot be supported without changing the issued bargain, keep generation held and obtain the lawful remedy. Future releases can carry complete anchors and typed terms from issue onward.

The eight-category manifest, execution text, incorporated accepted offer and required supporting files must be reviewed as one frozen package. A 94.5% text similarity score is not an execution-conformance result. Post-award access to accepted-offer bytes should be narrowly granted through BDS’s owner interface, not by broadening CM access to all bids.

**Final acceptance needs a three-way result:** Required / Not required with basis / Not established. Derive it from applicable LAW and issued TERM sources. A missing term must not default to no final acceptance or let an HOPF completion certificate displace an applicable AO statutory event. The synthetic `-FIN` naming pattern is a fixture device, not production logic.

### 3.2 Allocate and revalidate funding automatically

Recommended default for owner approval: for each awarded line, allocate its supported final amount across that line’s eligible frozen source shares, using the original requested-value proportions where that basis is valid. Preserve attributable discounts, tax and charges according to the published/accepted price basis. Use exact decimal money; allocate rounding residue deterministically, for example largest remainder with a stable source-ID tie break.

Check eligibility and available remainder for every source. If a proposed share exceeds its eligible remainder, **hold and return the specific issue to Budget/Award**; do not silently redistribute across departments, restricted funds or other lines. A different lawful allocation must be recorded through the owning source’s governed correction. Freeze the resulting allocation in the package and preserve it through retries. CM should not ask the contract preparer to invent the split.

For the KES 46,400,000 canonical award, the register supplies no reliable two-source values, so this advice does not invent a numeric split. Recreate the actual reservations through their owner commands and show the approved source-by-source allocation and total.

Revalidate before each signing attempt and at conversion. This is a check, not a new human approval. A successful check cannot guarantee funding remains unchanged while a party signs; conversion must detect later changes and enter the existing evidenced recovery path without pretending the signatures never occurred.

### 3.3 Keep Finance usable while preserving native ownership

Add clear actions on the relevant CM claim: **Record liability**, **Prepare credit adjustment**, **View differences**, and **Reconcile payment**, only for the existing permitted Finance capacities and applicable state. The exact labels/commands need the normal CM amendment, not a separate Finance task engine. Reuse native ERPNext draft, approval, submission and reconciliation mechanisms through the adapter; do not create another ledger or an unrestricted native form embedded inside CM.

Show gross invoice liability, linked credits/adjustments, cash payments and remaining payable separately. Only the native amounts actually allocated to that invoice affect its balance; another invoice’s credit must not offset it merely because the supplier is the same. ERPNext documents payment reconciliation as allocation of existing payments/credits to invoices, and separately documents bank-statement reconciliation [S4, S6]. These are distinct facts, not new cash movements.

Use purchaser-side **Debit Note / Purchase Invoice return** terminology where ERPNext does, explaining that it records a supplier credit [S5]. For assets, prove the early-liability and later-receipt treatment creates neither a duplicate asset nor a duplicate liability. Reference-only settlement data must remain “payment recorded” unless the supported settlement/reconciliation evidence establishes more.

### 3.4 Resolve corrections without repetitive work

A correction request names the faulty fact, source version and actual correction owner. Keep HOPF coordination where necessary, but route specialist corrections to the person who can fix them. Re-sign only the materially changed output under the existing rules; do not invent blanket confirmations of every unchanged fact.

Effective acceptance is immutable. Physical/accounting consequences use the native return/reversal and successor decision, with tests for already-paid units and fixed assets. ERPNext distinguishes a receipt return from a Purchase Invoice return, so the adapter must use the operation actually required rather than one generic “undo” [S5].

Dissent remains attributed evidence. A chair cannot erase it or establish acceptance outside the current mandate. The proposed usability improvement is reconsideration on existing evidence where appropriate; a remeasurement is necessary when the disputed facts require it, not merely because somebody dissented. Unresolved units remain Needs review.

### 3.5 Close security and reporting gaps without inventing law

An outstanding advance needs continuing guarantee coverage monitoring, not only a successful verification on the first day. Track the current owner, expiry/replacement and unrecovered amount. Expiry raises the applicable existing security work; it is not authority for automatic seizure.

A publication duty must retain its **original Award event trigger**, even when signing never follows. Missing legal/channel configuration creates an actionable owner resolution task and a visible duty, rather than a permanent non-actionable blocked item or a disappearing requirement. PPRA Circular 02/2025 describes PPIP/eGP integration and reporting changes; this is a reason to verify the intended deployment’s official path, not assume KenTender’s test channel satisfies it [S3].

Report identity should be the reporting period, type and authorised scope, with references to included contracts. It must not depend on whichever contract happens to be first. A registered scheduler requires an executed/catch-up test; manual invocation proves the computation, not unattended scheduling.

## 4. Legal and Finance policy closure

The following questions remain **owner-gated**. This advice specifies how to resolve them; it does not grant legal clearance.

| Question / rows | Required answer and interim treatment |
|---|---|
| LQ-01 / 14, 20 | Legal owner obtains the current Act/amendments, operative judgments/orders and any replacement instruments for the institution and date; states effect on existing issued contracts. Retain the retrieved baseline meanwhile; do not automatically reinstate invalidated regulations or invalidate existing contracts. |
| LQ-02 / 15, 102 | Decide the unchanged-rate quantity increase under the exact current §139 wording and relevant authority, including the twelve-month restriction. Keep that branch held; quantity/value ceilings do not settle the interpretation. |
| LQ-03 / 16, 110 | Decide security applicability/exemption and the relationship between final acceptance, the return clock and warranty clauses. Apply LAW and issued TERM distinctly; resolve conflicts before the affected action. |
| LQ-04 / 17, 103 | Finance/legal approve the actual damages and interest computations, applicability, authority, dates, rates and caps, including how §140 is treated. Do not use synthetic rates or a configurable percentage as legal authority. |
| LQ-05 / 18, 27 | Legal/Trust specify party capacity, corporate execution, witness treatment and the actual electronic proof method. No production execution until the chosen method and provider are proved. |
| LQ-06 / 19, 28, 79, 107, 108 | Procurement/reporting owner identifies current official destinations, deadlines, formats, triggers and action owners, including relevant eGP directions. Manual filing is acceptable only where the official process permits it and retained receipts prove it. |
| Signing window / 83 | Award/legal states earliest/latest lawful execution with the distinct validity/standstill/restriction basis; do not equate the tender-validity end automatically to the signing deadline. |
| Finance A1/A2/A3 / 24–26 | Entity Finance confirms recognition timing, settlement-role separation and capitalisation policy, with the actual native configurations and representative examples. No simulation setting is institutional policy. |

**Research limit, 16 October 2026:** primary-source searches identified the 4 December 2025 *Roads and Civil Engineering Contractors Association* judgment and a later 24 July 2026 *Kalmar Finland OY* appeal discussing the Regulations [S1, S2]. Full Kenya Law decision/Act retrieval was blocked or unavailable in this session. Their operative text, subsequent orders and deployment effect therefore require the legal owner’s verification; the mere existence of a later appeal is not proof that an earlier declaration was reversed or stayed. The available PPRA circular and ERPNext manuals were readable. No LQ item is declared resolved by these searches.

## 5. Item-by-item closure instructions

The source owner is retained below. “Close when” means **after evidence is reviewed and linked**, not after this advice is accepted. If implementation already satisfies a recommendation, supply its proof and record Already satisfied; do not rebuild it. A required new rule or screen first needs the indicated reviewed amendment.

### 1. Owner-document amendments owed (CM §17.10, §19.8)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-01 | AUTH owner | Adopt the eight CM responsibilities and subject mandates in the externally current AUTH document. Keep existing scope types and the six actual-history separations; do not reuse a Budget role merely because the same person holds it. | Proposed AUTH successor approved; role/read/export matrix and subject-history separation tests pass, including changed appointments. |
| FU-CM-02 | CFG owner | Put operation-specific readiness and recoveries in existing setup. Finance owns accounting mappings; a missing asset mapping must not block unrelated correspondence. | Current CFG successor names every used mapping and owner; missing-one-mapping tests hold only dependent operations. |
| FU-CM-03 | KT-STD owner | Record the named CM capacities, distinct Grace Wambui identity, isolated scenarios and CM-only tracker exception in current KT-STD. | Reviewed KT-STD successor and actor/appointment fixtures agree; no global removal of journey guidance. |
| FU-CM-04 | Budget owner | Adopt the implemented Budget close contract and retained-balance semantics together with FU-CM-59. | Approved BUD successor/tracker; repeated close, evidenced decrease, forbidden closed increase, retained position and omission-floor tests. |
| FU-CM-05 | AWD owner | Reconcile current AWD wording and receiver/update contracts, preserving event identity and original trigger times. | Approved owner amendment plus real Award delivery and acknowledgement evidence; label change causes no API rename. |
| FU-CM-06 | Tenders owner | Amend only demonstrated TPR source gaps. Add typed, source-bound metadata through the owner contract; never rewrite the issued Tender. | Per-source Applied/Already satisfied/Conflict result and complete real-package availability proof, including clause/version links. |
| FU-CM-07 | Template owner | Complete release/issued-instance mapping, incorporated files and agreement insertion bindings; use the no-rewrite treatment in §3.1. | Template owner approves exact mapping and output conformance; all applicable source categories and Form No. 4 bindings validate. |
| FU-CM-08 | BDS owner | Adopt the My contracts supplier link and independent CM organisation/signatory checks in current BDS. | CM present/absent navigation tests; another supplier and bid-only signatory cannot access or sign a contract. |
| FU-CM-09 | PRC owner | Record PRC integration only where CM actually consumes it; otherwise mark the proposed amendment Already satisfied/not applicable with the import trace. | Actual inspection/change evidence links resolve to immutable versions; no generic committee approval or CM dependency on Procurement. |
| FU-CM-10 | Trust owner | Adopt the core signing facade, exact-byte/manifest/capacity binding and safe retry/status contract in TRUST. | Approved TRUST amendment plus core/Proceedings/CM tests; real-provider proof remains separately gated by FU-CM-27. |
| FU-CM-11 | Legal owner | Curate an applicability-specific LAW/TERM/CONTROL rule table and the six LQ decisions; retain unresolved branches as explicit holds. | Legal owner signs sources, effective dates and clause impacts; only supported rules become verified, not a blanket profile waiver. |
| FU-CM-12 | Seed owner | Replace the impossible universal contracts-after-award seed stage with an explicit CM scenario entry using the approved real-date anchor; coordinate FU-CM-122/129. | Revised runbook/plan and repeatable scenario commands; seed validation passes without future native postings. |
| FU-CM-13 | Documentation owner | Update document, interface, roadmap and decision registers to the actual evidence state, including FW-008, IF-019 and DEC-016. | Version/hash/dependency reconciliation; implementation reported complete is distinguished from independently evidenced verification and production approval. |
### 2. External decisions, open evidence and production gates

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-14 | Legal / procurement owner | Obtain a dated deployment-specific legal update covering amendments, replacement instruments, judgments and any stays; assess existing contracts separately. | Signed LQ-01 disposition with retrieved operative texts and effect on each affected rule; search results alone do not close it. |
| FU-CM-15 | Procurement / legal partner | Keep early quantity additions that increase total value held until LQ-02 is resolved. Do not treat unchanged unit rates or percentage ceilings as permission. | Written interpretation of the exact unchanged-rate example, applicable authority and revised rule/profile tests. |
| FU-CM-16 | Procurement / legal partner | Retain no inferred security exemption; resolve statutory final acceptance versus warranty discharge explicitly. Do not add security retrospectively to an issued offer. | Legal treatment for this procurement and institution; sourced exemption if any; lawful return trigger and contradiction treatment tested. |
| FU-CM-17 | Procurement / legal and Finance policy owners | Require the legal/Finance owners to settle separate delay-damages and late-payment-interest bases, rates, caps, periods and authority. | Approved computation examples, source clauses and dates; production profile and Finance mapping tested before any enforceable deduction. |
| FU-CM-18 | Legal / Trust owner | Select one supported execution method for the actual corporate forms and witnesses. Retain party proofs and witness evidence; add witness attestation only if required by the verified method. | Legal/Trust method record and real-provider execution evidence on the complete package, including uncertain signing and witness cases. |
| FU-CM-19 | Procurement / reporting owner | Confirm current official reporting channels, actors, deadlines and trigger events for the deployment, including the eGP transition directions. | Current direction/format copies and accepted official submission example; no invented API, deadline or signature-only trigger. |
| FU-CM-20 | Legal / procurement owner | Issue a limited, dated production legal clearance for the institution and supported capabilities after LQ resolution. | Named verified rules and remaining disabled branches recorded; synthetic profile cannot satisfy this gate. |
| FU-CM-21 | Template owner | Review the installed release actually used, not the newest release found in the folder; include agreement, certificate and amendment layout/manifest/delivery. | Owner-reviewed source-to-render comparison for exact release/issued instance and CM-AC conformance evidence; no percentage-text-match shortcut. |
| FU-CM-22 | Finance / ERPNext owner | Run the complete native gate on the pinned MariaDB stack with real owner hooks and all identified Finance paths. | Receipts/assets/services, holds, maker/approver, early liability, settlement/reversal and imports evidence; independent-site proof covers its different purpose. |
| FU-CM-23 | Budget owner | Close with the approved BUD amendment and real integrated funding run, not the isolated service test alone. | CM-FUND-01 evidence through actual reservation, conversion, closure, permitted decrease and increased-funding refusal. |
| FU-CM-24 | Finance partner | Use existing Finance maker/approver capacities for MVP unless institutional policy specifically requires a separate settlement reconciler. | Finance records the policy decision; if separation is required, mandate/permission/fixture and negative self-reconciliation tests are added. |
| FU-CM-25 | Finance partner | Obtain the entity’s capitalisation policy and classify actual items accordingly. Do not use the demonstration classification as policy. | Finance-approved policy and configured representative stock, expense and asset items with native posting proof. |
| FU-CM-26 | Finance partner | Treat recognition timing as a contract-specific accounting assessment, not a universal acceptance-date assumption. Preserve an evidenced early-liability route where required. | Finance signs the ownership/recognition basis and tests the applicable posting/payment-hold treatment. |
| FU-CM-27 | Project Owner | Keep production signing disabled until the actual Trust provider and LQ-05 execution method pass the installed-site contract. | Real end-to-end proof with verified authority, exact bytes, original timestamps, correlation reconciliation and no duplicate proof on retry. |
| FU-CM-28 | Project Owner | Configure real notice/report/publication channels and their evidence recording; permit lawful manual official submission pending integration. | Delivery/submission receipts from actual channels and failure/retry proof. A test transport or successful CM send is not official publication. |
| FU-CM-29 | Documentation owner | Consolidate shared successor versions and installed extension evidence; read the externally current OVS before any shared visibility change. | Current-version manifest and approved amendments; installed AUTH/Trust proof and remaining gates explicitly reconciled. |
### 3. Found during planning (14 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-31 | Designer / Project Owner | Remove fixture-specific test banners from ordinary product views under DEC-044, but keep test/production proof distinguishable in environments and proof evidence. | Designer/owner approves revised text and screenshots; no synthetic proof or missing legal authority is presented as verified production evidence. |
| FU-CM-32 | Owning modules (Tenders, template release, Bid Submission / Evaluation, Award, Budget, CFG) implemented with CM | Treat the twelve-source package as mandatory formation work already authorised by OD-E; finish or prove each missing/partial source, including FU-CM-70/71/72/80/110. | Real owner-package availability matrix and test_cm_source_availability; no simulation substitution or silent waiver of a required source. |
| FU-CM-33 | CM / AWD owners | Make receiver selection deterministic; simulation stand-in must be silent with live CM installed outside explicit simulation. | Real and simulation flag tests, reversed hook ordering, replay and exactly-one durable receiver acknowledgement. |
| FU-CM-36 | Documentation owner | Reconcile actual externally current versions before changing citations; assess semantic effects instead of merely replacing version strings. | Per-clause difference log and Proposed successors where required. Do not overwrite newer external documents with old repository copies. |
| FU-CM-37 | Project Owner | Supersede this installation-planning reminder by FU-CM-62; do not record a completed dev install without a receipt. | Cross-reference the same owner authorisation and install evidence as 62; preserve original row history. |
| FU-CM-39 | Platform owner | Record ERPNext/Frappe versions and commits in the evidence manifest; rerun affected native gates on upgrades. | Pinned-stack acceptance receipt and explicit upgrade retest rule. Ongoing maintenance duty is transferred, not left perpetually Open. |
| FU-CM-41 | Project Owner / designer | Use the three proposed isolated references for partial, advance and outside-source boards, subject to owner confirmation and normal generated-ID binding. | Design/seed map distinguishes PART, ADV and OUTSIDE subjects; no conflicting event attached to the normal contract. |
| FU-CM-42 | Project Owner / designer | Reconcile every visible control with its actual purpose and command; do not map unrelated return actions just because their names are similar. | Approved command/read/action matrix and missing surface briefs, with immutable target version, next holder and clearing event. |
| FU-CM-44 | Planning owner | Repair Planning’s covered-board claim independently; add the actual comparison or remove the inaccurate coverage claim with a reason. | Planning fidelity gate passes from a reproducible fixture; do not relabel this as a CM defect. |
| FU-CM-45 | Template owner | Trace the canonical Tender to its issued instance, release identifier and hashes. Installation of 1.5 does not change an older issued contract. | Exact release/instance provenance and conformance result; Candidate manifest status is resolved under the owner’s release policy. |
| FU-CM-46 | Project Owner / KT-STD owner | Assign reviewed CM capacities explicitly to existing fixture people. Preserve distinct Peter Mugo and Dr Peter Kimani; Budget roles do not imply CM Finance authority. | Actor/assignment/appointment matrix matches AUTH and KT-STD; negative tests prove no inherited powers. |
| FU-CM-47 | CM owner | Retain the test-site preflight and shared execution lock as operational controls, not a permanent open feature request. | Documented wrapper refusal on dev without approved override; evidence run records site, lock, commit and isolation checks. |
| FU-CM-48 | CFG owner / Finance partner | Make Finance/CFG own native settings and mappings, including Finance role permissions. Do not silently change global Stock/Accounts Settings at CM install. | Approved settings delta and preflight diagnostics; maker/approver and alternative native payment routes tested with missing configurations. |
| FU-CM-50 | STD-TPL / TPR owners | Provide stable digest-bound anchors/fragments and only the typed terms required by supported CM actions, including final acceptance. | Exact issued-instance binding and future compatible-release mapping; missing is not converted to false or a synthetic default. |
| FU-CM-51 | Finance partner / CFG | Recommend disabling rejected-quantity billing for the deployment after Finance assesses other apps. Regardless, CM’s own guards must refuse rejected/unaccepted units. | Finance records global-setting decision; negative native-path test proves the CM invariant in supported configuration. |
| FU-CM-53 | Finance partner | Show invoice-specific gross liability, linked native credits, cash payments, noncash adjustments and remaining liability. Do not subtract the whole supplier balance. | Native allocation/reconciliation readback on corrected invoice and partial payments; supplier credit and purchaser Debit Note terminology explained. |
| FU-CM-56 | AUTH owner | Fold the eight registry additions and their native Finance permission mappings into the AUTH reconciliation, without granting users roles automatically. | AUTH amendment approved; install/migrate role creation and subject-authority negatives evidenced on target site. |
| FU-CM-59 | Budget owner / Project Owner | Adopt the already-built Budget semantics in BUD requirements and reload the new audit-event metadata through migration. | Approved successor and migration test on a site that closes commitments; link FU-CM-04/23/118 evidence. |
### 4. Found during Phase 4 (15 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-61 | CM / seed owner | Implement the already-approved real-calendar anchor decision across CM; do not reopen the policy choice or force future native dates. | One shared frozen run anchor and matching native dates; repeatable scenarios and no future Purchase Receipt posting. |
| FU-CM-62 | Project Owner | Prepare the dev-site install as a concrete reviewed change including native payment guards, fields, navigation and rollback. Execute only under the required owner deployment authorisation. | Authorisation plus migration/build/smoke receipts, before/after native configuration and recoverable rollback; closes 37 and 124 installation aspects. |
| FU-CM-63 | BDS owner | Add the implemented Contracts portal header item to current BDS and test CM present/absent composition. | Approved supplier navigation amendment and own-organisation route tests; no dependency on the buyer’s Procurement app. |
| FU-CM-64 | CM | Implement the supplier invoice attachment and authorised preview using existing file controls; do not require repeated transcription from it. | Upload, preview, access denial, unsafe-file rejection and exact claim association evidence. |
| FU-CM-65 | CM + core | Expose scoped register-picker sources for managing unit and responsible person; do not grant System setup access for filtering. | Only permitted options/suggestions/counts; clearing filters never widens authority; large option sets usable. |
| FU-CM-66 | CM | Extend certificate conformance beyond wording to header/version, evidence manifest, unit coverage, rendered layout and delivery receipt. | Exact frozen-output comparison and delivery/replay tests for acceptance, completion and other required outputs. |
| FU-CM-67 | Core owner | Review CM’s safe execution-context helper for reuse in core; prevent request-time user switching from replacing the browser’s session. | Session/cookie identity and authority restoration tests on success and exception; targeted audit of other request paths. |
### 5. Found during Phase 5 (15 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-69 | Award, CM | Run Award’s actual eligibility/delivery loop into CM on a correctly provisioned Award world, including retry. | No missing AO fixture; once-only package receipt, real sources and acknowledgement through eligibility.deliver(), not receiver tests alone. |
| FU-CM-70 | STD-TPL, TPR | Publish reviewed insertion metadata for the exact issued Form No. 4 bytes; do not guess blanks or edit issued legal prose. | Every required insertion has deterministic target, source and expected content; owner-reviewed render and absence-of-binding refusal. |
| FU-CM-71 | Budget, Award | Adopt the source-line funding allocation rule in §3.2; reconstruct real reservations through owner commands before proving the canonical award. | Budget/Award-reviewed split equals KES 46,400,000 exactly, respects eligible source remainders and persists one immutable allocation. No invented numeric split here. |
| FU-CM-72 | CFG | Expose the existing principal-address field in System setup, validate it and freeze its evidenced value in each signing package. | Authorised setup edit, meaningful address, historical package unchanged after later setup change; never copy a tender contact office by assumption. |
| FU-CM-73 | Award, CM | Send authoritative resolution updates from Award, with original issue identity and current revision; retain guarded manual evidence only for sources lacking an event. | Restriction→resolution→duplicate/out-of-order update tests; resolve only the named hold and preserve unrelated restrictions. |
| FU-CM-74 | CM spec | Add RecordContractNotProceeding and RecordRestrictionResolution to the current CM command/action contract, reviewing actual authority and effects. | Approved command definitions and exact surface/return/error mappings; evidence is not reinterpreted as an unauthorised procurement decision. |
| FU-CM-75 | TPR | Use deterministic typed metadata for supported term-driven actions, bound to the issued clause; retain narrative as evidence. Unknown advance/change/remedy terms stay Unknown. | Owner-reviewed term matrix and production missing-term guards; no AI interpretation deciding rights or no-advance default from absence. |
| FU-CM-76 | TPR | Type objectively measurable acceptance checks at the source; keep evidence/judgment checks explicitly manual with reasons and evidence. | ACC-001–005 mapped to a check/evidence requirement and supplier line; automatic comparison proof plus ambiguous-case Needs review. |
| FU-CM-77 | Suppliers | Add an own-purpose authorised supplier search in Supplier Accounts; return active verified identities without disclosing unrelated private information. | Country/registration identity and search results agree; wrong-organisation and inactive-account negatives. |
| FU-CM-78 | CM, core | Provide normal Add item/Remove unsaved row behaviour using existing repeating-row patterns; do not constrain users to three spare lines. | Create/edit a contract with more rows than the old limit; validation and saved identity/history preserved. |
| FU-CM-79 | CM | Implement the publication duty from the actual AwardDecisionRecorded event, independent of later signing. Verify Phase 8 did not merely add a screen. | Durable obligation, original trigger time, idempotent replay and lawful manual submission evidence; coordinate LQ-06 and 107/108. |
| FU-CM-80 | BDS | Provide narrowly authorised post-award access to the successful accepted offer’s exact bytes and clarifications for the incorporated package. | BDS custody-owner decision and source manifest/export tests; no losing bid, unopened content or bidder authority inherited by CM. |
| FU-CM-81 | CM, Budget | Revalidate reservations before each party’s signing attempt and again at commitment conversion; signing is not a funding lock. | Changed/unavailable funding blocks signing appropriately; concurrent later change is caught at conversion with recoverable linked proofs, never backdated cancellation. |
| FU-CM-82 | CM | Apply recorded owner-interface amendments to the externally current documents under one reconciliation pass, including EVL where actually changed. | Each source version/hash and Applied/Already satisfied/Conflict result retained; approved successors, not tracker-only assertions. |
| FU-CM-83 | Award, legal | Have Award/legal supply the signing interval and basis, retaining validity, standstill, restrictions and any lawful extension separately. Do not infer ends_on from validity alone. | Written LQ treatment of the exact signing-window example and boundary/extension tests; no routine manual extension in CM. |
### 6. Found during Phase 6 (15 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-84 | CM spec | Document ResolveDeliveryException and DecideContractAcceptance with exact mandate, frozen report target, outcomes and follow-up. | Reviewed CM amendment; AO decision is used only where authority requires it, without a duplicate acceptance approval. |
| FU-CM-85 | TPR, Award | Implement and test a real goods-plus-service source through TPR and Award even though the canonical goods-only case contains none. | Line kind/UOM, service requirement/deadline/evidence and linked criteria all available; no fabricated stock receipt for a service. |
| FU-CM-87 | CM, owner | Accept the AO’s appointment as authority evidence only if its actual text explicitly grants the acceptance power and scope and that grant is legally valid. Reuse that document; do not demand a duplicate delegation form. | Authority owner confirms mandate; missing/expired/out-of-scope authority blocks effectiveness while an inspection recommendation remains recordable. |
| FU-CM-88 | CM | Keep internal report correction separate from outward supplier correspondence; prove the Phase 8 send/reply path now exists. | Committee return and supplier notice have distinct recipients/content/version; supplier sees only authorised reasons, without committee deliberations. |
| FU-CM-89 | CM | Retain immutable effective acceptance; correct it through the governed reversal/return and successor path, with downstream stock/liability/payment guards. | Real-native reversal, partial quantities, already-paid case and exact old/new report links; no edit of the effective signed report. |
| FU-CM-90 | CM, owner | Permit evidenced committee reconsideration without automatic retesting of unchanged observations; require retesting only when evidence/measurement needs it. Chair cannot erase dissent. | Owner-approved rule, retained dissent and collective disposition, new report/proofs where material; unresolved units remain Needs review. |
| FU-CM-91 | CM | Keep reconciliation read-only, but add exact accepted-unit/serial/batch/asset identity checks and an explained valuation bridge; quantity totals alone are insufficient. | Wrong serial, duplicate asset, tax/landed-cost and partial-return tests; legitimate valuation differences are explained, never silently repaired. |
### 7. Found during Phase 7 (15 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-92 | CM spec | Consolidate the implemented duplicate resolution, liability reconciliation and advance record/verify/claim surfaces into CM’s own requirement and design sections. | Approved command/screen map, maker/approver guards and representative artboards; no code-only business workflow. |
| FU-CM-93 | CM, owner | Add a Finance-only Record liability action on the held claim, with clear explanation that payment remains blocked; do not add a second invoice. | Approved screen/command mapping and L2 held-claim→liability→correction/credit test with supplier scope and duplicate guards. |
| FU-CM-94 | CM, Finance | Link the actual native payment and its bank transaction/reconciliation where available; retain supporting confirmation using existing file controls when needed. Text reference alone is not reconciled settlement. | Partial payment, bank match/unmatch and evidence-access tests; label Payment recorded versus Settlement confirmed distinctly. |
| FU-CM-95 | CM | Preserve the asset duplicate-prevention restriction. Provide the supported early-liability route through Finance with native linkage and later receipt reconciliation. | Finance-approved treatment and real fixed-asset test produces one asset/unit and one supported liability; outside native entry is visible in CM rather than disappearing. |
| FU-CM-96 | CM | Verify Phase 8 adjustment preparation is usable now; distinguish contractual deductions, native credits and authorised write-offs. | Reviewed reason/authority/account mapping plus no-double-deduction tests; missing lawful basis holds only the affected adjustment/payment component. |
| FU-CM-97 | CM | Monitor outstanding advances against guarantee expiry, amendment/replacement and remaining recovery; alert the current owner before a due contractual action is missed. | Deterministic due-rule tests, owner reassignment and scheduler catch-up; expiry does not fabricate seizure or repayment authority. |
| FU-CM-98 | CM | Replace full-record-per-list-row reads with bounded, indexed projections and permission-safe batching. Do not make a permanent per-person cache the permission authority. | Representative-volume query/payload/paging measurements and role-expiry tests; detail remains available through the record. |
| FU-CM-99 | CM | Show each material difference with its actual reason and responsible owner on D08. Detailed comparison can expand, but the blocking cause must already be visible. | Finance can identify price/tax/quantity/receipt/duplicate/remaining-amount holds without visiting the supplier page. |
### 8. Found during Phase 8 (15 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-100 | Owner, design | Review the Phase 8 commands and missing action surfaces as a single CM amendment, retaining only necessary owner decisions. | Each listed command/screen has actor, target, effect, return/recovery and closed design input; no invented appointments or hidden actions. |
| FU-CM-101 | Owner | Replace the unreachable artboard with genuine missing/revoked/conflicted/out-of-scope appointment cases. Validate mandate at signing rather than assuming the build cannot lose authority. | Current-authority negative tests and corrected artboard; do not introduce artificial expiry merely to match a screenshot. |
| FU-CM-102 | CM, legal owner | Keep the 25% check as defence within its actual supported scope, but correct the explanation: it does not enable price/new-line changes or resolve the twelve-month question. | Review/proof of aggregate versus per-line bounds and LQ-02 guard; no artificial feature added just to exercise an unreachable threshold. |
| FU-CM-103 | Owner, Finance | Expose the deduction-account mapping through existing setup for Finance review and authorised configuration. Rate/cap come from verified law/issued terms, not site settings. | Current CFG/Finance amendment, mapping validation and exact legal computation test; missing mapping names a recovery owner. |
| FU-CM-104 | CM, Finance | Retain ERPNext return/asset/accounting ownership, but provide a CM-guided route to prepare the needed native reversal through the adapter where authorised. | Real fixed-asset return, prior asset reversal, replacement and credit reconciliation tests, including native rejection and recovery. |
| FU-CM-106 | Owner, CM | At effective termination, close/stop the unfulfilled native order through its supported service, preserving accrued liabilities, returns and lawful surviving work. | Native alternate-entry tests block new unauthorised fulfilment; source-specific funding split and surviving clause references validated. |
| FU-CM-107 | CM, reporting owner | Anchor multi-contract reports to the reporting period/scope, not an arbitrary first contract; support authorised department scope. External statutory output waits for a verified format. | Current report scope/format contract, actual scheduled invocation/catch-up and submission evidence; no report generated once per contract by accident. |
| FU-CM-108 | Owner | Keep the publication duty visible, and create one actionable Resolve publication requirements item for its responsible owner while the legal answer is missing. | No perpetual blocked task masquerading as publishing work; legal-resolution task has a real recovery path, then normal publication duty proceeds. |
| FU-CM-109 | CM | Resolve scheduled warranty work to the current responsible person at read/dispatch time; keep historical holder evidence. | Owner change/expiry and rerun tests move live responsibility without duplicate or lost warranty tasks. |
### 9. Found during Phase 9 (15 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-110 | Template release owner, CM | Make final-acceptance applicability an explicit LAW/TERM result; Unknown is not No. A missing issued term cannot displace an applicable statutory event. | Real owner source/profile supplies required/not-required with basis; applicable AO acceptance and security clock proved without a -FIN naming convention. |
| FU-CM-111 | Designer, CM | Return correction to the current owner of the actual faulty evidence, with HOPF coordinating only where needed. Reuse the existing return/resubmit cycle. | Named task/route/reason and exact source version; correction owner can act and re-submit without a new approval layer. |
| FU-CM-112 | Designer, CM | Adopt the completion-fact selector and its consequences in the screen brief. Keep mandatory missing completion facts open; surviving matters need a supported clause and owner. | Approved field/action contract and meaningful-value test; structural field-kind matching alone cannot prove fidelity. |
| FU-CM-113 | Owner | Do not add a menu button whose only result is refusal. Offer the existing issue/referral route for an authorised correction/legal challenge while termination remains effective. | Reachable HOPF-coordinated referral with evidence and holder; no automatic reopening of a terminated contract. |
| FU-CM-114 | CM | Close as a documented equivalent view if D20-T/P actually covers the same actor/state/content. Record Equivalent coverage rather than an unexplained Not compared. | Traceable replacement artboard mapping and visual assertion for the shared state; no duplicate page required. |
| FU-CM-115 | Owner | Assign surviving work by the capability and scope needed for that specific obligation, not a generic list of CM role holders. Supplier obligations retain a supplier party and internal accountable coordinator. | Owner-approved eligibility table; appropriate HoD involvement supported where permitted; no supplier gains internal Finance or decision authority. |
| FU-CM-116 | CM | Keep reopening separate from stock, money and legal restoration. Reconcile Budget again if corrected facts change its acknowledged closure; reuse acknowledgement only when its meaning is unchanged. | Changed-versus-unchanged funding-outcome tests, no automatic release/recommitment and versioned second-closure evidence. |
| FU-CM-118 | CM, Budget | Run the full canonical Award→CM→real Budget closure path after source/allocation/address fixes. | Real commitment created and closed through native owner hooks; replay/stale/amended amounts evidenced at the same revisions. |
### 10. Found during Phase 10 (15 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-119 | Owner, Finance | Use a small CM Finance action to prepare/link the native purchase return/debit note, with existing native maker/approver controls. Do not build a second credit ledger/editor. | Corrected posted claim, native credit allocation and payment hold proved; supplier credit note and purchaser Debit Note clearly distinguished. |
| FU-CM-120 | CM | Do not add a funding-allocation screen merely to satisfy a sentinel. Extend the disclosure test to every existing response, export, package and file that can expose that data. | Negative field-level tests on actual surfaces, including direct endpoints and unrendered data; future-screen extension tracked as maintenance. |
| FU-CM-121 | CM | Treat this as a release-critical disclosure verification gap, despite its Medium register label. Exercise files/downloads/exports for every defined reader and supplier boundary. | CM-AC-48/43 evidence, direct/guessed URLs, expired roles and cross-supplier tests; no bid authority inherited through contract access. |
### 11. Found during Phase 11 (15 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-122 | Owner | Keep isolated CM scenarios; integrate them with the already-approved real-date seed anchor. Amend the impossible gate wording instead of moving the whole world solely for one module. | Plan/SEED/runbook agree on real predecessor delivery, scenario times and commands; no future posting or overwritten canonical Award profile. |
| FU-CM-123 | Owner | Follow the approved hand-off notification column by default; expand only after a reviewed notification-rule change. Deduplicate alerts on the underlying action identity. | No alert on waiting/scheduled reads or retry; representative new-action/return notifications match the documented table. |
| FU-CM-124 | Owner | Keep CM demo masters namespaced and reversible; never clean unrelated existing accounts, items, workflows or suppliers. Dev deployment authorisation is shared with FU-CM-62. | Clean/rerun and referenced-master tests, settings restore evidence and an authorised dev-install receipt. |
### 12. Found during Phase 12 (16 October 2026)

| Item | Accountable owner in source | Recommended disposition | Close when / required proof |
|---|---|---|---|
| FU-CM-125 | Designer; CM | Dispose of all 24 un-compared boards individually: redraw changed surfaces, capture missing fixtures, or prove named equivalent coverage. | 157-board ledger has a justified coverage result for every board; major work-register and invoice views reviewed by representative roles. |
| FU-CM-126 | Maintainers of the seed world | Restore a dedicated known shared test world and fix the stale handoff-version assertion; then reinstate Home cross-module browser checks. Do not merely change expected counts. | No leftover fixtures; Award profile restore succeeds; source-derived Home tasks/waiting/oversight and CM integration gates pass. |
| FU-CM-127 | CM | Route test dates through the injected run clock; explicitly exercise midnight/timezone boundaries. Do not accept a flaky rerun as closure. | Deterministic liability and other affected tests on both sides of midnight and the same native posting-date basis. |
| FU-CM-129 | CM and seed-world owners | Complete the approved seed re-anchoring in one coordinated CM/seed change; use one frozen real-date-derived run anchor and relative scenario offsets. | CM worlds, demos, adapters, browser fixtures and expected labels retimed together; native dates never exceed actual time; no mixed fixed-2027 assertions. |

## 6. Items not marked Open in the source

Retain their original status and history; do not re-open them merely to reduce or increase a closure count. “Built” is not the same as approved documentation or production evidence.

| Items | Source position | Treatment |
|---|---|---|
| 30, 49 | Core signing work Built | Keep implementation result. Remaining owner documentation and real-provider contract/proof are covered by 10 and 27; do not call those closed. |
| 34, 35, 43, 52, 57, 58, 68, 86, 105, 117, 128 | Closed/Done as recorded | Preserve linked evidence. Related open items remain separate: 105 does not resolve LQ-03 or guarantee monitoring; 128’s one locked gate does not prove all shared test-world operations are isolated. |
| 38 | Independence site Done, SQLite caveat | Retain as dependency-independence proof only. Use MariaDB for native-posting acceptance; add a MariaDB independence site if the actual deployment needs combined proof. |
| 40 | Owner decision recorded | Preserve OD-E; its decision is not proof that every source gap was subsequently fixed. |
| 54, 55, 60 | Recorded limits/information | Transfer to the maintained operating/architecture notes: privileged database-write limit; issued-versus-official form difference; shared access-component duplication. Do not count these as verified security or conformance. |

These are the 18 non-Open rows; none is silently converted to Closed by this report.

## 7. Execute the closure pass in this order

1. **Freeze the evidence baseline.** Record installed app commits, platform versions, current CM requirement/design/tracker versions and exact external owner versions. Bring the register’s control date up to its actual reviewed-through date. Maintain its permanent IDs and original entries.
2. **Complete real formation sources and funding.** Resolve 32/45/50/70/71/72/75/80/81/110 and actual receiver selection/delivery. Produce one complete real-owner formation packet. No production signing is needed to prove source availability with controlled test proof.
3. **Reconcile documents once.** Apply the demonstrated owner amendments to the externally current AUTH, CFG, KT-STD, BUD, AWD, TPR, STD-TPL, BDS, EVL, PRC, TRUST, LAW, seed and register documents as applicable. Record Applied / Already satisfied / Conflict or missing evidence per change. Include code-authored CM actions/screens and update the single CM document; do not resurrect withdrawn full-copy owner proposals.
4. **Finish user paths and safety gaps.** Resolve claims/credits/settlement, asset returns, termination’s native-order effect, appointment authority, task reassignment, scoped pickers, editable item rows and field/file/export disclosure. Update only the affected boards and variants. Material blocking reasons must be visible before optional detailed comparisons.
5. **Stabilise the shared test world.** Complete the already-approved real-date re-anchoring across every CM fixture and native adapter; isolate scenarios, acquire the shared site lock, repair stale validators and restore Home’s cross-module tests. Do not change expected results just to obtain green tests.
6. **Run focused proofs, then the integrated acceptance run.** Cover real Award delivery; source conformance; real Budget conversion/closure; native goods, services, assets, payments, returns and credits; shared permissions; independence; source correction and retries. Reuse valid prior proofs only for unchanged commits/configuration/scenarios. Resolve or explicitly classify each of the 24 outstanding visual comparisons.
7. **Obtain bounded owner decisions and production evidence.** Legal/Finance decisions can be pursued alongside earlier evidence work. Apply their answers to reviewed requirements/profiles, then test the actual production provider/channels and deployment configuration. Do not replace this with a global CM-ready flag.
8. **Review closure by item and accept the actual scope.** Close each row only with its evidence and accountable reviewer. Keep a production-gated item open until its clearance exists, or transfer a genuinely excluded capability to a separately accepted scope with the operation disabled and clear user guidance. A transfer is not a claim that the full originally promised capability passed.

Do not repeat unchanged module suites after every editorial correction. Run the focused affected test first, its owner/contract group next, and one coherent integrated gate for the reconciled package. A source-interface, permission, signing or clock change requires its cross-module checks. Run performance checks on representative volume, not only nine contracts.

### 7.1 Minimal closure record

Reuse the existing follow-up tracker. Each disposition records: FU ID; Closed / Superseded by named row / Transferred to named maintained control / Still open; short reason; approved decision/amendment reference where needed; code and configuration revisions; exact test/artboard or delivery evidence; accountable reviewer and review date. A consolidated evidence receipt can support several rows, but each row must point to its own applicable result. Do not create a second closure database.

### 7.2 Exit tests that matter most

- A real accepted Award package reaches CM once, with every required source, actual template binding, principal address and exact owner funding allocation; missing data names its owner and blocks only the dependent action.
- A payment held in CM cannot be paid through an alternative supported native path; a credit, return or correction changes the right invoice only and creates no duplicate asset/liability.
- Final acceptance/security, report/publication and amendment behaviour uses the right source of authority and original event time, never a synthetic profile or later signature as a substitute.
- A reader cannot bypass field, file, download, export, supplier or appointment boundaries; required information remains visible to the authorised operational reader after handoffs.
- Current task owners, corrections, surviving work and reopening remain consistent after role changes and retries; a closed Budget acknowledgement is revisited when the corrected outcome changes it.
- The real-date, locked test world is repeatable, native-compatible and restorable; Home integration and all claimed visual coverage are evidenced.

## 8. Source notes

The supplied follow-up register is the source for all FU IDs, reported implementation facts, statuses and clause references. The references below support the limited external observations in this advice; they are not substitute deployment clearance. Official ERPNext manuals describe current product concepts and do not prove the reported ERPNext 16.10.1 / Frappe 16.12.0 installation behaves identically.

- **S1 — Kenya Law, Roads and Civil Engineering Contractors Association & others, [2025] KEHC 19224, 4 December 2025.** Primary decision located through indexed Kenya Law results; full retrieval blocked. [Primary judgment](https://kenyalaw.org/akn/ke/judgment/kehc/2025/19224/eng%402025-12-04)
- **S2 — Kenya Law, Kalmar Finland OY v Public Procurement Administrative Review Board & others, [2026] KECA 1500, 24 July 2026.** Later primary appellate decision located; full retrieval blocked. Its operative effect was not determined here. [Primary appellate judgment](https://kenyalaw.org/akn/ke/judgment/keca/2026/1500/eng%402026-07-24)
- **S3 — PPRA Circular 02/2025, PPIP integration with eGP.** Official page retrieved 16 October 2026. [Official circular](https://ppra.go.ke/ppra-circular-02-2025/)
- **S4 — ERPNext, Payment Reconciliation.** Official manual retrieved 16 October 2026. [Payment Reconciliation manual](https://docs.frappe.io/erpnext/payment-reconciliation)
- **S5 — ERPNext, Purchase Return.** Official manual retrieved 16 October 2026. [Purchase Return manual](https://docs.frappe.io/erpnext/purchase-return)
- **S6 — ERPNext, Bank Reconciliation.** Official manual retrieved 16 October 2026. [Bank Reconciliation manual](https://docs.frappe.io/erpnext/bank-reconciliation)

The source register remains unchanged. This advice does not approve the proposed decisions, install the app, certify tests, change issued terms or mark any FU closed.
