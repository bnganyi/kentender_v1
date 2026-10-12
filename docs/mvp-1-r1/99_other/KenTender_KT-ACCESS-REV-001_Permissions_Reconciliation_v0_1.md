# KenTender access reconciliation — role matrix and implementation brief

| Control | Value |
|---|---|
| Report ID | KT-ACCESS-REV-001 |
| Version / date | 0.1 / 7 October 2026 |
| Status | Completed document reconciliation; proposed amendments; implementation and runtime verification not performed |
| Authority | Project Owner instructed “Proceed” after requesting a system-wide permissions reconciliation. This authorises the review and draft remediation, not approval of new access grants. |
| Scope | All supplied MVP owner requirements; Home/Analytics proposals and CM working draft included as planned surfaces. |
| Output | One review report containing the access matrix, exact owner amendments, repository implementation brief and verification cases. This is not a second runtime permission store or a competing approved requirements baseline. |

The concrete problem is that authorised readers can encounter action-oriented pages which deny the entire record. The correction separates record disclosure from commands and makes destination access consistent with the originating view. Existing approved oversight grants are carried forward; new clarifications are explicitly proposed below. Read access does not grant preparation, approval, signature, opening, decryption or Finance posting authority.

## 1. Evidence and limits

The supplied latest requirements ZIP is the owner-source set for STR/BUD/NDS/PLN/REQ/TPR/BDS/BOP/EVL/AWD/PRC/STD and KT-STD. Current AUTH v1.10, OVS v0.6 and CFG v0.16 were additionally retrieved; Home v0.3 and Analytics v0.3 are proposed sources. CM is the 7 October within-version v0.3 revision. Controlling approval records prevail over contradictory retained drafting history. No repository, running server, actual User Responsibility Assignments, databases or route guards were inspected. Every implementation diagnosis below is a hypothesis to test, not a reported code finding.

OVS v0.6's controlling approval records its read additions as approved. Its §4.1 applies the additions with matching owner amendments. The matrix identifies their intended owner boundaries; it does not infer that they were implemented. OVS mentions CFG v0.17 but the retrieved CFG source is v0.16 and an exact v0.17 filename search returned no result. Do not claim the missing CFG successor was reviewed. TRUST's current complete operating profile, production baseline registers and runtime seed state were not inspected; custody/signing implementation must retain those owners' guards.

### 1.1 The reported AO failure

Observed screenshot: Amina Hassan, displayed as Accounting Officer, at `/desk/procurement-planning/dpp-classification/DPPS-MOH-02502-2026-001-V1`, receives **This record is not available to you.** The screenshot establishes a denied page. It does not establish the submission's state, underlying scope, effective assignment, whether the link was emitted by an authorised source view, or the failing guard.

First reproduce that exact user/URL and inspect the authoritative submission and assignment. If this is an accepted classification or source of an AO-readable submitted/approved Plan, the proposed PLN amendment supplies read-only access on that route without Planner commands. If it is an unsent departmental draft, retain the draft boundary and fix any upstream link which incorrectly promises access. A real missing record, expired assignment and protected cross-scope record must remain distinguishable internally without leaking protected existence to users. Never fix this by assigning the AO Procurement Planner or Administrator.

### 1.2 Findings

| ID | Evidence | Finding and remediation |
|---|---|---|
| F01 | PLN §6 AO row emphasises governed actions; §7.1 defines classification reads; PLN18-AC-025 requires complete AO source/evidence review | Read eligibility for individual DPP/classification destinations is underspecified. Add explicit read rows and same-route read-only rendering. |
| F02 | OVS §4.1 grants STR/BUD/NDS/PLN/REQ oversight reads; corresponding owner role tables still lead with workflow actors | Incorporate approved reader coverage into owner reads, registers and forbidden-state responsibility text; do not rely on office titles alone. |
| F03 | STR expressly distinguishes consumers from workflow readers; REQ §8 distinguishes authorised handoff from Draft access | Preserve consumer-only boundaries. A related-record link is not a general module grant. |
| F04 | KT-STD §3A.6 says technical readers read every record/detail; OVS §4.2 and BDS/BOP impose sealed-content restrictions | Consolidate the technical surface verdict and content-disclosure exception. Technical page access must not decrypt sealed content or expose credentials. Exact proposed shared amendment is §5. |
| F05 | OVS §§4/7 distinguish administrative Evaluation progress from full delivered records; EVL appointments grant working access separately | Preserve two disclosure paths. A secretary's working read is not restricted to oversight status, and oversight is not a working appointment. |
| F06 | OVS §8, owner deep links and Home/Analytics require authorised destination reads | Navigation grants and source/version selection require explicit edge checks. A menu being visible is not itself a defect; KT-STD keeps module navigation visible with a proper denied entry state. |
| F07 | AUTH §5.3 requires list and direct-document hooks; owner reads cover files and reports | UI permission checks alone cannot prove access correctness. Validate list/count/search/detail/file/export/API predicates together. |
| F08 | CM §6 mentions contract scope while AUTH registry supports Site-wide or Organisation Unit only | Represent Finance/contract/inspection assignments as owner subject eligibility on top of AUTH responsibility, not a third registry scope type or parallel authority store. |

## 2. Common interpretation

**Assignment:** current User Responsibility Assignment is the business-authority source. The role and its own scope/effective period are evaluated as a pair; multiple assignments are unioned without combining one role with another assignment's scope. Site-wide means within the single site. OU scope includes authorised descendants and the owner's exact consumed lead/contributor relationships. Financial year is a filter and business eligibility input, not a permission grant.

**Read:** evaluate record existence/disclosure, current assignment, authorised relationship, record/version state and audience. Return only the authorised projection. Being a task assignee is required only where the owning read contract requires it; absence of a task does not erase independent oversight access. Access to history is evaluated for the requested version; it does not reveal an unpublished successor or unfinished correction.

**Act:** additionally evaluate exact command capacity, task/appointment, current state/version, personal identity, conflict clearance, segregation and owner guards. A readable editor-shaped page can have an empty command set. GET/read/navigation creates no draft, task, receipt or decision.

**Destinations:** every emitted record/evidence link has a permitted destination and exact version under the same actor. Where only a summary is permitted, provide that summary rather than a link to protected full detail. Home, Analytics, meetings and search do not create disclosure rights. Counts/search suggestions may not leak protected records.

**Administrative navigation:** keep the shared menu policy. A user may select a module they cannot enter and receive its documented entry denial; that does not justify a dead-end link emitted from a permitted record. A missing optional module or unresolved route yields no invented link.

**Status:** Completed work remains findable while current responsibility authorises its read. This does not give perpetual access to a former employee, expired appointee or revoked supplier user. Historical attribution survives revocation; access is re-evaluated.

## 3. Oversight read matrix

Each row applies to every record, list, exact detail, evidence link and permitted export for the stated audience. “None added” means this reconciliation creates no grant; another explicit functional assignment may independently permit the record. All rights are bounded by §2. Column labels AO, HOPF and HoD denote valid assigned responsibilities, not display titles. **C** = existing owner/approved OVS contract; **P** = proposed precise extension/clarification. No row gives business mutations.

| Owner / records | AO | HOPF | HoD | Auditor | Technical reader (Administrator/System Manager) | Basis |
|---|---|---|---|---|---|---|
| STR approved current/historical plans, reasons | Site-wide approved versions | Same | Approved versions under OVS; Strategy is site-wide | Authorised plan/version/history | All ordinary versions, read-only | C: OVS §4.1; STR §§6/6.1/10 |
| STR Draft/pending review | None added | None added | None added | Owner-authorised audit reads only | Read-only all ordinary versions | C; no broad oversight draft grant |
| BUD approved allocations, reservations/commitments/history | Site-wide current/historical position | Same | Only funding facts attributable to scoped sources; no unrelated shared-line disclosure | Scoped exact versions/funding evidence | All ordinary records including Draft/review, read-only | C: OVS §4.1; BUD §§7/7.1/9 |
| BUD Draft/approval task | None added | None added | None added | Explicit audit read | Read-only; no approve/close/ledger action | C |
| NDS submitted/decided Needs, decisions, lineage | Site-wide | Site-wide | Assigned OU/subtree under NDS | Scoped Need revisions/history | All ordinary revisions/tasks, read-only | C: OVS §4.1; NDS §6 |
| NDS unsent Drafts | None added | None added | Existing NDS departmental scope; not arbitrary other departments | Existing owner audit grant | Ordinary technical read only | C; submission grant does not include unsent drafts |
| PLN submitted/approved Plan and exact source evidence | Site-wide governed review, decisions/history | Site-wide governed review, decisions/history | Scoped DPP/source and disclosed downstream position | Scoped Plan/evidence/history | All ordinary statuses/task-shaped routes, read-only | C: OVS §4.1; PLN §§6/7.1, PLN18-AC-025 |
| PLN certified submitted DPP and accepted classification/history | Read-only site-wide certified/accepted snapshot; no author draft or classification command | Same | Scoped certified/source snapshot; no Planner commands | Within audit scope | Ordinary read-only | P: A04 resolves ambiguous per-record eligibility; exact Plan-consumed sources already required by C |
| REQ authorised version, decisions, drawdown/handoff/history | Read-only site-wide authorised record | Existing submitted review and authorised follow-up | Complete scoped departmental/contributor record | Scoped immutable versions/decisions/funding | All ordinary Draft/submitted/stopped/authorised content | C: OVS §4.1; REQ §8 |
| REQ unsent Draft | None added | None added beyond current owner grant | Existing departmental/preparer authority | Existing audit grant | Read-only | C; AO does not inherit Draft preparation |
| TPR Tender/package/review/publication/history | Existing publication/cancellation and complete associated review read | Existing package/publication administration read | Source-scoped requirements and neutral progress | Scoped versions/evidence/history | Ordinary record read; no sealed box disclosure | C: TPR §§6/7.1; OVS §4.1 |
| BOP before reveal | Appointment/decision/admin metadata only unless independently appointed | Owner-authorised admin metadata; no implicit ceremony power | Scoped admin progress | Lawful non-content oversight | Safe non-content health/record projection | C: BOP §6; OVS §§4.1/4.2; content exception P A12 |
| BOP after governed reveal | Contextual revealed opening record | Contextual lawful record | Scoped revealed summary; no competing full bids | Lawful revealed historical evidence | Ordinary released owner record | C: OVS; no ceremony rights implied |
| EVL before report delivery | Administrative progress only, plus own appointment work | Administrative oversight; independent secretary appointment separately evaluated | Scoped administrative progress | Existing legally authorised audit projection; no generic inference of working access | Ordinary owner projection under technical policy, sealed source excluded | C: OVS §§4/7; EVL §3; A12 resolves technical wording |
| EVL delivered report and later correction | Full exact delivered report, evaluated bid versions/all submitted attachments, findings/reasons/due diligence/signatures | Same; persists after Award handoff | Scoped disclosed recommendation/outcome/reasons summary only | Owner-authorised full audit evidence | Ordinary delivered record read-only | C: OVS §§4.1/7; no unfinished correction exposure through oversight |
| AWD opinion/decision/notices/history | Complete own governed decision context | Complete opinion/returned-decision work | Scoped final decision/outcome/date/reason summary after decision; no unfinished deliberation | Owner-authorised historical evidence | Ordinary record read-only | C: AWD §§5/9; OVS §4.1 |
| PRC meeting register | Site-wide safe metadata | Site-wide safe metadata | Lead/contributor-scoped safe metadata | Approved audit scope | Site-wide safe metadata | C: OVS §11; register grant does not grant minutes/bid contents |
| PRC full minutes/attestations | Stage's independent BOP/EVL disclosure | Same | Only if independently permitted; not from register access | Stage-authorised evidence | Released ordinary record; sealed restrictions retained | C/P: owner rules plus A12 |
| CM agreements/deliveries/decisions/obligations/history | Proposed site-wide ordinary contract oversight and own decision context | Existing coordination/certification and proposed ordinary oversight | Relevant department/contract relation, ordinary evidence | Permitted contract history/evidence | Ordinary native-linked projections read-only | P: CM proposed baseline; A10 makes record audience explicit |
| CM financial details | Certified/payable/confirmed-cash/outstanding/holds and decision evidence | Same contractual position | Relevant contract summary; protected account data excluded | Financial evidence within authorised audit scope | Permitted diagnostic projection; credentials excluded | P: A10; Finance detailed editing remains separately assigned |
| CFG setup/responsibility administration | Relevant owner-approved setup evidence only; no general setup grant | Same | Same | Historical configuration evidence under owner grant | Setup under actual maintenance authority | C: CFG §6; AO office is not a configuration administrator |
| STD Templates | No new standalone grant; issued/bound template via authorised Tender/document context | Read-only owner inspection/concern reporting | Issued terms in scoped authorised source/Tender view | Authorised issued/historical evidence | Owner technical read/configuration boundary | C: AUTH v1.10; STD v0.15; no activation from read |
| BDS supplier Drafts/sealed bids | No content through office alone; metadata only as independently authorised | Same | No content | Lawful metadata; content only through later stage grant | Sealed content excluded; safe health/custody metadata | C: BDS §6; supplier own-organisation access distinct |
| Home | Compose permitted work/reads; no new authority | Same | Same within scope | Permitted read destinations; no invented personal decisions | No business work from technical status | P Home v0.3; owner verdict controls |
| Analytics | Owner-permitted cross-area aggregates/records | Same | Scoped owner summaries | Authorised oversight aggregates | Owner-permitted technical aggregates; limited support excluded | P Analytics v0.3; counts never broaden disclosure |

## 4. Functional role, read and action matrix

This table covers the role/capacity set in the reviewed owners. Read of other modules is limited to explicitly authorised source/consumer relationships, never inferred from the person's seniority. Role codes must be taken from the actual AUTH registry; labels here do not create new global roles. Capacity rows such as Chair/Receiver are owner appointments attached to a registered responsibility.

| Role / capacity | Read and navigation | Permitted action family | Scope / exclusions |
|---|---|---|---|
| Strategy Author | Plans, own permitted Draft/successor/return/history | Create/edit/submit | Site-wide; no own-version approval |
| Strategy Approver | Exact submitted review, structure, changes, source/history | Return or approve/activate | Site-wide; audit-based self-approval guard |
| Budget Officer | Drafts, submissions, current allocation, history, revision requests | Register/edit/submit successor; answer/decline revision request | Site-wide; cannot approve own submission |
| Budget Approver | Exact submitted/current Budget and evidence/history | Return/approve/activate; governed close | Site-wide; no automatic reservation release |
| Finance Confirmation Officer | Complete exact Plan funding review/reassessment and permitted live Budget facts | Confirm/return/reassess through PLN | Site-wide; no Budget authoring, reservation or payment power |
| Departmental Author | Own permitted Needs; scoped DPP; REQ own/contributor source content and context | Need/DPP preparation; permitted REQ source work and submission | OU/subtree and owner creator/contributor guards; no HoD decision unless separately assigned |
| Head of User Department | Scoped Needs/DPP/REQ and downstream summaries in §3 | Need decisions; DPP certification/submission; REQ preparation/certification/submission/return/withdrawal | OU/subtree; incompatible own-submission decision denied |
| Procurement Planner | Accepted Needs, certified DPP/classification, Plan workspace, Budget eligibility, source/drawdown/correction history | DPP accept/classify/correct; form/modify Plan; request Finance; correction/successor work | Site-wide; no certified source edit, REQ decision, Budget ledger command or final statutory approval |
| Procurement Officer | Authorised REQ handoff; assigned Tender work/history; STD inspection | Start/prepare/submit/correct Tender, draft addendum and authorised correspondence | Site-wide responsibility plus owner task; no REQ Draft entitlement; no HOPF/AO approval |
| Head of Procurement Function | Oversight §3 plus exact submitted REQ/Tender, delivered EVL and AWD evidence | Plan preparation signature; REQ return/authorise/unconsumed revoke; Tender review/publication confirmation/addendum; professional opinion; CM duties | Site-wide; no edit of certified source, proxy committee action or Finance approval from office alone |
| Accounting Officer | Oversight §3 plus exact decision/appointment/source/history | Plan adoption/Treasury evidence/withdrawal request; Tender publication/cancellation; committee appointment/replacement; Award decision; CM authorised signatures/change/termination/closeout | Site-wide; no Planner edits, proxy opening/evaluation participation, native payment or setup mutation from office alone |
| Configured statutory approving authority | Exact submitted Plan/resolution/review evidence/history | Applicable approval/return/withdrawal decision | Exactly one configured capacity: Cabinet Secretary, CECM, Board or Council; collective resolution/recorder is not another route |
| Opening chair/member | Exact appointed opening session, lawful reveal/record and own attestation target | Personal participation, governed opening/member proof; chair coordination | Exact tender appointment/state; no pre-deadline content, absent-member proxy or evaluation scoring |
| Opening recorder / designated PRC secretary | Authorised session attendance/events/minutes | Record actual facts/notes; prepare minutes/supplement | Exact owner appointment; cannot manufacture member attendance or proofs |
| Evaluation chair | Current appointed committee record/bids/checks/discussion/report | Coordinate/discuss/conclude under full-roster guard; authorise clarification; member work/signature if eligible | Tender-specific appointment/conflict clearance; no absent-member decision/signature |
| Evaluation member | Current eligible working bids/evidence/findings and exact report | Record attributable findings/concerns/dissent; participate and personally sign | Appointment and declarations; conflicted membership immediately stops affected access |
| Evaluation secretary | Appointed working records needed for organisation/discussion/correspondence/report | Organise/record/send authorised clarification/prepare report | No vote/finding/member signature solely from secretary status; separate valid membership evaluated separately |
| Contract preparer | Assigned intake/agreement/source/terms/history | Prepare/import/revise draft within CM | CM proposed responsibility and owner subject assignment; no entity signing or final decision |
| Contract owner | Relevant agreement/delivery/payment position/issues/warranty/history | Coordinate, record permitted issues/claims; prepare review/closeout | Contract relation on AUTH assignment; no receipt acceptance or Finance authority implied |
| Receiver | Assigned delivery/custody/quantity/source details/history | Record arrival/custody/return under CM | Cannot sign acceptance of same arrival recorded |
| Contract inspection chair/member | Assigned criteria/observations/evidence/report/quantity disposition | Record scoped observations; prepare/ personally sign exact acceptance report | Effective appointment/declarations; no actor proxy, conflict or rejected-unit passing receipt |
| Technical certifier | Assigned technical evidence/exact certificate | Personally sign technical certificate | Exact capacity/subject; not automatic inspection or payment authority |
| Finance maker | Assigned liability/payment editors, certification, accounts/tax/allocation/beneficiary evidence | Save/submit native-linked invoice/payment draft through KenTender | Cannot approve own entry; native validations/holds remain |
| Finance approver / authorised settlement recorder | Same supported native record/version and permitted settlement/reconciliation evidence | Configured native approve/post; evidenced settlement/correction within assigned authority | No bank execution; certifier/settlement segregation; never infer cash from zero balance |
| Supplier Representative | Own organisation account/bids/receipts; own clarification/notices and separately granted CM contracts/invoices | Prepare account/bid; answer own clarification; CM claim/correction/reply under CM grant | Cannot sign/submit/replace/withdraw a bid solely from representative role; no competitor/internal read |
| Supplier Authorised Signatory | Own arrangement and exact signed subject/evidence | BDS sign/submit/replace/withdraw; AWD response; CM signatures only under separately current contract grant | Organisation/arrangement, effective window and exact target; BDS signatory does not automatically grant CM command |
| Tenderer / opening attendee | Public issued material and lawful readout/register copy | Attend/request permitted register | No general PRC minutes, competing full bid or committee vote |
| Public visitor | Public published Tender/documents/issued notices only | Public search/read | No internal record/existence or account/bid mutation |
| Auditor | Current authorised oversight scope and owner version/disclosure rules | None | Registered business responsibility; no ceremony, decision, ledger or signing power |
| Administrator | Ordinary technical reads and safe sealed metadata; CFG/AUTH/STD administration under actual setup contract | Permitted setup, responsibility grants and exceptional missing-root repair | No business commands/impersonation; credentials and sealed content excluded by proposed A12 |
| System Manager | Same ordinary technical reads; permitted setup/assignment maintenance | Ordinary setup/assignment maintenance | No Administrator-only root repair; no business authority from technical role |
| Limited technical operator / recovery assignee | Only explicitly assigned non-content incident/operation status and recovery evidence | Exact approved recovery operation | Not Administrator read-all; no attest/sign/approve/decrypt/business completion |
| Authenticated owner services | Exact registered input/source projection | Owner-only event/transaction intents under trusted context | REQ/CM may invoke their Budget reserve/release/convert/adjust contracts; PLN/TPR/EVL/AWD cannot impersonate them. Services have no human UI role. |
| Multi-responsibility actor / acting officer | Union of independently valid responsibility-scope pairs | Union of commands which pass all domain/history guards | No role switch; no Cartesian scope widening; expiry, self-approval and conflicts remain binding |

## 5. Exact proposed owner amendments

The following text is the complete amendment schedule to incorporate into the listed self-contained owner documents. **C** aligns an existing grant; **P** makes an explicit proposed clarification/extension. It is reviewable amendment text. It is incorporated into the 19 self-contained requirement review copies in the companion package; original approved files and their registers have not been replaced. Do not implement a P grant as already approved. Existing C grants can be corrected against the approved source boundary. Successor version numbers and registry entries must come from the actual current document-control register, not guessed here.

### A01 — AUTH §5.3 / owner read registrations — P clarification

> Every owner declares read eligibility separately from command eligibility for its registers, counts, searches, exact-version records, task/editor-shaped detail, evidence files, reports and exports. Native permission hooks and custom service projections use the same role-bound assignment and record-disclosure policy. A read may succeed with no business command. Oversight read does not require current task ownership unless the owner expressly restricts that read. Multiple assignments are evaluated individually and unioned without transferring scope between roles. A read/navigation never invokes a mutation. No new capability-profile, per-user screen-grant or parallel authority store is introduced.

### A02 — KT-STD §3A and OVS §8 — P clarification

> A record/evidence link emitted to an authorised actor must resolve to that actor's permitted projection of the exact referenced version. Reuse the record's route in read-only mode when its normal view is task- or editor-shaped; otherwise the owner supplies its existing authorised summary/detail destination. A summary-only reader is not linked to protected full content. Permission denial, missing record, unavailable source and empty successful results remain separate states. Keep the standard module-menu policy; a visible module entry does not grant access. Protected content is not briefly rendered before the verdict, and controls are not the security boundary.

### A03 — STR §§6/6.1/10; BUD §§7/7.1/10; NDS §§6/10 — C alignment

> Include active AO and HOPF responsibilities in the owner read predicates for the approved OVS §4.1 states. STR also includes HoD for approved current/historical versions and approval reasons. BUD exposes AO/HOPF approved allocation and commitment/reservation position, and HoD only funding facts attributable to scoped sources. NDS exposes submitted/decided Needs and lineage to AO/HOPF site-wide. Preserve unsent-Draft and workflow-task restrictions. Registers, record/history/file reads and denied-state audience descriptions reflect these same grants. New independent workflow actions are absent.

### A04 — PLN §§6/7.1/UI routes and PLN18-AC-025 — C source review plus P DPP clarification

> AO and HOPF can read submitted/approved Plan versions, decisions and all exact source/evidence used in those versions. Additionally, they can read site-wide certified submitted DPP snapshots and accepted classifications with their correction/impact history. This adds no unsent departmental Draft or mutable successor access. `GetDepartmentalPlan`, `GetSourceEvidence` and `GetAcceptedDPPClassification` declare those readers explicitly. The DPP classification route renders the accepted/certified read projection for these actors; classify, accept, correct, save and package commands remain exclusive to the valid Planner authority and guards. HoD receives only scoped source/classification and disclosed downstream position. Editor/task ownership is not required for these read-only views. Parent/source links retain exact submission and Plan-version identity.

### A05 — REQ §8 / read and route contracts — C alignment

> Add active AO as a site-wide read-only audience for authorised Requisition versions, decision/history, funding and consumed handoff evidence. The record and authorised-detail routes render that immutable projection without edit/submit/authorise/revoke controls. HOPF retains current submitted/governed access; departmental and contributor reads remain scoped. AO oversight does not grant unsent Draft access. Procurement Officer consumes the authorised handoff and gains no Requisition Draft power.

### A06 — TPR §§6/7.1/9; BOP §6/read routes — C alignment

> Preserve existing AO/HOPF operational review and decision reads across task completion and history. Source-scoped departmental readers receive inherited requirements and disclosed progress only. After governed reveal, AO contextual read and HoD's scoped Opening summary open through the owner-generated destination; neither grant creates ceremony, decryption, attestation or full competitor-bid authority. Appointment and current personal member proof remain separate action guards. Bind the actual `/desk` and documented `/app` route registrations in the repository; do not invent aliases to mask a permission error.

### A07 — EVL §3 / delivered report / correction reads — C alignment

> Resolve independent appointed working access and oversight disclosure separately. AO/HOPF oversight before delivery contains only OVS administrative progress; after delivery it contains the exact delivered report and all authorised evaluated-bid evidence and submitted attachments. A return or handoff to Award does not remove the prior delivered version; show Returned for correction with its reason and retain version selection until the successor is delivered. HoD receives only the scoped disclosed recommendation/outcome/reason summary. A secretary's valid working access is not replaced by oversight status. Unfinished successor findings remain outside delivered-version oversight.

### A08 — AWD decision/history and supplier notice reads — C alignment

> Preserve HOPF/AO access to their governed opinion/decision/evidence and completed history. HoD's scoped projection discloses status and, after the final decision, outcome/date and authorised reason summary; it excludes unissued notices, draft opinion, internal correspondence and unfinished AO deliberation. Supplier reads are restricted to the addressed organisation's issued notice and permitted response/explanation. Related EVL links use the exact delivered version and independent current read verdict.

### A09 — PRC meetings/read contract — C alignment

> AO/HOPF, scoped HoD/auditor and Administrator/System Manager can read the authorised safe meetings register. Metadata excludes bidder identities/counts, prices, findings and discussion contents. Full session minutes/attestations require the stage owner's separate disclosure verdict. A metadata View record link goes to a safe session projection when full content is unavailable; it must not imply register access grants minutes. No meeting command is added.

### A10 — CM §§3/6/9 and native-linked projections — P (CM remains proposed)

> Define AO/HOPF ordinary contract oversight site-wide; HoD, owner, receiving and inspection readers require the recorded contract/department/appointment relation. Ordinary contract facts include agreement, attributable delivery/acceptance decisions, obligations, changes and history. Financial oversight exposes certified entitlement, liability/payment/settlement status, confirmed cash, noncash adjustments, outstanding amount and holds; restricted bank/account details require the explicit Finance/audit projection. KenTender record, invoice/payment review and evidence routes render these authorised projections without mutation. Finance maker/approver actions require separately current assignments and subject eligibility, native validations and segregation. Contract/appointment relation is an owner guard on AUTH's Site-wide/OU responsibility, not a third registry scope type. Supplier grants remain own-contract and do not inherit all BDS powers.

### A11 — CFG / STD / BDS boundaries — C alignment

> AO/HOPF/HoD business responsibility supplies only the contextual configuration/issued-template evidence the consuming owner permits. It does not grant general setup maintenance. HOPF/Procurement Officer template inspection and concern reporting follow AUTH v1.10; no template activation/edit from read. BDS supplier users read only their permitted organisation/arrangement. Office, technical status or an emitted link cannot reveal another supplier's Draft or sealed contents. Native accounting setup remains separately authorised.

### A12 — KT-STD §3A.6 / AUTH §8 / OVS §4.2 / BDS/BOP/PRC — P consolidation of conflicting text

> Administrator/System Manager have a permitted KenTender page verdict and read-only access to ordinary business records in all states. Before governed opening, sealed bid payloads and decryptable documents remain excluded; the page renders only authorised safe metadata/status. Signing credentials, custody secrets and keys are never ordinary record fields. After governed release, ordinary stage records follow the technical-read policy. A limited incident/support operator has only its explicitly assigned diagnostic/recovery access and is not the technical read-all audience. No technical role gains a business command, personal committee action, attestation, signature or release/decryption authority. Where prior text says “read everything,” this content exception is explicit. Production custody controls remain TRUST-owned.

### A13 — Home §6 / Analytics §6 — C/P alignment of proposed surfaces

> Compose only owner-authorised facts, counts and destinations. Retain the actor's exact permitted version and source context. Owners return safe summary links for summary-only readers; Home/Analytics do not link them to committee working detail. Revoked/expired assignments are rechecked on each read and at the destination. An authorised source failure is shown as unavailable; a denied stage is omitted without disclosing its existence. Technical status creates no personal business work.

### A14 — Shared fixtures / test and conformance sections — P verification addition

> For every registered role and owner route family, supply an allowed-read case, prohibited action case, out-of-scope/disclosure case, and exact-version/navigation case where applicable. Use canonical users with explicit dated assignments/appointments; title or a seeded Frappe Role is insufficient. Include acting, dual responsibility, role expiry and completed-task journeys. Keep business readers, Administrator/System Manager and limited support distinct. Report actual test outcomes with user, state/version, route/service and evidence; document review is not runtime success.

## 6. Claude Code implementation brief

Implement the approved-grant corrections and prepare proposed-grant changes as reviewable code according to the project's approval boundary. Do not invent a new permission architecture or fix failures by adding unrelated roles. The following is executable work scope once the repository is available; this review has not edited it.

1. **Reproduce and map.** Locate the real Planning classification route in the screenshot, its read service, current task guard, assignment resolution and native hook. Record the actual DPP state/version, scoped OU, relevant Plan lineage and denied predicate. Resolve all existing documented route families to actual repository registrations; `/app` in a requirement is not proof of the deployed `/desk` binding. Reuse canonical fixtures and add dates/appointments only under the source contracts.
2. **Inspect shared enforcement.** Identify AUTH's assignment resolver, scope map, `permission_query_conditions`, `has_permission`, whitelisted reads, file/download/export access and native-record adapters. Compare each with the matrix; identify role-label checks, task-only read guards, role/scope Cartesian products, stale projections, hidden writes on reads and permission bypass flags. Produce code/file references for each finding. Do not assume these defects exist before inspection.
3. **Correct by owner.** First fix AO Planning/source/classification and back navigation; then STR/BUD/NDS/REQ approved reads; then TPR/BOP/EVL/AWD/PRC stage disclosure; then technical content boundaries and proposed CM/Home/Analytics. Apply the same role-bound read policy to source queries/counts and direct services. Keep commands guarded independently and rechecked server-side. Do not use `ignore_permissions` or an unrestricted data endpoint to make a page work.
4. **Render authorised projections.** Reuse the existing shell, record screens and summary components. Read-only mode removes business mutation controls and suppresses auto-save/create behaviour. Keep legal decision facts, reasons and source evidence readable. Filter protected fields server-side, not by hiding DOM controls. Preserve exact version, selected tab and return context. Task queues contain actionable work; searchable registers contain permitted records even after work is complete.
5. **Close navigation.** Enumerate links from Home, Analytics, lists, task rows, Tender progress, meetings, history and evidence. Ask the destination owner for a current permitted route/projection. For summary-only readers use the safe summary. Never show an enabled record link that deterministically leads to an authorisation denial. Keep intentional top-level denied module entries consistent with KT-STD.
6. **Verify.** Run §7 cases using the actual actors and server services, followed by role journeys in the browser. Capture permission and data-leak regressions, not just screenshots. Test native/API/import Finance paths where CM is implemented. Record implemented/not implemented and pass/fail separately; planned surfaces cannot count as passed deployed journeys.
7. **Handoff.** Provide the changed-file list, exact source/approved-versus-proposed grant basis, migration/assignment impact, test results and unresolved route bindings. Review the supplied self-contained owner working revisions and register their approved successors in the actual baseline registers during the controlled documentation cutover. Do not leave this report as a second operative requirements source.

### 6.1 Required implementation inventory format

| Field | Required content |
|---|---|
| Owner / route ID | Stable owner screen/read identifier and actual deployed path |
| Record / version / state | Exact test subject and disclosure milestone |
| Role / assignment / relationship | Actual registry role, assignment period/scope and subject/appointment/contributor relation |
| Allowed projection | Fields/evidence/version range; safe summary versus full record |
| Allowed commands | Owner command list, possibly empty; independent task/state/segregation guards |
| Enforcement | Resolver/hook/query/service/file and frontend registration code locations |
| Entry and return links | Source screen/version, target projection and restored context |
| Evidence | Existing grant or proposed amendment ID; test result/artifact and implementation status |

Inventory every real screen/route variant; the source families in §8 are the starting set, not a claim of runtime completeness. Declared requirements without a concrete route binding remain an implementation gap. Do not mark a module complete because its landing page opens.

## 7. Verification cases

All cases are required future tests, not reported passes. For every positive read verify its matching list/count/search/detail/file/export paths; assert no protected fields in JSON as well as no prohibited buttons. Negative command tests call the server directly, regardless of hidden controls.

| ID | Actor / scenario | Required result |
|---|---|---|
| ACC-01 | Amina, exact reported DPP classification URL, accepted/certified submission with active AO assignment | Correct read-only snapshot/history/source/impact opens; no Planner accept/classify/save/correct command; Back restores source context. Record original failing predicate and corrected result. |
| ACC-02 | Same URL but unsent author Draft, missing record, expired AO assignment and unrelated valid role | Preserve each real boundary; protected existence masked; no permission gained from the URL/title. Incorrect upstream authorised-record link is removed or redirected to permitted summary. |
| ACC-03 | AO review → Plan item → exact DPP/Need → classification/history → source Budget facts → return | Every permitted linked source opens the exact consumed version; unrelated shared Budget-line data remains excluded; no source edit or approval by navigation. |
| ACC-04 | AO/HOPF STR approved/current/history; Draft successor exists | Approved versions/reasons available; successor Draft/review inaccessible solely from oversight; Source link remains exact. |
| ACC-05 | AO/HOPF BUD current/historical and funding events | Approved position/lineage readable; draft authoring/approval task and reserve/release/convert calls denied without their distinct authority. |
| ACC-06 | AO/HOPF NDS submitted/decided and author unsent Draft | Submitted/decided decisions/lineage readable; no unsent-Draft grant from oversight; no Need decision/edit from office alone. |
| ACC-07 | AO REQ authorised/history and unsubmitted Draft | Immutable authorised record/funding/handoff readable; Draft remains outside added grant; submit/authorise/revoke denied. |
| ACC-08 | HoD with lead OU, contributing OU, descendant and unrelated OU cases | Match exact consumed source relationships; relevant summaries available; unrelated protected records/counts/evidence excluded. Shared Budget line or current edited department cannot broaden access. |
| ACC-09 | Departmental Author, HoD, Planner and Procurement Officer through their normal journeys | Creator/contributor/current-role reads work; certified facts immutable; Author cannot act as HoD, Planner cannot decide REQ, Procurement Officer cannot open REQ Draft from handoff authority. |
| ACC-10 | Strategy/Budget author plus approver assignments on same user | Both permitted work sets visible; own-version approval denied based on history; role union does not widen an OU role's scope. |
| ACC-11 | Finance Confirmation Officer complete Plan review/reassessment | Entire permitted financial basis and exact source facts visible; confirm/return under current token; no Budget editing/reservation/payment authority. |
| ACC-12 | AO/HOPF/HoD BOP before and after reveal | Before: permitted appointment/admin facts only. After: correct contextual record or scoped summary. No implicit opening/decrypt/attest authority. |
| ACC-13 | Opening member/chair/recorder and public/attending supplier | Personally appointed working actions succeed under guards; recorder cannot proxy member proof; public readout/register never opens competitor bids/internal minutes. |
| ACC-14 | AO/HOPF EVL before delivery | Administrative facts only; no new bidder identities/counts/prices/findings/clarifications/notes in screen, JSON, search or export. Existing separately revealed Opening information remains under BOP. |
| ACC-15 | Eligible EVL member/chair/secretary | Working read/actions match capacity; secretary has no vote/signature by default; conflicts remove affected bid access immediately; replacement/roster guards retained. |
| ACC-16 | Delivered EVL report → Award → returned report → correction in progress → delivered successor | Old delivered evidence remains readable with status/reason; exact bid attachments/history preserved; unfinished correction inaccessible through oversight; successor becomes current only on delivery. |
| ACC-17 | HoD EVL/AWD progress and delivered/final result | Safe scoped summary/reasons open through correct destination; no full report, committee working notes, unfinished opinion or unissued notice. |
| ACC-18 | Supplier representative/signatory across BDS/EVL/AWD/CM | Own organisation/arrangement only; submission/signature require exact current authority; cross-organisation IDs/files denied; CM grants evaluated separately. |
| ACC-19 | Meetings register reader with no full minutes entitlement | Safe metadata/counts and safe destination work; no bidder identities/prices/notes; clicking View never requires general committee membership. |
| ACC-20 | Auditor site-wide and OU scopes | Correct owner disclosure/version/history and files; no business mutation; sealed restriction cannot be overridden by generic audit role. |
| ACC-21 | Administrator/System Manager across all ordinary statuses/task/editor routes | Permitted read-only records/search; no business command/My Work from technical role; pre-opening sealed content/keys/credentials excluded under reviewed A12. |
| ACC-22 | Limited support/recovery operator | Only assigned diagnostics/recovery evidence; no technical read-all, unrelated records, business commands, decryption or personal proof. |
| ACC-23 | AO/business user on CFG/STD bound evidence | Relevant contextual evidence and authorised template inspection work; setup edit/root repair/activation denied without the specific setup authority. |
| ACC-24 | CM contract owner/receiver/inspector/AO/HOPF/HoD | Relevant exact agreement/delivery/acceptance/obligation/history readable; commands restricted by assignment/appointment; receiver cannot accept same arrival, conflicted inspector cannot act/read affected scope. |
| ACC-25 | CM Finance maker/approver, ordinary oversight and supplier | Maker/approver get required protected editor/review fields; oversight gets contractual payment position; supplier gets own safe status; no account/beneficiary leakage or own-entry approval. Native validation/reversal holds preserved. |
| ACC-26 | Registered owner services, direct API/import/background calls | Only authenticated REQ/CM owner contexts invoke their Budget contracts; no human-role shortcut or Planning/Tender/Evaluation/Award funding mutation. |
| ACC-27 | Home/Analytics search/counts/links and existing owner registers | Same authorised set and correct summary/full destination; no denied-record identity/count leak, stale-version substitution or new grant from aggregate. |
| ACC-28 | Active/acting/scheduled/expired/revoked assignments and multi-role user | Scheduled role grants no early authority; acting window exact; expiry invalidates reads/commands; no role/scope cross product; historical evidence stays intact. |
| ACC-29 | Every permitted route by direct load, refresh, Back/Forward and file/export API | Same disclosure as linked navigation; exact version retained; permission resolves before render; reads produce no draft, task, decision or native posting. |
| ACC-30 | All real registered routes/variants compared with §8 and implementation inventory | Every route covered by positive/negative cases or explicit non-applicability; missing planned modules, unresolved bindings and failures reported without fabricated passes. |

### 7.1 Canonical actors

Use Amina Hassan (AO), Charles Mutiso (HOPF), Mercy Kilonzo (Planner), Julia Njeri (HoD), Grace Wanjiku (Departmental Author), Brian Wafula (Procurement Officer), Josphat Mwangi (Budget/Finance assigned capacity), Beatrice Kamau (Budget/Finance assigned capacity), Esther Muthoni (Strategy Author), Dr Alfred Ochieng (Strategy Approver), Naomi Chebet (Auditor), Daniel Rotich (configured statutory approver), Mary Wanjiku (supplier signatory), David Ouma (supplier representative), Daniel Otieno (technical reader/operator only as the fixture explicitly specifies), and Samuel Otieno (expired assignment). Confirm exact logins, dates, OU codes and existing capacities against KT-STD §8 and actual seeds before testing. CM appointments are isolated proposed fixture capacities; do not promote them to global powers. Add the other opening/evaluation participants from their canonical roster rather than substitute a named person merely to make the test pass.

## 8. Source and route-family inventory

The source digest records exactly which local requirement bytes were reviewed. It is provenance, not a security mechanism. Route families below are literal declared requirements, not verified deployed URLs. References inside prose may include retired routes; only active owner UI-route sections are listed. Conceptual BOP/EVL/PRC destinations need repository binding. `/desk/procurement-planning/dpp-classification/...` is additionally the observed deployed URL from the screenshot.


| Source | SHA-256 (first 16 characters) | Reviewed access sections |
|---|---|---|
| KenTender_AWD-CHG-001_Award_v0_5.md | `92da7f97302d7fda` | 9. UI architecture, menu and routes |
| KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_11.md | `34128a5c2d40923a` | 6. Responsibilities and permissions; 9. UI architecture, navigation and routes |
| KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_11.md | `2446e23f299bc1a3` | 6. Responsibilities and permissions; 9. UI architecture and routes |
| KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_12.md | `2b83ccd32f30d62c` | 7. Roles and permissions; 10. UI architecture and routes; 11.1A BUD-DES-01A — Budget & Funding workspace, technical reader with an open Draft or Submitted version |
| KenTender_EVL-CHG-001_Bid_Evaluation_v0_5.md | `7db065bf88e624bd` | 3. People and access |
| KenTender_KT-STD-001_Document_Design_and_Verification_Standards_v1_25.md | `2511baa64705838c` | 3A.6 Technical read; 3B.6 Technical readers |
| KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_16.md | `470d7762c9c2db88` | 6. Roles, assignments and permissions; 10. UI architecture, menu and routes |
| KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_29.md | `821a191f00adc01c` | 6. Roles, permissions and segregation; 7.1 Common envelope and reads; 9. UI architecture, navigation and presentation; 10.1A.6 Technical readers and other readers |
| KenTender_PRC-CHG-001_Minimal_Procurement_Proceedings_v0_11.md | `9c698a9825882d3e` | 6. Responsibilities and permissions; 9. UI architecture and routes |
| KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_14.md | `eaa44ad963eda04a` | 8. Roles and permissions; 12. UI architecture and routes |
| KenTender_STD-TPL-001_IT_Equipment_Tender_Template_Curation_and_Release_Pack_v0_15.md | `9d34e53e11bbb695` | Owner audience, source/consumer and disclosure paragraphs; shared control sections |
| KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_9.md | `df968d5d95c93e65` | 6. Roles and permissions; 10. UI architecture and routes |
| KenTender_TPR-CHG-001_Tenders_v0_17.md | `d0a7c1c6ecde9368` | 6. Roles and permissions; 9. UI architecture, menu and routes |
| KenTender_ANL-CHG-001_Procurement_Analytics_v0_3.md | `8651b06861451b9b` | 6. Roles and permissions; 9. UI architecture and routes |
| KenTender_AUTH-ADR-001_Role-Bound_Business_Responsibility_and_Organisational_Scope_v1_10.md | `68737c1f1dfabf7f` | 5.3 One predicate, registered as hooks; 12. UI architecture, menu and routes |
| KenTender_CFG-CHG-002_Site_Configuration_and_System_Setup_v0_16.md | `f1a5ba62d52567a1` | 6. Actors, permissions and segregation; 9. UI architecture and routes |
| KenTender_HOME-CHG-001_Home_v0_3.md | `b38ca8aa6fd2db00` | 6. Roles and permissions; 9. UI architecture and routes; HOME-DES-07 — technical reader |
| KenTender_OVS-CHG-001_System_Usability_and_Decision_Visibility_v0_6.md | `82a0bcd258059740` | 4. Role and disclosure contract |
| KenTender_CM-CHG-001_Contract_Management_v0_3.md | `5d38a5169f7019ed` | 6. Roles and permissions; 9. UI architecture, menu and routes |

### 8.1 Declared route families by owner

| Owner source | Section | Declared route families / binding |
|---|---|---|
| KenTender_AWD-CHG-001_Award_v0_5.md | 9. UI architecture, menu and routes | `/app/award`; `/app/award/{award_id}`; `/supplier/awards/{notice_id}` |
| KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_11.md | 9. UI architecture, navigation and routes | `/tenders`; `/tenders/{tender_reference}`; `/my-bids`; `/account`; `/account/receipts`; `/tenders/{tender_reference}/bid`; `/tenders/{tender_reference}/bid/{task_key}`; `/tenders/{tender_reference}/bid/review`; `/tenders/{tender_reference}/bid/submit`; `/tenders/{tender_reference}/bid/receipt/{receipt_reference}`; `/desk/tender-security-receipts` |
| KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_11.md | 9. UI architecture and routes | `/app/tenders/{tender_id}` |
| KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_12.md | 10. UI architecture and routes | `/app/budget`; `/app/budget/{budget_id}/version/{version_number}/edit`; `/app/budget/{budget_id}`; `/app/budget/review/{budget_version_id}`; `/app/budget/line/{budget_line_id}` |
| KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_16.md | 10. UI architecture, menu and routes | `/app/departmental-needs`; `/app/departmental-needs?view=department`; `/app/departmental-needs/new`; `/app/departmental-needs/{need_reference}/edit`; `/app/departmental-needs/{need_reference}`; `/app/departmental-needs/review/{review_task_id}`; `/app/departmental-needs/{need_reference}/accepted/{revision_number}`; `/app/departmental-needs/review/{review_task_id}/withdrawal`; `/app/system-setup` |
| KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_29.md | 9. UI architecture, navigation and presentation | Contextual owner record; exact binding specified by the owner/repository, not invented here |
| KenTender_PRC-CHG-001_Minimal_Procurement_Proceedings_v0_11.md | 9. UI architecture and routes | Contextual owner record; exact binding specified by the owner/repository, not invented here |
| KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_14.md | 12. UI architecture and routes | `/app/procurement-requisitions`; `/app/procurement-requisitions/new/{plan_item_id}`; `/app/procurement-requisitions/{requisition_id}`; `/app/procurement-requisitions/department-task/{task_id}`; `/app/procurement-requisitions/procurement-task/{task_id}`; `/app/procurement-requisitions/{requisition_id}/authorised` |
| KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_9.md | 10. UI architecture and routes | `/app/strategy`; `/app/strategy/plan/{plan_id}`; `/app/strategy/plan/{plan_id}/version/{version_number}/structure`; `/app/strategy/approval/{plan_version_id}` |
| KenTender_TPR-CHG-001_Tenders_v0_17.md | 9. UI architecture, menu and routes | `/app/tenders`; `/app/tenders/new/{handoff_id}`; `/app/tenders/{tender_id}`; `/app/tenders/{tender_id}/history`; `/app/std-templates/{template_release_id}` |
| KenTender_ANL-CHG-001_Procurement_Analytics_v0_3.md | 9. UI architecture and routes | `/app/analytics`; `/app/departmental-needs/{need_reference}`; `/app/procurement-requisitions/{requisition_id}/authorised`; `/app/procurement-requisitions/{requisition_id}`; `/app/tenders/{tender_id}`; `/app/strategy`; `/app/budget` |
| KenTender_AUTH-ADR-001_Role-Bound_Business_Responsibility_and_Organisational_Scope_v1_10.md | 12. UI architecture, menu and routes | `/app/system-setup#organisation-structure`; `/app/system-setup#users-and-responsibilities`; `/app/organisation-unit`; `/app/user-responsibility-assignment`; `/app/user-permission`; `/app/organisation-structure`; `/app/user-responsibilities` |
| KenTender_CFG-CHG-002_Site_Configuration_and_System_Setup_v0_16.md | 9. UI architecture and routes | `/app/system-setup`; `/versions/{version_id}`; `/calendars/{id}`; `/app/system-setup/tender-formats`; `/app/std-templates` |
| KenTender_HOME-CHG-001_Home_v0_3.md | 9. UI architecture and routes | `/app/home`; `/app/tenders/{tender_id}`; `/app/departmental-needs`; `/app/procurement-planning`; `/app/procurement-requisitions`; `/app/tenders` |
| KenTender_CM-CHG-001_Contract_Management_v0_3.md | 9. UI architecture, menu and routes | `/app/contracts`; `/app/contracts/register`; `/app/contracts/{id}`; `/supplier/contracts`; `/supplier/contracts/{id}`; `/app/contracts/{id}/invoices/{invoice_id}`; `/app/contracts/{id}/payments/{payment_id}` |

### 8.2 Owner audience coverage extracted from the reviewed sources

The following literal owner role tables retain narrower rules which the reconciliation must preserve. They are traceability evidence, not an instruction to ignore approved OVS additions or proposed amendments above. Tables duplicated in source history are omitted; committee and supplier capacities still follow their owner-specific guards.


**KenTender_BDS-CHG-001_Supplier_and_Electronic_Bid_Submission_v0_11.md — 6. Responsibilities and permissions**

| Responsibility | Scope | Exact work |
|---|---|---|
| Public visitor | Public published Tenders | Find and read published Tender information and documents; no bid or account action. |
| Supplier Representative | Assigned supplier organisation | Maintain permitted Account facts; start and prepare Drafts; upload evidence; view organisation receipts. Cannot submit, replace or withdraw. |
| Authorised Signatory | Assigned supplier organisation and active authority window | All Supplier Representative work plus digitally sign, submit, replace and withdraw the organisation's bid. |
| Procurement receipt owner | Site-wide procurement-function assignment | Record receipt of a required physical tender-security original; cannot read Draft or sealed bid content. |
| Auditor | Approved oversight scope | Read registration, command, receipt, signature and custody metadata under the legal access rule; no pre-opening bid content by default and no mutation. |
| Authorised technical operator | Explicit custody/support assignment | Monitor non-content service health and approved recovery evidence; cannot view responses, sign, submit, withdraw, open or evaluate. |
| Administrator / System Manager | Technical read under KT-STD-001 §3A.6 | Configuration/health metadata only for sealed bids; no business authority and no content access before governed opening. |
| System | Internal | Derive readiness, validate, bind evidence, enforce deadline, obtain approved signature/custody receipts, close the box and publish the opening handoff. |


**KenTender_BOP-CHG-001_Electronic_Bid_Opening_v0_11.md — 6. Responsibilities and permissions**

| Actor | Authority and limit |
|---|---|
| Accounting Officer | Appoints/corrects committee with history; cannot open on behalf of members by virtue of office alone. |
| Appointed chair/member | Each authenticates presence throughout the active ceremony, participates in controlled access and performs own target-specific attestation; chair coordinates but cannot represent absent members. No pre-deadline access, proxy signature, scoring or disqualification. |
| Recorder | Records factual attendance/notes and prepares minutes; cannot override member proof or custody. |
| HOPF/Procurement Officer outside appointment | Contextual lawful read after reveal, no implicit ceremony authority. |
| Tenderer or representative | Attends and hears statutory opening facts; submitting bidder may request final register; no full competing bid or internal minutes. |
| Auditor | Authorized historical oversight read, no ceremony mutation or pre-opening content by default. |
| Administrator/System Manager | Non-content health and incident support only; no opening, decryption, attestation or business completion. |


**KenTender_BUD-CHG-001_Clean_Budget_and_Funding_v1_12.md — 7. Roles and permissions**

| Business role | Scope type | Permitted actions |
|---|---|---|
| Budget Officer | Site-wide | Register the initial Draft, create a successor, edit Draft approval details and lines, and submit. |
| Budget Approver | Site-wide | Inspect a submitted version; return it with a reason, or approve and activate it; close a Budget after the fiscal year. |
| Finance Confirmation Officer | Site-wide | Open the current whole-Plan Finance review, confirm or return against its basis, and reassess exact Active Plan content through Planning. At most one review is open per Plan Version; completed reviews remain history. Confirmation creates no reservation and grants no Budget authoring, approval or activation authority. |


**KenTender_EVL-CHG-001_Bid_Evaluation_v0_5.md — 3. People and access**

| Person / responsibility | Work and access |
|---|---|
| Accounting Officer | Appoint or formally replace the committee; deal with declared conflicts and inability to serve. Appointment access contains no automatic right to read bids or alter findings. |
| Chair — appointed member | Coordinate work, convene discussion, record the committee's conclusions and authorise a written clarification. Cannot decide for absent members or sign for anyone. |
| Appointed member | Inspect bids and results, record evidence findings or concerns, participate in discussion, record their own disagreement and sign the report. |
| Secretary | The Head of Procurement or a procurement officer appointed in writing by that head. Organise records, record discussion, send the authorised clarification and prepare the generated report. Secretary status alone gives no member vote, finding authority or signature. |
| Head of Procurement | Appoint a procurement-officer secretary; receive the report and supporting record; return it with specific comments. Professional opinion is outside this document. |
| Supplier Representative / Authorised Signatory | See and answer only their organisation's clarification through the existing BDS authority model. No access to internal findings, ranking, committee notes or another bidder's material. A clarification is correspondence, not a replacement bid. |
| Auditor | Read the evaluation record within the assigned oversight scope; no mutation. |


**KenTender_NDS-CHG-001_Clean_Departmental_Needs_v1_16.md — 6. Roles, assignments and permissions**

| Business responsibility | Central scope classification | Permitted work |
|---|---|---|
| Departmental Author | Organisation Unit | View own Needs; create and edit own Draft/Returned Need; submit, resubmit and withdraw before acceptance; propose an update or withdrawal of own accepted Need. |
| Head of User Department | Organisation Unit | View Needs in the assigned OU subtree; decide submitted Needs, successor updates and withdrawal requests, except own submitted revision. |
| Procurement Planner | Site-wide | Read current accepted Need revisions through the typed source contract and exact read-only deep link; no Need decision and no separate intake-window workspace. |
| Auditor | Site-wide or approved OU oversight scope | Read scoped Needs, revisions, decisions and lineage; no business mutation. |
| Administrator / System Manager | KT-STD-001 v1.7 §3A.6 | Technical access is inherited from the controlling standard; NDS adds no business command or local exception. Separate setup maintenance remains CFG/AUTH-owned. |


**KenTender_PLN-CHG-001_Clean_Procurement_Planning_v1_29.md — 6. Roles, permissions and segregation**

| Actor | Workspace emphasis | Allowed work | Explicit boundary |
|---|---|---|---|
| Departmental Author | Own departmental Drafts/corrections | Direct/source funding and disposition Draft work | No HoD certification unless separately assigned |
| Head of User Department | Departmental certification/updates | Certify/submit within current substantive or acting authority | Cannot validate own certified Submission as Planner |
| Procurement Planner | DPP validation, classification correction, consolidation, pending requirements and Plan corrections | Classify/reclassify under §5.1.6; package work, Finance request and successor/correction management | No source-fact editing, accepted-decision mutation or final HOPF signature unless separately assigned; no procurement creation or MVP forecast maintenance |
| Head of Procurement Function | Plan ready for preparation signature | Complete review; Sign and submit Annual Plan | This is preparation accountability, not an added approval stage |
| Finance Confirmation Officer | Current plan-level review/reassessment | Confirm plan funding or Return to planner | No editing the Plan or reserving money |
| Accounting Officer | Adoption, Treasury evidence, late explanation and withdrawal requests | Existing governed actions | Does not impersonate the statutory authority |
| Configured statutory authority | Exact Plan adoption/withdrawal request | Approve, return or confirmed-unpublished withdrawal as allowed | Board/Council record collective resolution and authorised recording actor |
| Auditor/authorised reader | Plan and evidence navigation | Read-only history, permitted review pack | No business decision |
| Administrator/System Manager | Technical read under KT-STD-001 v1.7 §3A.6 | Read all Planning records site-wide through registered routes; no business command. Separately granted setup/publication-recovery authority uses the owning contract. | Technical read supplies no Planning decision or publication retry authority |


**KenTender_PRC-CHG-001_Minimal_Procurement_Proceedings_v0_11.md — 6. Responsibilities and permissions**

| Responsibility | Permitted PRC action | Constraint |
|---|---|---|
| Bid Opening owner service | Create/start/end, append authoritative events and request finalization | Owns statutory guards; cannot bypass member proof. |
| Owner-designated recorder/secretary | Record actual attendance and factual notes, prepare minutes, propose supplement | Bound to this Tender/session; cannot alter owner bid events or attest for others. |
| Appointed committee member | Read authorized session, attest exact assigned target | Identity must match owner's appointment; attendance alone does not confer member authority. |
| Tenderer/representative | Attend under owner procedure; receive the legally permitted readout/register route | No automatic general PRC read, bid-content or internal minutes permission. |
| Auditor | Read lawful historical record and proofs | Oversight scope; no mutation or pre-opening content by default. |
| Administrator/System Manager | Technical status/health and assigned infrastructure incident outside PRC | No PRC business action, member proxy, opening/attestation, or PRC actionable My Work. The synthetic TRUST proxy makes no confidentiality guarantee against infrastructure administrators; production separation belongs to the approved Trust operating profile. |


**KenTender_REQ-CHG-001_Structured_Procurement_Requisitions_v1_14.md — 8. Roles and permissions**

| Business role | Scope type | Exact work |
|---|---|---|
| Departmental Author | Organisation Unit | View eligible Planning allocations for the assigned department; prepare and correct a Draft; send a complete Version to the Head of User Department when acting for the lead Draft. A contributing-department Author may edit only their permitted source/item content, sees the combined context read-only, and cannot route or decide the package. |
| Head of User Department | Organisation Unit | View the complete departmental Requisition; prepare and submit directly, or return/submit an Author's locked Version; withdraw before authorisation; certify on behalf of every contributing department when more than one exists. |
| Head of Procurement Function | Site-wide | View the complete submitted Requisition and fresh Planning and Budget availability; return, authorise or revoke before consumption. May request upstream correction, or change lead via reasoned return for recertification; cannot edit requirements. Same registry entry as DSP-CHG-001 and TPR-CHG-001 use for this office. |
| Procurement Planner | Site-wide | Neutral read of Planning lineage and drawdown projection; receives the `PlanItemCorrectionRequest` task in §7.4A; no Requisition decision. |
| Procurement Officer | Site-wide | No Draft right in Requisitions by virtue of this role; consumes the authorised handoff in Tender Preparation. |
| Auditor | Site-wide or approved OU oversight scope | Neutral read of immutable Versions, decisions, drawdowns, reservations, handoffs and consumption evidence; no business transition. |
| Administrator / System Manager | Technical read-all under AUTH v1.9 §8 | Read Draft/submitted/authorised/stopped content and evidence; no business write or decision without the applicable live responsibility. |


**KenTender_STR-CHG-001_Clean_Strategy_Alignment_v1_9.md — 6. Roles and permissions**

| Business role | Scope type | Permitted actions |
|---|---|---|
| Strategy Author | Site-wide | Create plans and successor versions; edit Draft content; submit for approval. |
| Strategy Approver | Site-wide | Inspect a submitted version; return it with a reason, or approve and activate it. |


**KenTender_TPR-CHG-001_Tenders_v0_17.md — 6. Roles and permissions**

| Business responsibility | Scope | Exact work |
|---|---|---|
| Procurement Officer | Site-wide | Start and prepare Tender; submit; correct returned work; request Requisition correction; draft addendum; respond to supplier clarification. |
| Head of Procurement Function | Site-wide | Return/approve Tender package; reopen before publication authorisation; confirm channel publication with evidence and attestation; draft/issue addendum; respond to clarification; optionally recommend cancellation. |
| Accounting Officer | Site-wide | Authorise publication; v0.16: return an approved package to the Head of Procurement Function with a reason before authorising; withdraw authorisation only when confirmed unpublished and no channel was confirmed; cancel Tender. Cannot edit package/addendum content. |
| Departmental Author / Head of User Department | Organisation Unit | Read inherited requirements and neutral Tender/publication status already authorised by source scope; no Tender action. |
| Auditor | Site-wide or approved oversight scope | Read Versions, decisions, publication confirmations/evidence, addenda, clarifications, candidate-notice evidence and cancellation; no business action. |
| Authorised technical operator | Explicit future integration assignment | No MVP publication action. When §5.5.1 is implemented, may perform only approved reconciliation/recovery; cannot attest publication, edit content, authorise, issue or cancel. |
| Administrator / System Manager | Technical read | Read all records under KT-STD-001 v1.8 §3A.6; no business action unless separately assigned an explicit business/recovery responsibility. |
| System | Internal | Generate schedules/renders; validate and derive publication state from accountable confirmations; close submission period; publish Planning invitation actual and downstream event. |


**KenTender_CFG-CHG-002_Site_Configuration_and_System_Setup_v0_16.md — 6. Actors, permissions and segregation**

| Actor | Allowed configuration work / experience | Limits |
|---|---|---|
| Administrator | Entity, years/submission periods, funding, rules, schedules, calendars, reminders, public supplier-portal settings and source-check recording; AUTH-owned organisation/responsibility maintenance. | Direct maintenance under CFG11-EX-001; exceptional missing-root repair under CFG11-EX-003. Business technical access is governed by KT-STD-001 v1.7 §3A.6. |
| System Manager | The same ordinary maintenance, public portal settings and evidence recording; AUTH-permitted organisation/responsibility work. | No missing-root repair action; show the Administrator escalation. Business technical access is governed by KT-STD-001 v1.7 §3A.6. |
| Business actors | Owner-authorised relevant values, deadlines, current issues and decision evidence inside their business record/review. | Business responsibility alone gives no setup mutation or full setup access; each owner supplies its permitted correction/return path. |
| Auditor | Owner-authorised historical configuration evidence, separating the source check used at the decision from any current warning. | No setup mutation or new unrestricted configuration browser. |
| Technical reader examining records | Inherits KT-STD-001 v1.7 §3A.6. | Search/read-entry registration is mandatory; do not duplicate the common technical-read contract here. |
| Authenticated system service | Registered reads, current decision validation and scheduled expiry under fixed contracts. | No arbitrary rule edit, business task, self-asserted legal verification or wait-for-cleanup deadline bypass. |


## 9. Completion and next execution step

Completed: incorporated the precise amendments and relevant verification cases into 19 self-contained proposed owner review copies, retaining their source baseline text and truthful approval status; reviewed source/role/disclosure contracts; produced the oversight and functional matrices; identified the AO route investigation and conditional expected result; wrote 14 precise owner amendments, implementation scope and 30 verification cases; recorded source digests, declared route families and literal owner role-table provenance. Document consistency checks verify unique case/amendment identifiers and source coverage. No installed permission test, source-document approval, baseline-register update or application fix is claimed.

Next execution step: use §6 in the KenTender repository to reproduce Amina's exact Planning denial and correct the approved-grant paths, with the matrix governing the review. Incorporate the proposed clarifications into reviewed self-contained owner successors before treating them as new approved grants. Keep planned CM/Home/Analytics tests separate from deployed MVP tests. Completion evidence is the role-by-route inventory and actual allow/deny/navigation results, not another general assertion that permissions are fixed.
