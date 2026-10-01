# AWD-CHG-001 v0.4 — fixture chronology

Tracker AWD4-005. The §13 ordinary path and the isolated branches. Every branch starts from its own synthetic entry point (`award/seeds/playwright_ui_fixtures.py` `STAGES`, built from `award/test_services/sources.py`); none mutates the ordinary timeline. Instants are EAT (site time).

## Ordinary path (§13; canonical stage `award` on TND-MOH-2027-002; synthetic world `033`)

| Instant | Event | Command |
|---|---|---|
| 16 Jun 2027 14:07:01 | Evaluation report 1 delivered with 3 of 3 signatures | `ReceiveEvaluationReport` (system) |
| 17 Jun 2027 09:00 | Charles opens the opinion | `GetAwardRecord` |
| 17 Jun 2027 09:10 | Charles signs Professional opinion 1 | `SignProfessionalOpinion` |
| 17 Jun 2027 10:00 | Amina records Award and notifies bidders; coordinated test notices given | `RecordAwardDecision`, `IssueAwardNotices` |
| 17 Jun 2027 10:10 | Mary reads Award notice 1 (reply by 24 Jun 2027 17:00, a test term of the issued notice) | `GetSupplierAwardNotice` |
| 18 Jun 2027 09:00 | Mary accepts | `RespondToAward` |
| 18 Jun 2027 09:05 | Waiting period running; earliest permitted 2 Jul 2027 09:00 (test profile term) | `RefreshAwardEligibility` |
| 2 Jul 2027 09:00 | Package delivered to the test Contracting receiver | `DeliverAwardPackage` |

## Isolated branches (§13 list) and their entry points

| # | Branch | Entry stage | Board(s) |
|---|---|---|---|
| 1 | Incomplete source (annex unavailable) | `source-incomplete` | V02 |
| 2 | AO return | `returned` | V01 |
| 3 | Source successor during opinion drafting | `successor-report` | (D02 History) |
| 4 | Expired validity | `expired` → `no-award` | V03, V04 |
| 5 | No responsive bid | `no-responsive` | (V03 shape) |
| 6 | Unresolved tie (tender 036) | `tie` | V18 |
| 7 | Funding restriction | `funding` | (D02 Outstanding issues) |
| 8 | Authority expiry | test only | — |
| 9 | Unsuccessful bidder (tender 037, two bids) | `two-bid-issued` | V14 |
| 10 | Email failure | `notice-failed` | V05, V16 |
| 11 | Partial giving across two recipients | `two-bid-partial` | (V05 shape) |
| 12 | Late acceptance | `late-response` | V22 |
| 13 | Correction after a closed No award cycle | `closed-correction` | V21 |
| 14 | Successor cycle report/opinion and blocked revised notices | `correction-authorised` → `corrected-report` → `corrected-opinion` / `revised-held` / `revised-ready` | V19, V20, V23, V23p, V24, V25 |
| 15 | Decline | `declined` | V06 |
| 16 | Silence | `no-response` | V07 |
| 17 | Debrief closure and later correspondence | `debrief` → `debrief-closed` | D07, D07c |
| 18 | Board suspension | `order-hold` | V08, X04 |
| 19 | Precautionary hold | `challenge-hold` | X05 |
| 20 | Post-decision correction | `post-decision-correction` → `correction-decision` | V09, V17 |
| 21 | Cancellation / issue race | test only | — |
| 22 | Unknown authority status | `status-unknown` | V15s |
| 23 | Unavailable Contracting | `receiver-down` | V10 |
| 24 | Late restriction after package receipt | `delivered-restricted` | (D06 + issue) |
| — | Signing unavailable | `signing-unavailable` | V12 |
| — | Rules unverified | `rules-unverified` | V15 |
