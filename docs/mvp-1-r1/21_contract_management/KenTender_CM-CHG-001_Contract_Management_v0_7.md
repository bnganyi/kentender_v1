# CM-CHG-001 — Contract Management

| Control | Value |
|---|---|
| Document ID | CM-CHG-001 |
| Version | 0.7 |
| Date | 12 October 2026 |
| Change basis | Retains v0.6 corrections; 12 October usability revision consolidates task/state instructions, maps briefs to shared screens and defines purposeful actions and single-entry behaviour. |
| Status | Approved — requirements and artboard specification, Project Owner, 14 October 2026 |
| Supersedes | CM v0.6 as the working draft; earlier versions remain history. CTM v0.1 is a reviewed contribution, not a competing baseline. |
| Approval record | Project Owner, 14 October 2026: “Mark as approved” approves CM v0.7 requirements, artboard specification and CM-OD-02–09 product dispositions, retaining their stated source/policy conditions. Authorises design and incremental implementation; outstanding legal, template, shared-service, native Finance/stock and funding evidence remains required for affected acceptance/release. Historical approval, 8 October 2026: “Approved. Proceed” approves the coverage assessment and recommended direction, including deferring the proposed World Bank extension. The subsequent “Proceed” authorises this independent-review correction as v0.5; neither instruction certifies its new detailed rules, current law, integrations or production release. |
| Scope authority | CM v0.2 records the 1 October 2026 decisions. Supplied context: Basis v0.3 and ERPNext Fit and Gap v0.1. Basis v0.4 and Fit and Gap v0.2 were cited by CM v0.2 but were not supplied for this reconciliation; no claim that they were read. |
| Product | Open Tender; straightforward IT goods and minor related services; one lot; KES; fixed price |
| Finance | ERPNext Accounts is authoritative for the first MVP deployment |
| Governing standard | KT-STD-001 v1.25 — Approved, 6 October 2026; controlling table/approval record prevails over retained proposal history |
| Supplied current owner sources | AWD v0.5; BUD v1.12; TPR v0.17; BDS v0.11; PRC v0.11; STD-TPL v0.15; EVL v0.5; BOP v0.11; REQ v1.14; PLN v1.29; NDS v1.16; STR v1.9 |
| Shared-source reconciliation | AUTH v1.11 and CFG v0.18 supplied; relevant responsibility/scope and setup passages inspected. Permissions-review successor proposals AUTH v1.12, CFG v0.19, KT-STD v1.26 and owner successors inspected as proposals, not approved replacements. Current TRUST, LAW, SEED-OPS and registers still require verification. |
| Completion | All three stages and independent entry remain in scope. World Bank-specific functionality is deferred from MVP 1 (§5.16). §17 separates completed document work from owner amendments and outstanding verification. |

**KenTender prepares the agreement, checks delivery and inspection evidence against its terms, generates findings and payment checks, and tracks the contract to close-out. People establish physical facts, resolve exceptions and personally take responsibility for the decisions they are authorised to make. ERPNext holds the operational stock, asset and accounting records.**

**Current approval controls:** the 14 October 2026 approval supersedes retained historical “Proposed”, “for review” and pending-requirements-approval wording for CM v0.7 product requirements and artboard decisions. It does not approve externally maintained owner documents, certify legal applicability or installed behaviour, or close evidence/release gates.

## 1. Governing decisions and disposition

| Decision | Disposition |
|---|---|
| One Contract Management module | Preparation/signing, delivery/performance and payment/close-out share one case. No handoff after signing. |
| Full scope before detailed approval | All stages are covered; Stage 1 completion alone cannot complete these requirements. |
| Automation is the default | Generate checks and results; people do not re-enter calculations or individually confirm every successful automatic check. |
| ERPNext reuse | Reuse native operational records and extend documented gaps. No second stock, asset or payable ledger. |
| User experience | KenTender owns routine entry, display, review and approval. ERPNext owns operational records and native transaction behaviour. Routine work never requires opening standard Frappe forms. |
| First Finance deployment | ERPNext Accounts, agreed 1 October 2026. External Finance/IFMIS is future integration work. |
| Independent use | Contract Management works without KenTender’s tendering apps. Existing signed contracts enter through checked registration; no eGP API or IFMIS connector is assumed. |
| Close-out | Contract close-out belongs here. A project may span several contracts; closing a contract does not close the project. |
| Earlier “Contracting” destination | Contract Management — Prepare and sign. Approved Award v0.5 still uses “Contracting”; §17.4 specifies the narrow naming/interface amendment without changing the approved transport. |
| Profiles | Versioned rules with explicit source, applicability and verification; no runtime rule editor. The World Bank extension is deferred from MVP 1; no donor-specific route is enabled. |

### 1.1 Reconciliation disposition

| CTM contribution | Current disposition |
|---|---|
| Profile identity/version, legal basis and verification | Incorporated in §§4.1/5.16; evidence owner enables only reviewed rules. |
| Compliance triggers, evidence and reports | Incorporated in §§4.1/5.15; original triggers survive receipt delays and corrections. |
| Handoffs and segregation scenarios | Expanded in §§5.10/6/14; existing people/capacities are reused. |
| World Bank obligations | Deferred from MVP 1 by the approved coverage direction; §5.16 retains only the boundary and historical source references. |
| eGP provenance | A source option under existing signed-contract registration, not a separate unsigned-award intake. |
| Manual pass/fail, full-payment-only, automatic close-out | Not adopted. CM retains observations and automated findings, native partial settlement, and AO close-out. |
| Advances excluded; inventory/assets deferred | Not adopted. Lawful issued advances and ERPNext Stock/Assets remain covered. |
| Automatic release of every reservation remainder | Not adopted. §5.14 uses exact owner-authorised amounts and preserves shared reservations. |
| Quashed-Regulations defaults, unverified test variation limits, universal warranty/security dates | Not imported as operative rules. Source applicability, legal limits and actual terms must be established. |

This document contains the requirements, screen briefs, interaction mapping, fixtures, verification scenarios and counterpart amendment instructions. There is no separately versioned design or reconciliation specification.

## 2. Purpose, outcomes and exclusions

Ordinary workflow: **prepare and sign → receive and inspect → accept and follow up → certify invoices and track payment → complete obligations and close**. Partial delivery, invoices, payment and warranty work can overlap; the interface must not force them through a single serial status.

Outcomes are a signed agreement, attributable inspection and acceptance evidence, correct linked ERPNext transactions, visible unresolved obligations, factual performance reporting and an accountable close-out record.

### 2.1 Persona journey

Follow Julia Njeri, contract coordinator, through the ten-laptop demonstration. Names describe separately assigned fixture duties, not authority derived from employment.

| Moment | Person does | KenTender does |
|---|---|---|
| Prepare | Brian reviews the generated agreement; Charles resolves required terms/security evidence. | Reuses the award and issued terms; identifies missing facts. |
| Sign | Mary signs for the supplier; Amina signs for the entity on the same agreement version. | Retains both proofs, applies the agreement’s effectiveness conditions and creates the order update. |
| Receive | Grace records what physically arrived. | Creates custody and inspection work; does not accept or value the goods. |
| Inspect/accept | Peter records observations; Julia prepares the report; Julia, Peter and Brian each sign in their appointed capacities. | Calculates findings, accepted/rejected/deferred quantities and eligible native receipt work. |
| Resolve exceptions | Julia communicates the two failed units; David supplies replacements. | Links the replacement to the original entitlement and repeats the required inspection/acceptance checks. |
| Invoice | David submits his claim; Charles reviews differences and signs supported certification. | Compares the claim with acceptance and generates the linked Finance draft. |
| Finance | Josphat completes missing accounting choices; Beatrice reviews the native records and records independently supported settlement under the proposed Finance policy. | Reuses native calculations/posting; distinguishes posting from confirmed cash. |
| Finish | Julia follows remaining obligations; Amina signs final acceptance; Charles issues the completion certificate; Amina signs close-out. | Generates the fulfilment/reconciliation review and keeps unresolved work visible. |

Existing signed contracts enter through one registration form and source/opening-position review; no re-award or re-signing. Changes, warranty claims and termination are work within the same contract, not additional modules or stages.

Excluded: new procurement methods, works/complex service administration, negotiation, replacement-supplier selection, arbitrary variation, weighted supplier scoring, automatic debarment, AI acceptance/rejection, bank transfer execution and a new inventory/accounting system. Capture and route unsupported cases without pretending they are complete.

## 3. Ownership and dependencies

| Owner | Authority / record | Boundary |
|---|---|---|
| Award | Versioned award package, decision events and current restrictions | Contract Management cannot change an award, supplier or submitted tender sum. |
| Released template | Issued terms, supplier commitments and requirement identities | Item master changes cannot alter contractual criteria. Eligibility-only declarations are not delivery obligations. |
| Contract Management | Agreement versions, acceptance decisions, issues, contract changes, certification and close-out | Links to native transactions rather than copying their balances into a separate ledger. |
| ERPNext Buying / Stock | Generated Purchase Order; Purchase Receipt, returns and stock movements | Operational order is generated from the agreement, not a second award approval. |
| ERPNext Assets | Equipment identity, location, custody and accounting lifecycle | Finance-approved item classification controls stock versus fixed-asset treatment. |
| ERPNext Accounts / Finance | Purchase Invoice, credit/debit adjustments, Payment Entry and reconciliation | CM certification establishes contractual support, not bank settlement. |
| Shared authority / Trust / tasks | Current responsibility, personal signatures, evidence and work items | No parallel signing or identity mechanism; technical support gains no business powers. |
| Legal-rule owner / HOP | Verified applicable rules; publication and legal referrals | Source review alone does not prove current-law clearance. |

Changes affecting a supplier require a retained notice and delivery evidence. CM supplies its own authorised supplier-facing projection; optional BDS navigation links to it and cannot allow bid mutation. Optional Proceedings retains report references without owning contract decisions. These extensions are proposed interfaces in §17.

### 3.1 Independent Contract Management capability

Contract Management must install and operate without Strategy, Needs, Planning, Requisitions, Tenders, Bid Submission, Opening, Evaluation or Award. It reuses the existing core authority/evidence/task services, site configuration, shared signing capability and ERPNext Buying/Stock/Assets/Accounts. Do not rebuild those shared functions or assume that “standalone” means no ERPNext dependency. The concrete Frappe app name is an implementation decision; no mass app split is authorised by this document.

Dependencies point from an optional Award adapter to CM’s intake service. CM does not import tendering controllers, query tendering tables or require their DocTypes to exist. Source references use an external identity plus immutable evidence, with an optional live link if the originating app exists. Core cannot acquire a reverse dependency on CM or on tendering. Disabling an optional adapter leaves existing contracts readable and operable within their evidence/authority limits.

Two intake routes are in MVP:

- **KenTender award:** existing automatic versioned handoff, followed by preparation and signing.
- **Existing signed contract:** authorised officer registers exact executed contract and amendments, parties, source reference, operative dates, structured items/prices/terms and opening position. HOP confirms source and terms; Finance confirms opening accounting/stock links only when there is prior activity. This checks imported facts, not re-award or re-signing. A contract with no prior activity uses zero opening balances with supporting confirmation, not invented historical transactions.

External unsigned awards are not a third MVP route. Do not fabricate tender, bid, evaluation or Award cases for an imported contract. The existing-contract route accepts only the agreed simple IT-goods scope and a reviewed applicable rule profile; other products/regimes are recorded as unsupported, not silently reclassified as Kenyan public procurement.

KenTender owns its ongoing contract administration records. An external signed agreement stays authoritative for its terms; imported evidence is marked **Recorded from external source**, not **Verified by eGP**. Record the official system responsible for each external action and whether KenTender is authorised to perform it. Where another channel must hold the official decision, retain its actual result and reference. No optional-channel setting waives a legal requirement. No live eGP/IFMIS interface, public-sector adoption permission or NGO rule profile is claimed.

The CM supplier workspace uses shared supplier identity and scoped authorisation directly. It is usable without installing bidding features. Where BDS is installed, its navigation links to the same CM-owned view. One site remains one entity, without a client/PE selector or cross-client advisory dashboard.

## 4. Canonical domain model

All identifiers are generated. Existing names below describe business records, not a requirement to create a separate DocType for every row. Reuse native fields where they already own the fact. Every material write carries record/version, actor/service identity, recorded time and source command identity. Terms carry both their actual legal effective date and the time recorded; registering an old agreement does not make its terms effective on registration day.

| Record / minimum content | Validation and consumer |
|---|---|
| Contract case: source kind/reference/version, optional tender/lot and Award links, supplier, agreement versions, lifecycle and owner | One case per source contract identity; KenTender tender/lot links are optional for external contracts. Successor Award cycles attach without silently replacing a signed agreement. Drives list, authority and source history. |
| Agreement version: source digests, rendered agreement, mapped items/amount/terms, missing particulars, signatures/proofs, operative date | Exact terms derive from issued sources. Only released missing-particular fields are editable. Signing and subsequent obligations use the exact version. |
| Obligation: source clause/requirement, type, item/quantity or event, due rule/date, owner, fulfilment/disposition evidence | Generated where structured terms permit; unknown rules create an issue. Drives delivery, security, warranty, reporting and close-out. |
| Arrival event: agreement, supplier delivery reference, received/recorded time, destination, item quantities and serial references, receiver/evidence | Positive quantities; immutable after recording, linked corrections. Actual observation only; no stock or acceptance side effect. Generates custody and inspection work; no native receipt draft until effective acceptance. |
| Inspection: receipt/item/unit coverage, frozen criterion, observation/value/unit, observer/time, evidence, calculated finding/reason | Reuse Quality Inspection readings and controlled extensions. Missing observation gives Needs review. Consumer: acceptance version and report. |
| Acceptance version: exact inspections, accepted/rejected/deferred quantities, reasons, signer set, dissent and proof | Per-item quantities reconcile to inspected arrival coverage; no double acceptance. A signed version is immutable. Generates eligible posting request. |
| Issue: type, affected obligations/actions, facts/evidence, owner, response deadline if applicable, state, resolution | Each hold has explicit scope. Disposition must use authorised facts; no generic override. Drives next action and correspondence. |
| Change / termination record: request, contractual/legal basis, affected terms, financial/time impact, reviews, AO decision, signed amendment or effective notice | Effective changes create successors and preserve earlier calculations. Mere request/approval without required effectiveness evidence changes no operative term. |
| Supplier invoice submission: supplier reference/date, claim lines, attachment if supplied, original receipt time, linked native invoice | Structured claim captured once; correction is a linked version. Receipt time persists through disputes. Used for duplicate checks and certification. |
| Certification: exact claim, eligible quantities/milestones, contractual adjustments and reasons, certifier/proof, native invoice link | Frozen comparison; no unsupported claim proceeds to the payment route. Recheck revisions before use. |
| Transaction link: source operation identity, native document/row/version, status, attempts/error | Unique linkage prevents duplicate posting. Native records remain authoritative; failures do not erase acceptance. |
| Publication/reporting obligation: triggering event/time, rule/version, due date, recipient/channel, owner, evidence | Separate from contract stage. Completion requires required publication/reporting evidence, not event receipt. |
| Close-out version: fulfilment review, final acceptance/certificate, reconciled balance, security and surviving-obligation dispositions, AO proof | §5.9 defines the completion review. Unresolved completion conditions prevent closure; surviving obligations remain visible. |

Amount comparisons use the issued currency/precision and native tax treatment. Contract total, invoiced amount, paid cash, credits and balance are distinct. Never derive “cash paid” merely as total minus outstanding balance.

### 4.1 Profiles, compliance records and source boundaries

| Record / attributes | Purpose and invariant |
|---|---|
| Rule profile version: identity, instrument/edition, legal-basis evidence, applicable product, rule entries, approval evidence, status Draft/Verified/Suspended | Code-owned. Each entry identifies its source kind (law/donor instrument, issued term or product control), exact locator, verified parameters, affected actions and calendar. Profiles and results already used are immutable; correction creates a successor. |
| Contract profile binding: exact profile/version, applicability evidence, source regime and any donor overlay | Inherited from the reviewed source or established at intake. No arbitrary officer toggle between PPADA and donor rules. Funding source alone does not prove that national law is displaced. A later lawful regime/review change creates an attributed successor binding and affected-obligation review, never silent history rewriting. |
| Compliance obligation: stable identity, rule/version, original trigger identity/time, subject, responsible person/capacity, recipient/channel, due rule/time, evidence, disposition | Open, Satisfied, Not applicable with reviewed reason, or Superseded with successor. Overdue is computed only from a verified due rule. Missing applicability/deadline gives Needs review, never a fabricated deadline or automatic satisfaction. |
| Period report version: type, period boundaries/timezone, exact source versions/cutoff, rows, recipient, prepared time, submission/delivery evidence | Derived once per type/period/cutoff. Regeneration creates a successor. Submitted versions are immutable. Failed source reads mean Incomplete, not “No records”. |
| Security record: type, issuer, beneficiary, reference, amount/currency, issue/expiry dates, guarantee conditions, authenticity evidence, custodian and actions | Distinguish received, verified, rejected, replaced, claim pending and actual release. Guarantee type follows issued terms; no bank-only default is imposed. Replacements retain old instruments and applicability dates. |
| Committee appointment: contract/decision scope, current members/capacities, appointing authority/generated reference and written record, effective period, personal declarations and replacements | No business power merely from appearing in a fixture or having an Evaluation appointment. A conflicted/expired member cannot act. Signatures bind the actual authorised set/version. |
| Funding link: source reservation/drawdown allocations, committed amounts, exact owner event, operation identity, owner receipt and outstanding incident | Budget owns funding balances; ERPNext owns accounting/stock balances. A Contract funding link is provenance and a read projection, not a second ledger. |

**Production profile guard.** Draft or Suspended rules prevent the consequential actions they govern. Reads, saved preparation, factual arrival, restriction evidence, incident recording and protective correction remain possible within authority. No fallback removes a legal limit. Test scenarios use labelled synthetic, fully specified rules; test mode does not skip variation ceilings or admit unknown deadlines. Verification is recorded through the shared legal/configuration owner, not by a business form that edits executable parameters. Whole-profile deployment requires every applicable entry to be resolved, not merely one cited instrument.

**Operational ownership.** Supplier submissions and contractual certifications are evidence/entitlement records linked to Purchase Invoice; payment results are projections of native entries and independently supported settlement. Neither becomes an independently editable payable or payment balance.

## 5. Lifecycle and business rules

### 5.1 States and orthogonal progress

Case lifecycle: **Preparing → Awaiting signatures → Active → Closed**. **Did not proceed** is a reasoned terminal outcome before contract formation; **Terminated** records an effective termination and still shows unsettled obligations. A hold is a scoped restriction, not an extra lifecycle or permission to erase prior progress.

Show separate delivery, invoice/payment and remaining-obligation summaries. Do not mark all stages Done when work ends early. A historical contract stays available after closure, with active surviving-obligation links where the verified closure treatment permits them.

### 5.2 Receive Award and publication events

`ReceiveAwardPackage` validates the exact AWD v0.5 §5.8 package, records durable receipt and creates one **Prepare contract** task for HOP. Preparation can be performed by the authorised procurement officer; no manual “accept handoff”. An unavailable receiver does not acknowledge success. Retry returns the existing case/task.

`ReceiveAwardPublicationEvent` independently accepts `AwardDecisionRecorded v1`. Apply the verified trigger rules immediately, including events arriving before the package. No-award events do not invent contract-publication obligations. Corrections preserve prior event versions and publication evidence. Unknown applicability creates HOP **Resolve publication requirement**, retaining the original event time. Late receipt cannot move a deadline.

Source updates apply in source-version order; retain older events as history. Before each signature, operative amendment or other affected positive action, recheck authoritative restrictions. An order received after signing does not erase the agreement; it creates a scoped legal issue and prevents affected actions. Physical arrival, incident evidence and necessary protective records remain recordable.

### 5.3 Prepare, verify and sign

Generate the agreement from the issued form and mapped award terms. Brian’s procurement responsibility does not automatically confer contract authority; the effective responsibility binding must include this work. HOP owns unresolved preparation items and verifies required security using recorded evidence. Preserve issuer/amount/expiry/beneficiary and the basis of authenticity verification; a file upload is not verification.

**Send for signature** freezes a complete version after source, authority, legal-review, security and current signing-window checks. Proposed MVP sequence: supplier authorised signatory signs first; entity authorised signatory signs second. Both see the same whole version. The second signature is not a fresh award decision. Contract effectiveness follows its terms and verified rule, not an invented date default. Where signing outside KenTender is permitted, the authorised procurement officer records the complete executed version, party, named signatory/capacity, actual signature date, recorded time and evidence; HOP confirms source and authority. Missing electronic signing does not automatically permit outside signing. Both parties must be evidenced on the same whole version; mixed partial copies require reconciliation before any claimed formation.

Failed or uncertain signing retains the same attempt for recovery. A changed version ends outstanding requests and requires new signatures. Recheck restrictions and authority at each commit; expiry during signing prevents unsupported completion. A refusal or expired window creates HOP follow-up, not automatic supplier substitution or forfeiture. AO records any changed procurement outcome through Award’s route.

Once both required proofs and effectiveness conditions are established, set Active and automatically generate/link the operational Purchase Order. Failed order creation leaves **Contract signed — order update pending** with a technical task; it does not request fresh signatures or invent a second contract. Budget conversion follows §5.14 independently of native Purchase Order posting; real signatures and legal effectiveness are retained even when a financial exchange fails. No downstream posting may use a missing or stale order.

### 5.4 Arrival and custody

Record physical arrival once, including supplier note, observed items/serials, place, observation time and receiver. Unexpected, excess or premature goods remain recordable as exceptions, without acceptance or permission to use them. Missing serials remain unresolved; no fabricated serial is generated to pass receipt validation.

First-deployment design: unaccepted supplier-owned goods remain in a non-valued custody record within the contract, physically segregated. The record shows quantities in custody, returned and transferred to accepted receipt, with evidence for every movement. It is not an inventory valuation or stock ledger. No Purchase Receipt is submitted for these units merely to record arrival. Returns before acceptance close the custody quantity with the supplier’s collection evidence. Only an effective acceptance decision creates a native receipt draft for its accepted subset, through the durable posting intent. Arrival creates custody and inspection work only; it creates no native receipt draft. Rejected/uninspected units are never placed in a passing receipt.

This route applies only where the contract and Finance policy establish that ownership/accounting recognition follows acceptance. A contract transferring ownership earlier needs an evidenced accounting treatment before onboarding or posting; CM-PROOF-01 must resolve this on the installed site. Do not silently delay recognition or change ownership terms to fit the software.

Multiple deliveries and destinations follow the contract. Duplicate prevention uses supplier, source operation and item/unit coverage; an ambiguous repeated delivery note creates a review issue. Replacement units link the rejected/returned units and consume the original unfulfilled entitlement, not a new order quantity or price. A replacement after a previously accepted receipt requires the linked native return/credit treatment before re-receipt, with no double valuation.

### 5.5 Inspection and automated findings

Generate observations from exact contract criteria, not an editable current Item template. Supported rules are explicit typed comparisons, ranges and required-evidence checks. Units and coverage are preserved. No local formula editor, new criterion or unpublished sampling rule is permitted.

An appointed inspector records measurements and evidence against specified items/units. KenTender returns **Meets**, **Does not meet** or **Needs review**, with requirement, observation, evidence and reason. A blank required reading, unreadable evidence or unavailable verification source is Needs review. A clear failed measurement stays visible; correction preserves the original and the reason.

Observation scope must show whether it covers every unit or an authorised sample. Do not infer that one inspected serial represents an entire delivery. The allowed sampling/coverage treatment must come from approved requirements and the applicable inspection plan; otherwise the system requests the missing coverage. Authenticity and actual physical conformity remain matters for responsible people.

### 5.6 Acceptance and stock/asset posting

For the first product, use a written AO appointment under Act §48: chair and at least two other members, with named contract scope, effective dates and relevant competence. The product chooses this committee route for routine IT goods; it does not claim §48 mandates a committee for every purchase. The fixture appoints Julia Njeri (user department, chair), Peter Mugo (technical member) and Brian Wafula (procurement member). Written authority also identifies the AO’s representative for acceptance under §146 (revised-2022 primary body visually checked on 9 October 2026, printed/PDF p. 70; current applicability remains CM-LEGAL-01). Native appointments and replacements generate their reference and exact written appointment record; no mandatory manually typed appointment reference or uploaded letter is required. Preserve previous records as history. A later replacement applies prospectively; an absent member is not silently counted as having signed. HOP recommends the appointment; AO appoints or returns with reasons. Each member personally declares interest before acting. A declared conflict suspends that person’s affected authority and opens replacement work; unaffected observations remain evidence. Reconstitution while a report awaits signatures produces a reviewed successor report/signature set; no earlier signature is misattributed to a new member.

Technical confirmation under §150(3) is issued by the responsible technical department/professional when it supplied the technical specifications. HOP cannot replace that technical certificate. Generate the technical certificate from Peter’s recorded observations; his personal signature binds it. Committee acceptance uses that certificate, rather than asking Peter to repeat the checks. HOP’s invoice/voucher certification and the non-complex close-out certificate are separately identified outputs, each with its own purpose and exact subject.

The all-appointed-members report-signature rule is an explicit MVP accountability control. It is not borrowed from Evaluation §80 or asserted as identical statutory wording for inspection. A member can sign with recorded dissent or request correction. An unresolved dissent affecting conformity creates Needs review for those units; it cannot be outvoted by an undisclosed automatic rule.

The chair reviews the consolidated findings, resolves quantities and prepares one report. Members review it and personally sign that exact version, including recorded dissent where appropriate. They do not re-enter or approve each automatic check. A required unresolved observation prevents a supported acceptance conclusion for those units, while completed independent units may proceed. Supplier challenge is retained; supplier agreement is not an additional acceptance gate.

For each arrival item, accepted + rejected + deferred quantities equal the quantities covered by that report. Prior effective decisions are excluded from new coverage. Report completion atomically records the authoritative decision and one posting intent for accepted quantities. Signing does not falsely mark a failed native posting as complete.

The worker rechecks source versions, restrictions and quantity eligibility, then posts the linked native receipt/asset operation once. A retry retrieves the same document. Returned/rejected units use their own custody/return route; the system must not disable rejection controls globally to process a return. Initial contractual acceptance, provisional acceptance and final acceptance are distinct where the issued terms require them. Do not postpone every ordinary receipt/payment until the end of a warranty.

### 5.7 Performance, changes and termination

Automatically calculate remaining quantities, delivery delay, overdue corrective actions and proposed contractual deductions from operative terms. Show input dates and basis. Disputed causation, force majeure, waiver, extension entitlement and remedy selection require recorded judgment. No automatic accusation of fraud or debarment.

Supplier or contract owner can **Report issue** or **Request change**. HOP assembles grounds, impact, technical review and required legal/funding evidence for AO’s decision. An extension or variation changes the contract only after all applicable approval, signature and effective-date conditions are met. A fixed-price contract does not permit a discretionary price editor. Unsupported or unlawful requests receive a reasoned refusal or a named legal referral, with the relevant hold retained.

Termination requires the applicable advice, authority, notices and effective evidence. Preserve quantities already accepted, valid liabilities, recoverable advances and disputed balances. **Terminated** is not **Completed** or **Settled**. Complete the required termination reporting independently. A legally automatic consequence must be represented by its verified rule and evidence; no generic timer invents that consequence. The finite rule treatment in §5.11 governs supported changes; a conflict with the issued terms stays visible for Legal disposition.

Generate monthly contract-progress information from recorded facts for HOP review and submission under §5.15. Do not create a separate manual progress spreadsheet.

### 5.8 Invoices, certification and payment

Supplier submits an invoice against the contract once. Generate/link a draft ERPNext Purchase Invoice, preserving original submission and receipt time. A disputed claim remains recorded without becoming certified or paid. Corrections create a linked successor or native adjustment; do not reset the original receipt history to hide delay.

Automatically compare prices, tax treatment, accepted eligible quantities/milestones, previous claims, returns, credits and remaining contractual amount. Record the outcome and reason per discrepancy. Two concurrent submissions cannot reserve the same claim entitlement. An apparent duplicate is held for Finance review, not silently deleted. Invoice capture is not blocked merely because inspection is incomplete.

The required technical confirmation and authorised procurement certification use the same acceptance evidence. HOP’s **Sign certification** freezes the contractual support; it is not permission to re-evaluate every successful check. Technical certification follows §150(3); HOP certifies the invoice/voucher as the proposed procurement control. Finance verifies the institution’s payment authority before posting. This does not substitute for acceptance by the AO or an officer authorised in writing under §146 (revised-2022 primary body visually checked, printed/PDF p. 70; current applicability remains CM-LEGAL-01). Finance retains its own accounting approval and payment authority.

Finance maker prepares the native invoice/payment records through KenTender Finance screens. A separately authorised Finance approver posts/approves the consequential accounting/payment action under the verified native workflow. The same person cannot prepare and approve the same payment. This is the proposed first-deployment control, not a new procurement committee or an extra CM approval. The Finance workflow in §5.12 specifies the required separation; CM-PROOF-02 verifies its enforcement on the installed site.

Do not assume that liability recognition always waits for procurement certification: Finance must record a lawful liability when its accounting policy requires it, with the appropriate payment hold. Unsupported payment remains prevented. The ordinary accepted-goods fixture posts the invoice after certification.

Support more than one native payment allocation against a certified invoice. Every instalment consumes only its allocated supported amount; validate the outstanding entitlement atomically and prevent concurrent overpayment. Retain withheld/deducted/recovered amounts as their own facts. A partially settled invoice is Partly paid; a reversed or disputed settlement reopens follow-up without rewriting the original certification.

Use native Payment Entry and reconciliation. **Payment recorded** identifies the posted entry; **Payment confirmed** requires attributable Finance settlement evidence. A queued payment or zero balance is not proof of cash settlement. Credits, write-offs and deductions remain separately explained. Returns after invoicing/payment require linked native corrections and recovery, never edits to a historical acceptance record.

Advances are supported only where lawfully provided by the issued terms and verified profile, with required guarantee, approval and recovery schedule. No accepted-delivery condition is falsely applied to an authorised advance. Conversely, an “advance” label cannot bypass an unsupported invoice hold. §5.11 defines the advance branch; an absent or conflicting issued advance term is a source issue, not an officer-selectable option.

### 5.9 Warranty, security and close-out

Generate warranty and security obligations from the signed terms and their actual triggers, separately for affected items or deliveries. A claim identifies equipment, fault, notice date, evidence and remedy deadline. Supplier response, repaired/replaced units and verification link to that claim. Expiry never dismisses a claim made in time or proves that a security was released.

Distinguish (1) receipt and initial acceptance supporting stock/payment, (2) final acceptance where the contract requires it, and (3) contract completion and AO close-out. No universal warranty-end or sixty-day rule is introduced. The prior Regulations-only final-acceptance timetable is suspended as a design assumption pending CM-LEGAL-01. A lawful, independently supported contract term may still supply its own timetable after review.

For non-complex goods, HOP issues the §154 delivery-and-acceptance certificate to the contractor. AO records close-out once contractual completion is established. The generated review contains: deliveries and services accepted; required final acceptance; title/document handover; invoice/payment reconciliation; advances and recoveries; claims/disputes; security status; reporting evidence; and the disposition of every remaining obligation.

A remaining item either prevents completion under its governing term or survives completion with a named owner, due event and follow-up. The selected contract profile must say which and cite the source. The application cannot infer that every unpaid amount or future warranty prevents statutory completion, nor hide an unpaid amount by closing the case. Unresolved defects required for completion block close-out. A valid surviving warranty or payment follow-up remains in My Work after closure. An unclassified remaining obligation produces Needs review and prevents a supported closure conclusion.

Act §145 ties performance-security return to final acceptance and specifies thirty days. Record final acceptance by the AO, security-return due date, authorisation, actual return/discharge and evidence separately. HOP holds performance-security records; Finance holds advance-security and recovery records as the first-deployment custody arrangement. A claimed or disputed guarantee is not marked released by expiry. Conflicts between the Act, guarantee and issued terms are referred before a release or claim instruction.

Closed records are immutable history. A later surviving claim uses the same contract and its own open obligation; it need not reopen completed procurement. Evidence of erroneous closure triggers AO’s reasoned correction/reopening with the original closure retained. Termination settlement uses the same reconciliation but retains the Terminated outcome, including a separate settlement-completed date; it never becomes successful completion.

### 5.10 Next steps and handoffs

Use KT-STD §3B’s server-produced `next_step` and handoff contract. Every row below creates one linked My Work item for each required current holder; a notification links to that item, not a second approval. Notices to suppliers contain only their permitted projection. Failed dispatch retains the same identity and a delivery incident. “Waiting” names the holder and time the task passed to them; a scheduled event names its actual verified date/time.

| Event | Next holder / work item | Sender’s waiting-on item | Notification | Clears when |
|---|---|---|---|---|
| Eligible Award package durably received | HOP / Prepare contract; authorised Brian may prepare | Award retains recipient receipt | HOP | Complete request for signatures or reasoned Did not proceed |
| Required security received | HOP / Verify performance security | Supplier / Waiting for security verification | HOP | Verified or rejected with reason; rejection creates supplier replacement work |
| Signature request frozen | Mary / Sign contract | HOP / Waiting for supplier signature | Supplier signatory | Exact-version supplier proof; uncertain outcome stays pending |
| Supplier signature complete | Amina / Sign contract | HOP and supplier / Waiting for entity signature | Entity signatory | Required proof/effectiveness; unresolved signing incident retains evidence |
| Effective agreement requires Budget/order update | Authenticated worker; failure Daniel / Restore contract operation | HOP / Waiting for funding/order update | HOP on business failure; Daniel on service failure | Reconciled original operation, no fresh signature |
| Appointment recommendation | Amina / Appoint inspectors | HOP / Waiting for appointment | AO | Appointment or reasoned return to HOP |
| Appointment effective | Each member / Declare interest | HOP / Waiting for declarations | Each member | Personal declaration; conflict creates AO replacement task |
| Arrival recorded | Appointed Peter / Inspect delivery | Julia / Waiting for inspection | Inspector | Observations recorded; unresolved units retain issues |
| Technical certificate ready | Peter / Sign technical certificate | Chair / Waiting for technical confirmation | Technical certifier | Exact proof; no repeated measurements |
| Findings ready | Julia / Prepare acceptance report | Receiver / Waiting for acceptance | Chair | Frozen report with correct quantities and signer set |
| Report frozen / each required proof outstanding | Current required members / Sign acceptance report | Julia / Waiting for report signatures | Unsigned members | Required proof set; correction creates successor and chair work |
| Accepted posting intent fails | Daniel / Restore stock or asset update | Julia and Finance / Waiting for posting | Daniel | One reconciled native result; signed acceptance remains retained |
| Invoice discrepancies / supplier correction required | HOP / Review invoice, then David / Correct invoice | Supplier / Waiting for certification, or HOP / Waiting for correction | Current holder | Supported successor claim or reasoned disposition; original receipt retained |
| Certification ready | Charles / Sign certification | David / Waiting for certification | HOP | Exact-version proof and Finance item |
| Supported native draft | Josphat / Prepare invoice/payment, then Beatrice / Approve native entry | Charles and supplier / Waiting for Finance | Current Finance holder | Native authorised posting; own-entry approval refused |
| Payment entry posted | Beatrice / Confirm payment | Supplier / Waiting for payment confirmation | Finance settlement holder | Supported settlement/rejection; partial balance remains assigned |
| Change requested / review complete | HOP / Arrange review; appointed reviewers / Review change; AO / Decide change | Julia / Waiting for review/decision | Current holder | Required recommendation and AO decision; rejected case has reasons |
| Approved change needs executed amendment | Mary then Amina / Sign amendment | Julia / Waiting for amendment | Current signatory | Required proof and actual effectiveness, followed by owner updates |
| Termination request ready | Amina / Decide termination; then HOP / Deliver notice | Julia / Waiting for decision/notice | Current holder | Effective notice; settlement continues under Terminated |
| Reporting/publication duty triggered | HOP / Submit report or record actual publication | None | Responsible holder | Required submission/delivery evidence, not viewing or event receipt |
| Warranty claim / overdue supplier remedy | Julia / Send defect notice; supplier / Reply or remedy | Julia / Waiting for supplier remedy | Permitted supplier holder | Verified remedy/disposition; expiry does not close claim |
| Required final acceptance / completion certificate ready | AO or authorised acceptance capacity / Record final acceptance; Charles / Issue completion certificate | Julia / Waiting for completion evidence | Current holder | Required exact-version evidence and delivery |
| Security return authorised / due | HOP / Record security return | Julia / Waiting for return | Custodian | Actual discharge/return evidence, not expiry |
| Completion review supported | Amina / Sign close-out | Julia / Waiting for close-out | AO | Signed closure or reasoned return; surviving items retain owners |
| Delay adjustment reviewed | AO or exact verified decision authority / Decide adjustment | HOP / Waiting for adjustment decision | Current decision holder | Supported disposition; dispute preserved; native mapping issue stays assigned if absent |
| Security claim prepared / approved | AO / Decide claim; then HOP custodian / Send claim; Finance / Record actual recovery | Coordinator / Waiting for decision or issuer outcome | Current holder | Exact claim decision/communication/actual outcome independently evidenced; not request alone |
| Warranty remedy verified | Technical verifier; automatic exact issue resolution when required native/report evidence complete | Coordinator / Waiting for missing reconciliation where applicable | Missing evidence/Finance holder | Verified remedy plus all required acknowledgements; no extra user approval |
| Close-out correction prepared | AO / Decide close-out correction | HOP / Waiting for correction decision | AO | Reasoned retain/reopen/return; old closure retained and only actual pending work recreated |
| Termination settlement reconciled | HOP / Prepare settlement; AO / Complete termination settlement | Coordinator / Waiting for completion | Current holder | Exact supported completion proof; Terminated retained; survivors and funding acknowledgement separate |
| Commitment closure acknowledgement absent | Budget owner/technical recovery / Reconcile funding finalisation | Coordinator / Waiting for funding finalisation | Named incident owner | Original owner result reconciled once; no new release or duplicate closure signature |
| External opening facts complete | Finance / Confirm opening position when prior activity; HOP / Start management | Preparer / Waiting for source/opening checks | Current holder | Exact confirmed intake activated, no historic reposting |
| Restriction / missing appointment / legal rule unresolved | HOP / Resolve issue; AO for reserved decision/appointment | Affected actor / Waiting for named fix | Named holder | Supported disposition lifts only affected hold |

Closed tasks retain outcome and attribution in history. Reassignments preserve prior holder/time; expired authority removes future command access. A terminated or closed contract can still carry explicitly surviving payment/warranty tasks; it is never made to look like successful completion merely because a task disappeared.

### 5.11 Contract rules and bounded exceptions

Rules are code-owned, versioned and tied to their source clause/instrument. A business officer records facts and requests a decision; they cannot author executable rules or turn off a statutory guard. Published/signed terms remain immutable. A later legal correction records the affected population and effective application, rather than rewriting historical findings.

| Subject | Explicit MVP treatment |
|---|---|
| Price / quantity / period changes | Preserve fixed pricing. For an applicable Act §139 profile, check written awarding-authority approval, timing, original quantities/value and cumulative changes. The reviewed 2022 text sets a twelve-month bar on upward price variation, a 15% goods-quantity ceiling and a 25% cumulative value increase ceiling; excess cannot be approved through this form. These are ceilings, not an entitlement to vary a fixed-price contract. Price adjustment needs a lawful issued basis and verified method; otherwise refuse or refer with a hold. |
| Extension | Retain supplier justification, technical assessment and evaluation-committee recommendation or the route prescribed by the signed agreement under §139(2A), followed by AO decision. Never assume the original Evaluation committee is still appointed. Record effective date and unchanged/changed financial effect explicitly. A changed amount also passes the price/quantity rules. |
| Funding | Any increased commitment requires confirmed funding and Budget’s owner adjustment for a linked contract (§5.14), plus the required native order/accounting update, before the changed obligation becomes spendable. The original contract remains operative while a request is pending. |
| Advance | Only if tender and signed agreement provide it; never before signature. In the revised-2022 Act body, §146 contains both the executed/delivered-and-accepted payment condition and the tender/contract-specified advance exception, including no advance before signature; §147 sets the advance cap/security, and §148 limits use to tender-related activities and addresses recovery through security for misuse. These bodies were visually checked on 9 October 2026, printed/PDF p. 70; current applicability remains CM-LEGAL-01. Exceptional advance at most 20% of tender price, secured for the advance amount. Verify issuer, instrument, beneficiary, amount, expiry and claim terms. Record contractual use and recoveries on subsequent invoices. Outstanding advance is visible on termination. |
| Damages and overdue interest | System proposes the exact calculation from the operative rule: rate source/date, eligible principal, period, exclusions and cap. §140 and the signed terms must be reconciled before any deduction. Record causation and disputes separately; a risk flag is not a debt. No automatic cancellation is derived from former regulation 133 alone. |
| Termination | HOP submits grounds, notice requirements, legal advice, accepted work, costs, advances and proposed settlement to AO. Issue the approved notice with delivery evidence; apply the effective consequence only at the correct time. Legal clearance is a proposed product safeguard, not a claim that the quashed Regulations currently prescribe a particular external adviser. |
| Publication and reporting | Act §§138, 139(5), 152 supply the award-reporting, quarterly-variation and monthly-progress obligations. Preserve independent award, signing and change events. Each deadline/channel cites an operative direction or term. Former regulation 131’s fourteen-day clocks and regulation 141’s quarterly termination report are not enabled solely on that invalidated source. Unconfirmed deadlines create an immediate HOP issue, not a false future due date. |

A refused or unsupported request retains its grounds, responsible reviewer and reason. A permissible request proceeds through technical/legal advice, the required recommendation, AO decision and executed amendment/notice. Only the effective successor changes calculations. The supplier receives the exact decision or notice; an unanswered message does not constitute consent.

### 5.12 Finance and posting controls

One certified entitlement is consumed once across invoices, advances, credits, returns and recoveries. Monetary calculations use decimal arithmetic and ERPNext’s configured currency/tax precision. For received-goods invoices, quantity eligibility comes from effective acceptance less prior allocations/returns; advances use the distinct advance entitlement. Lock/recheck allocations within the posting transaction, not only on opening a page.

Finance maker drafts Purchase Invoice or Payment Entry in the KenTender editor. The designated Finance approver reviews that same native record through KenTender and invokes its configured native approval/submission transition through a controlled server operation. This is one Finance workflow, not an additional CM approval. Native workflow state, permissions and validations remain binding. A maker cannot approve their own entry. Approval does not trigger a bank transfer from KenTender. CM supplies contractual support; Finance remains responsible for tax, beneficiary and bank controls. A changed beneficiary or amount invalidates pending payment approval. Supplier profile edits never silently change an approved payment destination.

Keep five facts distinct: invoice received, contractual certification, accounting liability posted, payment entry posted, settlement confirmed. If accounting requires recognition before certification, Finance may recognise the liability under the approved accounting policy but a server-enforced payment hold remains until support/authority is complete. No payment-capable path may bypass it, including direct Payment Entry, Journal Entry settlement, reconciliation/allocation, API/import or background task. Native rights alone are insufficient. CM-PROOF-02 must demonstrate this before package D acceptance and production enablement of payment-capable paths; an authorised feasibility spike may establish that evidence during design.

Settlement evidence identifies the native entry, amount, bank transaction/reference, effective settlement date and authorised Finance recorder. The settlement recorder must hold current Finance approval responsibility and native evidence-read rights; the payment maker and its procurement certifier are excluded. Under proposed CM-OD-08, the native approver may record settlement supported by independent bank/reconciliation evidence: this records an external fact and grants no bank execution authority. If the installed Finance policy requires a distinct reconciler, bind that capacity and revise the fixture before package acceptance. A clearance date typed without supporting evidence is insufficient. Match bank reconciliation where available; otherwise use attributable external settlement evidence. Credit notes, withholding, write-offs and advance offsets reduce balances but are separately labelled; only confirmed cash transfers appear as Cash paid.

For accepted stock, post one native Purchase Receipt and serial/batch linkage. For fixed assets, use native item classification, receipt and asset creation; no duplicate Stock Entry for the same asset. Quality Inspection may be split by unit/accepted subset so rejected units are never included in a passing receipt. Do not globally weaken Quality Inspection settings or permit billing rejected quantities. Native cancellation/amendment is used for corrections after posting; the contract decision history remains intact. A downstream cancellation creates an exception and recalculation before further certification/payment.

### 5.13 Register an existing contract

Workflow: **enter source and terms → reconcile prior activity → review differences → start management**. Save remains possible while incomplete; consequential actions remain unavailable with the exact missing facts and owner displayed.

Required intake facts: source system and contract reference; signed agreement and amendments; supplier identity; signature/effectiveness evidence; currency; original and current value; item/quantity/UOM/rate/tax treatment; delivery and acceptance requirements; payment terms; warranty/security conditions; active restrictions; contract owner; cutover instant. Each structured obligation cites its source clause/page. PDF-only upload is insufficient, and AI extraction cannot certify the mappings.

Opening position records accepted and returned quantities; goods still in custody; invoiced, credited and confirmed cash amounts; unpaid liabilities; advance/recovery balance; existing ERPNext receipt/asset/invoice/payment references; and unresolved claims. Finance reconciles monetary/native links, HOP the agreement/obligations. Preserve both effective date and date recorded. Unknown amounts remain unknown, not zero. Prevent opening plus new activity from exceeding contractual entitlement.

A stable unique key (site, origin system, external contract identity) prevents duplicate cases; changed files with the same key become reviewed successors. Reference collisions or a later KenTender handoff that represents the same contract create a reconciliation issue, not a second live case. Once reconciled, history links the origins under one case.

Historical records never call normal receipt/invoice/payment posting commands. Link existing ERPNext balances first; any required opening accounting migration is a separate Finance-controlled, reconciled operation, not an automatic import side effect. After HOP confirms the source and Finance confirms nonzero prior activity, **Start management** makes the existing agreement Active at its actual effective date and creates only outstanding tasks. It never asks the parties to sign again, changes their original dates, or republishes already evidenced notices. Unsupported accounting ownership or missing material terms prevent that activation.

### 5.14 Budget conversion, adjustment and closure

For a KenTender award, preserve every REQ source allocation/reservation identity and exact awarded price allocation; a managing OU does not replace source departments. The mapping must reconcile awarded goods and related-service amounts, tax treatment and rounding to the package’s complete supported price. A missing mapping is a funding issue, never an arbitrary allocation by the contract officer.

| Action | Existing BUD v1.12 owner contract | CM treatment |
|---|---|---|
| Revalidate before consequential formation/change | `revalidate_reservations` and authorised position reads | Authenticate the contract service principal; read exact source reservations, restrictions and remaining amounts. No local Budget table query. |
| Effective contract obligation | `convert_reservation` | Convert exact funded allocations once, retaining contract/event and idempotency keys. No new reservation or duplicate commitment on retry. |
| Effective lawful variation/termination adjustment | `adjust_commitment` | Pass exact supported new contractual total and owner event. Accepted work, recoveries, valid unsettled liabilities and settlement costs determine the supported obligation; it is not automatically reduced to certified invoices alone. |
| Unused reservation portion | `release_reservation` | Only an explicit owner-authorised cancellation/revocation/remainder disposition with exact amounts can release it. One reservation may fund multiple commitments. Signing does not prove all unconverted funds are unused. |
| Final commitment closure | Proposed Budget-owned `close_commitment` (CM-CP-02; not installed or approved by this CM draft) | Close exact reconciled commitment revision once; retain final supported current amount and funding charge. Status closure releases no funds. The precise proposed owner contract follows; missing acknowledgement leaves funding finalisation pending. |

A signature provider cannot be rolled back by a local database failure. Persist real proof and the legally correct agreement outcome, and a durable funding/order intent. Prevalidate before requesting consequential signatures; after a failure show **Contract signed — funding update pending**, restrict affected spending/posting and reconcile the original intent. Owner-side operations are atomic/idempotent within Budget; cross-owner work uses durable acknowledgements/reconciliation, not a claimed distributed transaction. Once required funding and order operations are reconciled, eligible downstream work resumes. An increase has no authorised spend path until funding is confirmed.

An external registered contract does not automatically draw from KenTender Budget. Retain its funding-authority evidence and show **Not linked to KenTender Budget**. Adding a link later requires Budget’s verified opening/reconciliation contract, not conversion of already recognised liabilities a second time. Contract completion, accounting settlement and Budget commitment closure remain separate truthful facts; an outstanding required funding disposition prevents unsupported financial finalisation.

#### 5.14.1 Proposed Budget-owned closing contract

Apply as an exact proposed amendment to BUD's commitment, position and service sections, preserving its pending permissions additions. `close_commitment(commitment_id, expected_revision, contract_outcome_event, reconciliation_evidence_refs, idempotency_key)` accepts only the authenticated contract service principal and an exact Closed/termination-settlement owner outcome. The owner event identifies final supported obligation and allocation links; the operation never accepts a browser-entered release amount. Lock commitment and affected positions, verify contract/source identity and current amount, reject stale/conflicting/repeated-content payloads, and return the durable closed revision plus before/after positions and acknowledgement.

Before closing, CM requests any lawful final obligation decrease through existing adjust_commitment. The final amount includes performed/paid work and legitimate surviving liabilities or costs; paying an invoice does not reduce it. A mismatch with the reconciled owner event is an error, not an implicit adjustment. close_commitment changes status and records attribution only: amount and Available remain unchanged. BUD's position calculation must include Closed commitments at their retained current_amount; otherwise changing status would incorrectly free consumed funding. Record a zero-value closure event with unchanged before/after positions; original conversions/adjustments remain immutable.

Closing never replenishes a reservation, releases another allocation, cancels a debt, confirms settlement or increases available funding. An exact, separately authorised decrease may later reconcile a Closed commitment under BUD's existing adjustment service and retained correction evidence; do not delete its history. An increased obligation requires owner revalidation and an eligible Budget/funding decision before use, and cannot bypass a closed-Budget prohibition through CM reopening. Define/install those owner guards before enabling affected corrections. Until this owner amendment and proof exist, show Funding finalisation pending even if the contract is correctly Closed or Terminated.

Required owner tests: final charge KES 1,000,000 remains counted after status closure; approved unperformed KES 200,000 decrease produces retained KES 800,000 then zero-effect closure; shared reservation remainder unchanged; identical replay returns same result; different payload/stale revision fails; concurrent adjustment cannot close mismatched amount; no increase/new obligation into a Closed Budget. These tests prove owner behaviour, not CM's cached totals.

### 5.15 Compliance obligations and generated reports

Each triggered duty uses §4.1’s obligation record and the verified profile. Publication, variation reporting, progress reporting, retention, security action remain separate from the lifecycle. A supplier signature does not discharge a publication obligation; a submitted report does not prove every row’s contract is complete. Unknown applicability creates HOP review work immediately and preserves the original event.

| Report / output | Minimal generated content | Recipient and period |
|---|---|---|
| Contract progress | Contract/reference/title/supplier, actual commencement, current legal outcome, delivery/services fulfilled and remaining, operative amount, cash confirmed, noncash adjustments, financial outstanding, expected completion, material open issues | AO; monthly where the verified profile requires it; otherwise clearly identified internal management output |
| Award/signing publication and report | Exact decision/signing versions, supplier, subject, amount and applicable start/completion facts; statutory fields restricted to the verified channel specification | Profile-specified recipient/channel and trigger; no signature-only or fourteen-day assumption |
| Effective variation report | Original/current amount and quantities, cumulative change, grounds, recommendation/decision, effective amendment and funding outcome | Profile-specified reporting duty, including the applicable Act §139(5) treatment after legal verification |
| Payment follow-up | Invoice received, certified, liability posted, instalments/settlements, noncash adjustments, outstanding and delay against each established payment rule | Internal Finance/HOP output; external statistics only where independently verified |
| Termination/settlement record | Grounds/notice/effective date, accepted work, unsettled liabilities, advances/recoveries, costs, disputes and settlement disposition | Internal AO/HOP; no Regulations-only quarterly statutory default |
| Donor-specific outputs | Deferred; not generated or presented in MVP 1 | Future reviewed successor only |

A period uses the site timezone and explicit inclusive start/exclusive next-period start. Scheduled generation creates one report per type/period; source failures retain an Incomplete draft and recovery owner. An empty report states **No records in this period** only after all required source reads succeeded. Historical report rows use the retained cutoff and exact source versions; regenerated versions never overwrite submitted evidence. HOP submits a reviewed report or records its actual external submission reference/copy/date and destination; no fresh AO approval of routine submission is introduced. Internal submission tracks dispatch/delivery separately. Required recipients/fields and exact source-rendered report templates remain evidence items under §17, rather than invented statutory formats.

Calendar rules retain timezone, event instant/date, count basis, holidays where applicable and boundary treatment. A clock is calendar-day or business-day only where the source says so. Missing required holiday data or an uncertain invoice trigger gives Needs review. Receipt corrections and late event delivery cannot restart a legal clock. No universal statutory 60-day payment deadline or automatically chargeable interest is imported from CTM.

### 5.16 Deferred World Bank extension

The Project Owner approved the coverage assessment and its recommendation to defer the proposed World Bank extension on 8 October 2026. MVP 1 supports the agreed Kenyan simple-IT-goods scope only. No donor profile activation, no-objection editor, donor plan/evaluation, donor seed branch or donor-specific test is part of this release. An external signed contract with unsupported regime/applicability remains a saved unsupported intake; it cannot start management under a fabricated Kenya binding.

Keep the versioned source/profile/obligation architecture used by the Kenyan scope. This does not authorise a generic regime selector. Historical World Bank source findings from v0.3 remain in §17.6 for provenance only. A future extension requires a reviewed successor with its actual project/edition, national-law relationship, duties and interfaces; it cannot be enabled merely by a site setting.

### 5.17 Operation failure and permitted-work matrix

Evaluate every open hold independently. The permitted action set is the intersection of all applicable guards; the most prominent task never masks another restriction. A pending operation retains its original identity, proof, inputs and recovery owner. Source reads and authoritative status reconciliation precede retry. Factual/protective recording stays possible only within the actor's authority and the particular restriction; it grants no permission to use goods, pay, vary or waive a legal order.

| Pending / failed operation | Truthful state and permitted work | Blocked consequences | Recovery / resumption |
|---|---|---|---|
| Signature outcome uncertain | Awaiting signatures; read frozen version and record incidents | New attempt, Active, PO/funding conversion based on assumed formation | Trust recovery reconciles original attempt; proceed only with exact verified proof/effectiveness |
| Agreement effective; Budget conversion or PO failed | Active; Contract signed — funding/order update pending; retain proof, physical custody/observations and supplier claim capture | Native receipt/asset posting, new supported spending and payment until required funding/order guards pass | Separate Budget and native-order operation records; technical recovery with HOP/Budget owner where business correction required; both required results must reconcile |
| Acceptance signed; receipt/asset posting failed | Effective acceptance retained; stock/asset update pending; read/report evidence and receive invoice claim | Ordinary accepted-goods certification and payment based on missing/stale native result; use/disposal of unposted goods | Technical owner reconciles exact accepted subset/native result; no repeat report signatures. Lawful early liability recognition is permitted with payment hold |
| Native invoice posting uncertain/failed | Certification remains historical proof; invoice update pending; factual follow-up and correction request allowed | Payment against absent/unconfirmed supported liability | Finance/technical owner reconciles original native ID/operation. Changed financial subject requires maker review and fresh approval |
| Native payment posting uncertain/failed | Payment update pending; no claim of settlement | Duplicate instalment, settlement confirmation without confirmed entry/evidence | Finance/technical owner checks native outcome and allocation under original identity before retry |
| Posted payment; settlement not confirmed | Payment recorded — settlement not confirmed; follow up bank/reconciliation evidence | Cash paid claim or repeating the same allocation as a new payment | Finance settlement authority confirms actual amount/date/evidence or records failed/reversed outcome; no bank execution by CM |
| Effective amendment; Budget/order update pending | New legal terms/history retained; funding/order update pending | Spending against changed entitlement; other independent work only if every applicable hold permits it | Recover exact successor and owner operations, retaining original legal effective date. No fictional rollback of signatures |
| Closure signed; owner financial finalisation failed | Closed or Terminated remains truthful; funding finalisation pending; surviving duties remain assigned | Financially finalised badge or release of any funds | Budget/Finance owner reconciles original close operation; no fresh AO close-out signature for technical retry |

### 5.18 Corrections and downstream consequences

Correction is a linked successor, not a historical edit. Record subject, affected units/amount, factual reason, actor, evidence and the exact downstream records. A correction request immediately holds further affected certification/payment while the authorised decision is obtained; it does not erase effective evidence. Independent unaffected lines remain eligible where separable. Refunds, credit notes and recovery are not inferred cash receipts.

| Changed fact | Required treatment | History and resumption |
|---|---|---|
| Acceptance report before full proof | Withdraw outstanding requests; chair prepares successor with current signer set | Prior proofs retained as superseded; no new receipt intent from incomplete report |
| Effective acceptance before native posting | Authorised committee signs correction; supersede unexecuted intent after checking no native success | New accepted subset consumes eligibility once; old decision retained |
| Acceptance/return after native receipt | Retain physical evidence; authorised correction creates native cancel/amend or return as supported by downstream links | Hold affected claims/stock disposition pending reconciliation; restore entitlement only for confirmed returned scope, never by editing report quantity |
| Corrected claim before native posting | Recalculate matching; old certification no longer authorises successor claim; HOP signs current support | Supersede draft/request; native draft regenerated through normal methods; no receipt-clock reset |
| Claim/accepted quantity changed after liability posting | Freeze affected payment allocations; Finance uses native amendment/credit/debit adjustment as permitted; HOP certifies revised support | Keep original liability/certification; link adjustments and evidence. Resume only against reconciled supported outstanding amount |
| Accepted-and-paid goods returned/replaced | Hold affected new claims; reconcile linked native return/credit, supplier refund/recovery or replacement treatment | Prior payment stays historical cash fact; replacement uses existing unfulfilled obligation, not a second payable for the same unit |
| Amount/beneficiary changes during payment review | Invalidate pending approval; maker submits corrected exact native subject for independent review | Preserve previous approval as history; do not change already posted payment destination silently |
| Payment reversed or settlement correction | Use native reversal when ledger correction is required; Record/CorrectFinanceSettlement changes evidenced settlement projection only | Reopen outstanding supported amount/task; show original cash and reversal separately; allocate again only after reconciliation |
| New evidence after closure | AO reviews reasoned correction under §5.21; hold affected positive actions and keep survivor work | Retain original closure. A new ordinary warranty/payment follow-up alone does not reopen completed procurement |

### 5.19 Mixed claims and contractual adjustments

**MVP policy: correction before certification of a disputed received-goods invoice.** Record the whole supplier claim and original receipt instant, show supported and disputed lines, and request a corrected supported claim. Do not introduce partial certification of the original disputed invoice. The rejected portion remains attributable correspondence/issue, not a deleted claim. Multiple legitimate corrected/separate claims and instalment payments remain supported. This policy is distinct from partial delivery and partial payment.

If Finance already recognised the original liability under its policy, correction must reconcile the native liability with authorised credit/amendment operations before supported payment. Do not create a second liability for the same corrected claim. Payment due dates follow the verified operative trigger; a successor's receipt time is retained but never automatically replaces the original for legal/contractual clock calculations. A deduction differs from disputing supplied quantity: apply only an authorised contractual adjustment with exact basis, support and native accounting treatment.

Delay calculations show original/operative due date, actual event, extension effect, count basis, eligible principal, rate, exclusions and cap. HOP records causation and proposed disposition, including supplier challenge; the authority named by the verified contract/profile decides the adjustment. Where the route lacks defined authority/accounting treatment, hold only the affected consequence with a named owner. An AO decision in the isolated fixture is an explicit test authority, not a universal statutory deduction rule. Extension requests alone change no date or deduction.

### 5.20 Warranty and security actions

The contract coordinator records the equipment/claim, timely notice, remedy requested, response and evidence. An appointed technical capacity verifies repair; a replacement requiring new contractual acceptance follows the current inspector/report route. VerifyContractRemedy commits the technical verification and automatically resolves the warranty issue through ResolveContractIssue when required report/native return/credit/receipt links are already reconciled. Otherwise the claim remains open with the specific missing evidence and holder. This is one verified outcome, not a further manual approval. The supplier can respond/propose remedy, never self-accept it. Historical acquisition/payment is retained; do not create a second order value or invoice entitlement for a like-for-like warranty replacement.

For a paid returned unit, keep segregated custody; Finance determines the reviewed native return/credit and replacement treatment. Pending credit may temporarily expose a balance while a payment hold prevents unrelated duplicate settlement. The accepted replacement restores the contractual coverage once, with its actual warranty rule from issued terms; it does not assume a new universal warranty period. Damage repair without transfer need not create fictitious receipt/return documents.

Security actions are typed Receive, Verify, Reject, Replace, Extend, Request claim, Decide claim, Record claim outcome, Authorise return and Record return. The custodian prepares facts/evidence; HOP reviews performance-security action and AO decides a consequential claim/return under the verified authority route. Finance holds advance-security/recovery custody and records attributable proceeds. Request/decision alone never means an issuer paid or discharged the guarantee. Verification of a replacement/extension precedes superseding the old instrument; absence of overlap/coverage is a held issue. If an instrument restricts the authorised claimant, enforce that evidence rather than treating an AO decision as sufficient. Actual claim communication/outcome is linked correspondence and immutable evidence; payment/recovery uses Finance's native path. No separate security ledger.

### 5.21 Close-out correction and termination settlement

HOP prepares a reasoned closure-correction request identifying the wrong completion fact, affected obligation and proposed disposition. AO may Return, Confirm closure remains valid with explicit surviving work, or Reopen for required completion work. ReopenContractCloseout records a successor decision, preserves the original closure and restores Active only for a previously Closed contract. It cannot change Terminated into Active or successful completion; termination correction requires its own legal authority/effective record. Reopening does not restore funding or undo native records automatically. Any increased obligation needs the same lawful owner/funding checks; unresolved funding correction blocks affected spending.

For an effective termination, Finance reconciles accepted work, authorised costs, liabilities, credits, confirmed cash, advances/recoveries and disputes. HOP prepares settlement completion; AO completes it only if every remaining item is either settled or validly classified as a named surviving obligation by the verified terms/profile. CompleteTerminationSettlement records a separate date/proof; lifecycle stays Terminated. An unresolved unclassified debt/recovery/dispute blocks supported settlement completion. Budget closing and Finance outcomes are separately acknowledged, never inferred from this signature.

## 6. Roles and permissions

CM registers Contract preparation, Contract coordination, Receiving, Contract inspection, Technical certification, Entity contract signing, Finance preparation and Finance approval through AUTH’s existing responsibility registry and its existing scope/effective-period mechanism. AO/HOP use existing responsibilities. Inspection, technical-certification and entity-signing actions additionally require a written contract-specific appointment/capacity; appointment evidence supplements, never bypasses, the shared resolver. Supplier actions require the existing current organisation binding. Financial authority is a KenTender business assignment plus the required native Finance permission; ERPNext Company/Cost Center never substitutes for AUTH’s OU scope. A disabled or expired assignment removes future action access.

Procurement preparer, HOP, named user-department contract owner, receiver, appointed inspectors/chair/members, entity signatory, supplier representative/signatory, Finance maker/approver, auditor and technical operator have separate business capacities. Reuse existing people and shared authority; no new global role grants access to every contract.

The receiver records arrival; inspectors record observations; chair composes the report; appointed signers sign. Supplier representatives submit claims/issues; only current supplier signatories sign the agreement. HOP certifies only under the verified authority route. Finance authority does not grant contract amendment authority. Auditor reads the permitted history, with no mutation. Technical business read follows approved KT-STD v1.25 §3A.6 and its §8.3 Technical Operator decision: Administrator, System Manager and Daniel Otieno have site-wide read-only access to CM business surfaces, with no business commands. Sealed content and credentials remain excluded. Incident recovery authority is separately scoped to service operations; it does not confer Finance approval or permit user-account impersonation.

Server authorisation applies to reads, documents, exports, mutations, imports, background work and ordinary ERPNext screens. Privileged database operations remain governed by shared operating controls; this document does not claim software permissions make a database administrator incapable of alteration.

### 6.1 Segregation and appointed capacities

Enforce at server command time and through native routes:

- An acceptance-report signer cannot sign procurement certification of a claim supported by that acceptance, including a corrected claim or a mixed claim relying on it. Check actual signer identities against every supporting acceptance version at certification time; suppress the action with the exact incompatibility and route to a separately authorised certifier. Reassignment alone cannot erase the earlier signature. This is the proposed product control CM-OD-09, not an asserted statutory prohibition.
- A receiver cannot sign acceptance for the same arrival they recorded. This does not prohibit a contract owner from coordinating suppliers.
- A change requester cannot sign its independent recommendation or make the final decision; an appointed reviewer cannot make that same final decision. No universal new variation committee is created unless the applicable route requires one.
- A Finance maker cannot approve their own invoice/payment; a payment maker or procurement certifier cannot execute/confirm that same payment settlement. Native permissions do not waive these conditions.
- A conflicted member cannot observe, sign or decide the affected scope. Replacement preserves earlier attributable evidence and creates the correct current appointment/signature set.
- Supplier representatives may submit claims, corrections and replies for their own contract; only current supplier signatories sign agreements/amendments. Bid submission power is not reused as contract invoice authority.

CM registers business responsibilities through AUTH’s existing extension point with its existing Site-wide or Organisation Unit scope, effective periods and segregation tags. Contract appointments are CM-owned subject bindings checked in addition to AUTH; they do not add a Contract scope type or a contract field to User Responsibility Assignment. Do not introduce CTM’s new people or a global Payments Officer merely to record native settlement. AUTH/TRUST extension behaviour must be checked against the supplied current services before implementation (CM-SHARED-01); no unprovided shared specification is claimed to have been changed.

### 6.2 Responsibility scopes and read profiles

Use AUTH's exact role-bound resolver. Contract preparation, Contract coordination and Receiving are Organisation Unit responsibilities, matched to the managing unit and descendants. Finance preparation and Finance approval are Site-wide business responsibilities plus required native permissions. Contract inspection, Technical certification and Entity contract signing are Site-wide registry responsibilities whose domain commands and case reads additionally require the exact effective CM-owned appointment/signature subject; assignment alone grants no contract access. AO/HOP remain Site-wide and may prepare/coordinate through their existing office authority. AO may sign for the entity only under the current entity-signatory authority check; an AO read does not grant inspection authority. Auditor scope follows its actual AUTH assignment. Supplier authority uses the existing organisation binding. Appointments supplement the required registered responsibility, enabled identity and coarse framework permission; they are not a new AUTH scope type or a substitute role derived from fixture membership. The new CM registry entries and projections are proposed owner bindings in §17.4, not assumed installed.

For user-department oversight, an Active Head of User Department may discover/read a contract whose managing unit is in their assigned subtree, or whose immutable source allocation explicitly names a unit in that subtree. Source participation permits this contract's agreement, progress, acceptance and contractual totals, not arbitrary contracts or whole-Budget details. Source allocation detail is restricted to that permitted departmental projection. Departmental Author, Planner or Evaluation membership alone grants no CM access. No primary/home department, first matching assignment, browser context or ERPNext Company grants authority.

Read profiles below apply to list/count/search, all five case tabs, task records, evidence, generated documents, exports and direct links. A task is neither required for read nor an authority grant. Read-only users see the same case navigation and authorised facts, with decision/editor controls absent. Sections with no permitted content show a neutral empty explanation within the case, rather than denial of a record the actor may read. Resolved/draft/closed/terminated history stays readable within actual current authority; expired users do not retain live access merely because they once acted. Preserve their historical attribution.

| Reader | Discoverability and readable subject | Restricted fields / command boundary |
|---|---|---|
| AO / HOPF | Site-wide contracts in all lifecycle states; all five tabs, appointments, changes, compliance and history | Finance-only accounts/full bank details omitted unless independently authorised. AO/HOP action powers remain those in §§5–7; no member or Finance power from read |
| Contract preparer | Contracts within assigned managing-unit subtree, including drafts, agreement/source, deliveries, invoice support, obligations/history | Operational totals readable; no Finance editor/approval or protected banking; preparation only |
| Contract coordinator | Same scoped cases; all five tabs and supplier/exception follow-up | No approval from coordination; Finance-only fields omitted |
| Head of User Department | Managing/source participation as defined above; complete contractual case/progress and permitted source projection | No preparation, inspection, signatory or payment command without separate authority |
| Receiver | Scoped managing-unit cases; all five read-only tabs with arrival/custody/acceptance and operational financial summary | Receiving editor only; no acceptance of own arrival; no Finance-only fields |
| Current inspector/chair/technical certifier | Exact appointed contract, all five tabs, source criteria and corresponding report/history, even when declaration pending | Pending/conflicted capacity retains read of permitted appointment, contract and history context; observation, signature and decision commands remain prohibited for affected scope. A separate authoritative disclosure restriction is enforced on its own evidence, not inferred solely from conflict. No unrelated cases, Finance editor or bank data |
| Entity signatory | Exact appointed signature subject and contract context/obligations/history needed to understand it | No unrelated cases or implicit inspection/payment powers; current signing checks govern action |
| Finance maker / approver | Site-wide contract financial/source/acceptance/obligation context, native record projections and all five tabs | Approved Finance projection includes required accounts/verified beneficiary; credentials/private keys never readable. Maker cannot approve own subject; Finance read grants no variation power |
| Auditor | Cases in actual assigned oversight scope; all five tabs and audit evidence | No mutation; full banking only if an independently reviewed oversight projection grants it; credentials excluded |
| Administrator / System Manager / Technical Operator | Site-wide read of CM business cases, versions, reports and financial status, including drafts | Permitted business accounts/status visible under the existing site-wide technical-read policy. Credentials/private keys and fields already classified as protected by current shared policy are excluded; specialist diagnosis uses its separate reviewed scope. Do not invent a new blanket technical financial-read denial. No business mutations. Technical recovery is separately scoped |
| Supplier representative / signatory | Own organisation's case list and five supplier tabs; agreement, supplier-visible inspection/disposition, their claims/payments, addressed issues, notices and history | No internal deliberation, other suppliers, legal advice, staff declarations, funding allocation, accounts or protected banking. Representative claims/replies; only current signatory signs |

Record audience and field-set identifiers in the owner read contract; apply filters before pagination/count and retrieve only authorised fields. Independent legitimate responsibilities may provide additional projections, but one role's OU never broadens another role. Current action guards are rechecked at commit. Return stable denial only for genuinely unreadable records; absence of a mutation responsibility must produce a readable view for an authorised reader, not a page denial. Read-contract tests must exercise AO direct navigation without a task, every capacity, cross-OU/source membership, multi-role scope separation and exports.

#### 6.2.1 Command responsibility and subject binding

| Command family | Required responsibility and additional binding |
|---|---|
| Preparation/intake and request signatures | Contract preparation within managing OU, or Site-wide HOP; exact source/current version |
| Coordinate issues/change/warranty/close-out preparation | Contract coordination within managing OU, or HOP; current case subject. Supplier request/reply uses own-organisation authority |
| Record arrival/custody return | Receiving within managing OU; actual arrival/units; accepted-unit correction requires its signed decision before consequential posting |
| Recommend inspectors / appoint or replace / declare | HOP recommends; AO appoints/replaces; named appointee personally declares after appointment with enabled identity. Declaration is not itself inspection or an authority grant |
| Inspection/acceptance report | Contract inspection plus exact effective appointment/capacity; chair prepares, every required current signer personally signs; conflict/receiver separation rechecked |
| Technical certificate/remedy verification | Technical certification plus exact current technical appointment/source competence; cannot substitute HOP certification |
| Entity contract/amendment signature | AO with reviewed entity-signatory authority, or Entity contract signing plus exact current written mandate; same frozen version; no approval by proxy |
| Supplier signature / invoice/correspondence | Current supplier signatory for signing; current supplier representative/signatory for own claim/correspondence; no tender/BDS power inferred |
| Procurement certification / completion certificate | HOP with exact verified authority and current support; native finance/technical certificates remain separate |
| Change/termination/close-out/correction/settlement decision | AO plus exact supported subject/required advice/signature. Final acceptance may use the AO or Contract inspection plus the exact explicitly appointed AO-representative mandate under reviewed source authority, not a generic receiver |
| Finance draft / independent approve / settlement | Finance preparation / Finance approval respectively, plus native permission/current verified workflow; actual maker separation. Settlement recorder Finance approval under explicit CM-OD-08; fixture Beatrice may confirm the entry she approved only with independent bank/reconciliation evidence. Actual maker and procurement certifier cannot confirm that same payment |
| Security decision / actual action | AO consequential claim/return decision subject; HOP performance custodian, Finance advance custodian. Issuer claimant mandate and actual return/recovery evidence remain required |
| Native posting / funding / recovery | Authenticated scoped service principal with original owner decision; technical recovery scope grants no new business decision or direct ledger write |

Appointments can identify a person whose base responsibility must still be provisioned through the approved shared mechanism before consequential work. Show the missing assignment and administrator owner rather than inventing authority from an appointment task. Existing office holders need no redundant per-contract AO/HOP assignment. Read-only audiences still use §6.2 even when a command prerequisite is missing.

### 6.3 Task priority and simultaneous work

My Work retains each independently actionable obligation. Use one logical item per command subject/version/required holder; delivery retries and event replay never create a second item. Reassignment preserves previous holder/time and current holder; old task identity does not confer command authority.

Case/list Next action is actor-specific. For that actor, order actionable work by: protective/legal/security deadline at risk, other verified overdue duty, earliest verified upcoming due instant, then undated work by assignment instant and stable task ID. A blocked duty remains visible with its exact fix owner; it cannot hide actionable independent work. Waiting/scheduled rows are shown below actionable work in the same ordering. Unknown dates say Not established, never an invented urgency score.

Every §10 brief inherits the conditional Other work region when simultaneous permitted items exist; unlisted fabricated rows remain prohibited. D40 is the reference presentation of this shared region, not an additional panel or route to append to D10. A command subject/version/holder appears once in the task presentation: exclude the leading task from Other work and do not repeat an existing Other work table. Domain facts may appear in the relevant record details without creating duplicate task rows. The case shows one leading next-step block and a compact Other work region for the remaining permitted items: task label, state, verified due date or Not established, responsible person and Open. When there is no actor-owned action, the leading item names the next current holder and true assignment time. Neutral readers have no personal task block and can read the permitted work register. Closed/Terminated records retain surviving items in My Work and All contracts. Task completion is the command's authoritative outcome, not opening, reading, receiving a notification or closing an issue unrelated to the obligation.

### 6.4 Purposeful actions and automatic work

Every required human step must establish a physical fact, exercise a decision, make a personal declaration/signature, submit a claim or communication, or confirm independently sourced evidence. A successful system calculation or internal handoff never creates an extra confirmation task.

| Required human step | Why it remains | Work the system must handle |
|---|---|---|
| Agreement review and party signatures | Each party accepts the exact terms in its own capacity. | Populate terms, freeze the version, route signing and generate the order; no manual handoff acceptance. |
| Inspector recommendation/appointment and personal declaration | Establish the actual authorised people and conflicts. | Generate the appointment record/reference and route only missing declarations. |
| Physical arrival/collection and inspection observations | The system cannot establish physical facts by itself. | Reuse expected items; calculate findings and coverage; no manually selected pass/fail or reconfirmation of every match. |
| Technical certificate and acceptance report signatures | Distinct technical and acceptance responsibility under the current policy. | Generate both from the same recorded evidence; no re-entry of observations or quantities. |
| Supplier invoice/correction and procurement certification | Retain the supplier claim and the authorised contractual support. | Compare quantities/amounts and create one linked Finance draft; no separate approval of every matched line. |
| Native Finance maker/approver actions | Complete required accounting choices and preserve native segregation. | Prepopulate established values and calculate totals; no parallel CM approval of the same native transaction. |
| Settlement recording | Establish actual cash movement using independent external evidence. | Reuse provider/reconciliation results when available; never infer cash from a posted entry or zero balance. |
| Change/termination request, current required review, decision and required signature/notice | Establish reasons, authority and effective terms/outcome. | Generate comparisons, calculations and routing; hide steps that the bound source does not require. |
| Issue/notice communication and factual response | Establish the actual remedy request and delivery/outcome. | Draft from existing facts; preserve dispatch status and reuse the same message on retry. |
| Existing-contract source/opening review | Confirm imported terms and prior activity without historical reposting. | Reuse linked balances and show differences; no fresh procurement or signing. |
| Final acceptance, completion certificate and close-out | Separate completion and closure responsibilities in the current policy. | Generate each review from the same fulfilment evidence; no repeated checklist entry, new invoice review or general “everything complete” confirmation. |

Only required work creates a personal task. Read-only pages, optional View/Open/Cancel controls, successful source reads and automatic posting acknowledgements create none. A dialog commits its originating action once; it is not an additional approval. Native or legal evidence may show that a retained step needs amendment; record that decision rather than silently deleting its authority or proof requirements.

## 7. Service and command contracts

Common envelope: subject identity, expected revision, stable operation key, actor/service authority and only the business inputs below. Material commands validate current sources and record audit + task/event effects durably. Retrying the same key with different content fails; an identical retry returns the original result. Stale versions return a conflict without losing unsaved user text.

| Command / read | Inputs and result |
|---|---|
| `ReceiveAwardPackage` / `ReceiveAwardUpdate` | Exact AWD package or immutable update; durable case/update receipt and tasks. Source updates cannot overwrite a signed version. |
| `ReceiveAwardPublicationEvent` / `RecordContractAwardPublication` | AWD event; or obligation, required channel/evidence. Receipt and completion remain distinct; preserve original trigger times. |
| `RegisterExistingContract` / `ReviseContractIntake` | Source identity, executed evidence, structured clauses and cutover position; one draft case and review findings, no ledger effects. |
| `ConfirmOpeningPosition` / `StartContractManagement` | Exact intake revision; Finance confirms accounting facts when prior activity exists, HOP confirms source/terms. Activate once, with outstanding tasks only. |
| `RecordCustodyReturn` / `RecordAcceptanceCorrection` | Exact units, collection/correction evidence and reason; custody update or linked reversal request, never historical overwrite. |
| `SignTechnicalCertificate` / `IssueCompletionCertificate` | Exact technical or HOP certificate subject and proof; separate audience/purpose, underlying observations reused. |
| `RecordSecurityAction` / `RecordWarrantyClaim` | Instrument or equipment, action/notice, date, authority and evidence; no release from expiry. |
| `RecordFinanceSettlement` / `CorrectFinanceSettlement` | Native payment, amount/date and settlement evidence; attributable confirmation/correction without ledger write. |
| `CompleteTerminationSettlement` | Termination version, reconciled outcome and AO authority; keep Terminated and retain surviving tasks. |
| `SaveContractParticulars` / `RequestContractSignatures` | Released missing fields; then exact generated version. Frozen signing request after checks. |
| `SignContractVersion` | Exact request/version and shared signature operation; proof or pending/failure. Order/link created after complete effective agreement. |
| `RecordContractArrival` | Actual items/units, time, destination and evidence; immutable arrival, custody and inspection tasks, with no native receipt draft. |
| `RecordInspectionObservations` | Exact criteria/coverage, observed values/evidence; attributable revision and automatic findings. |
| `PrepareAcceptanceReport` / `SignAcceptanceReport` | Quantity disposition/reasons; then exact report/proof. Required signatures create one effective decision and posting intent. |
| `PostAcceptedReceipt` | Service-only decision/order version and operation identity; native receipt/asset links or retryable incident. |
| `SubmitContractInvoice` / `CorrectContractInvoice` | Structured claim or linked correction; retained submission, draft native invoice and automatic matching. |
| `SignContractCertification` | Exact matching report, supported adjustments and proof; certification and Finance work item. |
| `SaveNativeFinanceDraft` / `SubmitNativeFinanceForApproval` / `ApproveNativeFinanceRecord` / `ReturnNativeFinanceForCorrection` | KenTender façade operations over the exact native invoice/payment ID/version and configured workflow transition; draft fields or return reason, current authority/entitlement/holds, stable operation identity. Use native methods, never ledger writes or a parallel approval. Return authorised record/status/field errors to the same screen. |
| `ReceiveFinanceResult` | Trusted native document/version/event and settlement evidence where provided; authoritative status projection, never an independent ledger. |
| `RecordContractIssue` / `RespondToContractIssue` / `ResolveContractIssue` | Scope/facts, response or reasoned disposition; correspondence and affected hold only. Final disposition closes that thread; later evidence creates a linked issue. |
| `RequestContractChange` / `DecideContractChange` / `ActivateContractChange` | Grounds/impact; authorised decision; then required executed amendment/notice evidence. Terms change only on activation. |
| `PrepareContractCloseout` / `SignContractCloseout` | Generated review and authorised exact-version proof; closure only against verified conditions. |
| `GetContractWorkspace` / `GetContractHistory` | Current actor/subject; authorised current view or versioned history, with actions and named next holder. |
| `RecommendContractInspectors` / `AppointContractInspectors` / `ReturnContractAppointment` / `DeclareContractInterest` | Current recommendation/appointment version, named members/capacities or personal declaration; authority and effective period checked. Conflict creates replacement work, never inherited Evaluation power. |
| `RecordContractSecurity` / `VerifyContractSecurity` / `RejectContractSecurity` | Actual instrument/evidence, source requirement and reason; upload is not verification; retained replacement history. |
| `RecordOutsideContractSignature` / `ConfirmOutsideSignatureEvidence` | Exact executed document/party and attributed evidence; permitted method and authority rechecked; ambiguous version remains an issue. |
| `GenerateContractReport` / `SubmitContractReport` / `RecordContractReportSubmission` | Service-generated cutoff/period/version; authorised internal submission or actual external evidence; immutable submitted rows, pending delivery on failure. |
| `RecordLegalSourceEvidence` | Attributed source/reference/date/copy and proposed applicability review; sends legal-owner work. It never edits an executable rule or declares it verified by itself. |
| `PrepareContractClosureCorrection` / `ReopenContractCloseout` / `ConfirmContractClosure` | HOP request, exact prior closure/revision/reason/evidence; AO returns, retains closure with classified surviving work, or records reasoned reopening. No native/funding rollback and no reversal of effective termination. |
| `RequestContractFundingUpdate` / `ReceiveContractFundingResult` | Service-only durable intent, exact allocation/owner event and original operation identity; owner's idempotent result or retained incident, no CM ledger writes. |
| `PrepareContractAdvance` / `SignAdvanceCertification` | Issued advance clause, supported entitlement, verified guarantee/recovery plan and exact proof; native Finance flow, never acceptance fabricated for an advance. |

Additional coverage commands use the same revision/authority/idempotency contract:

| Command | Exact input / result |
|---|---|
| PrepareContractAdjustment / DecideContractAdjustment | Operative rule/version, actual delivery events, proposed calculation/causation, supplier response and exact subject; prepare held proposal then authorised approve/refuse/return with reasons. Result is a supported adjustment, not an editable calculation or direct ledger write |
| RequestSecurityClaim / DecideSecurityClaim / RecordSecurityClaimOutcome | Exact verified instrument, grounds/amount, authority/correspondence or issuer outcome/evidence; request/decision/actual outcome distinct. RecordSecurityAction handles verified Replace/Extend and authorised Return; no release from expiry |
| VerifyContractRemedy | Exact warranty issue/equipment, current technical appointment, measured remedy evidence and required native links; verified outcome or named incomplete condition. ResolveContractIssue requires this output before supported closure |
| PrepareTerminationSettlement | Effective termination, generated Finance reconciliation, source/version and classified remaining items; HOP review prepared for existing CompleteTerminationSettlement with exact AO proof |

Each adjustment/claim/reopening hold identifies affected line/quantity/amount and commands, current owner, reason and clearing evidence. Read operations expose this scope; a generic issue comment cannot lift it.

Additional exact subjects reuse the common command envelope: `SubmitContractChangeForDecision` freezes the reviewed change for AO; `ReturnContractChange` and `ReturnContractTermination` retain reasons and correction holder; `DecideContractTermination` records only the AO decision; `RecordTerminationNotice` records actual dispatch/effectiveness evidence; `SignFinalContractAcceptance` signs the authorised final-acceptance subject; `SendContractCorrespondence`/`ReplyContractCorrespondence` retain the addressed issue/notice and delivery evidence; `RequestAcceptanceCorrection`/`RequestInvoiceCorrection` retain the exact current source and reason; `ReturnContractCloseout` returns the review to its named correction owner. These are CM commands, not substitute native ledger operations. `RecordContractChangeReview`/`SignContractChangeReview` use the actual appointed route, version and declarations. No reviewer/decision command executes without current authority.

Native invoice/payment posting uses ERPNext commands under the same domain validation; do not create substitute ledger-writing CM commands. Every accepted posting intent is durable; service recovery observes native success before attempting a duplicate. Uncertain outcomes are reconciled by operation identity.

## 8. Error contract

| Code | User-visible message | Fix / holder |
|---|---|---|
| CM_SOURCE | The contract details do not match the source record. | HOP reviews source issue; View issue |
| CM_CHANGED | This record has changed. Review the latest version before continuing. | Reload current comparison; retain unsaved text |
| CM_AUTHORITY | You are not authorised to take this action. | Shared access page; current holder where disclosure permits |
| CM_RULE | The applicable requirement has not been confirmed. | HOP/legal owner; View issue |
| CM_HOLD | This action is on hold. | Show specific reason and holder; View issue |
| CM_SIGNING | Signing is unavailable. Your work has been saved. | Technical recovery of original attempt |
| CM_INCOMPLETE | Some required observations are missing. | Inspector; Review missing observations |
| CM_QUANTITY | These quantities do not match the delivery record. | Chair/receiver; View quantity comparison |
| CM_POSTING | The record is signed. The stock update is still pending. | Technical owner; View update status |
| CM_INVOICE | This invoice needs review before certification. | Finance/HOP issue owner; Review differences |
| CM_DUPLICATE | This submission may already be recorded. | View existing submission; Finance reviews ambiguity |
| CM_CLOSURE | The contract still has obligations that prevent close-out. | View remaining obligations; named holder per item |
| CM_FUNDING | The contract funding update needs attention. | HOP/Budget owner; View funding issue; do not ask for new signatures |
| CM_APPOINTMENT | The inspectors are not ready to act on this contract. | AO/HOP/missing declarer; show missing appointment or declarations |
| CM_SEGREGATION | Another authorised person must take this action. | Name eligible capacity without revealing protected assignments |
| CM_RECONCILE | The correction must be reconciled before this action can proceed. | Current Finance/stock/Budget owner; View affected records |
| CM_REPORT | This report is incomplete because a source could not be read. | Daniel; View update status; submission absent |

No internal tables, hashes or stack traces in business messages. Pending, rejected and unavailable are distinct. Read-only/denied pages follow KT-STD §3A, not a modal or an invitation to obtain unsafe privilege.

## 9. UI architecture, menu and routes

Menu **Contract Management** → **Contracts**. Internal list `/app/contracts`; registration `/app/contracts/register`; case `/app/contracts/{id}`. Sections are tabs within that case: **Agreement**, **Deliveries**, **Invoices**, **Obligations**, **History**; the selected tab has its own authorised deep link. Appointment, security, issue, change and report tasks open focused records linked to the same contract. Supplier list `/supplier/contracts`; detail `/supplier/contracts/{id}` with **Agreement**, **Deliveries**, **Invoices**, **Obligations**, **History**, restricted to supplier-visible content. No role-specific parallel case or new module per stage. “Contracting” in upstream routes is a historical destination label, not a second module.

List columns: Contract, Supplier, Status, Next action, Responsible person. Filters: **Search contracts** (reference/title/supplier), **Status**, **Source**, **Responsible person**, and **Managing unit**, using only permitted values. **All contracts** and **My work** are two list views, not new pages per role; **My work** includes outstanding assigned items only. Historical Closed/Terminated/Did not proceed records remain findable in All contracts. No decorative dashboard metrics. Record header shows generated reference, title, supplier and lifecycle. Operational screens prioritise the current task, key differences and next holder. Detailed source/audit evidence is a disclosure. Separate progress summaries replace a misleading single completion percentage.

### 9.0 Screen and navigation map

One menu entry opens Contracts. My work and All contracts are views of the same list. Opening a row gives one contract with five tabs. A focused task opens from that contract or My work and returns to its source with the selected tab/filters preserved. A task ID or artboard number is never a menu destination.

| Location / reusable surface | Purpose | Brief coverage; suffixes are states or persona views |
|---|---|---|
| Contracts list | Find current work or a historical contract. | D01, D01-S, empty/filter/reader states |
| Agreement tab — agreement review/signing | Prepare, read and sign the actual version. | D02, D03, D26; pending/held/party views |
| Agreement tab — appointment/authority task | Recommend/appoint inspectors and declare conflicts. | D23, D24; recommendation/declaration/replacement views |
| Deliveries tab — arrival/inspection/acceptance task | Record physical facts, review findings and sign the report. | D04–D07, D19, D31; partial/replacement/service/pending views |
| Invoices tab — claim/native Finance task | Submit/correct/certify a claim; prepare/review native invoice/payment and read settlement. | D08, D09, D17, D18, D28, D29, D33; correction/partial/advance/reader states |
| Obligations tab — issue/change/security task | Correspondence, extension/quantity/delay decisions, security and warranty follow-up. | D13, D14, D16, D25, D27, D34–D37; request/review/decision/remedy states |
| Obligations tab — remaining-work/completion task | See simultaneous work, review completion/closure, termination and settlement. | D10/D40 are one presentation; D11, D20, D22, D32, D38, D39 are focused subjects/states |
| Focused register/report form linked to the case | Register existing contracts or submit period reports. | D12/D21 are intake/reconciliation; D15 is the reporting task |
| History tab / evidence preview | Read existing versions, signatures, correspondence and linked native evidence. | Shared View actions; no separate editing workflow |

Reusable visual patterns are list, compact record, form, comparison/review, signature review and evidence preview. Changes of actor, status or contract subject reuse these patterns; they do not justify a new navigation system. D30 remains retired. D-ERR and D-DENIED use shared error/denial pages.

### 9.1 KenTender entry and display boundary

All routine contract registration, delivery, inspection, receipt/asset review, supplier invoicing, Finance preparation/approval, settlement recording and correction journeys remain within KenTender. Reuse native DocTypes, calculations and lifecycle methods behind purpose-built KenTender components matching KT-STD. Do not embed a standard Frappe form in an iframe or use it as the normal editor. Standard forms are reserved for separately authorised configuration, administration and specialist diagnosis; access to them does not confer business authority or bypass CM controls.

The case Invoices tab hosts invoice and payment editors/reviews at `/app/contracts/{id}/invoices/{invoice_id}` and `/app/contracts/{id}/payments/{payment_id}`. These are KenTender surfaces linked to the same native records, with case context and return navigation. Deliveries and Obligations likewise display linked receipt, inspection and asset facts in KenTender. Read-only evidence and document previews open within the KenTender journey; underlying identifiers are references, not native-form launch buttons.

Enter each business fact once. Generate native drafts from the exact supplier claim, acceptance, agreement and certification; Finance completes only missing accounting choices. Read-only source facts cannot be retyped into a competing copy. Native documents own accounting totals, allocations, posting/workflow states and reversals; CM owns its decisions, evidence and task state. Display an authorised projection of those sources with identifiers and effective/recorded timestamps; never treat a cached projection as posting authority. A failed or stale read shows unavailable/update pending and prevents consequential action rather than displaying an unverified success.

Use controlled server operations for native save, approval/submission, cancellation/amendment and reversal. Recheck current authority, source/document version, allocations and holds within the operation, invoke supported native methods and return field-level validation errors in KenTender. Retain entered values on validation failure or stale-version comparison. A changed approval subject requires fresh review. Saving a draft, signing acceptance, posting liability, posting a payment and confirming settlement are separately displayed outcomes. Pending operations retain their identity; retries do not create duplicate transactions. Extra native fields required by the installed configuration must receive reviewed KenTender controls before the affected journey is enabled; a redirect to Desk is not the fallback.

### 9.2 Simplicity requirements

- Show one current task/obstacle and its holder. Show only the actor’s permitted actions; no disabled wall of unrelated roles’ buttons.
- Render simultaneous permitted work once. The leading task is not repeated in Other work. Neutral readers see permitted status without a personal-task block.
- Keep the material facts and differences visible; put supporting evidence/history behind one closed disclosure. A decision must not require opening evidence simply to discover its amount, affected units or obstacle.
- Enter every fact once. Source fields are read-only; reviewed defaults are prefilled. Finance edits only missing or genuinely changed accounting choices. Corrections retain prior versions and the user’s unsaved input on failure.
- Do not ask users to acknowledge successful automatic checks, pass data between modules, recover a technical operation or re-sign because a posting failed.
- Use the same reason, signing, return/correction and pending/error patterns for all subjects. Show the next holder after a handoff; do not create a new confirmation page merely to display success.
- Filters stay compact: Search and Status visible; Source, Responsible person and Managing unit in one optional Filters disclosure. The available fields/query permissions are unchanged.
- No new dashboards, stage modules, per-persona routes, custom rule editors or routine Desk redirects. A focused task retains contract context and a clear return path.

## 10. Static design contract — closed input for design

Apply approved KT-STD-001 v1.25 §2, including its current Frappe surfaces, white enabled fields, corner values and information hierarchy. This section alone supplies module-specific visual inputs; §§7 and 11 are excluded from design prompts. The designs below are proposed review fixtures, not a claim that the shared seed has been amended. These fixtures use synthetic data; retained demo provenance follows the existing shared standard. The supplied §10 fixture label **Illustrative test record** remains until the current externally maintained KT-STD/DEC-044 treatment is reconciled; do not introduce a new global banner. Generated references are represented by the fixed display value **CM-MOH-2027-001** only in this isolated design fixture.

### 10.1 Shared fixture and composition

Fixture: Ministry of Health; **IT equipment delivery**; Afya Digital Supplies Limited; contract CM-MOH-2027-001, agreement 1. Isolated CM demonstration: 10 laptops at KES 100,000 each, total KES 1,000,000 including the fixture’s tax treatment; delivery due 20 July 2027; 12-month warranty from each unit’s acceptance event. The two replacement units are accepted on 27 July 2027, so their warranty ends 27 July 2028. These values do not replace the canonical Award’s KES 46,400,000. The canonical integration scenario must derive its actual line values and terms from the source package.

Common top-to-bottom record composition: context path **Contract Management / CM-MOH-2027-001** is fixture metadata outside the artboard; do not draw a breadcrumb or Frappe chrome. Within the artboard: title and supplier; single next-step block; task content; subordinate **Evidence and history** disclosure, initially closed; task-footer actions. Level 1 is the action/exception and exact quantities or amount; Level 2 is its comparison and responsible people; Level 3 is technical provenance, excluded from business view. No decorative full-width status banner or repeated instructions. **Declared CM exception to KT-STD §2.9.2:** there is no single sequential journey tracker for overlapping delivery, invoicing and surviving obligations. The named section tabs, lifecycle fact and one current-task next-step block supply orientation; no completion percentage or fictitious current stage is introduced. Appointment/change tasks use their supplied task state. This CM-specific exception is approved with v0.7, 14 October 2026; counterpart recording in the current shared standard remains an owner amendment.

Each brief below supplies actor, instant, revision, purpose, primary action and complete visible task content. The local state cards produce separate review artboards, using the same screen surface. Unlisted controls are absent. **Back to contracts** is secondary navigation on internal records; supplier screens use **Back to my contracts**. Evidence disclosure contains the listed document references only, without invented file contents.

### 10.1A One shared page shell

Task cards name the persona/context, title and state, visible facts/fields, actions and evidence. All module-specific visual content is here in §10. Technical commands and test outcomes belong in §§11/14, not on the screen.

**Order:** title + supplier + resolved contract reference/lifecycle → selected case tab → one next-step block → task facts/comparison/form → closed Evidence and history disclosure → task-footer actions. Back to contracts sits beside the heading; supplier uses Back to my contracts. List pages have no next-step block or case tabs. Material facts never disappear into the evidence disclosure. Decision-report preview can start open only where its task card says so.

One primary action represents the current authorised task. Listed secondary controls support that task. Read-only means no mutation; unlisted controls are absent. Labels/values in a named dialog are part of the same card. Status appears once beside the reference. Fixture metadata (actor, timestamp, revision, authority and source profile) stays outside the artboard unless named as visible content.

Each task family below contains its normal content, local field/dialog details and exact state variants. Resolve that family’s explicit variant before drawing; do not collect a second waiting-line override from elsewhere. A linked document is not permission to invent its content. State variants replace conflicting normal facts and actions rather than adding banners. A state shares unchanged fields with its adjacent normal card only; never borrow facts from another contract branch.

### 10.1B Scenario facts — metadata, not extra screen content

| Scenario | Resolved contract | Task families / fact boundary |
|---|---|---|
| Ordinary ten-laptop delivery | CM-MOH-2027-001 | Formation, eight accepted/two rejected, replacement, invoices and later completed branch. |
| Existing signed contract | CM-MOH-2027-EXT-001 | D12/D21; imported opening position; no re-signing or historic reposting. |
| Delivery extension | CM-MOH-2027-EXTENSION-001 | D14/D27; no base delivery history; due date changes only after effective amendment. |
| Security return | CM-MOH-2027-SEC-RETURN-001 | D16; TEST-G-RETURN-001, distinct verification/signing/return history. |
| Security verification | CM-MOH-2027-SEC-VERIFY-001 | D25; TEST-G-001, no D16 discharge. |
| Open warranty claim | CM-MOH-2027-WAR-OPEN-001 | D16-W/P, D11-B, D32-H; claim remains open on 21/28 Jul 2028. |
| Resolved paid-unit warranty | CM-MOH-2027-WAR-001 | D35; replacement/native corrections reconciled, claim closed 15 Jul. |
| Termination/settlement | CM-MOH-2027-TERM-001 | D20, D11-T, D39; eight accepted units only; no base replacements/invoice 2. |
| Related service | CM-MOH-2027-SVC-001 | D31; ten laptops plus training; no training in base D22. |
| Quantity change | CM-MOH-2027-QTY-001 | D34; source limits and funding; no base changes. |
| Delay adjustment | CM-MOH-2027-DELAY-001 | D36; its own delivery/extension facts and calculations. |
| Security claim | CM-MOH-2027-SEC-001 | D37; TEST-SG instruments; decision is not cash recovery. |
| Close-out correction | CM-MOH-2027-CLOSE-001 | D38; retained original closure and correction. |
| Posted-liability correction | CM-MOH-2027-CLAIM-001 | D08-L; Finance correction required before certification. |
| Partial payment / advance / outside signing | Explicitly isolated subject identities in D28 / D29 / D26 | Use their own records and evidence; never import the ordinary branch’s settlement/signature outcomes. |

The following source chronology is fixture metadata. Task cards resolve their visible content and controls locally; this table does not add screen fields.

All dates without a year in §§10.2–10.5 are in 2027 unless a brief explicitly says 2028. In §10.8 each variant inherits its base branch year, contract/subject/version, EAT timezone and selected tab unless explicitly replaced; waiting lines use the stated event/assignment instant. Base managing unit **Digital Health** (`OU-MOH-DHI`); source kind **KenTender award — illustrative package CM-DEMO-AWD-01**, distinct from Award’s canonical source. The synthetic rule profile is labelled **Illustrative test terms**; it supplies the stated 30-day contractual invoice term and unit-based warranty without claiming statutory validity. Issued source **CM-DEMO-TERMS-01** has the 10 laptops/rates/criteria in §10.1; agreement becomes effective at **2 Jul 2027, 10:30 EAT** after Mary signs at 10:05 and Amina at 10:30. Request sent 09:20; the main no-security branch does not borrow D16’s guarantee.

Base accepted receipt and asset/stock classification are a labelled test configuration; posting occurs once at **20 Jul 2027, 14:31 EAT**, after the report’s last required signature. INV-01 v1 is received **21 Jul 2027, 08:05 EAT**, corrected v2 received **21 Jul 2027, 10:00 EAT**, with original receipt retained. Charles signs certification at 10:15; Josphat submits the accounting invoice at 11:00 and Beatrice posts it at 11:30 through D33; Josphat prepares the payment entry **22 Jul 2027, 13:00**; Beatrice approves the native entry **22 Jul 2027, 14:15**. Settlement confirmation **23 Jul 2027, 10:00** gives KES 800,000 cash. Replacement units 011/012 arrive **27 Jul 2027, 09:00**, are accepted **27 Jul 2027, 15:30**, and posted 15:31, linked to original rejected units 009/010; source quantity remains 10. A separate eligible invoice INV-02 for KES 200,000 remains unpaid in D15. The completed branch confirms it at **2 Aug 2027, 10:00**, giving total cash KES 1,000,000. The ordinary branch’s final acceptance is recorded by Amina **28 Jul 2028, 08:30**, completion certificate signed/delivered **09:00/09:05**, closure **10:00**. The timing is fixture data, not a legal deadline.

**Isolated identity overrides.** D20/P/T, D11-T and D39-P/D39/C use CM-MOH-2027-TERM-001. The first eight units were accepted 20 Jul 2027; their supported KES 800,000 is settled by KES 600,000 confirmed 2 Aug and KES 200,000 confirmed 19 Aug. Units 9/10 were never delivered or accepted; no base replacement receipts or INV-02 are inherited. Default notice/cure evidence is complete before the 10 Aug review; notice delivered/effective 10 Aug 11:00. The final unperformed KES 200,000 is extinguished under the reviewed termination outcome, with Budget adjustment/reconciliation evidenced by 20 Aug. D20-P is the 10:15 pre-delivery state; D20-T/D11-T are the 11:00 effective state. D16 uses SEC-RETURN-001, D16-W/P and D11-B WAR-OPEN-001; D35/V/C/H WAR-001, and D25 SEC-VERIFY-001; these cases never import base security, warranty, acceptance or cash facts. All D37 variants retain SEC-001 and its distinct TEST-SG instruments. Every inherited header uses the brief’s resolved contract identity rather than the global base reference.

**Extension identity and chronology.** D27/R/A and D14/P share **CM-MOH-2027-EXTENSION-001**, issued source **EXTENSION-TERMS-01**, agreement 1 and change 1. Source terms are 10 laptops / KES 1,000,000 / delivery due 20 Jul 2027; no advance or performance security. Mary signs agreement 1 on 2 Jul at 10:05 EAT and Amina at 10:30; it is Active from 10:30. No delivery or acceptance has occurred at the 18 Jul request or 19 Jul decision/signing views. D27 is the request at 18 Jul 10:00; D27-R follows the current reviewers’ recommendation at 11:00; D14 is AO review at 19 Jul 10:00; approval is recorded at 10:15, yielding D14-P. D27-A is Mary’s amendment 1 signing task at 11:00; Mary signs at 11:05 and Amina at 11:30. Only both required signatures make amendment 1 effective at 11:30 and change the due date to 27 Jul; approval alone leaves 20 Jul operative. This successful fixture later records delivery of all 10 units on 27 Jul at 09:00, with acceptance not yet established at that instant. It never inherits the base 20 Jul delivery, rejection/replacement history, invoices, cash settlements, final acceptance or closure. Declined/returned variants do not inherit the successful approval/signature/effectiveness events.

**Open warranty identity.** D16-W/P, D11-B and D32-H share **CM-MOH-2027-WAR-OPEN-001**, source **WAR-OPEN-TERMS-01**, agreement 1 / claim 1, unit **CM-WAR-OPEN-004**. The defect notice is timely on 10 Jul 2028; the remedy remains pending on 21 and 28 Jul. These branches never inherit D35’s 15 Jul remedy or the base completed story. D35/V/C/H retain **CM-MOH-2027-WAR-001**, unit **CM-WAR-004**, and its distinct resolved-remedy chronology. D16 uses **TEST-G-RETURN-001**; D25/R/J retains **TEST-G-001** on SEC-VERIFY-001, with its own confirmation/expiry and no D16 discharge.

**Expanded Evidence and history** shows only the named links and the exact events supplied for that brief/branch. Default is closed; material reasons and quantity/financial differences are never hidden in it. Common tabs are Agreement, Deliveries, Invoices, Obligations, History; selected tab: D02/D03/D12 Agreement; D04–D07/D19 Deliveries; D08/D09/D17/D18/D21/D33 Invoices; D10/D11/D13–D16/D20/D22 Obligations. D01 is a workspace and has no case tabs. D21’s selected Invoices tab is a cutover financial comparison, not a new accounting screen.

### 10.2 Main screen briefs

#### D01 — Contract list; Work workspace archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, site HOP, 2 July 2027 09:01 EAT. Primary question: what requires attention? Title **Contracts**; header action **Register existing contract**. Columns **Contract**, **Supplier**, **Status**, **Next action**, **Responsible person**. One row: CM-MOH-2027-001 / Afya Digital Supplies Limited / Preparing / Prepare contract / Charles Mutiso. View selector **My work** selected, alternative **All contracts**; Search text field **Search contracts** is empty; status filter **All statuses**, source **All sources**, responsible person **All people**, managing unit **All units**. Only Search and Status are expanded initially. Source, Responsible person and Managing unit are in the closed **Filters** disclosure. Choice values: statuses Preparing, Awaiting signatures, Active, Closed, Did not proceed, Terminated; sources KenTender award, External records, eGP; responsible people Brian Wafula, Charles Mutiso, Julia Njeri, Peter Mugo, Grace Wanjiku, Amina Hassan, Josphat Mwangi, Beatrice Kamau; managing unit Digital Health (OU-MOH-DHI). These are fixture-permitted values, not a global people directory. Row link **Open contract**. No next-step block or journey on this list. The next action must be understandable without opening the row.

**Resolved state cards.** Use the Guidance column as the only next-step block; facts/actions replace the normal card.

| Artboard | Guidance / persona context | Facts and actions |
|---|---|---|
| D01-E | Use the exact state message in Facts and actions; no extra block. | No rows. “No contracts are available.” Search/filter and Register existing contract remain; no next-step block. |
| D01-F | Use the exact state message in Facts and actions; no extra block. | Search `unknown`; “No contracts match your search.” Clear search is the only additional action. |
| D01-T | D01 All contracts with Administrator/Daniel or Naomi at 3 Aug 2027 12:00, full permitted register read. Register existing contract absent; My work view empty; no next-step block or tracker. | Normal authorised facts retained; no new controls. |
| D01-AUD | D01 All contracts with Administrator/Daniel or Naomi at 3 Aug 2027 12:00, full permitted register read. Register existing contract absent; My work view empty; no next-step block or tracker. | Normal authorised facts retained; no new controls. |

#### D02 — Prepare agreement; Record detail archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Brian, separately authorised preparer, 2 July 09:15; agreement draft 1. Title **Prepare contract**. Next step: **Review the contract and send it for signature.** Holder Brian Wafula. First region: summary KES 1,000,000; delivery 20 July 2027; warranty 12 months; security **Not required under these test terms**. Second: read-only **Agreement summary**, with the facts above and **View agreement 1**. No missing particulars in this state. Primary **Send for signature** in the task footer; secondary **View award**. Evidence: **Award package 1**, **Issued terms 1**. CM-TPL-01 blocks the full legal-document preview. For this review artboard show the exact summary above and the link **View agreement 1**; do not draw invented contract text. Signing-document design acceptance remains blocked until the source-rendered artifact is supplied.

**Resolved state cards.** Use the Guidance column as the only next-step block; facts/actions replace the normal card.

| Artboard | Guidance / persona context | Facts and actions |
|---|---|---|
| D02-H | Use the exact state message in Facts and actions; no extra block. | “Contract signing is on hold.” Charles Mutiso; “An award restriction requires review.” Only View issue and View award; Send for signature absent. |
| D02-S | Waiting on someone — Technical operator Daniel Otieno is restoring signing; incident assigned 2 Jul 2027, 09:20 EAT. Holder Daniel. | Signing unavailable; work saved. Daniel Otieno; View update status and Back to contracts only; no new signature attempt. |

#### D03 — Supplier signature; Review or decision archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Mary Wanjiku, authorised signatory for Afya, 2 July 10:00; frozen agreement 1. Title **Sign contract**. Next step: **Review the agreement before signing.** Holder Mary Wanjiku. Visible summary: **KES 1,000,000; delivery due 20 Jul 2027; warranty 12 months; security Not required under these test terms**. **View agreement 1** opens the frozen version; no invented agreement text. Primary **Sign contract**; secondary **Report a problem**. No other bidders, internal findings or Finance details. Evidence: **Agreement 1**. The signing result uses the adjacent D03-W state.

**Resolved state cards.** Use the Guidance column as the only next-step block; facts/actions replace the normal card.

| Artboard | Guidance / persona context | Facts and actions |
|---|---|---|
| D03-W | Waiting on someone — Accounting Officer Amina Hassan must sign agreement 1; assigned 2 Jul 2027, 10:05 EAT. Holder Amina. Supplier proof remains in the record, not repeated in the guidance line. | Amina Hassan; read-only View agreement and Back to my contracts. |
| D03-A | Use the exact state message in Facts and actions; no extra block. | Amina’s internal entity-signatory view; Mary Signed; Amina Awaiting signature. “Review agreement 1 and sign for the entity.” Sign contract; Report a problem; Back to contracts. |

#### D04 — Receive goods; Form or editor archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Grace Wanjiku, separately authorised receiver, 20 July 09:00; arrival draft 1. Title **Record delivery**. Next step: **Record the goods that arrived.** Holder Grace Wanjiku. First region: delivery due 20 July, destination **ICT receiving area**. Entry fields: Supplier delivery reference `AFYA-DN-01` (text); Received at `20 Jul 2027, 09:00 EAT` (datetime); Destination `ICT receiving area` (authorised destination select). Item table columns Item / Expected / Arrived / Unit references: Laptop / 10 / 10 / `CM-DEMO-001`–`CM-DEMO-010`. Arrived is numeric; **Enter unit references** opens a ten-line text dialog prefilled with the expanded consecutive values. Primary **Record delivery**; secondary **Cancel**. Help: **Recording delivery does not accept the goods.** Evidence: **Delivery schedule 1**. Table is necessary to compare expected and observed quantities.

**Local fields and dialogs.** **D04 unit-reference dialog**, titled **Unit references**, has ten separate lines, in order: CM-DEMO-001, CM-DEMO-002, CM-DEMO-003, CM-DEMO-004, CM-DEMO-005, CM-DEMO-006, CM-DEMO-007, CM-DEMO-008, CM-DEMO-009, CM-DEMO-010. Editable text area, **Use references** primary, **Cancel** secondary. Use references updates the local arrival draft only. Duplicate/blank lines remain a validation issue.

#### D05 — Inspect delivery; Review or decision archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Peter Mugo, separately appointed inspector, 20 July 11:00; arrival 1, observations 1. Title **Inspect delivery**. Next step: **Complete the missing observations.** Holder Peter Mugo. Coverage **10 laptops; each unit inspected**. Comparison columns Check / Required / Observed / Result: RAM / At least 16 GB / 16 GB on all 10 / Meets; Storage / At least 512 GB / 512 GB on all 10 / Meets; Starts successfully / Yes / 8 Yes; 2 not recorded / Needs review. Primary **Record observations** opens unit rows 009/010 with **Starts** select Not recorded/Yes/No (Not recorded selected) and Evidence text/link; **Save observations** and **Cancel**. Secondary **View all observations** opens the ten-unit detail; no free criterion editor. Evidence: **Arrival 1**, **Contract requirements 1**. Missing observations remain visually prominent. Next-step kind **Your turn**: Peter can complete the observations now. D05-M alone is blocked by unreadable evidence; missing observations by themselves do not make the normal observation-entry task blocked.

**Local fields and dialogs.** **D05 full observation detail**, initially opened by View all observations, has columns Unit / RAM (GB) / Storage (GB) / Starts / Evidence. Rows 001–008 each carry 16 / 512 / Yes / Test log 20-Jul-01; row 009 carries 16 / 512 / Not recorded / Test log 20-Jul-09; row 010 carries 16 / 512 / Not recorded / Test log 20-Jul-10. Prefix every row’s unit with CM-DEMO-. The only editable missing-observation dialog rows are CM-DEMO-009 and CM-DEMO-010, Starts select options Not recorded, Yes, No (Not recorded selected), Evidence reference text prefilled with those test-log references. Save observations / Cancel. D06’s successor records No for both with evidence retained, rather than manually selecting Fail. A read-only **Technical certificate** summary and the signed acceptance report are separate versions/outputs.

**State cards — replace normal facts/actions.**

| Artboard | Visible change and actions |
|---|---|
| D05-M | Required evidence unreadable. “The inspection evidence needs review.” Peter Mugo; Record observations and View all observations remain; no acceptance action. |

#### D06 — Acceptance review; Review or decision archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Julia Njeri, separately appointed chair, 20 July 14:00; report draft 1. Title **Review inspection**. Next step: **Prepare the acceptance report.** Holder Julia Njeri. Summary: Delivered 10; Meets 8; Does not meet 2; Needs review 0. Unit rows 009 and 010: Starts successfully / Required Yes / Observed No / Does not meet. Quantity disposition: Accepted 8; Rejected 2; Deferred 0. Reason **Two laptops did not start during inspection. Replacement is required.** Primary **Prepare report for signing**; secondary **View observations**. Disclosure **Report preview**, initially open, shows generated findings, quantity disposition, reason and signer names Julia Njeri, Peter Mugo, Brian Wafula. Above the footer, read-only technical evidence **Technical certificate 1 — signed by Peter Mugo, 20 Jul 2027, 13:35 EAT**. Required quantities and the failed start reason remain visible outside the disclosure. Evidence: **Inspection 1**. No confirm-each-check action.

#### D07 — Acceptance signature; Review or decision archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Brian Wafula, separately appointed member, 20 July 14:30; frozen report 1. Title **Sign acceptance report**. Next step: **Review and sign report 1.** Holder Brian Wafula. Visible findings: Delivered 10; Meets 8; Does not meet 2; Needs review 0. Units CM-DEMO-009/010 failed to start; Accepted 8 / Rejected 2 / Deferred 0. Report reason **Two laptops did not start during inspection. Replacement is required.** Signatures: Julia Njeri Signed; Peter Mugo Signed; Brian Wafula Awaiting signature. Primary **Sign report**; secondary **Request correction** opens required Reason textarea with **Send request** / **Cancel**. Report preview is open; evidence is subordinate. Technical certificate 1 was signed by Peter Mugo at 13:35 EAT; Julia signed report 1 at 14:10, Peter at 14:15; Brian is signing at 14:30. These are separate attributable acts. A signature belongs to this exact report, not a generic approval checkbox.

**Resolved state cards.** Use the Guidance column as the only next-step block; facts/actions replace the normal card.

| Artboard | Guidance / persona context | Facts and actions |
|---|---|---|
| D07-P | Waiting on someone — Technical operator Daniel Otieno is restoring the stock update; incident assigned 20 Jul 2027, 14:31 EAT. Holder Daniel. | All report signatures complete. Daniel Otieno; View update status and View report only. |

#### D08 — Invoice review; Review or decision archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, authorised certifier for the fixture, 21 July 09:00; claim INV-01 version 1. Title **Review invoice**. Next step: **Resolve the quantity difference.** Holder Charles Mutiso. Comparison columns Item / Invoiced / Eligible / Rate / Claimed / Supported: Laptop / 10 / 8 / KES 100,000 / KES 1,000,000 / KES 800,000. Message **Two laptops have not been accepted.** Primary **Request correction**; secondary **View acceptance report**. No Sign certification action. Correction dialog: recipient Afya (read-only), message **Please correct the invoice to match the eight accepted laptops.**; **Send request** / **Cancel**. Evidence: **Supplier invoice INV-01**, **Acceptance report 1**, **Receipt 1**. The fixture assumes no partial certification of this disputed invoice; a corrected claim follows.

**State cards — replace normal facts/actions.**

| Artboard | Visible change and actions |
|---|---|
| D08-C | Corrected claim version 2: Invoiced 8; Eligible 8; Claimed/Supported KES 800,000. “Review and sign the certification.” Charles; Sign certification and View acceptance report. No request to repeat individual matches. |

#### D09 — Payment follow-up; read-only Record detail archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Contract owner Julia Njeri, 23 July 09:00; corrected claim INV-01 version 2, KES 800,000. Title **Invoice and payment**. Next step: **Finance is confirming payment.** Holder Beatrice Kamau. Vertical facts: Invoice KES 800,000; Certification Signed; Accounting entry Posted; Payment KES 800,000 recorded; Settlement Not confirmed. No mutation action. Secondary **View payment record**, **View certification**. Evidence: **Payment entry 1**, **Certification 1**. Do not display Paid or Complete.

**Exact guidance and reader states.** The following is the single guidance line for that state, replacing any shorter normal/state wording above.

| Artboard | Kind / headline / holder |
|---|---|
| D09 | Waiting on someone — Finance approver Beatrice Kamau must confirm payment; assigned 22 Jul 2027, 14:15 EAT. Holder Beatrice. |
| D09-T | D09 with Administrator/Daniel or Naomi at 23 Jul 2027 09:00. Same permitted business facts, no mutation; Not involved, guidance block absent. Evidence remains read-only and credentials excluded. |
| D09-AUD | D09 with Administrator/Daniel or Naomi at 23 Jul 2027 09:00. Same permitted business facts, no mutation; Not involved, guidance block absent. Evidence remains read-only and credentials excluded. |

#### D10 — Contract obligations; Record detail.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Julia, 23 July 09:15. Title **Remaining obligations**. Next step: **Follow up the replacement delivery.** Holder Julia Njeri. Leading-task context: **Replacement of units CM-DEMO-009/010; due 27 Jul 2027; awaiting supplier**. Render one **Other work** table, columns Task / State / Due / Responsible person / Action: **Payment confirmation / Waiting / 23 Jul 2027 / Beatrice Kamau / Open**; **Warranty for eight accepted units / Scheduled / 20 Jul 2028 / Julia Njeri / Open**. This is the D40 shared region; do not append another obligation/task table containing the same rows. The underlying warranty is Active; Scheduled is its follow-up task state, not a change to warranty status. Primary **Open replacement issue**; secondary **View agreement**. No close-out action. Evidence: **Issue 1**, **Agreement 1**. Dates are isolated fixture terms, not universal statutory deadlines.

#### D40 — Other work; contract record variant.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Julia, 23 Jul 2027 09:15, base Active contract, Obligations tab. Leading task Follow up replacement delivery due 27 Jul; Other work uses the same single table as D10: Payment confirmation / Waiting /23 Jul 2027 /Beatrice Kamau/Open; Warranty for eight accepted units / Scheduled /20 Jul 2028/Julia Njeri/Open. D40 demonstrates D10’s shared simultaneous-work region and reader variants, not a second panel. Leading replacement follow-up is excluded from Other work. The warranty itself remains Active; Scheduled describes the follow-up task. This does not grant Julia Finance mutation.

D40-AO: Amina same instant; all five tabs and read-only contract context visible, no personal task block, no signing/Finance controls without a current subject; open payment follow-up shows authorised status and cash, protected account/bank detail absent.

D40-HOD: Julia Njeri with a separately isolated Active Head of User Department assignment to Digital Health only, 23 Jul 2027 09:15, same case through managing/source involvement; same contractual totals, only own source allocation detail.

D40-D: Grace Wanjiku with only her canonical Departmental Author assignment and no receiver authority, 23 Jul 2027 09:15; shared denial, no record facts.

D40-F: Josphat Mwangi, 23 Jul 2027 09:15, sees permitted Finance context and his own preparation tasks; no approver action.

D40-T: Daniel Otieno, 23 Jul 2027 09:15;

D40-AUD: Naomi, authorised site-wide auditor, same instant; both read permitted facts without task controls.

D40-S: David Ouma, same instant, supplier representative; supplier Other work lists only own replacement remedy due 27 Jul 2027, current holder David, View issue, never internal Finance tasks. These explicit isolated actors/scopes must be bound in the seed; no designer invents an appointment or responsibility.

#### D11 — Close-out review; Review or decision archetype.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Amina, authorised AO, 28 July 2028 10:00; closure draft 1 in isolated completed branch. Title **Close contract**. Next step: **Review and sign the close-out record.** Holder Amina Hassan. Summary: 10 accepted; KES 1,000,000 invoiced; KES 1,000,000 confirmed cash paid; zero balance; warranty ended with no unresolved claim; security not required; required reporting complete. Completion certificate reference **Certificate 1**. Primary **Sign close-out**; secondary **Return for correction** with Reason / **Return** / **Cancel**. Evidence: **Completion certificate 1**, **Financial reconciliation 1**. This isolated branch has completed all contractual obligations; it is not a universal warranty-expiry closure rule.

**Resolved state cards.** Use the Guidance column as the only next-step block; facts/actions replace the normal card.

| Artboard | Guidance / persona context | Facts and actions |
|---|---|---|
| D11-B | Use the exact state message in Facts and actions; no extra block. | Override to CM-MOH-2027-WAR-OPEN-001 / claim 1, 21 Jul 2028 09:00 EAT; completion review remains blocked pending the surviving remedy. Replace the base warranty-ended/no-claim summary with Warranty expired; timely claim remains open; no completed base closure is inherited. Open warranty claim for unit CM-WAR-OPEN-004. “Resolve the remaining claim before close-out.” Julia; View claim and View remaining obligations only. Sign close-out absent. |
| D11-C | Done — Amina Hassan closed the contract on 28 Jul 2028, 10:00 EAT. No live holder or action. | Read-only View close-out record and View history; no next action owner or live tracker. |
| D11-T | Waiting on someone — Finance approver Beatrice Kamau is settling KES 200,000; assigned 10 Aug 2027, 11:00 EAT. Lifecycle Terminated, holder Beatrice. | Override contract to CM-MOH-2027-TERM-001, 10 Aug 2027 11:00 EAT; 8 accepted units, accepted obligation KES 800,000, cash KES 600,000, supported unpaid KES 200,000; no warranty-completed/10-unit/base-close-out summary. Lifecycle Terminated; Beatrice; View termination record and View settlement only. Never show Completed. |

### 10.3 Required variants

Use the adjacent normal/state cards with the one shared shell. The exact state’s facts and actions replace the normal ones. No hidden alternate business action is implied.

The state cards are placed directly beneath their task family in §§10.2/10.4/10.5/10.7/10.8. They are artboard alternatives, not additional application pages. Shared error/denial pages below use no normal task facts.

| Shared page | Exact content/actions |
|---|---|
| D-ERR | Content load fails: “This record could not be loaded.” Retry and Back to contracts; no stale business action. |
| D-DENIED | Shared KT-STD §3A denial page; “You do not have access to this contract.” Back to contracts only; no protected content. |

The additional review briefs below complete the issue/change/reporting, Finance and independent-entry compositions. Source-rendered legal-document previews remain CM-TPL-01; this draft must not be represented as a final design input pack until that specific gap is closed.

### 10.4 Additional task and exception briefs

#### D01-S — My contracts; Register.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Mary Wanjiku, supplier signatory, 2 July 2027 10:00, supplier list. Question: which contract needs my action? Title **My contracts**. Read-only list with row CM-MOH-2027-001 / IT equipment delivery / Awaiting signatures / Sign contract. Primary row link **Open contract**. Search **Search contracts**, empty; no internal owners/Finance balances. No next-step block or tracker. D01-S-E replaces the row with **No contracts are available.** All other content unchanged.

#### D12 — Existing contract; Form or editor.

**Fixture:** CM-MOH-2027-EXT-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Brian, authorised preparer, 3 August 2027 09:00, isolated CM-MOH-2027-EXT-001 draft 1, title **Register existing contract**, state Preparing. Action block **Record the signed contract and its current position.** Holder Brian Wafula. Top region: Source **External records** (select: External records, eGP); Source contract reference **MOH/ICT/2027/EXT-01** (text); Supplier **Afya Digital Supplies Limited** (verified supplier select); Signed agreement **Agreement EXT-01** (file link); Amendments **None**; Signed on **2 July 2027**, Effective on **2 July 2027**, Cutover **3 August 2027, 00:00 EAT** (date/date/datetime). Middle region: original/current value KES 1,000,000; currency KES fixed. Item table Laptop / 10 / Each / KES 100,000 / tax included; serial-tracked Yes. Terms summary: delivery 20 July 2027; acceptance each unit inspected against 16 GB RAM, 512 GB storage and successful start; payment within 30 days of correct invoice and eligible acceptance; warranty 12 months per accepted unit; security not required under test terms; advance not provided; restrictions None recorded; completion after all contractual obligations. These are synthetic terms, not legal defaults. **View source clauses** expands exact locators Agreement EXT-01 §§2–8, with the foregoing matching values. Primary **Save and review**; secondary **Cancel**. Evidence: Agreement EXT-01. No Sign contract action.

**Local fields and dialogs.** At 3 Aug 2027, Source select External records/eGP defaults External records; Supplier select contains Afya Digital Supplies Limited only in this scoped fixture. Original value/current value numeric KES 1,000,000; item description Laptop (text), quantity 10 (decimal), UOM Each (select), rate KES 100,000 (money), tax treatment Included (select: Included, Excluded), serial tracking Yes (read-only imported fact). Named owner Julia Njeri; Managing unit Digital Health; supplier signatory Mary Wanjiku, entity signatory Amina Hassan, both signed on 2 Jul 2027, actual effectiveness 2 Jul 2027. Review regime **Kenya public procurement — applicability review pending** (read-only), source clause reference text **Agreement EXT-01 §§2–8**. Entered operative terms use date fields for delivery, integer field 30 for contractual payment days, integer 12 for warranty months, read-only no-advance/no-security terms pending source verification. Do not add a live statutory-rule selector. Opening fields: accepted 4, in custody 2, invoiced KES 400,000, credits KES 0, confirmed cash KES 300,000, outstanding KES 100,000, advance KES 0; references Linked receipt 1, Linked invoice 1, Linked payment and settlement 1. Those are draft entered facts, not confirmed native balances until D21. Unknown values stay blank with **Not established**; eGP variant requires **eGP tender reference** and **eGP contract reference**, and labels its evidence **Recorded from external source**. No eGP verification badge.

#### D13 — Delivery issue; Record detail.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Julia, contract owner, 20 July 2027 15:00, issue 1 version 1, Active. Title **Two laptops need replacement**. Action **Send the inspection findings to the supplier.** Holder Julia Njeri. Facts: units CM-DEMO-009 and CM-DEMO-010; result Does not meet; observed Both units failed to start; requested remedy Replacement; requested reply date 22 July 2027. Message textarea prefilled **Two laptops did not start during inspection. Please arrange replacement and confirm the delivery date.** Primary **Send message**; secondary **View acceptance report**. Evidence: Acceptance report 1; Inspection 1.

D13-S: David, supplier representative, 21 July 09:00, same issue with message delivered; Action **Reply to the replacement request.** Holder David Ouma; reply textarea **We will deliver two replacement laptops on 27 July 2027.**; primary **Send reply**; View acceptance report secondary.

D13-C: Julia, 27 July 16:00, Closed issue; no reply field; **This issue is closed.** Resolution **Replacement units 011 and 012 were accepted on 27 July 2027.** No action holder; **Report a new issue** and **View replacement acceptance** secondary.

#### D14 — Extension review; Review or decision.

**Fixture:** CM-MOH-2027-EXTENSION-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Amina, AO, 19 July 2027 10:00, isolated **CM-MOH-2027-EXTENSION-001 / agreement 1 / change 1 draft 1**, Active. Title **Review delivery extension**. Action **Decide the requested delivery date.** Holder Amina Hassan. Comparison table: Delivery date / 20 July 2027 / 27 July 2027; Contract value / KES 1,000,000 / KES 1,000,000; Quantity / 10 / 10. Reason **Supplier requests seven additional days because the shipment was delayed.** Recommendation **Approve the revised date; no price change.** Evidence shown by links: Supplier request 1; Technical review 1; Current committee recommendation 1; Legal review 1. Primary **Approve extension**; secondary **Decline**, **Return for correction**. Each opens a decision dialog with Reason textarea, entered value **The documented grounds support the revised date without changing price or quantity.** for approval; Confirm decision / Cancel. D14-P shows approval recorded but amendment not effective: Waiting on someone **The supplier’s amendment signature is pending.** Holder Mary Wanjiku; only View amendment and View decision. No edited operative due date shown until effectiveness.

**Exact guidance and reader states.** The following is the single guidance line for that state, replacing any shorter normal/state wording above.

| Artboard | Kind / headline / holder |
|---|---|
| D14-P | Waiting on someone — Supplier signatory Mary Wanjiku must sign amendment 1; assigned 19 Jul 2027, 10:15 EAT. Holder Mary. |

#### D15 — Contract reporting; Record detail.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, HOP, 1 August 2027 09:00, July progress report draft 1. Title **Monthly contract progress**. Action **Review and submit the July report.** Holder Charles Mutiso. One row: CM-MOH-2027-001 / IT equipment delivery / KES 1,000,000 / 2 July 2027 / Active / Cash confirmed KES 800,000 / Expected completion 27 July 2028. Read-only below: **10 laptops accepted; 2 were replacement units. Unpaid KES 200,000; no noncash adjustment. No open delivery issue.** Column labels Contract / Title / Contract value / Commenced / Status / Cash confirmed / Expected completion. This single report row is a statutory/management output, not the operational record layout. Primary **Submit report**; secondary **View contract**. Recipient Amina Hassan, read-only. Evidence: Agreement 1; Finance reconciliation 2. D15-L is a separate obligation detail, Charles at 2 July 2027 11:00, title **Publication requirement needs review**; state Needs review; Your turn, blocked **The applicable publication deadline needs confirmation.** Holder Charles Mutiso. Trigger **Award decision recorded 17 Jun 2027, 10:00 EAT** in this isolated source; separate fact **Contract signed 2 Jul 2027, 10:30 EAT**. Deadline **Not confirmed**; responsible review **Legal-rule owner**. Primary **Record source evidence** opens fields Source reference (text, empty), Dated (date, empty), Copy (file, empty), Notes (textarea, empty); Save evidence / Cancel. It records proposed evidence for the legal owner, not an executable rule, officer-authored deadline or verified status. Secondary **View source event**, **View signing record**. No fourteen-day countdown; signing cannot erase the earlier event.

#### D16 — Security follow-up; Record detail.

**Fixture:** CM-MOH-2027-SEC-RETURN-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, HOP, 1 August 2027 09:30, isolated CM-MOH-2027-SEC-RETURN-001 / agreement 1, Active. Title **Performance security**. Action **Record the security return.** Holder Charles Mutiso. Instrument TEST-G-RETURN-001; guaranteed amount KES 100,000; final acceptance 27 July 2027; return due 26 August 2027; status Return due. Return date date-field **1 August 2027**; evidence file **Bank discharge TEST-G-RETURN-001**; primary **Record return**; secondary View guarantee. This branch has synthetic terms requiring security, with TEST-G-RETURN-001 verified by Charles on 3 Jul 2027 at 09:00 EAT; Mary signs agreement 1 on 3 Jul at 10:05 and Amina on 3 Jul at 10:30, which is the recorded effectiveness instant. This independent formation sequence overrides the base 2 Jul signing dates. At return there is no open claim or continuing secured obligation. Source clause TEST-SEC-RETURN-01 permits the stated return after evidenced final acceptance. Do not borrow D25’s separate instrument or expiry. These dates are illustrative, pending CM-LEGAL-01; security return is not universally tied to warranty expiry.

D16-W: Julia, 10 July 2028 09:00 EAT, separate CM-MOH-2027-WAR-OPEN-001 / agreement 1, warranty claim 1, Active; title **Warranty claim**; Action **Send the defect notice.** Unit CM-WAR-OPEN-004, accepted 20 Jul 2027 under this branch’s source WAR-OPEN-TERMS-01; fault **Battery does not charge**; warranty ends 20 July 2028; evidence Diagnostic 1; notice textarea same fault; primary Send notice; View warranty secondary. D16-P inherits CM-MOH-2027-WAR-OPEN-001 / claim 1 at 21 Jul 2028 09:00 EAT and keeps the claim open after expiry with **The supplier’s remedy is pending.** Waiting, holder David Ouma; View notice and View claim history only. D16-W/P carry no performance-security instrument; their open claim is not present in the base D11/D32 closure branch. D32-H continues this same open-claim contract at 28 Jul 2028, 08:30 EAT; no resolved D35 history is inherited.

**Exact guidance and reader states.** The following is the single guidance line for that state, replacing any shorter normal/state wording above.

| Artboard | Kind / headline / holder |
|---|---|
| D16-P | Waiting on someone — Supplier representative David Ouma must respond to the warranty remedy; requested 10 Jul 2028, 09:10 EAT. Claim remains open in the isolated post-expiry view at 21 Jul 2028, 09:00. |

#### D18 — Supplier invoice; Form or editor.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

David, supplier representative, 21 July 2027 08:00, invoice draft 1, Active. Title **Submit invoice**. Action **Enter the invoice details.** Holder David Ouma. Fields Invoice number INV-01 (text), Invoice date 21 July 2027 (date), Invoice file Supplier invoice INV-01 (file). Item row Laptop / Quantity 10 / Rate KES 100,000 / Tax Included / Total KES 1,000,000. Primary **Submit invoice**; secondary Cancel. Evidence Agreement 1. D18-R retains the claim with Status Needs review and message **Two laptops have not been accepted.** Waiting, holder Charles Mutiso; View invoice and View acceptance only. D18-C is supplier correction: title Correct invoice, Action **Correct the invoice quantity.** Holder David; prior version 1 preserved; editable quantity 8, total KES 800,000; Reason **Corrected to the eight accepted laptops.** Primary **Submit correction**; secondary Cancel.

**Exact guidance and reader states.** The following is the single guidance line for that state, replacing any shorter normal/state wording above.

| Artboard | Kind / headline / holder |
|---|---|
| D18-R | Waiting on someone — Procurement head Charles Mutiso must review the invoice; assigned 21 Jul 2027, 08:05 EAT. Holder Charles. |

#### D19 — Technical certificate; Review or decision.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Peter, appointed technical member/certifier, 20 July 2027 13:30, certificate 1 draft 1, Active. Title **Confirm technical inspection**. Action **Review and sign the technical certificate.** Holder Peter Mugo. Exact document summary: Contract CM-MOH-2027-001; inspected 10; conforms 8; fails 2; missing evidence 0; test RAM ≥16 GB, storage ≥512 GB, successful start; units 009/010 failed start. Recipient Amina Hassan. Primary **Sign technical certificate**; secondary Request correction. Evidence Inspection 1. The generated certificate reuses the recorded findings; no re-entry of measurements.

#### D20 — Termination review; Review or decision.

**Fixture:** CM-MOH-2027-TERM-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Amina, AO, 10 August 2027 10:00, isolated CM-MOH-2027-TERM-001 / agreement 1 / termination 1 draft 1, Active. Title **Review contract termination**. Action **Decide the termination request.** Holder Amina Hassan. Facts: material non-delivery; contractual notice completed in this synthetic branch; accepted value KES 800,000; cash paid KES 600,000; supported unpaid amount KES 200,000; advance balance KES 0; disputed claim KES 0. HOP recommendation Terminate unperformed balance. Evidence Contract clause 8; Default notice and delivery proof; Cure-period record; Legal advice 1; Settlement calculation 1. Primary **Approve termination**; secondary Decline and Return for correction, with required reason dialog.

D20-P: approved notice awaiting delivery, Waiting on someone **The termination notice has not been delivered.** Holder Charles Mutiso; View notice and View delivery status.

D20-T: effective termination, Waiting on someone **Finance is settling the accepted delivery.** Holder Beatrice Kamau; lifecycle Terminated; no Complete contract action.

**Exact guidance and reader states.** The following is the single guidance line for that state, replacing any shorter normal/state wording above.

| Artboard | Kind / headline / holder |
|---|---|
| D20-T | Waiting on someone — Finance approver Beatrice Kamau is settling KES 200,000; assigned 10 Aug 2027, 11:00 EAT. Lifecycle Terminated, holder Beatrice. |
| D20-P | Waiting on someone — Procurement head Charles Mutiso must deliver the termination notice; assigned 10 Aug 2027, 10:15 EAT. Holder Charles. |

#### D21 — Opening position; Review or decision.

**Fixture:** CM-MOH-2027-EXT-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Beatrice, Finance approver, 3 August 2027 10:00, external case EXT-001 intake version 1, Preparing. Title **Review prior activity**. Action **Confirm the opening position.** Holder Beatrice Kamau. Comparison rows: Accepted units / Source 4 / Native linked 4; In custody / 2 / Custody record 2; Invoiced / KES 400,000 / KES 400,000; Cash paid / KES 300,000 / KES 300,000; Outstanding / KES 100,000 / KES 100,000; Advance / KES 0 / KES 0. Primary **Confirm opening position**; secondary Report difference. Evidence External acceptance 1; Linked receipt 1; Linked invoice 1; Linked payment and settlement 1.

D21-H: Charles, 3 August 11:00, opening confirmed; Action **Start managing this contract.** Holder Charles; source/terms Checked; opening Confirmed; next work Inspect two units in custody; primary Start management; secondary View source contract. No posting or signing task is displayed as an intake result.

#### D22 — Completion certificate; Review or decision.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, HOP, 28 July 2028 09:00, completion certificate draft 1 in completed branch, Active. Title **Confirm contract completion**. Action **Issue the completion certificate.** Holder Charles Mutiso. Summary: 10 laptops delivered and accepted; initial 8 accepted 20 July 2027, replacement 2 accepted 27 July 2027; no contracted service line; no unresolved defects; final acceptance recorded; all obligations fulfilled; recipient Afya Digital Supplies Limited. Primary **Sign and issue certificate**; secondary View completion evidence. Evidence Final acceptance 1; Financial reconciliation 1.

D22-P: issue pending, Waiting on someone **The certificate has not been delivered.** Holder Charles; View delivery status and View certificate. D11 follows the completed issue in this isolated branch.

**Exact guidance and reader states.** The following is the single guidance line for that state, replacing any shorter normal/state wording above.

| Artboard | Kind / headline / holder |
|---|---|
| D22-P | Waiting on someone — Procurement head Charles Mutiso must confirm certificate delivery; assigned 28 Jul 2028, 09:00 EAT. Holder Charles. |

### 10.5 Additional reconciled briefs

Each base below inherits §§10.1/10.1A shared page shell, fixture label, heading/actions/evidence placement and explicit no-linear-tracker exception. The brief fixes the remaining actor, state, content, priority and variants; nothing is supplied from runtime §§5/7. **Level 1** is the stated task and material exception/amount; **Level 2** is the supplied comparison or working fields; **Level 3** is the named source/proof links, initially closed. No field is added by the designer. Newly specified dialogs are 520 px and use the same labels/content on their originating page.

#### D23 — Appoint inspectors; Review or decision.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Amina, AO, 3 Jul 2027 10:00, appointment proposal 1, base contract Active, Agreement tab. Title **Appoint inspectors**. Your turn **Review the proposed inspectors.** Holder Amina Hassan. Compact member list: Julia Njeri / Chair / User department; Peter Mugo / Member / Technical; Brian Wafula / Member / Procurement. Proposed period **3 Jul 2027–31 Jul 2028**; recommended by Charles **3 Jul 2027, 09:00**; recommendation reference **CM-APPT-01**. One primary **Appoint inspectors**; secondary **Return for correction**, **View recommendation**. Appointment dialog: From date **3 Jul 2027**, Until date **31 Jul 2028**; read-only generated appointment summary with names/capacities/period, **Appoint**, **Cancel**. Successful appointment generates reference **AO/CM/2027/001** and written record **Appointment CM-01** in this fixture; neither is typed or uploaded to perform a native appointment. Return dialog Reason empty, **Return**, **Cancel**. Evidence **Recommendation CM-01**. First-view acceptance: composition, period and personal authority are clear; declarations are not claimed complete.

D23-R: Charles, 3 Jul 09:00, draft recommendation; same members, editable member/capacity/period fields, primary **Recommend inspectors**, secondary Cancel.

D23-P: Charles, 3 Jul 10:05, recommendation/appointment complete, Waiting on someone **Peter Mugo must declare his interest; assigned 3 Jul 2027, 10:05 EAT.** Julia and Brian No conflict declared; Peter Declaration pending. No appoint button; View appointment secondary.

#### D24 — Declare interest; Form or editor.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Peter, appointed member, 3 Jul 2027 10:10, appointment 1, Active, Agreement tab. Title **Declare interest**. Your turn **Declare any conflict for this contract.** Holder Peter Mugo. Contract/supplier summary; radio choices **I have no conflict of interest**, **I have a conflict of interest**, neither selected. Description textarea visible in D24-C only, prefilled **A close family member works for the supplier.** Primary **Save declaration**, secondary **View appointment**. D24-C retains primary and a visible explanation **You will not be able to inspect or sign this contract while this conflict remains unresolved.**

D24-S: Peter, 10:11, No conflict saved; Done **Peter Mugo recorded his declaration on 3 Jul 2027, 10:11 EAT.** Read-only declaration, View appointment only.

D24-X: Charles, 10:12, isolated declared-conflict branch; Your turn, blocked **Peter Mugo must be replaced before the affected inspection can proceed.** Holder Charles; primary **Revise appointment recommendation**, secondary View declaration. No automatic substitute or sign-as-other-person control. Evidence Appointment CM-01 and Personal declaration 1.

#### D25 — Verify security; Review or decision.

**Fixture:** CM-MOH-2027-SEC-VERIFY-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, HOP, 2 Jul 2027 09:10, isolated pre-signing security branch, Preparing, Agreement tab. Contract **CM-MOH-2027-SEC-VERIFY-001**, agreement 1. Title **Verify performance security**. Your turn **Check the issuer’s confirmation.** Holder Charles Mutiso. Contract sum KES 1,000,000; test terms required KES 100,000; amount supplied KES 100,000; issuer **Test Bank**, beneficiary **Ministry of Health**, reference **TEST-G-001**, issued **1 Jul 2027**, expires **31 Aug 2028**. Source verification status **Confirmation received**; confirmation **TEST-CONF-01**, received **2 Jul 2027**. Primary **Verify security**, secondary **Reject security**, **View guarantee**. Verify dialog carries those confirmation facts and **Verify**, **Cancel**; rejection dialog Reason empty, **Reject**, **Cancel**. Evidence **Guarantee TEST-G-001**, **Issuer confirmation TEST-CONF-01**. These amount/expiry facts are synthetic issued terms, not a universal threshold/validity formula. D25-R, Charles 09:05: instrument not yet captured; title Record performance security, same instrument fields editable, attachment **Guarantee TEST-G-001**, primary **Save security**, secondary Cancel. D25-J, supplier David 09:15 after reason **The issuer could not confirm this instrument.**, Waiting on someone **Afya Digital Supplies Limited must supply a replacement security; requested 2 Jul 2027, 09:15 EAT.** Only View rejection and View contract. Rejected instrument remains history.

#### D26 — Record an outside signature; Form or editor.

**Fixture:** Isolated permitted outside-signing branch; no electronic-signing proof is inherited; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, HOP, 2 Jul 2027 10:10, isolated permitted outside-signing branch, Awaiting signatures, Agreement tab. Title **Record an outside signature**. Your turn **Record the supplier’s signed agreement.** Holder Charles. Fields Party select **Supplier** (other option Procuring entity), Signed by text **Mary Wanjiku**, Capacity text **Authorised signatory**, Signed on date **2 Jul 2027**, Signed copy **Signed agreement 1 — supplier**, Notes empty. Whole-document version **Agreement 1**, authority source **Afya assignment 1**, reviewed method **Outside signing permitted in these test terms**. Primary **Save signature evidence**, secondary **View agreement 1**. Save does not masquerade as a Trust electronic signature.

D26-H: mixed signed copies, Your turn, blocked **The signed copies do not match agreement 1.** Same entered facts preserved; primary **Record source evidence**, secondary View differences.

D26-E: Amina’s evidence subsequently recorded on the same complete version, HOP review at 10:35, title Check signed agreement, Your turn **Confirm the parties and signed version.** Primary **Confirm signature evidence**, secondary Report a problem. View links disclose both exact copies; their content remains subject to CM-TPL-01. No signature-provider success is fabricated.

#### D27 — Request a change; Form or editor.

**Fixture:** CM-MOH-2027-EXTENSION-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Julia, contract coordination, 18 Jul 2027 10:00, isolated **CM-MOH-2027-EXTENSION-001 / agreement 1 / change 1 draft 1**, Active, Obligations tab. Title **Request delivery extension**. Your turn **Explain the requested delivery date.** Holder Julia. Current delivery **20 Jul 2027**, proposed date **27 Jul 2027** (date), Reason textarea **Supplier reports a seven-day shipment delay.**, Supplier request file **Supplier request 1**; amount and quantity read-only **KES 1,000,000; 10 laptops; no price change**. Primary **Request extension**, secondary Cancel. Evidence Agreement 1.

D27-R: HOP Charles 18 Jul 11:00, review ready with Technical review 1, current committee Recommendation 1 and Legal review 1 retained; Your turn **Submit the supported request for decision.** Primary **Submit change for decision**, secondary Return for correction. This isolated reviewed route names Grace Wambui, Peter Mugo and Ruth Achieng as expressly appointed reviewers, not reused Evaluation appointments. Reviewer declarations No conflict and signed recommendation **Approve date extension without price change**, signed 18 Jul at 10:40/10:45/10:50 respectively, appointment reference **AO/VAR/2027/001**. Source test rule requires this review. D14 is the resulting decision view.

D27-A: Mary 19 Jul 11:00, approved but not effective, Your turn **Review and sign amendment 1.** Old/new dates 20/27 Jul; amount/quantity unchanged; primary **Sign amendment**, secondary Report a problem; View amendment 1. Amina receives the same whole-version signing task after Mary. Pending amendment never changes the operative date. Missing current reviewer appointment is a blocked variant with **Review authority needs confirmation**, Charles, View appointment only.

#### D28 — Partly paid invoice; Record detail.

**Fixture:** Isolated partial-payment branch; use TEST-PE-PART-01/02, no base settlement history; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Julia, contract owner, 23 Jul 2027 11:00, isolated partial-payment branch INV-01 v2, Active, Invoices tab. Title **Invoice and payment**. Waiting on someone **Finance approver Beatrice Kamau is following up the remaining KES 300,000; assigned 23 Jul 2027, 10:05 EAT.** Facts in compact vertical rows: Certified KES 800,000; Cash confirmed KES 500,000; Noncash adjustment KES 0; Outstanding KES 300,000; Invoice Partly paid. One settlement row TEST-PE-PART-01 / KES 500,000 / Confirmed 23 Jul 2027, 10:00 / TEST-BANK-PART-01. No mutation action; View certification, View settlement secondary.

D28-F: Josphat, Finance maker, 24 Jul 09:00, Your turn **Prepare payment for the remaining KES 300,000.** Proposed native entry TEST-PE-PART-02, KES 300,000, no hold, certified outstanding 300,000; primary **Prepare payment**, opening the payment editor with read-only Ministry of Health / Afya / KES / INV-01 v2 / Certification 1 / posted liability / verified test beneficiary ending 1234 / hold None / outstanding KES 300,000. Prefilled editable values: posting date 24 Jul 2027; method Bank transfer recorded; bank Test operating bank; payable account Test supplier payable; amount/allocation KES 300,000; reference TEST-PAY-PART-02. Deductions, advance recovery and unapplied amount KES 0. Primary Submit payment for approval; secondary Save draft, View certification, Cancel. Native approval remains Beatrice’s distinct action within KenTender.

D28-C: Julia, 25 Jul 10:00 after second cash settlement, Done **Finance confirmed the remaining KES 300,000 on 25 Jul 2027, 10:00 EAT.** Total cash 800,000; outstanding 0; both rows retained.

D28-V: reversal of second settlement at 26 Jul 10:00 restores outstanding 300,000 and Waiting on Beatrice since then; original settlement and reversal links remain. No “cash paid” inferred from zero accounting balance.

#### D29 — Advance support; Review or decision.

**Fixture:** Isolated advance branch; use its stated ADV-01/TEST-AG-01 facts, no base cash history; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, authorised certifier, 5 Jul 2027 09:00, isolated advance branch, Active, Invoices tab. Title **Review advance request**. Your turn **Review the advance and its guarantee.** Holder Charles. Synthetic issued clause allows **10% of KES 1,000,000 = KES 100,000**, paid after effective signature, recovery **KES 10,000 per laptop accepted and invoiced**. Advance guarantee **TEST-AG-01**, beneficiary Ministry of Health, amount KES 100,000, issuer Test Bank, valid through **31 Aug 2027**, issuer confirmation **TEST-AG-CONF-01**, Verified. Claim **ADV-01**, KES 100,000. No acceptance-required warning. Primary **Sign advance certification**, secondary View advance clause and View guarantee.

D29-H: guarantee not verified, Your turn, blocked **The advance guarantee has not been verified.** HOP/Finance custody owner Josphat named as follow-up; only View guarantee, View issue.

D29-R: first accepted-goods invoice KES 800,000, recovery KES 80,000, proposed further cash KES 720,000, advance remaining KES 20,000; matched evidence retained and Sign certification primary. Prior cash advance KES 100,000 remains distinct. Last two units invoice KES 200,000 would recover KES 20,000 and require KES 180,000 cash; no second claiming of that advance. Actual issued-source support and installed accounting proof remain approval evidence, not an advance option added to the base no-advance contract.

#### D30 — Reserved historical identifier.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

The donor branch is deferred from MVP 1. Produce no D30 artboard, route, fixture or command. Reusing this identifier for unrelated scope is prohibited.

#### D31 — Required services; Review or decision.

**Fixture:** CM-MOH-2027-SVC-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Peter, appointed technical certifier, 27 Jul 2027 12:00, isolated goods-plus-service package **CM-MOH-2027-SVC-001**, Active, Deliveries tab. Title **Review training completion**. Your turn **Record the training evidence.** Holder Peter. Agreement **10 laptops KES 1,000,000 plus one training session KES 50,000; total KES 1,050,000**. Required service **Train ten named users to start and operate the supplied laptops**; deadline 27 Jul 2027; evidence required **Attendance and completed practical checklist**. Observed attendance **10 of 10**; practical checklist **10 complete**; reference **TRAIN-01**. Generated finding **Meets**. Primary **Save observations**, secondary View service requirement.

D31-A: Julia at 13:00, technical certificate signed by Peter at 12:30; frozen service acceptance report includes separate line Training / 1 session / Accepted 1 / Deferred 0. Required signers Julia, Peter, Brian are all Awaiting signature. One **Sign report** primary for Julia; the same immutable report then goes to Peter and Brian, with posting/entitlement effects only after the full required proof set. This does not treat the chair’s signature alone as acceptance. Invoice entitlement for the service is KES 50,000 once. No asset/stock unit or serial is manufactured for a training service. This separate package does not change the base ten-laptop sum.

#### D32 — Final acceptance; Review or decision.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Amina, AO acceptance authority for the base completed branch, 28 Jul 2028 08:30, Active, Obligations tab. Title **Record final acceptance**. Your turn **Review the final acceptance evidence.** Holder Amina. Facts: 10 units accepted; initial 8 warranty ended 20 Jul 2028, replacements 2 ended 27 Jul 2028; no unresolved completion defect; test-source final-acceptance treatment **All obligations fulfilled**. Evidence links Initial report 1, Replacement report 1, Warranty history 1. Primary **Sign final acceptance**, secondary Return for correction (Reason empty; Return / Cancel). Exact output Final acceptance 1; required source-rendered certificate remains CM-TPL-01.

D32-H: isolated **CM-MOH-2027-WAR-OPEN-001 / agreement 1 / claim 1**, Julia Njeri, **28 Jul 2028, 08:30 EAT**, Active, Obligations tab. Unit **CM-WAR-OPEN-004** still has the Battery does not charge defect notified on 10 Jul 2028 under WAR-OPEN-TERMS-01; its warranty expired 20 Jul but the timely claim remains open, continuing D16-P/D11-B. Title **Record final acceptance**. Your turn, blocked **Unit CM-WAR-OPEN-004 still has an unresolved completion defect.** Holder Julia; **View claim** only; no final-acceptance signature. Replace the base no-defect/all-obligations-fulfilled facts and base Initial report/Replacement report/Warranty history links with **Warranty expired; timely claim remains open**, **Supplier remedy pending**, and branch links **Claim 1**, **Diagnostic 1**, **Defect notice 1**. No final acceptance, completion certificate or closure has been issued for this branch; no base replacement or D35 closed-claim history is inherited. Final acceptance and HOP completion certificate are separate attributable outputs.

### 10.6 Shared state presentation

The task cards contain their exact persona/state wording locally. Show one next-step block only. Your turn identifies a permitted action; Your turn, blocked names the obstacle and fix holder. Waiting on someone names the current holder and actual assignment time. Done has the evidenced result/time and no live holder. Neutral readers have no personal guidance block. Pending signing/posting/dispatch retains the original task and operation; a business user receives no technical-retry mutation. D-ERR has no trusted business actions; D-DENIED exposes no protected facts.

### 10.7 Embedded Finance editor and review fixtures

These are the complete local Finance task cards for D33, D09-F and D17; use the §10.1A shared page shell. Case CM-MOH-2027-001, agreement 1, supplier Afya Digital Supplies Limited, lifecycle Active, Invoices tab and existing white-sheet form/review surfaces apply. The account, tax and bank labels below are isolated configured test choices, not production defaults. No native form or bank-transfer control is shown.

#### D33 — Finance invoice preparation; Form or editor.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Josphat, 21 July 2027 11:00, Your turn **Complete the accounting details for invoice INV-01.** Title **Prepare accounting invoice**. Source claim INV-01 version 2 and Certification 1 are read-only. Company Ministry of Health; supplier Afya; currency KES; invoice date 21 July 2027; accepted Laptop / 8 / KES 100,000 / Total KES 800,000 are generated and read-only. Editable Posting date 21 July 2027 (date), Payable account **Test supplier payable** (authorised account selector), Accounting treatment **Test IT equipment** (configured classification selector), Tax treatment **Test tax included** (configured template selector), Cost centre **Test Ministry operations** (selector). Tax breakdown is generated from the configured fixture template and must reconcile to the displayed tax-inclusive KES 800,000; the fixture does not invent a statutory rate. Required native item/account/warehouse/asset dimensions are generated from reviewed classification mappings; an unresolved mapping shows **The accounting setup needs review.**, holder Finance configuration owner, and disables submission. Primary **Submit invoice for approval**; secondary Save draft, View certification, Cancel. Evidence Supplier invoice INV-01 version 2, Certification 1, Receipt 1. After submission: Waiting on Beatrice, assigned 21 July 2027 11:00 EAT, **Finance is reviewing the accounting invoice.**

D33-A: Beatrice 21 July 11:30, same fields read-only, Your turn **Review the accounting invoice.**, primary **Approve accounting invoice**, secondary Return invoice for correction, View certification. Return dialog Reason **Please review the accounting classification.**, Return invoice / Cancel. Successful native posting yields **Accounting invoice posted.**; no claim that payment occurred. Payment preparation is available only against confirmed supported native liability in this fixture.

#### D09-F — Finance payment preparation; Form or editor.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Josphat, 22 July 2027 13:00, native Payment Entry TEST-PE-01 draft 1. Title **Prepare payment**; Your turn **Prepare the payment record.** Read-only Company Ministry of Health; supplier Afya; currency KES; source INV-01 version 2; Certification 1; posted accounting invoice; payable/certified outstanding KES 800,000; hold None; beneficiary **Verified test account ending 1234**. Editable Posting date 22 July 2027 (date), Payment method **Bank transfer recorded** (configured selector; recording only), Bank account **Test operating bank** (authorised selector), Payable account **Test supplier payable** (authorised selector), Amount KES 800,000 (currency), Invoice allocation INV-01 / KES 800,000 (currency), Reference **TEST-PAY-01** (text). Read-only supported deductions KES 0, advance recovery KES 0, unapplied amount KES 0; native totals recalculate after edits. Beneficiary changes use the separate verified Finance process and invalidate pending approval. Primary Submit payment for approval; secondary Save draft, View certification, Cancel. Evidence Certification 1, accounting invoice, verified beneficiary reference. Saved state **Payment draft saved.**; submitted state Waiting on Beatrice, assigned 22 July 2027 13:00 EAT, **Finance is reviewing the payment record.** Posting validation appears against the affected field; stale review says **This payment has changed. Review the latest version.** D17 uses these exact values and adds maker Josphat and settlement Not confirmed. Approval at 22 July 14:15 yields **Payment entry posted. Settlement is not confirmed.** D17-S records the separately evidenced settlement already specified above.

#### D17 — Finance payment approval; Review or decision, KenTender review of the linked native entry.

**Fixture:** CM-MOH-2027-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Beatrice, separately assigned Finance approver, 22 July 2027 14:00, Payment Entry TEST-PE-01 draft 1, Active. Title **Review payment**. Action **Review the payment record.** Holder Beatrice Kamau. Facts: supplier Afya Digital Supplies Limited; invoice INV-01 version 2; certified/payable KES 800,000; proposed cash KES 800,000; prepared by Josphat Mwangi; payment hold None; beneficiary reference Verified test account ending 1234; settlement Not confirmed. Primary **Approve payment**; secondary **Return payment for correction**, View certification. Read-only fields: Ministry of Health; Afya Digital Supplies Limited; KES; INV-01 version 2; Certification 1; posted accounting invoice; posting date 22 Jul 2027; method Bank transfer recorded; bank account Test operating bank; payable account Test supplier payable; amount/allocation KES 800,000; reference TEST-PAY-01; deductions/advance recovery/unapplied amount KES 0; beneficiary Verified test account ending 1234. This records a native Finance decision, not a bank transfer. Approve invokes the configured native transition in place and shows Posted only on confirmed success; pending shows **The payment update is still pending.** with View update status. Return dialog requires Reason, fixture **Please review the payment allocation.**, with Return payment / Cancel; it preserves the draft and assigns Josphat correction work. No additional CM approval or navigation to a native form. D17-H replaces hold with Certification missing, Your turn, blocked **This payment is on hold.** Holder Charles Mutiso; only View missing certification and Back to contracts. D17-S, Beatrice 23 July 10:00, entry posted: Action **Record payment confirmation.** Amount KES 800,000; settlement date 23 July 2027; bank reference TEST-BANK-01; evidence Test bank confirmation 1; primary **Confirm payment**; secondary View payment record. No bank transfer button.

**Read-only linked record views.** View payment record, View settlement and View accounting invoice retain the KenTender case header, Invoices tab and Back navigation. Show the same authorised facts, exact native reference/version, current workflow/posting status, allocations, confirmed cash separately from noncash adjustments, and linked cancellation/reversal where present. No mutation for Julia, supplier, auditor or technical reader. Supplier projections omit internal accounts, protected bank detail and Finance-only controls. View certification and receipt/inspection/asset evidence use exact-version KenTender previews, with posted/pending/cancelled status from their native source. Restricted facts are omitted rather than fetched into hidden controls.

### 10.8 Coverage-completion briefs and read variants

All new briefs inherit §10.1A shared page shell, white enabled controls, no-linear-tracker exception, evidence disclosure and the exact synthetic branch below. Values are illustrative; no synthetic guard establishes current law. Existing production rules and installed native choices remain evidence-dependent. These branches are isolated from the canonical and base ten-laptop stories. Add no unlisted controls.

#### D34 — Quantity variation; Form or editor / decision variants.

**Fixture:** CM-MOH-2027-QTY-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Julia, coordination, 18 Jul 2027 09:00, isolated contract CM-MOH-2027-QTY-001, agreement 1 Active, Obligations tab. Synthetic reviewed source allows one additional laptop at the unchanged rate; test ceilings 15% goods quantity and 25% cumulative value, with no prior change. Title Request quantity change; Your turn Explain the additional quantity. Read-only Laptop / Original 10 / Rate KES 100,000; editable Proposed quantity 11; proposed total KES 1,100,000 and cumulative quantity/value change 10% are generated. Reason One additional user needs the same specified laptop; source request Test quantity request 1. Primary Request change; secondary Cancel.

D34-R: Charles, 18 Jul 10:00; reviewed technical recommendation Test QTY review 1, legal/source evidence Test QTY basis 1, source funding allocation Digital Health KES 100,000 additional and Funding confirmation QTY-01; current/proposed totals 1,000,000/1,100,000; primary Submit change for decision, secondary Return for correction.

D34-A: Amina 18 Jul 11:00; same read-only comparison and evidence; Approve change, Decline, Return for correction; decision dialog reason Additional quantity is supported at the unchanged issued rate; Confirm decision/Cancel.

D34-P: Mary 19 Jul 09:00; amendment 1 comparing quantity 10/11 and totals; Sign amendment, Report a problem; entity Amina subsequently signs exact same version.

D34-H: both signatures/effectiveness recorded 19 Jul 10:00, Budget adjustment acknowledged but order update failed; title Contract change recorded; Waiting on Daniel since 10:00; Operative quantity 11, order update pending, affected new spending held; View update status/View amendment only.

D34-X: proposed quantity 12 (20%), source test ceiling 15%; Your turn, blocked Proposed quantity exceeds the applicable limit; Julia; View rule/View issue; no submit/approval. No officer edits the rate or calculated percentage.

#### D35 — Paid-unit warranty replacement; Record detail and verification variants.

**Fixture:** CM-MOH-2027-WAR-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Julia, 10 Jul 2028 09:00, isolated base-sized contract CM-MOH-2027-WAR-001 Active; all ten units accepted, invoiced and cash confirmed KES 1,000,000. Obligations tab; unit CM-WAR-004, warranty ends 20 Jul 2028; fault Battery does not charge; notice sent 10 Jul 09:00; remedy Like-for-like replacement under issued terms. Title Follow up warranty replacement; Your turn Arrange return of the faulty laptop. Display Returned No, replacement Not received, Finance correction Pending, owner Josphat. Primary Record return opens unit/actual collection date 12 Jul/evidence Test collection WAR-01; Record return/Cancel; The screen records actual collection and shows the pending authorised return/accounting correction separately. Recording collection does not claim that the native return is posted; its operation mapping is in §11.1.

D35-V: Peter current technical/inspection capacity, 15 Jul 10:00, returned unit 004/replacement CM-WAR-011, original return/credit and accepted replacement receipt Reconciled, unchanged acquisition entitlement 10 units/KES 1,000,000, additional cash/payable KES 0. Generated RAM 16/Storage 512/Starts Yes findings with Test WAR log 1; verification source current technical certificate and fully signed replacement report. Title Verify warranty remedy; Your turn Confirm the remedy evidence; Verify remedy/Request correction; Verify remedy closes the claim automatically only when verification and all required native/report evidence succeed; otherwise it remains open.

D35-C: Julia 15 Jul 11:00, remedy verified, claim closed, original cash KES 1,000,000, no additional invoice entitlement, original unit/replacement links; View remedy/View history only.

D35-H: credit/receipt reconciliation incomplete; Your turn, blocked Finance must reconcile the replacement; Josphat named; View affected records/View claim only; no close-claim command. Warranty treatment follows exact source; this fixture retains the original expiry and introduces no universal replacement warranty default.

#### D36 — Contractual delay adjustment; Review or decision.

**Fixture:** CM-MOH-2027-DELAY-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, 29 Jul 2027 09:00, isolated CM-MOH-2027-DELAY-001; agreement Active; all 10 goods accepted 25 Jul. Synthetic clause: due 20 Jul; five calendar days late 21–25 Jul  inclusive; eligible principal KES 1,000,000; 0.1% per day; cap 10%; no effective extension. Calculation KES 1,000 per day × 5 = KES 5,000; cap KES 100,000; proposed adjustment 5,000. Title Review delivery delay; Your turn Review the proposed adjustment. Causation Supplier shipment delay; supplier challenge Requests exclusion of two days; evidence Delivery 25 Jul, clause TEST-DELAY-01, supplier response 1. Primary Submit adjustment for decision (PrepareContractAdjustment output); secondary Return for correction/View clause.

D36-A: Amina, 30 Jul 09:00, explicit synthetic decision authority; same computation, technical/legal recommendation No supported exclusion; Approve adjustment/Decline/Return for correction, reason Supplier-responsible five-day delay established; Confirm decision/Cancel.

D36-S: HOP certifies supported invoice gross KES 1,000,000, authorised adjustment 5,000, proposed cash 995,000; Finance uses reviewed native adjustment mapping, not an edited invoice rate; noncash adjustment KES 5,000 and confirmed cash KES 995,000 settle KES 1,000,000 without reporting the adjustment as cash.

D36-H: native deduction mapping unverified; payment held, Josphat owns fix; View calculation/View issue only. D36-E is separate effective-extension branch due 22 Jul  before relevant event; late 23–25 Jul  three days, generated KES 3,000 with old computation retained; an unsigned extension request cannot select this variant.

#### D37 — Security claim; Review or decision.

**Fixture:** CM-MOH-2027-SEC-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, 12 Aug 2027 09:00, isolated termination/security contract CM-MOH-2027-SEC-001, Terminated; verified TEST-SG-01 amount 100,000, expiry 31 Aug 2027, custodian Charles; evidence instrument, default/cure/termination notice, claim basis TEST-SG-CLAUSE-01. Title Review security claim; Your turn Prepare the supported claim. Proposed amount 40,000 generated from test loss review; grounds Failure to perform the unfulfilled obligation; recipient Test issuer; claimant authority Reviewed test mandate 1. Primary Request claim; secondary View instrument/Cancel.

D37-A: Amina, 10:00, Decide claim; Approve claim/Decline/Return for correction with required reason; amount 40,000 unchanged, no cash status from decision.

D37-P: Charles, 13 Aug 09:00; approved exact claim, communication delivered 12 Aug 11:00; Waiting on Test issuer; outcome Not recorded; Record claim outcome opens issuer reference TEST-SG-OUT-01/date 13 Aug /evidence Test issuer outcome 1/actual proceeds KES 40,000; Save outcome/Cancel. Actual cash receipt requires Finance-native recovery and confirmation separately.

D37-X: instrument extension/replacement needed; Charles, 15 Aug 09:00, new TEST-SG-02 amount 100,000 expiry 30 Sep and issuer confirmation TEST-SG-CONF-02; Verify replacement/Reject replacement mapped to VerifyContractSecurity/RejectContractSecurity and RecordSecurityAction Replace after verification. Until verified, old instrument remains operative with coverage issue visible. No expiry-based release.

#### D38-P — Prepare close-out correction; Form or editor.

**Fixture:** CM-MOH-2027-CLOSE-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, HOP, 29 Jul 2028 11:00, isolated Closed CM-MOH-2027-CLOSE-001, closure 1 dated 28 Jul, Obligations tab. Title Request close-out correction; Your turn Explain the completion error. Read-only original closure 1 and affected Completion certificate 1; editable Reason Required completion certificate delivery was recorded without evidence; evidence Delivery incident 1; proposed disposition Reopen for completion (read-only recommendation in this fixture). Primary Submit correction, secondary Save draft/Cancel, mapped to PrepareContractClosureCorrection with Draft/Submitted intent; save creates no AO decision. Submission creates the exact AO task shown by D38.

#### D38 — Correct close-out; Review or decision.

**Fixture:** CM-MOH-2027-CLOSE-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Amina, 30 Jul 2028 09:00, isolated Closed CM-MOH-2027-CLOSE-001, closure 1 dated 28 Jul; HOP correction 1 identifies required completion certificate delivery falsely marked complete, actual delivery not established; original financial total 1,000,000 unchanged. Obligations tab; title Review close-out correction; Your turn Decide the correction. Exact evidence Closure 1, delivery incident 1, HOP review 1. Primary Reopen contract; secondary Keep closed with surviving work, Return for correction, View closure. Reopen dialog reason Required completion evidence was not established; Confirm reopening/Cancel. Keep closed is unavailable for this fixture because the bound completion rule requires that evidence; display explanation rather than a bypass.

D38-R: Active with closure 1 and reopening 1 retained; Charles task Confirm certificate delivery; no restored spending/stock or altered legal dates.

D38-T: Terminated source; Reopen contract absent; View termination/View settlement only; use legal referral for termination correction.

#### D39-P — Prepare termination settlement; Review or decision.

**Fixture:** CM-MOH-2027-TERM-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, HOP, 20 Aug 2027 09:00, isolated Terminated CM-MOH-2027-TERM-001, Obligations tab. Title Review termination settlement; Your turn Review the reconciled settlement. Read-only Finance reconciliation TERM-01, accepted 800,000, cash 800,000, advance/credits/costs/disputes 0, final supported obligation KES 800,000, Budget decrease acknowledged; no unclassified remaining item. Primary Submit settlement for completion, secondary Return for correction/View reconciliation, mapped to PrepareTerminationSettlement; Finance correction task if returned. AO task is D39.

#### D39 — Termination settlement completion; Review or decision.

**Fixture:** CM-MOH-2027-TERM-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Amina, 20 Aug 2027 10:00, isolated Terminated CM-MOH-2027-TERM-001; HOP reviewed reconciliation, accepted work KES 800,000, cash 600,000+200,000 confirmed, advance 0, credit 0, authorised costs 0, dispute 0, unsupported/unperformed KES 200,000 extinguished by effective termination. Final supported obligation KES 800,000; Budget decrease acknowledged; closure acknowledgement Pending. Title Complete termination settlement; Your turn Review the settlement record. Primary Complete settlement; secondary Return for correction/View termination. Completion dialog records reason All required settlement facts reconciled; Confirm completion/Cancel.

D39-C: Terminated — settlement completed 20 Aug 10:00; Funding finalisation pending with Budget owner, not Completed; View settlement/View funding update only.

D39-H: outstanding advance 20,000 with no valid survivor disposition; Your turn, blocked The advance recovery needs resolution; Finance owner; View recovery/View remaining obligations; no complete action.

#### D08-L — Corrected claim after early liability posting.

**Fixture:** CM-MOH-2027-CLAIM-001; supplier Afya Digital Supplies Limited; EAT display. Explicit variant contract identities replace this normal fixture.

Charles, 21 Jul 2027 10:15, isolated CM-MOH-2027-CLAIM-001; supplier original 10-unit claim KES 1,000,000 received 08:05, accepted 8/support KES 800,000, corrected claim KES 800,000 received 10:00; Finance had posted original liability KES 1,000,000 with payment hold. Title Review corrected invoice; show native liability KES 1,000,000, required credit KES 200,000, reconciled payable Not established, support KES 800,000, original receipt retained. Your turn, blocked Finance must reconcile the original liability; Josphat owner. View correction/View accounting invoice only; no second liability draft or payable 1,800,000. After native credit reconciles at 11:00, D08-C certification view shows current supported amount 800,000; current claim/certification version required. Supplier's disputed two-unit claim remains history/issue.

New evidence/output links use exact fixture summaries above only; full legal-document renders remain CM-TPL-01. Each new decision's authoritative source/effect is §5, not a design label. All new Decline/Return/Request correction decisions open the existing required-reason dialog with Reason empty, Confirm decision or the subject-specific Return/Send request, and Cancel; no outcome commits without the entered reason. Read-only View rule/View calculation/View remedy/View affected records/View reconciliation links open exact authorised KenTender previews, never native forms. D36/D37 review submissions freeze the stated exact proposal; supplier challenge/reply uses existing correspondence surfaces and own-organisation authority.

## 11. Functional interaction requirements — excluded from design prompts

| Controls | Effect and failure treatment |
|---|---|
| Recommend inspectors / Appoint inspectors / Return appointment / Revise appointment recommendation / Save declaration | `RecommendContractInspectors` / `AppointContractInspectors` / `ReturnContractAppointment` / revised `RecommendContractInspectors` / `DeclareContractInterest`; exact scope, version and authority retained. |
| Save security / Verify security / Reject security | `RecordContractSecurity` / `VerifyContractSecurity` / `RejectContractSecurity`; expiry/source and issuer evidence checks, no upload-as-verification. |
| Save signature evidence / Confirm signature evidence | `RecordOutsideContractSignature` / `ConfirmOutsideSignatureEvidence`; method allowed and exact document/parties required. |
| Request extension / Submit change for decision / Sign amendment | `RequestContractChange` / `SubmitContractChangeForDecision` / `SignContractVersion` with amendment subject; current terms unaffected until `ActivateContractChange`. |
| Record source evidence | `RecordLegalSourceEvidence`; attribution only, no executable-rule edit. Donor commands and screens are deferred. |
| Sign advance certification | `SignAdvanceCertification` on `PrepareContractAdvance` output; issued clause, guarantee and recovery verified before native Finance follows. |
| Use references | Local arrival draft only; `RecordContractArrival` commits the recorded units. |
| Sign final acceptance | `SignFinalContractAcceptance`; exact AO/acceptance authority and current completion evidence. |
| Prepare payment | Open the authorised KenTender payment editor for the exact native draft/amount/entitlement; same maker/approver and hold checks as §5.12. |
| All contracts / My work / Source / Responsible person / Managing unit | Read-only owner-filtered list query; filters persist per view and never broaden authority. |
| Appoint / Verify / Reject / Save evidence / Confirm decision / Return in a named dialog | Invoke the originating named command above once with preserved fields and stable operation key. A dialog label is not another approval. |
| Register existing contract / Save and review / Confirm opening position / Start management | Navigate to registration / `RegisterExistingContract` or `ReviseContractIntake` for a saved draft / `ConfirmOpeningPosition` / `StartContractManagement`. Save does not activate/post; activation rechecks exact confirmed version and creates only outstanding work. |
| Send message / Send reply / Send notice / Report a new issue / Report a problem / Report difference | `SendContractCorrespondence` / `ReplyContractCorrespondence` / `SendContractCorrespondence` on notice subject / `RecordContractIssue` for each issue/problem/difference. Retain addressed exact content and dispatch status; later evidence creates a linked successor issue. |
| Approve extension / Decline extension / Return change for correction | `DecideContractChange` (Approve/Decline) or `ReturnContractChange`; exact current reviewed version/reason, no operative effect before required amendment. The originating D14 dialog may label Decline and Return for correction because its subject is unambiguous. |
| Approve termination / Decline termination / Return termination for correction | `DecideContractTermination` (Approve/Decline) or `ReturnContractTermination`; exact request/reason; `RecordTerminationNotice` supplies actual effective notice, never approval alone. D20 uses its short labels within that subject. |
| Submit report / Record source evidence | `SubmitContractReport` / `RecordLegalSourceEvidence`; exact report delivery or proposed source evidence for owner review. Unknown legal source cannot be converted to an arbitrary officer-authored deadline. |
| Record return / Sign technical certificate / Sign and issue certificate | `RecordSecurityAction` (Return) / `SignTechnicalCertificate` / `IssueCompletionCertificate`; exact instrument/certificate and personal authority, persist pending delivery separately from signing. |
| Approve payment / Confirm payment | `ApproveNativeFinanceRecord` for the exact payment version/configured native transition / `RecordFinanceSettlement`; remain in KenTender; no bank execution or payment-hold bypass. |
| Submit invoice / Submit correction | Preserve original receipt time and version; mismatch does not discard the supplier’s claim. |
| Search contracts / All statuses / Clear search | Authorised list query; no mutation. Clear search preserves status filter; empty results use D01-F. |
| Open contract / Back / section navigation | Load exact authorised current record/section; denial uses D-DENIED, failure D-ERR. |
| View award / agreement / evidence / history / report | Open exact linked version in a read-only view. No navigation silently changes the selected document version. |
| Send for signature / Sign contract | Request/sign commands in §7. Pending uses D02-S or D03-W; success never inferred from a timeout. |
| Enter unit references / Record delivery | Edit local draft; Record commits arrival command. Cancel discards only unsaved changes after dirty-state confirmation. |
| Record observations / Save observations | Edit coverage-scoped observations; save recalculates findings and persists author/time. Stale save retains entered values for comparison. |
| Prepare report for signing / Sign report | Prepare/freeze, then sign exact report. A correction request creates chair issue and suspends that report’s remaining signing; superseded report retains prior proofs. |
| Request correction / Send request | `RequestAcceptanceCorrection` for an acceptance/technical report, or `RequestInvoiceCorrection` for a claim; exact subject/reason, then `SendContractCorrespondence`. Dispatch failure retains unsent state and retries same message; never claims supplier receipt without evidence. |
| Sign certification | Current corrected claim and match report required; stale claim prevents signature. Creates one Finance work item. |
| View payment record / View settlement / View accounting invoice | Read the exact native transaction through its authorised KenTender projection; no native-form redirect. |
| Save draft / Submit invoice for approval / Submit payment for approval | `SaveNativeFinanceDraft` / `SubmitNativeFinanceForApproval` for the exact invoice/payment subject; server-calculated native totals and supported entitlement; retain errors/entered values in KenTender. |
| Approve accounting invoice / Return invoice for correction / Return payment for correction / Return invoice / Return payment | `ApproveNativeFinanceRecord` or `ReturnNativeFinanceForCorrection` with exact subject/version and required return reason; native transition and current authority/segregation enforced. |
| Open replacement issue / View issue / View claim | Open current issue with correspondence, named holder and permitted response. Final disposition closes replies to that thread; later correspondence creates a linked issue. |
| Sign close-out / Return for correction | `SignContractCloseout` / `ReturnContractCloseout` on the exact generated review after current checks, or reasoned HOP correction task. No close-on-click before proof. |
| Retry / View update status | Read retry or operation-status projection; technical write recovery remains assigned to its owner. A business user cannot repeat a payment by refreshing. |
| Disclosures / Cancel | Display-only; Cancel closes the local dialog and preserves committed evidence. All save/send dialogs return to their originating record and show recorded/pending/error result. |

### 11.1 Coverage interaction mapping

| Visible action | Command / consequence |
|---|---|
| Request change / Approve change / Decline / Sign amendment (D34) | RequestContractChange / DecideContractChange / SignContractVersion on exact amendment; ActivateContractChange only after effectiveness; pending owner updates retain hold |
| Record return (D35) | RecordAcceptanceCorrection on accepted-unit return; collection evidence and native correction intent; not RecordCustodyReturn for already accepted units |
| Verify remedy / Request correction / Close claim | VerifyContractRemedy (automatically resolves through ResolveContractIssue when all required remedy/native evidence is complete) / RequestAcceptanceCorrection; no duplicate claim entitlement |
| Submit adjustment for decision / Approve adjustment / Decline | PrepareContractAdjustment freezes calculation then DecideContractAdjustment on exact reviewed version; Finance native adjustment follows supported decision |
| Request claim / Approve claim / Record claim outcome / Save outcome | RequestSecurityClaim / DecideSecurityClaim / RecordSecurityClaimOutcome (Save outcome commits the exact issuer-outcome dialog once; Cancel discards its unsaved edits); separate claimant authority/dispatch/actual recovery and Finance evidence |
| Verify replacement / Reject replacement | VerifyContractSecurity / RejectContractSecurity; verified Replace or Extend activates through RecordSecurityAction without erasing old instrument |
| Reopen contract / Keep closed with surviving work / Return for correction | ReopenContractCloseout / ConfirmContractClosure / ReturnContractCloseout on correction subject; reason required; unsupported survivor treatment cannot bypass completion rule |
| Submit correction / Save draft (D38-P) / Submit settlement for completion (D39-P) | PrepareContractClosureCorrection with Draft/Submitted intent / PrepareTerminationSettlement; no closure/settlement decision from preparation |
| Complete settlement / Confirm completion | CompleteTerminationSettlement on PrepareTerminationSettlement's exact reconciliation and AO proof; Terminated retained; financial acknowledgements independent |
| Other work / Open / View affected records | Authorised GetContractWorkspace/GetContractHistory or exact task/read projection; no mutation on navigation |

Return actions route to the originating subject's named preparer; distinguish ReturnContractChange, ReturnContractTermination and ReturnContractCloseout. Failed dispatch/signing/posting uses existing scoped status/recovery contract; no design label silently executes a native operation.

## 12. Audit and historical integrity

Record source version, actor/capacity, observed and recorded time, decision reason, evidence references, before/after revision, rule version and signature proof for material changes. Automated findings identify their inputs and rule; later recalculation creates a successor. Preserve supplier correspondence and delivery outcomes separately.

Use UTC storage and site-timezone display. Never backdate the recording timestamp to the physical arrival time. Reversal/correction history remains linked across CM and native documents. Public reporting excludes protected personal, bank and confidential evidence. Retention follows the verified shared records policy and bound profile, with completion trigger/date, retention rule, minimum retained-until date and any legal hold recorded separately. Closure or expiry never triggers CM deletion. A records-policy change creates an attributed successor and does not erase existing retained evidence; no local automatic deletion rule is introduced.

## 13. Seed contract

Use the existing canonical people in KT-STD §8. Proposed extra capacities must be explicitly appointed/assigned in isolated CM fixtures: Julia as contract owner and separately appointed inspection chair/user-department representative; Grace Wanjiku as receiver; Peter Mugo as appointed technical member/certifier; Brian Wafula as appointed procurement member; Josphat as Finance maker; Beatrice as Finance approver. Evaluation appointments do not confer these capacities. Charles remains HOP and invoice certifier; Brian prepares only when authorised and signs acceptance only under the separate current CM appointment, Amina entity signatory/AO, Mary supplier signatory and David supplier representative. Daniel Otieno has site-wide technical read with no business action; separately assigned recovery handles safe technical operations. These CM-specific bindings are proposals in §17.4, not changes already contained in KT-STD v1.25. The SEED-OPS source was not supplied; its successor number must be taken from its actual current owner register. They do not change canonical OUs or grant authority merely because a person exists. Daniel’s business read follows the latest technical-read standard; recovery is separately assigned.

The coverage branches in §10.8 are isolated fixture variants with separate source/operation identities. Provision the required CM registry responsibilities and exact appointment subjects, including Contract inspection/Technical certification/Entity contract signing where used. Julia's D40-HOD branch is oversight-only, not implicit chair/coordinator power; Grace's D40-D lacks Receiving. AO/HOP retain their authoritative office responsibilities. Native AO inspector appointments generate their written record/reference. Generate references deterministically in test setup; production numbering is not constrained to preserve screenshot strings. Fixture employment affiliation is display information only, never authority; use the canonical OU register and reviewed staff affiliation source rather than kt_primary_department or first role assignment. Where no authoritative affiliation is established, show Not recorded; no invented department or appointment ineligibility gate.

Canonical integration fixture starts from Award’s actual generated tender reference and eligible package at 2 July 2027 09:00 EAT. Derive source line values and terms; preserve Award’s KES 46,400,000 amount. The independent ten-laptop demonstration in §10 uses a separate synthetic source package and identifiers; it must never overwrite the canonical chain.

Seed through production commands with labelled synthetic Trust and Finance settlement evidence. Reruns return the same identities. No real email, signing or banking. Isolate holds, empty observations, rejected items, replacements, late signatures, duplicate claims, race conditions, payment reversal, expired authority and termination from the ordinary story.

## 14. Acceptance contract

These are required test scenarios, not reported test passes. Document consistency checks in §17.8 do not establish runtime test success.

| ID | Required result |
|---|---|
| CM-AC-01 | Replayed Award package creates one case/task; earlier publication event survives independently. No-award event creates no false contract publication. |
| CM-AC-02 | Later restriction during delivery/signature retry blocks only affected positive actions; arrival/evidence remains recordable. |
| CM-AC-03 | Exact source/terms persist; Item/template edits cannot alter existing agreement or inspection criteria. |
| CM-AC-04 | Supplier and entity sign the same version; changed content or expired authority cannot complete the old request. Unknown signing outcome reconciles without a second attempt. |
| CM-AC-05 | Signed agreement/order-post failure shows true partial completion and recovers once without fresh signatures. |
| CM-AC-06 | Arrival does not create usable stock; excessive/premature goods remain attributable exceptions. |
| CM-AC-07 | Empty required observations, unreadable evidence and unavailable verification yield Needs review; no default Accepted leaks into the CM finding. |
| CM-AC-08 | Serial/unit coverage, sampling authority and partial quantities reconcile; repeated unit use cannot silently create duplicate acceptance. |
| CM-AC-09 | Report signatures bind the exact conclusions; correction retains prior proof, and all required current signatures precede posting. |
| CM-AC-10 | Mixed accepted/rejected goods, segregated custody and returns work without weakening global validation. Stock and fixed-asset branches reconcile to Finance. |
| CM-AC-11 | Partial invoice and replacement claims consume entitlement once; concurrent/duplicate requests cannot over-certify or overpay. |
| CM-AC-12 | Price/tax/quantity differences show a reason and holder; original invoice receipt time survives correction. |
| CM-AC-13 | Certification, liability posting, payment entry and settlement confirmation remain distinct. Credit settlement is not displayed as cash paid. |
| CM-AC-14 | Authorised advances follow their own guarantee/recovery route; no unsupported advance bypasses controls. |
| CM-AC-15 | Approved effective changes preserve previous terms/calculations; pending requests alter none. Termination leaves legitimate settlement visible. |
| CM-AC-16 | Security/warranty expiry alone releases nothing. Close-out respects the verified completion rule and tracks surviving obligations. |
| CM-AC-17 | Direct ERPNext, API, import and background routes enforce the same authority, quantity and source controls; no UI-only safeguard. |
| CM-AC-18 | Native posting timeout, cancellation, reversal and changed downstream records reconcile without duplicate ledger effects or erased evidence. |
| CM-AC-19 | Every condition in §5.10 and §10.3 shows the correct holder/fix/wait state; no disabled-action dead end. |
| CM-AC-20 | Cross-supplier access, expired appointment, supplier self-acceptance, Finance self-approval, payment-maker settlement confirmation, acceptance-signer procurement certification (including corrected/mixed supporting claims) and technical business action fail without side effects. Brian’s separate appointment permits acceptance; Charles’s independent current capacity permits certification. |
| CM-AC-21 | Canonical and isolated fixtures remain separate, rerunnable and free of live external side effects. |
| CM-AC-22 | Publication/reporting due dates preserve trigger times; correction/failed dispatch never falsely completes the obligation. |
| CM-AC-23 | Contract, stock, asset, payable, cash and credit totals reconcile across partial delivery, replacement and reversal. |
| CM-AC-24 | §17 distinguishes requirements approval, isolated feasibility authority, affected-package acceptance and production release. Open proof does not prevent authorised evidence work; it prevents acceptance/enablement of affected behaviour. Source review never substitutes for installed-version verification. |

### 14.1 Independent operation and adversarial scenarios

| ID | Required result |
|---|---|
| CM-AC-25 | Install CM with its shared/ERPNext dependencies and no tendering apps. Register an existing signed contract and perform partial receipt, invoice follow-up and close-out without absent-DocType errors or fabricated Award records. |
| CM-AC-26 | Import a contract with 4 accepted units, 2 in custody, KES 400,000 invoiced, KES 300,000 cash paid and KES 100,000 outstanding. Link existing balances; import posts nothing. A further invoice cannot claim those four units twice. |
| CM-AC-27 | Repeat registration, change the source file under the same external ID, and later deliver a KenTender package for the same contract. Keep one live case, preserve source history and require reconciliation on conflict. |
| CM-AC-28 | Missing external signatures, an unreadable price schedule, unsupported product, unknown opening balance or unconfirmed official action owner prevents activation with a named issue. It does not create a false zero, eGP verification or new signature request. |
| CM-AC-29 | A legitimate surviving warranty/payment obligation stays visible and assigned after supported close-out; an unresolved completion defect blocks it. A security-expiry timer never records release. |
| CM-AC-30 | An invalidated Regulations-only deadline cannot appear as a verified statutory deadline. A supported independent contract term retains its source and correct classification. |
| CM-AC-31 | A changed beneficiary, Journal Entry settlement or direct reconciliation cannot bypass the payment hold or maker/approver separation. Credits and write-offs never inflate Cash paid. |
| CM-AC-32 | Disabling optional BDS/PRC/Award adapters leaves CM supplier actions, records and tasks functional; external official actions still require their genuine evidence. |

### 14.2 Reconciliation-specific scenarios

| ID | Required result |
|---|---|
| CM-AC-33 | A shared reservation funds two commitments; forming the first contract cannot release the other allocation. Exact conversions/replays reconcile to BUD’s owner balances. |
| CM-AC-34 | Signing succeeds but Budget conversion/PO creation fails: original legal proof stays retained, affected spending held, original intent reconciled once, no re-signature or false rollback of provider proof. |
| CM-AC-35 | Effective variation/termination funding adjustments account for supported obligations, not certified totals alone. Missing Budget closure operation never produces a direct state write or false financial finalisation. |
| CM-AC-36 | Each applicable profile rule has cited classification, parameters/calendar and evidence; unverified/suspended rules block affected positive actions, while factual/protective recording remains possible. Test mode never skips statutory constraints. |
| CM-AC-37 | Period reports use exact cutoff/versions; failed source reads yield Incomplete, not empty success. Submission/dispatch/retry and corrections preserve original report and obligation triggers. |
| CM-AC-38 | Committee appointment, personal declaration/conflict, replacement, receiver separation and pending report reconstitution preserve attribution and prevent stale authority/signature reuse. |
| CM-AC-39 | Native payments of KES 500,000 and 300,000 settle one KES 800,000 entitlement exactly once; a concurrent excess is refused and reversal of the latter reopens KES 300,000 with prior evidence retained. |
| CM-AC-40 | Source-signed imports retain actual effective dates and exact versions; outside-signature copies cannot be mixed or labelled Trust electronic proof. Duplicate/ambiguous identities require reconciliation. |
| CM-AC-41 | D29’s advance KES 100,000, first recovery 80,000 and final recovery 20,000 reconcile with cash 100,000 + 720,000 + 180,000, totalling KES 1,000,000; entitlement is consumed only once. |
| CM-AC-42 | A related-service acceptance/invoice creates no fabricated stock/asset unit; goods KES 1,000,000 plus service 50,000 reconcile under the separate package. |
| CM-AC-43 | Latest technical readers see site-wide permitted CM read without mutation, and supplier signatories/representatives see exactly CM-granted contract powers without inherited bid submission authority. |
| CM-AC-44 | Every action/dialog/variant in §10 resolves to one §7/11 command/read, exact fixture identity/instant and next-step kind; current surfaces/archetypes and deliberate tracker exception conform to KT-STD v1.25. |
| CM-AC-45 | Complete supplier claim, Finance invoice/payment preparation, separate approval and settlement entirely through KenTender; no routine step launches or embeds standard Frappe forms. Captured source facts are reused once; Finance enters only missing accounting choices. |
| CM-AC-46 | Configured tax/account/dimension requirements and native validation errors are surfaced in KenTender; unsupported configuration blocks the journey with a named owner. Native totals/allocations are authoritative; saving a draft cannot imply posting or settlement. |
| CM-AC-47 | A native change/reversal, stale projection, concurrent approval or uncertain posting updates the KenTender view truthfully; current versions/holds are rechecked server-side, entered values preserved, and retries create no duplicate. Protected fields remain excluded from unauthorised projections. |

### 14.3 Coverage-completion scenarios

Each case has a fixed branch/source/actor/version, expected native and Budget results, denied direct-command assertions and replay/stale checks. These are required tests, not passed results.

| ID | Required result |
|---|---|
| CM-AC-48 | Every §6.2 reader opens permitted list/count, five tabs, focused record, exact evidence/export/direct API without task-dependent page denial; AO and HOP can navigate without mutation. Cross-OU/source-only and multi-role cases prove no scope laundering; protected fields are not fetched to hidden controls |
| CM-AC-49 | Arrival produces custody/inspection only, zero native receipt drafts; fully effective acceptance generates one accepted-subset draft/posting intent, excluding rejected/deferred units and repeat coverage |
| CM-AC-50 | Apply each §5.17 failure alone and in combination. Retain true legal state/proof, permitted factual work and independently visible incidents. No payment/native accepted receipt bypasses missing required funding/order/result; early liability remains held |
| CM-AC-51 | D34 changes quantity 10 → 11 and value KES 1,000,000 → KES 1,100,000 at the unchanged rate; valid synthetic source/funding/authority reviewed. Pending approval/signature changes no terms; an effective amendment followed by failed order update holds changed spending. A 12-unit request (20%) is refused under the synthetic 15% ceiling; replay adjusts once. |
| CM-AC-52 | D08-L retains original receipt 08:05 and correction 10:00. Liability KES 1,000,000 plus linked credit KES 200,000 gives KES 800,000, never a second KES 800,000 liability. New claim requires current support; partial certification of disputed original is absent |
| CM-AC-53 | D35 accepted/paid unit return and replacement preserve total entitlement10 units/1,000,000; native correction/replacement reconciled once, no new cash/payable. Missing reconciliation prevents claim closure; verified repair without transfer creates no fictitious return |
| CM-AC-54 | D36 exact five-day calculation5,000 and effective-extension three-day3,000 preserve prior inputs. Pending request changes nothing. Supplier challenge, authority and native adjustment mapping required; missing mapping holds payment |
| CM-AC-55 | D37 request/decision does not mark KES 40,000 recovered. Claimant mandate/dispatch/issuer outcome and separate Finance evidence required. New instrument not operative until verification; expiry releases nothing |
| CM-AC-56 | D38 preserves closure 1 and reasoned reopening 1; required missing completion evidence cannot be hidden as survivor. No automatic spending/funding/native rollback; effective termination cannot become Active through closure correction |
| CM-AC-57 | D39 settlement of KES 800,000 retains Terminated, separate completion instant and true Budget pending status. Unclassified advance/dispute blocks; valid survivor needs explicit rule/owner and remains assigned |
| CM-AC-58 | Proposed Budget closure retains KES 1,000,000 current_amount and position charge after Closed; approved decrease to KES 800,000 adjusts once, then closure changes no amount/Available/reservation. Concurrent/stale/conflicting replay fails; closed FY accepts no increase |
| CM-AC-59 | Multiple actionable/waiting/unknown-date tasks obey §6.3 ordering, remain discoverable and deduplicated; expired/reassigned authority is rechecked. Closed surviving warranty/payment stays in My Work |
| CM-AC-60 | §5.18 correction at each boundary before proof, before posting, after receipt, after liability and after settlement retains history, invalidates affected future support/approval, creates required native reconciliation and holds only affected scope |
| CM-AC-61 | Ordinary and existing-contract journeys stay within the Contracts list, five-tab case and contextual task surfaces. D-numbers/state variants add no menu destinations or per-persona routes; return navigation preserves context. |
| CM-AC-62 | Every actionable/blocked/waiting state identifies the task or obstacle, material quantity/amount and correct holder on first view. A neutral reader has no personal-task block; Other work excludes the leading task and duplicates. |
| CM-AC-63 | Award/terms, arrival observations, supplier claim and supported native Finance values are entered once and reused. No extra acknowledgement of successful checks/handoffs; native posting failure does not trigger fresh signatures, duplicated records or a Desk redirect. |
| CM-AC-64 | A designer can resolve each normal/state task from its local card plus the shared shell; no separate waiting override or field supplement is needed. D05 options, evidence/footer order, Finance fields and D10/D40 presentation agree with the actual build. |

### 14.4 Maintained coverage and delivery sequence

This table is the operative trace, maintained inside CM rather than a separately versioned implementation specification. A row is not complete because a screen exists: its source, command, projection, owner acknowledgement and executed evidence must agree. AC-01–47 remain in force; donor AC identifiers are retired historical items outside MVP1.

| Coverage finding | Operative requirement / command | Screen / variant | Verification / owner dependency |
|---|---|---|---|
| COV-01 Access | §§6.2/9 reads and command separation | D40 reader variants; existing read-only records | AC-20/43/48; AUTH/KT-STD pending audience proposals |
| COV-02 Receipt timing | §§4/5.4/5.6/7 RecordArrival/PostAcceptedReceipt | D04–D07 | AC-06/10/49; native accepted-subset proof |
| COV-03 Failures | §5.17 original intents/recovery | D02-S/D07-P/D34-H/D39-C | AC-05/18/34/47/50; Trust/Budget/ERPNext |
| COV-04 Budget closure | §5.14.1 proposed close_commitment | D39-C, case financial status | AC-33–35/58; exact proposed BUD owner amendment |
| COV-05 Corrections | §5.18 exact successors/holds | D08-L/D35/D38; existing correction dialogs | AC-18/31/47/60; native cancellation/credit/reversal proof |
| COV-06 Value/quantity | §§5.7/5.11/5.14 Request/Decide/ActivateChange | D34 variants | AC-15/35/51; source rules/funding/order |
| COV-07 Mixed invoice | §5.19 correction-first policy | D08/D18/D08-L | AC-11–13/52; Finance early liability/credit |
| COV-08 Remedy/security | §5.20 typed actions and verification | D35/D37 | AC-16/29/53/55; custody/native/security mandates |
| COV-09 Delay | §5.19 adjustment proposal/decision | D36 variants | AC-54; operative term/calendar/native mapping |
| COV-10 Closure/termination | §5.21 correction/settlement commands | D38/D39 | AC-56/57; authority/survivor rule |
| COV-11 Other work | §6.3 priority/read/task deduplication | D40; all five case tabs | AC-19/59; shared task/read services |
| COV-12 Evidence | §§15/17 exact source/installed verification | Document previews and supported native fields | AC-24/45–47; legal/template/shared owner proof |

Deliver six packages within one module: A foundations (source/authority/holds/task/native contracts); B both entry routes and formation; C delivery/inspection/acceptance/native stock/assets/services; D certification/embedded Finance/advances/settlement; E changes/delay/warranty/security/reporting/termination; F closure and whole-chain verification. Specify all boundaries before requirements approval, then implement incrementally with an early narrow full-chain scenario. Each package retains its own failed/stale/denied/correction states. Package B alone cannot be called a complete CM MVP. The final acceptance suite includes normal goods, mixed acceptance/replacement, multiple delivery/invoice/instalments, quantity variation, disputed delay, paid-unit warranty, termination with advance, and imported prior activity; isolated branches must never alter canonical source fixtures.

## 15. Implementation and test constraints

Use the supported Frappe v16 extension/event facilities and native document methods; no ERPNext core fork or direct ledger writes. Preserve core validations and native cancel/amend/reversal rules. Prove on the exact installed Frappe/ERPNext/KenTender versions, not merely the inspected upstream commit.

Build reusable KenTender editors, review sheets, status projections and document previews around a controlled native-record adapter. Verify all required installed native fields and workflow transitions are supported before enabling a journey. UI components never replace server-side permissions/validation. Include CM-AC-45–47 in installed-site proof.

Bind financial and item classifications to configured Company, accounts, taxes, UOM, warehouses and asset categories without inventing business defaults. Retry and concurrency controls are server-side and transaction-aware. No release by document approval alone; existing Gate 1 boundaries and shared Trust/operating controls remain unchanged.

## 16. Prohibited shortcuts

No duplicate invoice or stock ledger, generic acceptance checkbox, arbitrary approval chain, hidden supplier score, retrospective signed-document edit, waiver by comment, “paid” inferred from zero balance, publication completion inferred from a queued job, or CM completion inferred from Stage 1 alone. No unsupported actions disguised as “Record outcome”. No routine redirect/iframe to standard Frappe forms, duplicate entry of already captured facts, competing accounting balances, hidden native validation failures or approval/cancellation/reversal bypass through a custom screen.

## 17. Evidence, coordinated changes and approval conditions

### 17.1 Source status and legal findings

CM v0.2 records a 3 October 2026 reading of the official High Court judgment *Roads and Civil Engineering Contractors Association & another v Attorney General & another*, [2025] KEHC 19224, 4 December 2025, paragraph 65, quashing the 2020 Regulations, and the Court of Appeal judgment *Kalmar Finland OY v PPARB & 5 others*, [2026] KECA 1500, 24 July 2026, paragraph 100. Those are inherited research findings. This reconciliation obtained the High Court dispositive passage through indexed official-source search; direct judgment/PDF retrieval failed. It did not independently re-read the Court of Appeal passage or establish the absence of later stays, appeals or replacement instruments. The latest operative position must be established under CM-LEGAL-01.

Consequently CTM’s Regulations-only committee representation, fourteen-day publication/monthly-report clocks, sixty-day statutory payment/final-acceptance rules, security threshold, extension prohibition and Attorney-General route are not imported as current statutory defaults. A source independently established in the Act, issued terms or an express product control must retain that classification. A historical finding is not a verified executable profile.

**9 October 2026 primary-text correction.** The government-hosted Kenya Law revised-2022 Act PDF linked in §17.6 was successfully downloaded (SHA-256 `44e276d746d9776d3a5fe5c7011a0959f2a56f84a5d88244c27b8540529fd842`). Its extracted text has an encoding defect; rendered printed/PDF p. 70 was visually inspected directly for §§146–148, rather than inferred from search snippets or the contents headings. Section 146’s body contains the executed/delivered-and-accepted payment condition, acceptance by the AO or an officer authorised in writing, the specified tender/contract exception and the no-advance-before-signature restriction. Section 147’s body contains the exceptional advance cap of 20% and equivalent advance security; §148 concerns use for tender activities and recovery for misuse. The rendered §147 heading anomalously repeats the performance-security heading; this is preserved in the source extract and is not used to infer its body. §§5.6/5.9/5.11 now identify the actual inspected edition/page. This closes only that narrow body-text retrieval question, not operative law, amendments, litigation, institutional applicability or all CM citations. The preceding indexed-only finding was insufficient evidence and is superseded by this direct inspection. CM-LEGAL-01 remains open for the current legal profile and every remaining citation.

Act-section findings already specified in §§5.6/5.9/5.11 are retained from CM v0.2’s reviewed revised-2022 text, not newly certified current law through this revision. This document does not settle eGP coexistence or institutional adoption authority. The historical donor source locators are retained in §17.6; the donor extension is deferred and no project applicability is asserted. A Kenya profile cannot be silently replaced by selecting a funding source.

### 17.2 Technical findings and proof boundary

The supplied Fit and Gap v0.1 is a source-level assessment pinned to ERPNext `af63cde4941570ec7b9e12422c68302762cfcf91`, not installed-site proof. CM v0.2 records later source findings about Quality Inspection default/manual results, Stock Controller warning/post-receipt paths, configurable fiscal-year invoice duplicate checks and rejected-material valuation/billing; the cited Fit and Gap v0.2 was not supplied here. These are retained predecessor findings, not fresh source reads or passed integration tests.

v0.4 retains the design response: generated frozen criteria and Needs review, accepted-subset native postings, evidenced custody/ownership, locked entitlement allocations, payment holds through every native path, maker/approver separation, settlement evidence and recovery by stable operation identity. ERPNext reuse remains the selected architecture; installed proof must establish its configuration and remaining extensions before affected package acceptance and production enablement, under the separate gates below.

### 17.3 Approval evidence and scope decisions

| ID | Owner / exact evidence | Remaining effect |
|---|---|---|
| CM-LEGAL-01 | Legal/procurement owner: effective Act/instruments, litigation/status through intended deployment, operative publication/reporting directions, final-acceptance/security/closure and eGP official-action ownership. Record instruments, locators, date, reviewer and consequential rules. | No production legal profile activation; historical Regulations defaults stay disabled. |
| CM-TPL-01 | Template owner: exact installed release identity/manifest, executed form/SCC, source-to-agreement/certificate mappings, supported payment/advance/security/acceptance/warranty clauses and renderer artifacts. Start from approved STD-TPL v0.15, preserving older published releases. | Final agreement/certificate design previews and exact contract-rule defaults remain open. Destination families alone do not prove a finished renderer. |
| CM-PROOF-01 | ERPNext/Finance owner: accepted/rejected/partial/return/replacement, related services, serials and fixed assets on exact installed commits; ownership/custody, ledgers, recovery and cancellation evidence. | Posting feasibility/configuration is unverified. Evidence gates package C acceptance; materially different results require a reviewed requirements amendment before affected behaviour is accepted. |
| CM-PROOF-02 | Finance/AUTH owner: native maker/approver and payment holds, early liability, partial cash/credits/recoveries, duplicate/concurrent claims, Journal Entry/reconciliation bypasses, settlement/reversal and imported opening balances. Provide policy and authority bindings; prove the KenTender invoice/payment editors, native transitions and protected/status projections in CM-AC-45–47. | Native Finance integration is not approved as complete until proved. |
| CM-FUND-01 | Budget owner: exact allocation/rounding, permitted remainder-release events, increased commitment handling and applied §5.14.1 closing/position contract; adapter tests on the actual BUD successor preserving pending reader changes. | Linked funding conversion/finalisation cannot be assumed available; CM must not invent owner API or release shared holds. |
| CM-SHARED-01 | Obtain remaining current TRUST, LAW, SEED-OPS, document-control and baseline-register sources; reconcile supplied AUTH v1.11/CFG v0.18 with pending successor proposals; confirm existing extension points, registry bindings, signing fallback and seed procedure. OVS source is also required before changing its shared oversight contract. | Reconciliation uses only supplied current documents; missing counterparts cannot be labelled amended, approved or fully checked. |
| CM-WB-01 | Historical deferred work: donor edition/project/national-law verification belongs to a future reviewed extension. | Not an MVP1 approval blocker; no donor activation or seeds. |

| Decision | Approved disposition | Approval state |
|---|---|---|
| CM-OD-01 — World Bank extension | Defer donor-specific functionality from MVP1; retain base profile/obligation architecture. | Direction approved with coverage assessment, 8 October 2026. |
| CM-OD-02 — CM capacities and fixture bindings | Reuse canonical people and AUTH registry/resolver mechanisms; proposed CM responsibilities and subject bindings are explicit in §§6/13. No blanket Payments Officer or invented fixture people. | Approved by Project Owner, 14 October 2026; stated source/policy conditions and evidence gates retained. |
| CM-OD-03 — overlapping-work presentation | Approve the declared §10.1 exception: tabs and current-task next step without a misleading linear journey. | Approved by Project Owner, 14 October 2026; stated source/policy conditions and evidence gates retained. |
| CM-OD-04 — mixed invoice policy | Correction-first in §5.19: preserve original receipt; obtain a supported corrected claim before certification, rather than partially certifying the original mixed claim. This can delay the undisputed amount and must be reviewed against issued payment terms. | Approved by Project Owner, 14 October 2026; stated source/policy conditions and evidence gates retained. |
| CM-OD-05 — acceptance proof set | Every required current appointee signs the frozen report; no chair-only or quorum shortcut. Absence requires prospective reconstitution and a successor proof set. | Approved by Project Owner, 14 October 2026; stated source/policy conditions and evidence gates retained. |
| CM-OD-06 — custody and posting | Arrival records segregated custody only; accepted-subset native receipt draft/posting follows effective acceptance. Rejected/unaccepted goods cannot be used or valued as accepted stock. | Approved by Project Owner, 14 October 2026; stated source/policy conditions and evidence gates retained. |
| CM-OD-07 — signature sequence | Supplier signs the frozen agreement first, then the entity signatory signs the same version; no effect from either signature alone unless verified source requires otherwise. | Approved by Project Owner, 14 October 2026; stated source/policy conditions and evidence gates retained. |
| CM-OD-08 — settlement recorder | Current Finance approver may record evidenced settlement of their approved entry; payment maker and procurement certifier excluded; no bank execution. A verified native policy requiring a different reconciler supersedes this fixture through review. | Approved by Project Owner, 14 October 2026; stated source/policy conditions and evidence gates retained. |
| CM-OD-09 — acceptance/certification separation | An actual acceptance signer cannot procure-certify a claim relying on that acceptance. Brian is appointed procurement member; Charles retains HOP certification/security/completion duties. | Approved by Project Owner, 14 October 2026; stated source/policy conditions and evidence gates retained. |

**Separate approval gates.** (1) Requirements approval reviews the complete lifecycle, CM-OD decisions and proposed owner contracts; open evidence items remain individually recorded with accountable owners and affected packages. (2) Authorised feasibility work may inspect installed dependencies and implement narrowly isolated prototypes for CM-PROOF/FUND/TPL/SHARED evidence; it does not enable consequential production actions or count as package completion. Requirements approval authorises incremental A–F implementation, not release. (3) Package acceptance requires applied owner contracts and passed evidence for its own boundaries: TPL/SHARED for formation and signing, PROOF-01 for receipts/assets, PROOF-02 for Finance/payment paths, FUND-01 for linked funding, and legal-source verification for affected executable rules. Failed evidence triggers a reviewed amendment and holds only affected behaviour. (4) Production readiness requires CM-LEGAL-01 current applicability/operative instruments, Trust/provider clearance, all applicable package/whole-chain acceptance and explicit release authority. No unverified rule or payment/posting path is enabled merely because requirements were approved. Open dependencies cannot be described as complete.

Production Trust/provider clearance remains a separate release gate. “Proceed” authorised preparing this document; it did not approve a real contract, verify a legal profile, amend owner baselines or establish integration success.

### 17.4 Exact counterpart amendment schedule

These are proposed owner edits, with their target sections and result, contained here for coordinated review. Per-owner change instructions are listed in §17.10; current owner files must be amended in place without importing stale full copies. No live-register edits are claimed. On approval, apply them to actual current owner versions and register the new identities atomically at the documentation level.

| ID / supplied target | Required amendment / retained boundary |
|---|---|
| CM-CP-01 / AWD v0.5 §§1/3/5.8/7 and AWD-IF-05 | Replace destination label Contracting with Contract Management — Prepare and sign. Preserve independent `AwardDecisionRecorded v1`, package/update acknowledgements, current-authority rechecks and original trigger times. Register receiver names already consumed by CM §7; add no transmission approval or signature-only publication trigger. |
| CM-CP-02 / BUD v1.12 §§4.6/4.9/5/9.1; pending v1.13 audience proposal | Apply exact §5.14.1 close_commitment contract and Closed-amount position semantics; preserve existing services, funding-reader proposal and multi-commitment reservation history. Add owner closure/concurrency/adjustment tests. No status-induced release, CM table writes or new appropriation ledger. This amendment is specified here but not claimed applied to BUD. |
| CM-CP-03 / TPR v0.17 §4.5.3 and STD-TPL v0.15 §9.2 | Verify concrete mappings for goods, offered technical values, related services, acceptance, warranty/support, awarded price/discount allocation and source funding. Eligibility-only responses remain Not carried forward. Add only demonstrated missing mappings in a successor release; never repair a previously issued tender in place. Exact current release/renderer must be inspected under CM-TPL-01. |
| CM-CP-04 / BDS v0.11 §§6/9 navigation and own-organisation projections | Link My contracts to CM’s supplier routes if CM is installed. Reuse supplier identity; signing and contract claim rights remain CM-owned. No bid mutation, competitor/internal Finance disclosure or bidding-app dependency for CM. |
| CM-CP-05 / PRC v0.11 §§2/6/7 | Define a CM owner projection only where inspection/change proceedings require the shared facility. Link immutable appointment/report/proof references; do not transfer acceptance/variation authority or add a generic committee gate to every action. |
| CM-CP-06 / KT-STD v1.25 §8.3 | Add the reviewed CM-only bindings in §§6/13 after coordinated approval for existing actors, with appointments/effective periods and isolated fixture identity. Preserve David Ouma, current OUs, expired assignments, technical read and canonical supplier people. A person’s existence or Evaluation appointment grants no CM capacity. No visual-standard rewrite is needed; the CM tracker exception remains in CM. |
| CM-CP-07 / supplied AUTH v1.11 and pending v1.12 proposal; current TRUST not supplied | Add §6.2 responsibilities using existing Site-wide/Organisation Unit types only; preserve pending role-bound reader amendment. Register CM subject/read profiles, personal appointments and segregation without adding Contract scope_type or duplicating assignment machinery. Trust signature targets include changes, adjustment/claim decisions, closure correction and settlement. Actual extension validation remains open. |
| CM-CP-08 / current LAW/SEED-OPS/registers (not supplied) | Record profile verification and actual legal directions; add CM stage after Award using actual generated source references; keep the isolated ten-laptop, external intake and correction branches separate; remove donor branches from MVP1 seeds. Record CM’s actual current review status with exact dependencies/decisions and document hashes; obtain all owner versions/statuses from the current register. No guessed successor numbers, approvals or completed seed claims. |

The ZIP’s versions/statuses remain authoritative for supplied owners. Its approved KT-STD v1.25 supersedes presentation proposals retained in its narrative. The ZIP does not contain TRUST/LAW/SEED-OPS or either current register; this document cannot certify their current contents from predecessor citations.

#### 17.4.1 Current-source coordination and application status

The 7 October permissions package proposes AUTH1.12, CFG0.19, KT-STD1.26, BUD1.13, AWD0.6, PRC0.12 and other owner successors. They are proposed reader reconciliations, not silently approved baselines. CM v0.5 consumes the approved predecessor identities and explicitly defines its own complete read contract. Apply its counterpart changes on the actual latest owner working copies, retaining those proposed audience clauses and any subsequently reviewed secretary/home-unit work; do not produce duplicate successor numbers.

CFG owns setup records/native configuration; CM adds no global entity, department or fiscal context, no runtime rule editor and no new setup approval. Required CM native mappings/authority registry entries must be inspected through the existing setup/diagnostic facilities and verified before journeys enable. KT-STD owns fixtures and shared surfaces; append only the reviewed CM branch capacities/isolated fixture identities, no changes to canonical Award amounts or existing role office holders. BUD owns close_commitment and field/position semantics; apply §5.14.1 in its owner sections. AWD retains original transport/receipt and clock identities with destination label changed. PRC/BDS are optional navigation/projections, not authority or installation dependencies.

This revision supplies per-owner change instructions in §17.10. The previous full-copy handoff is withdrawn because owner documents have changed externally; current owner baselines and newer work govern each amendment. Earlier TRUST/LAW/SEED-OPS/register sources were subsequently located (§17.10), but their current successors remain unresolved; no installed result or owner approval is invented. Coordinated owner application and proof remain explicit gates for affected package acceptance and production enablement, rather than prerequisites to authorising their design or feasibility work.

### 17.5 Interface ownership

| ID | Producer / consumer | Contract |
|---|---|---|
| CM-IF-01 | Optional Award adapter → CM | Approved AWD v0.5 package/publication/update contracts; CM §7 durable receiver, no direct tender table dependency. |
| CM-IF-02 | Published definition/issued contract source → CM | TPR v0.17 projection and STD-TPL v0.15 destinations consumed as immutable obligations tied to exact published release; no free-text reconstruction. |
| CM-IF-03 | CM ↔ ERPNext | Unique native transaction/row/version/operation links; entitlement/authority/reversal/settlement controls; CM-PROOF-01/02. |
| CM-IF-04 | AUTH/Trust/tasks ↔ CM | Actual current extension contracts and verified appointments; no parallel role/signing/task engine; CM-SHARED-01. |
| CM-IF-05 | Optional BDS/PRC ↔ CM | Same supplier contract projection and exact immutable proceedings references; no new authority from navigation. |
| CM-IF-06 | External signed-contract intake → CM | Attributed source/terms and reconciled cutover; no historical reposting or claimed eGP verification. |
| CM-IF-07 | CM ↔ Budget | Existing BUD v1.12 services plus proposed owner closure contract; CM §5.14; no distributed signature rollback claim. |
| CM-IF-08 | Profile evidence owner → CM | Code/version binding and reviewed applicability/effective successor; business source-evidence capture is not profile activation. |

### 17.6 Research and supplied-source register

| Source | Access in this reconciliation | Use / limit |
|---|---|---|
| CM v0.2; CTM v0.1; Basis v0.3; Fit and Gap v0.1 | Supplied local copies | Working requirements, comparison and provenance; approvals not inferred. |
| KT-STD v1.25; AWD v0.5; BUD v1.12; TPR v0.17; STD-TPL v0.15; BDS v0.11; PRC v0.11 | Supplied ZIP; relevant controlling/status, interface, template, authority, design and fixture passages inspected | Current owner alignment. Inspection of relevant passages is not a claim that every line or installed artifact passed review. |
| STR v1.9; NDS v1.16; PLN v1.29; REQ v1.14; BOP v0.11; EVL v0.5 | Supplied ZIP identities and CM-related source references checked as applicable | Existing upstream flow retained; unrelated module behaviours are not revised. |
| World Bank Seventh Edition, September 2025 | Official PDF inspected 6 October 2026, §2.1, §§5.97–5.98, Annex II §§6.2/9, Annex XI | Historical deferred source only; no operative MVP1 donor profile or duty. |
| High Court judgment [2025] KEHC 19224 | Indexed official-source dispositive passage retrieved; direct official fetch failed | Supports preserving legal uncertainty; no complete current-docket assurance. |
| Court of Appeal [2026] KECA 1500; revised-2022 Act; ERPNext commit findings | Inherited CM v0.2 research; not independently fully re-read here | Findings remain explicitly bounded by CM-LEGAL-01/CM-PROOF-01/02. |
| Government-hosted revised-2022 Act, printed/PDF p. 70 | Downloaded 9 October 2026; rendered §§146–148 bodies visually inspected; exact source hash in §17.1 | Supports the narrow body-text statements; no complete/current-law clearance. Part XI source extract accompanies the handoff for further citation review. |
| AUTH v1.11; CFG v0.18; permissions successors AUTH1.12/CFG0.19/KT-STD1.26/BUD1.13/AWD0.6 | Supplied current documents and prior proposed successor working copies; relevant scope/registry/position/reader passages inspected 8 October 2026 | Reconciled own CM rules and exact counterpart schedule; proposed successors are not approved baselines or installed proof. |
| Basis v0.4; Fit and Gap v0.2; TRUST/LAW/SEED-OPS/current registers | Not supplied; no retrieval claimed | Resolve actual sources before asserting counterpart completeness. |

Primary reference links:

- [World Bank IPF Procurement Regulations, Seventh Edition, September 2025](https://thedocs.worldbank.org/en/doc/c84273d1b230aeb2b0b8134de5dc8cd7-0290012025/original/Procurement-Regulations-7th-Edition-Sep-2025.pdf).
- [High Court judgment [2025] KEHC 19224](https://new.kenyalaw.org/akn/ke/judgment/kehc/2025/19224/eng@2025-12-04/source.pdf).
- [Court of Appeal judgment [2026] KECA 1500](https://new.kenyalaw.org/akn/ke/judgment/keca/2026/1500/eng@2026-07-24/source.pdf).
- [Kenya Law Act, revised-2022 source](https://new.kenyalaw.org/akn/ke/act/2015/33/eng@2022-12-31/source).
- [Act, revised-2022 government-hosted copy](https://pppkenya.go.ke/wp-content/uploads/2020/07/Public-Procurement-and-Asset-Disposal-Act-33-of-2015-Revised-2022.pdf).
- [Historical 2020 Regulations](https://www.treasury.go.ke/sites/default/files/PPDA/Public-Procurement-and-Asset-Disposal-Regulations-2020.pdf).
- [ERPNext inspected predecessor commit](https://github.com/frappe/erpnext/tree/af63cde4941570ec7b9e12422c68302762cfcf91).

### 17.7 Compact change and decision record

v0.3 retains CM’s complete lifecycle, automated inspection, ERPNext operational ownership, lawful advances, native Finance and authorised closure. It adds profile/compliance/report structures, explicit handoffs/segregation, partial settlement, Budget owner contracts and a proposed donor extension. It corrects David’s identity, latest technical-read treatment, current source versions, fictional companion-successor claims and unprovided-document provenance. The v0.3 historical additions covered appointments, declaration, security, outside signatures, changes, advances, partial payments and then-proposed donor obligations; interaction/test mappings remain in the same document. No owner approval, legal clearance or runtime test result is promoted.

**7 October 2026, within v0.3:** user requested the CM update following the ERPNext-reuse UX discussion. KenTender now owns routine entry/display/review/approval; native operational ownership is preserved. Removed native-form payment handoffs; specified embedded invoice/payment preparation, approval/return, protected projections, native validation and additional acceptance scenarios CM-AC-45–47. This revision changes requirements and fixtures, not installed software or approval status.

### 17.8 Reconciliation review and remaining sequence

The 7 October UI revision was checked for removal of routine native-form handoffs, alignment of Finance screen actions/commands and preservation of native ownership/controls. The 7 October acceptance register contained 47 CM scenarios and 5 conditional donor scenarios. The v0.7 register contains 64 CM scenarios, including four usability outcomes; the 5 donor scenarios are retired from MVP1. None is reported as passed.

The v0.4 document review covered section numbering, action-to-command mapping and fixture identity/amount chronology, but the independent review identified gaps corrected below; no claim of exhaustive reconciliation is made. Review also covered exact source versions, Budget authority/operation boundaries, overlapping status/remaining-obligation treatment, supplier and technical read, deferred donor scope and truthful approval/evidence status. This is a document review; runtime checks in §14 remain required future tests.

Next: CM v0.7 and CM-OD-01–09 product dispositions are approved as recorded on 14 October 2026; obtain current shared/registered sources and apply coordinated owner amendments. Authorise isolated feasibility work to close TPL/SHARED/PROOF/FUND evidence and revise requirements where results differ. Implement A–F incrementally after requirements approval; accept each package against its evidence gates. Verify current legal applicability and complete whole-chain/Trust checks before production release. Signing preview acceptance cannot be claimed before the exact source-rendered documents are available.

### 17.9 Coverage revision and verification record — 8 October 2026

v0.4 integrates approved assessment findings COV-01–12 into domain, authority/read, operation/correction, task, design/interaction and acceptance sections. It removes donor activation/screens/commands/tests from MVP1, resolves receipt-draft timing, states correction-first mixed-claim policy and specifies a proposed zero-effect Budget closure with retained funding charge. New D34–D40 and D08-L supply quantity variation, paid warranty remedy, delay adjustment, security claim, closure correction, termination settlement and simultaneous-work/reader states. AC-48–60 verify the new behaviour; none has been executed.

The v0.4 consistency checks covered headings/trace IDs, exact synthetic quantities/amounts, command/action mapping, remaining donor operational references, receipt-timing wording, scope-type compatibility, retained proof and truthful approval/dependency status. That revision’s legal findings were inherited evidence-bound statements. The v0.5 narrow citation check is recorded in §17.1; complete current-law clearance remains open. Installed ERPNext/configuration/authority/Trust/Budget feasibility remains CM-PROOF/CM-SHARED/CM-FUND evidence. Source-rendered previews remain CM-TPL-01. The scope/coverage direction is approved; new detailed policies/interfaces are proposed for review in this single successor.

### 17.10 Owner change instructions and Claude Code feasibility handoff — 9 October 2026

**Apply changes to the current owner documents.** The user confirmed on 9 October 2026 that the other module documents have changed outside this workspace. Their current working copies govern. The previously supplied complete owner-document proposals are withdrawn as merge inputs; do not replace current files with them or reuse their assumed successor numbers. The handoff now describes the required outcomes by document. CM v0.5 remains the CM requirements source; these are cross-module amendments, not another CM specification.

For each current document: locate the equivalent owner sections, determine what is already satisfied, add only missing clauses and update affected references/tests. Preserve unrelated and newer changes. Return Applied / Already satisfied / Conflict or missing evidence per change, with exact current/resulting identity, section and diff. A material conflicting requirement remains explicit for resolution; do not silently choose the older copy. Obtain version numbers and document status from the current control process; this instruction supplies neither approval nor successor numbers.

| Current owner document | Changes to include | Verification / boundary |
|---|---|---|
| AUTH-ADR-001 — responsibilities and authorization | Bind CM preparation, coordination and Receiving to managing-OU scope; inspection, technical certification and entity signing to Site-wide registry responsibility **plus exact current CM subject appointment/mandate**; Finance preparation/approval to Site-wide plus native permissions. Reuse existing office/registry/resolver mechanisms or map equivalent current entries; do not duplicate them. Apply CM §6.2 read profiles to lists, counts, direct pages, five tabs, evidence, documents and exports. AO/HOPF read all cases without a task; Heads of User Department read managing-OU or immutable source-participation cases; technical business read follows current shared policy. Enforce receiver/acceptance, acceptance-signer/procurement-certifier, maker/approver and maker-or-procurement-certifier/settlement separation using actual subject history. | Map current entries/codes; no new Contract scope type, parallel assignment engine, home-unit authority or task-based read gate. Pending/conflicted appointees retain permitted context but cannot act on affected scope. Verify every role, separate multi-role scopes and API/native bypasses. CM-OD-08/09 remain explicit proposed product controls. |
| CFG-CHG-002 — setup and diagnostics | Expose/inspect CM integration readiness through existing setup facilities: registry mappings, native stock/assets/item classification, Finance workflow/accounts/beneficiary projections, currency precision and Trust configuration. Name the missing mapping and recovery owner; hold the affected operation while retaining permitted case reads. | No global CM-ready waiver, new entity/FY context, runtime rule editor or extra setup approval. Preserve current staff home-unit and secretary-delegation work; neither becomes CM authority. Standard Frappe forms remain specialist setup/diagnosis, while routine CM entry and review remain in KenTender. |
| BUD-CHG-001 — commitment model, positions and owner services | Define proposed owner `close_commitment(commitment_id, expected_revision, contract_outcome_event, reconciliation_evidence_refs, idempotency_key)` or reconcile an equivalent current service. Validate exact CM Closed/termination-settlement outcome, lineage, supported amount and revision under locks; return durable closed revision/acknowledgement. Apply any supported final decrease separately through adjustment. Closure retains current_amount and creates a zero-amount attributed closure event; **Committed includes Active and Closed retained amounts**. Carry this into positions, successor floors and protected line-omission checks. Permit evidenced decreases/corrections without erasing closure/history or replenishing reservations; increases require eligible owner funding and cannot bypass a closed FY. | Closing changes neither Available nor amount, and confirms neither payment nor bank transfer. A Cancelled status cannot hide a legitimate positive amount outside positions. Test replay/conflicting payload, stale revision, adjust/close races, shared reservation, Closed charge and omission/floor protection. Distinguish commitment closure from Budget-year closure. |
| AWD-CHG-001 — downstream ownership, navigation and handoff | Use destination label **Contract Management — Prepare and sign**. Preserve versioned Award package, independent AwardDecisionRecorded/publication event, restriction/update messages, stable event identities, original trigger times and durable acknowledgements. Map receiver operations to CM’s current owner adapters. | Rename user-facing destination only; do not rename deployed API/schema from a label. Add no send approval, repeated acceptance or signature-only publication clock. Verify duplicate receipt, late restriction and independent publication delivery; preserve canonical Award amounts/people. |
| TPR-CHG-001 — published-source projection | Ensure the immutable published source carries release/instance, requirement and supplier-response identities; goods/UOM/quantity, offered technical values, related services/evidence, acceptance criteria, awarded price/discount/tax allocations, funding links, and issued delivery/payment/advance/warranty/security terms with clause locators. | Eligibility-only declarations remain Not carried forward. Identify demonstrated gaps; no invented defaults, Item-master reinterpretation or edit of an already issued tender. Verify each carried value against the installed release. |
| STD-TPL-001 — contract mappings and outputs | Map the issued source to the agreement and required technical/acceptance/completion outputs, including goods/services, acceptance, payment/advance recovery, warranty/support, security, changes/completion and monetary/source allocation. Retain exact clause/value/response/release lineage; provide actual installed renderer previews and missing-coverage results. | Add only demonstrated missing mappings to a compatible future release; preserve published instances/digests and current simple setup/On-Off process. A mapping family name is not a completed renderer. CM-TPL-01 stays open until actual outputs are reviewed. |
| BDS-CHG-001 — supplier navigation | Where CM is installed and the actor has an authorized own-organisation projection, link **My contracts** to the KenTender CM supplier workspace. CM checks representative claim/reply rights and current signatory rights independently of bid-submission authority. | Omit optional navigation when CM is absent; preserve public discovery/bidding. No competitor, internal deliberation, staff declarations, funding allocation, account or protected-bank exposure. Verify direct links/exports and expired/cross-supplier authority. |
| PRC-CHG-001 — owner proceedings profile | Add a CM projection only where inspection/change proceedings use the shared facility. Link exact immutable appointment/declaration/report/proof/recommendation/decision versions, with CM-authorized audiences and retained correction lineage. | Shared proceedings confer no inspection, variation, signing or Finance authority. Add no generic committee gate or mandatory PRC dependency to every contract action; preserve existing Opening/Evaluation profiles. |
| KT-STD-001 / current shared fixture register | Record reviewed CM-only capacities for existing people: Julia Njeri chair/coordinator, Peter Mugo technical member/certifier, **Brian Wafula procurement inspection member**, Charles Mutiso HOPF invoice certifier/security/completion duties, Grace Wanjiku receiver, Josphat Finance maker and Beatrice Finance approver. Preserve Grace Wambui as a distinct change reviewer; Evaluation appointments grant no CM authority. Isolate base, TERM, security-return, security-verification, warranty, security-claim and other CM branches using §10’s complete identities/chronology. Record the proposed tabs/current-task presentation exception without rewriting the shared visual standard. | Effective assignments, appointments and personal declarations required; creating a person grants nothing. Preserve upstream canonical OUs, amounts/offices and current home-unit corrections. Record CM-OD-03 and the other CM product dispositions as approved on 14 October 2026; externally maintained owner adoption remains separately recorded. |
| TRUST-ADR-001 — owner signature targets | Reuse current signing/attestation extension contracts for exact agreement/amendment, acceptance/technical certification and any decision/completion targets requiring proof under the verified source. CM supplies actor authority, frozen subject/version, target and purpose; Trust owns provider verification/evidence. Preserve personal action, rejected/unavailable/indeterminate states and same-operation reconciliation. | Check current fallback/provider policy rather than restoring the old ADR. No second signing engine, proxy signing, workflow-click legal-signature claim or fabricated success on timeout. Unverified production method/legal equivalence remains a release gate. |
| LAW-REG-001 / legal-profile owner | Register CM’s outstanding current-source questions separately from product decisions: applicability of Act §§48,138,139(2A)/(4),140,145,146–148,150(3),152,154; operative instrument/litigation/stay/replacement status; reporting/publication directions, final acceptance/security and official eGP action ownership. For each record source edition/locator/date, applicability, reviewer finding and affected executable rule. | This is a verification queue, not a new legal opinion or approved constant. Preserve any newer verified findings. Synthetic fixture ceilings/terms remain synthetic until verified; no historical Regulations-only default silently activates. |
| SEED-OPS-001 — current seed/runbook | Add CM after the actual Award stage through supported domain commands once the reviewed capability exists. Describe generated-reference relationships, assignments/appointments/declarations and isolated receipt/credit/termination/security/warranty/intake branches. Include rerun/restore, negative-authority and uncertain-operation outcomes. | Preserve current stages and upstream canonical data. Do not hardcode production counter results or invent installed commands. Do not reset earlier records merely to fit a screen, use typed-reference bypasses or report seeds executed without evidence. |
| Current baseline register and Documentation Control Register | Register the actual resulting CM/owner filenames, versions, dependencies, open decisions/evidence and hashes under the current schema. Keep requirements, implementation, verification and release status distinct; synchronize the existing workbook from its actual authoritative register. | Do not import the old register wholesale or reset newer approvals/statuses. Record new amendments as proposals until approved; preserve prior approvals as history. This handoff provides no assumed owner version, approval, implementation pass or release. |

These amendments retain the selected MVP scope and existing controls. Where the current owner already provides the outcome, record Already satisfied with its exact evidence and make no duplicate clause or service. Documentation readiness and installed feasibility remain separately demonstrated under the following handoff.

Additional earlier sources located and inspected in part: TRUST v0.1 (27 September architecture decision; full text read), LAW v1.2, SEED-OPS v1.19 and the 1 October baseline register (targeted initial sections read). The latter three are older than the current ZIP and their remaining contents/current successors were not verified. The old register still contains predecessor versions and therefore is not overwritten as the current baseline. Trust already distinguishes owner authority, exact targets and Unavailable/Rejected/Indeterminate/Verified results; no second signing engine is needed. Its production provider/legal-equivalence deferral remains in force. Current documentation workbook, newer register/Trust/legal/runbook identities and installed extensions remain CM-SHARED-01 evidence; discovery of an older source does not close it.

**Handoff to Claude Code.** Use CM v0.5 as the single CM requirements/design/fixture/acceptance source and the per-document changes above as documentation amendment instructions. Do not use the withdrawn full owner-document copies as merge input. First read the actual repository instructions, current controlled requirements/registers and installed app commits. Read the current owner files and identify equivalent sections and already implemented outcomes; preserve newer permissions, Home organisation unit and HOPF secretary-delegation work. Identify source conflicts explicitly; apply nonconflicting CM clauses in the owner sections, assign successor numbers from the actual current register, and return exact diffs/identities/hashes. Do not mark requirements or product decisions approved from this handoff. The user has authorised preparation and investigation; production changes and real contractual/financial operations are outside this evidence task.

Work on an isolated synthetic site/branch. Implement only the minimal feasibility harness/adapters needed to test the following boundaries; no real bids, signatures, inventory or cash. Use actual domain/server/native methods and current responsibilities, not database setup that bypasses the control being proved. A working draft or test attestation is not a legal signature. Keep routine entry/review in the KenTender UI; separately authorised native setup/diagnosis does not count as the product journey.

| Evidence | Concrete investigation | Required returned proof / gate |
|---|---|---|
| CM-SHARED-01 | Match proposed responsibilities/read profiles to actual AUTH resolver/registry; inspect Trust target/outcome/task extension contracts and current registers/runbook | Installed codes/commits/extension points, exact owner diffs; AO/HOP all-tab read without task, each role/OU/source/export negative; acceptance signer certification and maker settlement denied server-side. Package A/B boundary evidence; no invented Contract scope |
| CM-TPL-01 | Inspect installed release/instance and actual source-to-contract/certificate mapping | Manifest/digests, field/clause coverage, actual generated agreement/certificate previews; missing mapping becomes named gap. Formation/signing design acceptance held where unsupported |
| CM-PROOF-01 | Trace ten goods: arrival/custody, 8 accepted/2 rejected, all required proofs, accepted-subset receipt, stock/fixed-asset and serials; then return/replacement and related service | Before/after native documents/ledgers and custody/ownership; no arrival receipt, rejected use/valuation or duplicate entitlement; timeouts/cancellation/replay. Package C acceptance evidence |
| CM-PROOF-02 | Native invoice/payment in KenTender, independent maker/approver, early liability+credit, split cash/noncash, payment holds through direct Payment Entry/Journal Entry/reconciliation/API/import/background paths | Native transition/permission/configuration evidence; concurrent overclaim denied; factual settlement independent evidence; original and corrected liability reconcile once; no native-form routine handoff. Package D acceptance evidence |
| CM-FUND-01 | Owner conversion/adjustment and proposed close_commitment on actual BUD revision; shared reservation, legal final decrease and Closed charge | Exact before/after Reserved/Committed/Available; same-key replay and stale/conflict/race failures; Closed commitment remains charged and protects floors/omission; no cash/release inference. Linked funding package acceptance evidence |
| CM-LEGAL-01 | Record available operative editions/directions and route current-status questions to legal/procurement owner | Per-section source/locator/date/applicability and reviewer decision for 48,138,139(2A)/(4),140,145,146–148,150(3),152,154; litigation/stay/replacement and eGP ownership. No runtime constant selected from an unverified historical source; production profile remains disabled |

Return one evidence result per item: Verified with reproduction and exact environment, Failed with observed contradiction, or Not tested/Blocked with missing fact and accountable owner. Include commands/log/test artifacts and required requirements amendments; never label source-code inspection as an executed pass. Failed feasibility changes are reviewed in the authoritative CM/owner documents before acceptance. Do not silently enable production while testing. Requirements approval, package acceptance and production release remain separate.

Seed/runbook integration follows supported commands and reviewed requirements: add a CM stage after the actual Award stage, preserve canonical source values, declare generated-reference relationships rather than hardcoded production counters, isolate TERM/security/warranty/intake/credit branches, and expose restore/rerun results without pretending a nonexistent command already exists. The live baseline/workbook update must record CM v0.7 as Approved on 14 October 2026, implementation Not evidenced, verification Pending and release Not approved, with actual filename/hash/dependencies. Owner proposals retain their own actual approval status. Preserve prior approvals as history; no approval or release is inferred from “Proceed”.

CM-OD-02–09 product dispositions are approved on 14 October 2026 with their stated source/policy conditions. Reconcile the described owner changes against their current documents; applied owner status and feasibility evidence remain open. Feasibility evidence can be gathered while those records are being reviewed, within the isolated scope above.

## 18. Approval effect

Historical v0.5 was proposed; current CM v0.7 requirements and CM-OD-02–09 product dispositions are approved by Project Owner on 14 October 2026. Requirements approval authorises design and incremental implementation within the selected product/profile scope; it may record open evidence with the package gates in §17.3. It does not approve real contractual decisions, verify law, certify installed integration, amend absent registers by implication or establish production release. The stated evidence blockers must close for affected package acceptance and production enablement; World Bank-specific scope is explicitly deferred. Earlier supplied requirements retain their own approval until their reviewed successors are approved.

**8 October 2026 — v0.5 independent-review correction.** Separates acceptance and procurement certification in commands, fixtures and AC-20; exposes six previously implicit product choices as CM-OD-04–09; removes the requirements/proof approval cycle using four gates; gives termination/security/warranty branches explicit identities and chronology; maps Save outcome and includes Grace Wanjiku in the permitted responsible-person filter. Canonical KT-STD identifies Grace Wanjiku (receiver in CM) and Grace Wambui (separately appointed change reviewer) as distinct people; neither name is normalised into the other. Reconciles §146/147 citation use while retaining current-law verification as open. Fixes collapsed fixture text. Review screenshots are independent input, not evidence of installed behaviour or owner approval. No owner files, seeds, design boards or application code have been changed.

**9 October 2026 — focused v0.5 correction.** Separates open claim D16-W/P/D11-B as CM-MOH-2027-WAR-OPEN-001, unit CM-WAR-OPEN-004, from D35’s resolved CM-MOH-2027-WAR-001 remedy. D20-T/D11-T share the accepted-delivery settlement message; SEC-RETURN-001 records 3 Jul verification before both signatures/effectiveness; AC-51 spacing and control date corrected. Primary revised-2022 §§146–148 bodies were directly inspected on p. 70; current-law verification remains open. Reviewer endorsement is recommendation evidence, not Project Owner approval of CM-OD-04–09. CM-OD-08’s separate-reconciler/current-Finance-policy question remains for the Finance/procurement partner. No current external owner documents or runtime code were changed.

### 17.11 Claude Design fixture and presentation correction — 12 October 2026

v0.6 retains the 9 October v0.5 warranty separation and primary-source record. It explicitly binds D32-H to WAR-OPEN-001; gives D14/P and D27/R/A one EXTENSION-001 identity with formation, approval, signing and effectiveness chronology; distinguishes D16’s TEST-G-RETURN-001 from D25’s TEST-G-001; makes normal D05 actionable and D05-M blocked; removes services from goods-only D22; uses Cash confirmed consistently in D15; and defines D10/D40 as one shared, deduplicated task presentation. This is a focused correction within existing scope, not approval of outstanding policies, legal rules or integrations.

Design handoff: use this exact v0.6 for affected D05/M, D10/D40 reader variants, D11-B, D14/P, D15, D16/W/P, D22/P, D25/R/J, D27/R/A and D32/H. Carry resolved identities into headers, links, previews and dialog subjects; regenerate dependent fixture data and screenshots from these facts. No external owner document, runtime application or design board was changed by this document revision. The earlier coordinated-review ZIP contains v0.5 and is historical; it is not the current CM design source. Other-module amendments remain the owner instructions in §17.10, to be reconciled against their externally maintained current versions.

### 17.12 Usability and design consolidation — 12 October 2026

v0.7 keeps the v0.6 scenario corrections and existing business authority/command contracts. It adds the persona journey (§2.1), human-action purpose and automatic-work contract (§6.4), screen-family map (§9.0) and simplicity requirements (§9.2). No forty-page menu is authorised: D-numbers are review identifiers for shared task surfaces and their states. D10/D40 remain one work presentation. Extra list filters are collapsed without removing their capability.

Design instructions use one shared shell with a single evidence/footer order. D04/D05/D12 field/dialog supplements and the separate required-state and exact-waiting overrides are now colocated with their task family; Finance D09-F has one complete editor card. Dense inline variants are separated into local paragraphs. D05 uses Starts = Not recorded/Yes/No consistently. D35’s drawing instruction describes observable state; technical operation ownership remains §11. The reviewed duties and signatures remain required, but their source data, successful checks and handoffs must not create duplicate entry or acknowledgement tasks.

Retained review decisions: source-rendered signing previews, Finance settlement-recorder policy, current legal/native/shared-source evidence and owner amendments remain unresolved as specified in §17. The existing fixture label versus externally changed DEC-044/KT-STD needs current-owner reconciliation; this revision grants no authority to change those external documents. No software, design boards or runtime evidence was produced by this requirements revision.

Usability acceptance: demonstrate one ordinary and one existing-contract journey without a native-form redirect; identify every D-number as a shared screen/task state; show task and holder without opening supporting evidence; enter physical/invoice/Finance facts once; show one leading task and nonduplicated Other work; exercise partial delivery/replacement, invoice correction, failed posting, partial/reversed settlement and open warranty without losing history or inventing completion. Use the CM-AC scenarios together with this walkthrough; document validation alone is not a runtime pass.

### 17.13 Project Owner approval — 14 October 2026

Instruction: “Mark as approved”. CM-CHG-001 v0.7 requirements and artboard specification are Approved. CM-OD-02–09 dispositions, including the declared overlapping-work presentation exception, are approved as product requirements with their recorded conditions. CM-OD-01 donor deferral retains its earlier approval. Document version and revision date remain 0.7 / 12 October 2026; approval date is 14 October 2026. No scope or command behaviour changed in this approval update.

Design and incremental implementation may proceed. Open source-specific Finance policy, legal applicability, source-rendered templates, installed/native/shared-service/funding proof and external owner amendments remain evidence work for the existing package/production gates. This approval is not a runtime test pass or production release. External registers/workbook and owner documents are not edited by this record; their current maintainers must record the actual CM approval without overwriting newer changes.
