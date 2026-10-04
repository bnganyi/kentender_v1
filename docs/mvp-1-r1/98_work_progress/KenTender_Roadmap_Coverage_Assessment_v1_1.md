# KenTender Roadmap Coverage Assessment

**Document ID:** KT-RCA-001  
**Version:** 1.1  
**Date:** 25 September 2026  
**Status:** Gate 1 reconciled — future programme work retained  
**Source roadmap:** *KenTender ePublic Milestone Overview v2*  

## 1. Purpose and authority

This assessment admits the initial client roadmap as a persistent programme reference and compares it with the current KenTender requirements baseline.

The roadmap is preserved unchanged. It is **directional, not normative**: it describes intended programme outcomes and sequencing, while the approved module requirements, architecture decisions, statutory correction register and document standard define what may be implemented. A roadmap statement must not silently override a later legal, security, usability or ownership decision.

## 2. Executive conclusion

KenTender is **on track for a coherent end-to-end MVP vertical slice**, but it is **not yet complete against the full Phase 1 roadmap**.

The strongest continuous path now runs from Strategy and Budget through Departmental Needs, Procurement Planning and Requisitions into Tender preparation, publication and structured electronic bid submission. For the currently supported product—straightforward IT Goods, Open Tender, single lot, KES and fixed price—the requirements are substantially more rigorous than the original roadmap.

The present vertical slice stops at an immutable, sealed handoff to **Bid Opening**. Supplier prequalification, Bid Opening, Evaluation and Award remain separate bodies of work. Additional procurement methods and Works/Services/RFP products also remain deliberately unsupported rather than partially or generically implemented.

The public/vendor requirements through sealed Bid Submission are now reconciled by CFG v0.16, TPR v0.10, BDS v0.7 and STD-TPL v0.9. General clarifications, Start-bid candidate registration, mandatory notices, public support/legal links, the template boundary and the future-module stop are explicit.

Implementation remains gated by exact template-manifest approval and the production trust, time, encryption, custody and recovery operating profile. Bid Opening, Evaluation and Award, Supplier Management/prequalification, additional methods and additional product families are planned future work rather than gaps to fill inside Bid Submission.

## 3. Coverage status

| Roadmap capability | Status | Current position | Required action |
|---|---|---|---|
| Strategic-plan alignment | **Strong** | Governed strategic frameworks, periods, hierarchy, active resolution and immutable Planning snapshots are defined. The implementation uses one coherent framework model instead of hard-coding every roadmap label. | Retain the simpler model. Add explicit plan-type labels only if a real reporting or legal need is demonstrated. |
| Budget linking, validation and locking | **Strong within boundary** | Approved allocations, immutable versions, Budget lines, affordability, reservations and commitments are governed. KenTender does not enact or approve the public budget itself. | Keep Parliament, board and county-assembly approval outside KenTender; store the approved source and effective budget evidence. |
| Departmental and annual procurement planning | **Strong** | DPP/APP preparation, consolidation, governance, approval, funding, methods, schedules and reservation treatment are extensively defined. | Implement against the reconciled Planning, CFG and statutory baseline. |
| Purchase Requisition | **Partial / decision required** | Structured requirements, HoUD certification, HOPF authorisation, Budget reservation and Planning drawdown are defined. Stock checking is absent. The route does not reproduce the roadmap's separate Finance and AO approvals. | Record an explicit variance decision. Decide whether automated Budget control plus HoUD/HOPF is legally sufficient. Define a future Inventory-owned stock-availability contract rather than inventing stock data in Requisitions. |
| Supplier portal account | **Strong for access** | Supplier organisation registration, representatives, sign-in and Tender-bound single/JV arrangements are defined. Registration is correctly not treated as eligibility approval. | Proceed as the access layer for the Open Tender slice. |
| Supplier register / prequalification | **Not yet covered** | The roadmap's approved supplier lists, classifications, verification and prequalification are intentionally outside Bid Submission. | Create a separate Supplier Management requirements document with data-minimisation, lawful-purpose and method-specific rules. Do not place it inside Bid Submission. |
| Tender preparation and publication | **Strong but narrow** | Preparation, technical/user review, HOPF approval, AO publication authorisation, publication evidence, general clarifications, addenda, candidate notices and cancellation are defined with complete artboard contracts. | Implement and verify TPR v0.10 for the Open Tender/IT Goods slice. |
| Public Tender discovery | **Strong** | Public list and Tender detail, documents, addenda, answers, deadlines, eligibility summary, supplier support, privacy/terms/accessibility links and sign-in-at-action are defined. | Implement the CFG-owned projection and public BDS surfaces; retain anonymous read access when configuration is incomplete. |
| Candidate interest and notices | **Strong within slice** | **Start bid** atomically creates or returns the Tender-bound candidate registration, mandatory-notice address and workspace. Tenders freezes notice audiences and delivery evidence. There is no passive Follow Tender or separate declaration-of-interest step. | Implement the atomic owner contracts, outbox and truthful retry/delivery states. |
| Structured electronic bid preparation | **Strong but gated** | STD-driven fields, evidence, declarations, pricing, security, addendum acknowledgement, saving/resuming, validation and signing are defined for the supported Tender release. | Rebuild, validate, manifest and approve the exact template release; resolve external trust and custody gates before production use. |
| Submission, replacement, withdrawal and receipt | **Strong but gated** | Atomic submission, trusted receipt, replacement lineage, withdrawal, automatic close and sealed custody handoff are specified. | Approve the production signature, trusted-time, encryption, custody, incident and recovery operating profile. |
| Bid Opening | **Handoff only** | Bid Submission deliberately provides sealed envelopes and custody evidence but no open/decrypt command or ceremony. | Produce a dedicated Bid Opening requirements document before implementing opening or post-close disclosure. |
| Evaluation and Award | **Foundation only** | Published response rows carry downstream evaluation/contract mappings. No evaluation workflow, committee decisions, professional opinion, AO award, notification, standstill or debrief process is defined. | Produce Evaluation and Award requirements after Bid Opening, preserving published criteria and preventing post-publication criterion invention. |
| RFQ, Restricted, Direct Procurement | **Not yet covered** | The present release supports Open Tender only. | Define method-specific candidate selection, invitations, approvals and publication rules after the Open Tender slice is stable. |
| RFP | **Not yet covered** | No weighted technical/financial proposal workflow is supported by the current Goods profile. | Create a separately curated RFP product and template release; do not retrofit weighted scoring into the Goods pass/fail release. |
| Works and other Services | **Not yet covered** | The current template and Bid renderer support straightforward IT Goods only. | Curate separate product profiles, response controls, BOQ/schedule treatment, evaluation mappings and artboards. |
| Contract Management | **Programme-deferred** | Phase 2 has not yet been converted into controlled module requirements. | Start only after Award ownership and the awarded-contract handoff are stable. |
| IFMIS, Inventory, Stores and Assets | **Programme-deferred** | Phase 3 is not yet specified. Budget and Requisition currently use explicit owner boundaries rather than pretend integrations. | Preserve those boundaries and define integration contracts when the external owners and interfaces are known. |

## 4. Public and vendor-facing findings

### 4.1 Resolved: supplier clarifications

TPR v0.10 now owns one governed pre-bid clarification facility. An authenticated Active Tender-bound candidate may ask before the deadline without an addendum already existing. The source identity is protected; a non-changing answer may be direct or anonymised/general; an answer that changes published content remains blocked until its linked addendum is Issued and effective. BDS v0.7 creates no parallel response store.

### 4.2 Resolved: candidate registry and notification ownership

BDS v0.7 owns Tender-bound registration and the verified mandatory-notice address. **Start bid** creates or returns both atomically with the workspace. TPR v0.10 owns audience freeze, mandatory notices, dispatch/retry evidence and delivery state. Failed delivery does not change Tender effectiveness or become false receipt. The MVP deliberately has no passive **Follow Tender** or separate declaration-of-interest workflow.

### 4.3 Production submission is specified, not yet operationally cleared

The requirements correctly refuse to assume that a State Portal, trust service, government identity service or tender-box integration exists. Production electronic submission therefore remains disabled until the Project Owner approves an exact operating profile covering:

- legally acceptable electronic signing and certificate validation;
- authoritative time and deadline enforcement;
- encryption and key/custody separation;
- sealed-storage administration and access logging;
- backup, recovery and incident handling;
- supplier receipt and non-repudiation evidence; and
- independent security and recovery verification.

This is an implementation-readiness gate, not a defect in the functional design.

### 4.4 Supplier registration must be narrowed before it is specified

The roadmap's supplier-registration list mixes several different purposes:

- portal identity and access;
- reusable organisation evidence;
- method-specific prequalification and approved lists;
- tender-specific eligibility and due diligence;
- contract performance monitoring; and
- external criminal, professional, tax, company and civil-status checks.

Combining these into one registration form would create an intrusive black box and poor user experience. It would also risk collecting sensitive data before there is a defined legal purpose.

The future Supplier Management document should separate these purposes, record source and freshness, support human review and correction, and prohibit automatic disqualification or contract termination merely because an external lookup is unavailable or returns an unresolved match.

### 4.5 Post-close disclosure belongs to Bid Opening

The roadmap proposes a post-close report containing received tenders, total tender sums and tender-security details, distributed to internal officers and all tenderers. Bid Submission correctly does not expose bid identities, prices or content at automatic close.

Any opening register or bidder-visible disclosure must be generated only by the governed Bid Opening process, after the lawful opening event, and must contain only facts that the applicable rule permits to be announced. The roadmap wording should not be implemented directly from the submission module.

## 5. Material roadmap variances requiring an owner decision

| Variance | Recommended resolution |
|---|---|
| Requisition roadmap includes a Stores stock check; current Requisition does not. | Treat Inventory as the future owner. For MVP, either record an explicit **Stock check unavailable/not applicable** outcome or defer the check by approved decision; do not create a fake stock balance. |
| Requisition roadmap routes through Finance, AO and HOPF; current model uses HoUD and HOPF with automated Budget controls. | Retain the simpler route only after legal/business confirmation that Finance and AO do not need separate Requisition decisions. Record the decision explicitly. |
| Roadmap expects system selection of suppliers. | Apply only to methods that lawfully use invited/approved lists. It does not belong in the public Open Tender path. |
| Roadmap implies automated supplier compliance and registry decisions. | Use evidence-assisted checks with source, freshness, match confidence, review and appeal/correction. Never make an opaque external result self-executing. |
| Roadmap expects all methods and product types in Phase 1. | Use controlled product/method releases. Prove Open Tender IT Goods first, then add RFQ/Restricted/Direct, RFP and Works/Services as separate supported profiles. |

## 6. Recommended requirements sequence

### Gate 1 — Reconcile the current public/vendor slice — requirements closed

1. **Closed in requirements:** TPR v0.10 and BDS v0.7 define general pre-bid clarifications consistently.
2. **Closed in requirements:** candidate registration, **Start bid**, mandatory notice ownership and delivery evidence are explicit.
3. **Closed in requirements:** CFG v0.16 owns public support and privacy/terms/accessibility links; TPR/BDS own communication evidence at their exact boundaries.
4. **Implementation gate:** reconcile, rebuild, validate and obtain exact-manifest approval for STD-TPL v0.9 release 1.1.
5. **Production gate:** approve and verify the signing, trusted-time, encryption, tender-box custody, backup/recovery and incident operating profile before enabling submission.

### Gate 2 — Complete the procurement decision chain

6. Produce **Bid Opening** requirements, including committee/authority, opening time, custody verification, late/withdrawn/superseded treatment, failure recovery, opening minutes/register and lawful disclosure.
7. Produce **Evaluation and Award** requirements, including published-criterion enforcement, evaluator conflicts, pass/fail and scoring models, clarifications, due diligence, professional opinion, AO decision, notifications, standstill, debrief, securities and award acceptance.

### Gate 3 — Expand supplier and procurement coverage

8. Produce **Supplier Management and Prequalification** as a separate module, with method-specific lists and data-minimisation controls.
9. Add method/product releases in controlled increments: RFQ/Restricted/Direct; RFP; Works; other Services.
10. Re-run an end-to-end cross-document contract review whenever a new method or product profile is admitted.

## 7. Review rule to prevent future document drift

Every new module or supported product/method should be admitted only with a cross-document interface matrix showing:

| Required interface fact | Question to close |
|---|---|
| Upstream owner | Which approved record and immutable Version authorises this work? |
| Downstream owner | What exact handoff is emitted, and what may the receiver do? |
| Actor and scope | Which live responsibility authorises each decision? |
| Public/vendor effect | What does an external user see, submit, receive or challenge? |
| Status and event semantics | Which action changes legal/business state, and which actions only save or display? |
| Evidence and audit | What proves the action, time, content, source and delivery? |
| Failure and recovery | What happens on retry, outage, stale Version, missing integration or partial delivery? |
| Design contract | Is every required actor/state represented by a complete, direct and usable artboard? |
| Acceptance and seed | Can the state be reproduced and tested without inventing facts? |

The programme should not call a module complete merely because its own document is internally consistent. Completion requires its interfaces with the immediately preceding and following modules to be closed.

## 8. Overall assessment

The programme has not drifted away from the client roadmap. It has converted the broad roadmap into a safer and more implementable architecture, while deliberately narrowing the first production slice.

The key risk is not lack of depth in the documents already produced. It is **mistaking one well-defined Open Tender/IT Goods vertical slice for complete Phase 1 coverage**. Gate 1 requirements are now reconciled; implementation must follow G1-REG-001 v1.0 and preserve the explicit stop at sealed Bid Submission. The programme remains on a sound course if the template and operating-profile gates are proved before production submission and the later modules are developed as separate controlled bodies of work.

## 9. v1.1 reconciliation record

| Change | Result |
|---|---|
| General clarification contradiction | Resolved by TPR v0.10 and BDS v0.7. |
| Candidate registration and notification ownership | Resolved with atomic Start bid, BDS-owned registration/contact and TPR-owned notices/evidence. |
| Public support/legal/accessibility ownership | Resolved by CFG v0.16 and the allowlisted consumer projection. |
| Template operational-record boundary | Resolved by STD-TPL v0.9; exact bundle rebuild/manifest approval remains implementation work. |
| Production submission | Functional contract complete; default-false deployment flag and external operating-profile evidence remain release gates. |
| Future programme work | Bid Opening, Evaluation/Award, Supplier Management, other methods/products and later phases remain explicitly planned, not silently absorbed into Gate 1. |
