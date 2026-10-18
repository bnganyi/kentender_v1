# KenTender — opening failure reconciliation handoff

18 October 2026. This is a reading and implementation index, not a parallel requirements specification.

**Status: Approved — 18 October 2026.** The Project Owner instructed “Mark the documents as approved”, approving BOP v0.16, TPR v0.24, PRC v0.14, AWD v0.9 and TRUST-OPS v0.2 together. The Owner has also explicitly instructed implementation. Proceed through implementation and verification using this handoff. Earlier “once approved” wording is superseded. Approval does not establish integration-test, operational-drill, legal or production clearance.

## Exact starting points

| Complete owner document | Business rule | Service/event binding | Existing-screen variants | Fixtures | Acceptance | Closure evidence |
|---|---|---|---|---|---|---|
| BOP v0.16 | §5.2 | §7.2, with existing §7.1 | §§10.7–10.8 | §13.1 | §14.1 | §15.1 |
| TPR v0.24 | §5.12, with §§5.7–5.7A | §7.6, with existing CancelTender and recovery contracts | §§10.13, 10.19 | §13.6 | §14.13 | §§15.4–15.6 |
| PRC v0.14 | §5.1 | §7.2 | §10.1 | §13.1 | §14.1 | §15.1 |
| AWD v0.9 | §5.11 | §7.2, with existing GetAwardAuthorityStatus | §10.5 | §13.1 | §14.3 | §15.1 |
| TRUST-OPS v0.2 | §§5, 9–10 | §9.2 | §9.3 | §11.1 | §11.2 | §11.3 |

Start with these named sections; follow their existing owner command, access, error and screen references. Inspect repository instructions and actual current code before choosing implementation details. A requirement for an adapter, record or test is not evidence that it already exists. No indiscriminate scan of all historical document revisions is needed to find this change.

## Work to complete

1. Map each changed acceptance criterion to the current service, screen, test and existing follow-up ID. Preserve unrelated external documentation changes. These successors build on the supplied BOP v0.15, TPR v0.23 proposal over approved v0.22, PRC v0.13, AWD v0.8 and TRUST-OPS v0.1.
2. Complete the current owner bindings rather than inventing another workflow. Support records an attributed recovery finding; the chair retries/resumes only a nonterminal case under the existing full-roster/custody controls. Cannot recover or Not held routes the AO to the existing TPR decision item. No generic skip-bid, force-complete, late-start or administrator unseal action.
3. Implement the allowed and blocked TPR decision variants. Preserve verified grounds and current legal/profile requirements. Consume AWD's durable Tender-level authority, including before an Award case exists. Missing authority is Unknown; it cannot be replaced by “no case found”. Give each blocker its exact reason, holder and permitted route. A technical fault alone establishes no cancellation ground.
4. Prove the shared cancellation/first-notice fence. Recheck authoritative source revisions inside that guard. A stale queued issue cannot send after cancellation; an uncertain external send cannot revert to Not issued by timeout. Do not hold a database transaction across external dispatch. Keep all existing notice-giving, decision, correction and funding-allocation rules.
5. Consume the existing TenderCancelled event. Before Start, preserve terminal Not held; after Start, preserve terminal partial BOP/PRC history through CloseAbortedProceeding. Deny further ceremony actions as soon as authoritative cancellation is known. Retry failed delivery with the original event and no duplicate closure, task receipt or compliance obligation. The exact AO item clears only on its defined committed BOP/PRC outcome.
6. Preserve the already-approved cancellation financial recovery: PLN v1.32, REQ v1.20, BUD v1.17 and the TPR recovery contract. Release no money solely because an opening failed. A lawful cancellation uses the exact unused source set and original owner transaction, preserves scope locks/history and creates no replacement automatically. Do not require decrypting an unopened bid or completed opening minutes to prove a cancellation.
7. Correct incident reads and closure. Apply the scoped support/AO/Auditor access rules; Administrator/System Manager status conveys no additional authority. Keep purposeful detail-read/export auditing and safe diagnostics. A proceeding lawfully ended without repaired service can have the defined cancellation-based incident closure, with separate defects and obligations retained. An unresolved decision cannot be dismissed through a note or “acknowledged”.
8. Complete the existing-screen journey and actual owner integration, including direct API refusals, retries, task create/clear and read permissions. Maintain existing ordinary/empty opening, committee proofs, Evaluation separation and security-intake exclusions. Update the actual current repository registers and operational references accurately; no stale control-register copies are supplied for replacement.

## Verification and closure

Map each owner's twelve `*-OF-AC-001`–`012` criteria to meaningful evidence. Shared integrated scenarios may satisfy corresponding criteria; do not create repetitive tests merely to duplicate IDs. Execute OF-F01, OF-F02 and OF-F03 against the real BOP/TPR/PRC/AWD adapters. Financial recovery checks also use real REQ/Planning/Budget adapters.

Required branches include recovered pre-start and paused cases; an irrecoverable timely bid; Not held; verified cancellation and missing ground; no Award case with durable negative evidence; missing/stale authority; Issue in progress/Issued/Unknown; both cancellation/notice race orderings; crash/duplicate/out-of-order event delivery; a cancelled proceeding whose service remains faulty; and permission/diagnostic leakage attempts. Browser checks must show the actual allowed, blocked and terminal task journeys. Preserve all predecessor acceptance requirements and regress approved financial behaviour.

PR-001 closure separately requires the procedure's exercises, accepted results and exact operating evidence. Trust L1/L2 and LAW-V-001 remain open unless independently supported by current source review and the selected production profile. No new legal interpretation, signing provider, password threshold, external-channel equivalence or production release is approved here.

Report implementation files/commits, requirement-to-evidence mapping, actual test commands/results and environment, operational-drill status, remaining adapters and exact failed closure conditions. Keep requirements approval, implementation, deployment/migrations, integration evidence, legal clearance and production release distinct. A missing condition must remain visible and owned; do not conceal it by deleting a gate.

## Unchanged documents

BDS v0.16, TRUST-ADR v0.6, supplied LAW v1.2 and AUTH are unchanged. Preserve approved AUTH v1.16 funding controls rather than regress to the supplied older v1.15. PLN v1.32, REQ v1.20 and BUD v1.17 remain approved and unchanged. Current control registers, legal operating-profile evidence, code and implementation reports were not supplied for editing in this exercise.
