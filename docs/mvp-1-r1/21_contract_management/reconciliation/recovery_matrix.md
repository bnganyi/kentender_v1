# CM-CHG-001 v0.8: recovery and correction matrix

| Control | Value |
|---|---|
| Version | 0.8-recovery.1 |
| Date | 14 October 2026 |
| Source | CM v0.8 §5.17 and §5.18, copied verbatim by `tools/build_recovery_matrix.py` (tracker CM8-304); code model in `kentender_contracts/services/recovery.py` and `capabilities.py` |
| Status | The specification columns are approved text. The **Code model** columns are an authored reading of the prose into guarded consequences and are **for owner review** |

**Counts:** 8 operation rows (§5.17) and 9 correction rows (§5.18).

**Rule** (CM v0.8 §5.17, verbatim): "Evaluate every open hold independently. The permitted action set is the intersection of all applicable guards; the most prominent task never masks another restriction."

## Guarded consequences

| Key | Consequence a hold can block |
|---|---|
| `new_signing_attempt` | Start another signing attempt |
| `activate_contract` | Treat the agreement as in force |
| `convert_funding` | Convert or adjust funding on an assumed effect |
| `create_order` | Create or change the native purchase order on an assumed effect |
| `post_receipt` | Post a native receipt or asset |
| `new_spending` | Begin new supported spending |
| `certify_invoice` | Certify an invoice or claim for payment |
| `certify_advance` | Certify an advance for payment |
| `pay` | Prepare, approve or submit a payment |
| `confirm_settlement` | Confirm that a payment settled |
| `claim_cash_paid` | State that cash was paid |
| `use_goods` | Use or dispose of goods |
| `vary_contract` | Vary, extend or waive a contract term |
| `release_funds` | Release committed funds |
| `mark_financially_finalised` | Show the contract as financially finalised |
| `final_accept` | Record final acceptance |
| `close_contract` | Sign close-out |
| `close_claim` | Close a warranty claim on a verified remedy |

Recording a fact, an issue, a supplier claim or a lawfully required liability is never blocked by a hold; it stays within the actor's authority (§5.17).

## §5.17 Operation failure and permitted-work matrix

| ID | Pending / failed operation | Truthful state and permitted work | Blocked consequences | Recovery / resumption | Spec line | Code model: raised by | Blocks | Recovery owner |
|---|---|---|---|---|---|---|---|---|
| R17-01 | Signature outcome uncertain | Awaiting signatures; read frozen version and record incidents | New attempt, Active, PO/funding conversion based on assumed formation | Trust recovery reconciles original attempt; proceed only with exact verified proof/effectiveness | 388 | Signing attempt; states Attempting, Uncertain | `new_signing_attempt`, `activate_contract`, `convert_funding`, `create_order` | Trust recovery |
| R17-02 | Agreement effective; Budget conversion or PO failed | Active; Contract signed — funding/order update pending; retain proof, physical custody/observations and supplier claim capture | Native receipt/asset posting, new supported spending and payment until required funding/order guards pass | Separate Budget and native-order operation records; technical recovery with HOP/Budget owner where business correction required; both required results must reconcile | 389 | Funding conversion, Purchase order (subject `agreement…`); states Recorded, Attempting, Failed, Uncertain | `post_receipt`, `new_spending`, `pay` | Technical recovery; Budget owner |
| R17-03 | Acceptance signed; receipt/asset posting failed | Effective acceptance retained; stock/asset update pending; read/report evidence and receive invoice claim | Ordinary accepted-goods certification and payment based on missing/stale native result; use/disposal of unposted goods | Technical owner reconciles exact accepted subset/native result; no repeat report signatures. Lawful early liability recognition is permitted with payment hold | 390 | Accepted receipt; states Recorded, Attempting, Failed, Uncertain | `certify_invoice`, `pay`, `use_goods` | Technical recovery |
| R17-04 | Native invoice posting uncertain/failed | Certification remains historical proof; invoice update pending; factual follow-up and correction request allowed | Payment against absent/unconfirmed supported liability | Finance/technical owner reconciles original native ID/operation. Changed financial subject requires maker review and fresh approval | 391 | Native invoice; states Recorded, Attempting, Failed, Uncertain | `pay` | Finance; technical recovery |
| R17-05 | Native payment posting uncertain/failed | Payment update pending; no claim of settlement | Duplicate instalment, settlement confirmation without confirmed entry/evidence | Finance/technical owner checks native outcome and allocation under original identity before retry | 392 | Native payment; states Recorded, Attempting, Failed, Uncertain | `pay`, `confirm_settlement` | Finance; technical recovery |
| R17-06 | Posted payment; settlement not confirmed | Payment recorded — settlement not confirmed; follow up bank/reconciliation evidence | Cash paid claim or repeating the same allocation as a new payment | Finance settlement authority confirms actual amount/date/evidence or records failed/reversed outcome; no bank execution by CM | 393 | state: `settlement_unconfirmed` | `claim_cash_paid`, `pay` | Finance settlement authority |
| R17-07 | Effective amendment; Budget/order update pending | New legal terms/history retained; funding/order update pending | Spending against changed entitlement; other independent work only if every applicable hold permits it | Recover exact successor and owner operations, retaining original legal effective date. No fictional rollback of signatures | 394 | Funding adjustment, Purchase order (subject `amendment…`); states Recorded, Attempting, Failed, Uncertain | `new_spending`, `pay` | Technical recovery; Budget owner |
| R17-08 | Closure signed; owner financial finalisation failed | Closed or Terminated remains truthful; funding finalisation pending; surviving duties remain assigned | Financially finalised badge or release of any funds | Budget/Finance owner reconciles original close operation; no fresh AO close-out signature for technical retry | 395 | Funding closure; states Recorded, Attempting, Failed, Uncertain | `mark_financially_finalised`, `release_funds` | Budget owner; Finance |

## §5.18 Corrections and downstream consequences

| ID | Changed fact | Required treatment | History and resumption | Spec line | Code model: holds | Invalidates | Owner |
|---|---|---|---|---|---|---|---|
| R18-01 | Acceptance report before full proof | Withdraw outstanding requests; chair prepares successor with current signer set | Prior proofs retained as superseded; no new receipt intent from incomplete report | 403 | `post_receipt` | — | Inspection chair |
| R18-02 | Effective acceptance before native posting | Authorised committee signs correction; supersede unexecuted intent after checking no native success | New accepted subset consumes eligibility once; old decision retained | 404 | `post_receipt` | — | Inspection committee |
| R18-03 | Acceptance/return after native receipt | Retain physical evidence; authorised correction creates native cancel/amend or return as supported by downstream links | Hold affected claims/stock disposition pending reconciliation; restore entitlement only for confirmed returned scope, never by editing report quantity | 405 | `certify_invoice`, `pay`, `use_goods` | — | Technical recovery; Finance |
| R18-04 | Corrected claim before native posting | Recalculate matching; old certification no longer authorises successor claim; HOP signs current support | Supersede draft/request; native draft regenerated through normal methods; no receipt-clock reset | 406 | `pay` | — | Head of procurement |
| R18-05 | Claim/accepted quantity changed after liability posting | Freeze affected payment allocations; Finance uses native amendment/credit/debit adjustment as permitted; HOP certifies revised support | Keep original liability/certification; link adjustments and evidence. Resume only against reconciled supported outstanding amount | 407 | `pay` | — | Finance |
| R18-06 | Accepted-and-paid goods returned/replaced | Hold affected new claims; reconcile linked native return/credit, supplier refund/recovery or replacement treatment | Prior payment stays historical cash fact; replacement uses existing unfulfilled obligation, not a second payable for the same unit | 408 | `certify_invoice`, `pay` | — | Finance |
| R18-07 | Amount/beneficiary changes during payment review | Invalidate pending approval; maker submits corrected exact native subject for independent review | Preserve previous approval as history; do not change already posted payment destination silently | 409 | — | pending payment approval | Finance maker |
| R18-08 | Payment reversed or settlement correction | Use native reversal when ledger correction is required; Record/CorrectFinanceSettlement changes evidenced settlement projection only | Reopen outstanding supported amount/task; show original cash and reversal separately; allocate again only after reconciliation | 410 | `pay` | — | Finance |
| R18-09 | New evidence after closure | AO reviews reasoned correction under §5.21; hold affected positive actions and keep survivor work | Retain original closure. A new ordinary warranty/payment follow-up alone does not reopen completed procurement | 411 | `pay`, `certify_invoice`, `release_funds`, `vary_contract` | — | Authorising officer |

## Reversal order of native documents

Proved by spike S7: a later document blocks the cancellation of an earlier one, so a reversal runs in this order and never the reverse.

| Reverse first | Then | Source |
|---|---|---|
| Quality Inspection | Purchase Receipt | Spike evidence `evidence/v0_8/spike/` (S7), tracker B-findings |
| Purchase Invoice | Purchase Receipt | Spike evidence `evidence/v0_8/spike/` (S7), tracker B-findings |
| Asset | Purchase Receipt | Spike evidence `evidence/v0_8/spike/` (S7), tracker B-findings |

## Boundaries this model keeps

- **A pending operation changes no lifecycle state and no signature.** The case stays Active, Closed or Terminated as it was; a retry never asks for a repeat signature (§5.17: "no repeat report signatures", "no fresh AO close-out signature for technical retry", "No fictional rollback of signatures").
- **Recovery reads the owner first.** `services/intents.py` looks up the owner's document by operation identity and links what exists before any retry.
- **Termination and closure share the funding-finalisation row (R17-08).** A failed owner finalisation holds only `mark_financially_finalised` and `release_funds`; `close_contract` stays permitted and surviving payment and warranty duties stay assigned.
- **Dispatches have no row.** A failed or uncertain Report dispatch or Notice dispatch is retried by its own recovery and holds nothing; §5.17 lists no blocked consequence for it.
- **A correction request holds only the affected scope.** `Hold.scope` names the subjects; unaffected separable lines stay eligible (§5.18). R18-07 places no hold; it invalidates the pending approval.
