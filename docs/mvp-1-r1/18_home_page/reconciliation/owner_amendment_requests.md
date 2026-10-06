# Owner-document amendments Home needs (row HOME6-0904)

Date: 5 October 2026. Prepared for the owners of each module; no owner document has been edited. Home v0.6 §17.1 asks each owner to state how its module feeds Home. Each provider is built and tested against what the owner's code already does (`<owner>/services/home_provider.py`); the amendments below make the owner documents say what the code now does, or name the choice the owner still has to make. Source detail: `owner_feed_matrix.md`, `FOLLOW_UPS.md` (the FU numbers).

## Every owner

State in one short section: the entries the module gives Home (My work, Coming up, Waiting on others, Records you oversee, Recently completed actions), who sees each, and the destination of each. Say plainly that the Home feed adds no task, state or stored field of its own. Give the business title and the action text as two separate pieces (FU-HOME-03): several documents write the reference into the title (for example "Authorise publication of Tender {ref}").

## Per owner

| Owner | What the document should say | FU |
|---|---|---|
| Tenders (TPR) | The Home title/action split for the hand-offs in its §5.11. Coming up: whether the clarification deadline, submission deadline and cancellation due dates become Home entries (the provider gives none today). Why a clarification answer is blocked, as a reason on the row, and how four clarification rows on one Tender are told apart. | 03, 25 |
| Bid Opening (BOP) | Already defines "Start opening" as Scheduled. Say that oversight is empty for everyone (no outstanding concept) and what a member's waiting row says. | 26 |
| Bid Evaluation (EVL) | The evaluation deadline as a dated rule (FU-EVL-18). A holder for waiting rows. The delivered-report destination: see HOME6-0901 below. | 04, 26 |
| Award (AWD) | Its Home entries: holder on waiting rows, the reason "A required notice is not yet confirmed" as a row field, who gets My work and Completed (Head of Procurement Function and Accounting Officer), and the "award notices awaiting delivery" question for the Head of User Department. | 06, 27 |
| Requisitions (REQ) | The Head of Procurement Function authorisation item (its register has only "Purchase ready for requisition"), its wording ("Authorise requisition" or "Decide whether to authorise"), and the empty oversight. | 02, 28 |
| Departmental Needs (NDS) | Which wording leads: "Review need" (§7.6) or "Decide whether this requirement is available to Procurement Planning" (§5.5). Whether the fiscal-year closing instant is a Coming up entry. | 03, 28 |
| Planning (PLN) | That it gives no Scheduled entry (by its own rule), and what oversight it offers (no owner read for outstanding matters today). | 29 |
| Budget (BUD) | Its approval and revision-request entries, and that it gives no waiting or scheduled entry. | 14 |
| Strategy (STR) | A Home feed section: it had no provider; the new one reads its existing approval tasks. | 14 |
| Contract Management | Not a provider yet (deferred, OVS OD-3). Name the entries when the module is built. | 07 |

## HOME6-0901: the Evaluation delivered-report destination

The Evaluation code already serves a report to the Accounting Officer and Head of Procurement Function: `ReadEvaluationReport` takes a version and returns delivered versions only to a reader outside the committee, and the Evaluation screen opens a version at `/desk/tenders/{Tender}/evaluation/report/{report version}`. EVL v0.5 does not name that route as the delivered-version destination Home asked for. Home now builds "View report" (HOME-DES-23, HOME-AC-07) on the link Evaluation's own stage summary offers, `/desk/tenders/{Tender}/evaluation/report` (5 October 2026, owner instruction). The Evaluation document should still name that route as the delivered-version destination.

## Register entries (HOME6-0010, done)

Done 5 October 2026 on the owner's instruction: HOME-CHG-001 v0.6 and ANL-CHG-001 v0.8 are entered in the baseline register and KT-STD-001 moves from v1.15 to v1.22 (FU-HOME-12).
