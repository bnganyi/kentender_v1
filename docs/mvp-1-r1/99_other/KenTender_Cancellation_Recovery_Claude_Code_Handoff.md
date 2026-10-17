# KenTender — approved cancellation recovery implementation handoff

Date: 17 October 2026. This is an implementation instruction and reading index, not a second requirements specification.

The Project Owner has approved PLN v1.32, TPR v0.21, REQ v1.20 and BUD v1.17 together and instructed: “Mark them as approved and give me a handoff for Claude Code to implement”. Implement the complete cancellation recovery path across the four owners, including its existing-screen presentation, failure handling, legacy reconciliation and integrated verification. Continue through implementation and evidence; do not stop after producing a plan.

## Approved authority and reading index

Use the approved files supplied with this handoff. Their current approval records govern predecessor Proposed/pending language retained as history. REQ v1.20 incorporates the v1.19 display changes; v1.19 has no separate retrospective approval. Budget v1.17 builds on approved v1.16, not the older v1.15 upload; preserve the approved funding, annual-entry, commitment and segregation rules.

| Document | Recovery rule | Model and service contract | Screen variants | Fixtures and acceptance | Closure and impact |
|---|---|---|---|---|---|
| PLN-CHG-001 v1.32 | §5.4.7 | §§4.11, 7.8 | §10.19 | §§13.5, 14.16 | §§15.5, 17.5 |
| TPR-CHG-001 v0.21 | §5.7A | §§4.11, 7.5 | §10.18 | §§13.5, 14.12 | §§15.5, 17.1 |
| REQ-CHG-001 v1.20 | §9.1D | §§5.15, 10.3 | §13.15 | §§16.6, 17.6 | §§19.1, 22.4 |
| BUD-CHG-001 v1.17 | §8.9 | §§4.13, 9.5 | §11.23 | §§15.9, 16.9 | §§17.4, 19.5 |

Start with these sections and follow their named existing command, authority, error and screen references. You do not need to rediscover this amendment by scanning all four documents. Inspect the surrounding existing contracts and repository instructions where necessary to implement and preserve their behaviour. Use the actual current repository and owner interfaces; do not assume a field, adapter, migration or endpoint already exists because it is specified.

## Intended behaviour

An authorised whole-Tender cancellation registers recovery automatically. KenTender restores the exact verified unused original Planning drawdown and releases its matching unused Budget reservations together. The cancelled Tender, original authorised REQ, consumed handoff, decision history and permanent item scope lock remain unchanged. The user can make a fresh ordinary REQ against restored, still-eligible original allowance, with current approvals and fresh financial/handoff identities.

MVP 1 supports the complete unused source set of that cancelled Tender. A REQ may originally have drawn only part of the Plan allowance. A converted source, surviving obligation, partial legacy effect or unsupported mapping must not trigger a guessed or proportional recovery. Retain the affected resources, show the actual issue and use the governed owner correction route. Cancellation is not contract termination.

## Implementation sequence

1. **Map the change to the repository.** Identify current cancellation, handoff consumption, Planning reversal/eligibility, Budget release/conversion, owner evidence and outbox implementations. Record the requirement ID, affected file/service and intended verification in the existing implementation tracker. Reuse existing services and issue IDs where appropriate; do not create a parallel defect register inside partner requirements.
2. **Establish the owner transaction and evidence boundary.** Implement and verify the approved service contracts: REQ `RegisterCancellationResourceRecovery`, TPR `GetTenderCancellationRecoveryBasis.v1`, Planning `RegisterCancellationRecoveryHold`, REQ recovery/read/outcome contracts, the cancellation mode of `ReverseRequisitionDrawdown`, and the bounded REQ cancellation mode of `release_reservation`. Prove the compatible transaction and lock order before treating recovery as available. No cross-owner table access, cached absence proof or pre-lock-only validation. Use existing authoritative Award/CM contracts for their facts; close any missing adapter explicitly. If a genuine requirements conflict appears, report the exact conflict and continue independent authorised work without inventing a new policy or weakening a guard.
3. **Wire the existing cancellation decision.** Atomically register the durable intent, affected-source hold and outbox delivery with the Accounting Officer's cancellation. Preserve lawful-ground, pre-award-notification and downstream exclusion guards. Registration failure must not return committed cancellation success. Once cancellation commits, recovery failure cannot reopen it. Extend the existing `TenderCancelled` contract; preserve Bid Opening delivery, notices, reporting and sealed-data restrictions.
4. **Implement exact recovery and retries.** REQ coordinates the complete original source set. Verify and pin owner evidence, serialise with authorisation/conversion, and commit the exact Planning reversals, Budget releases, recovery completion, hold removal and outcome together or none of them. Enforce uniqueness by cancellation/originating drawdown line, including retries with a new key. Use the approved Pending / Completed / Needs attention outcomes and existing incident handling. A retry may execute the same verified intent; it cannot change amounts or confer new authority.
5. **Complete the user journey.** Add the approved status, amounts, reasons and permitted links to existing owner screens and progress surfaces. Show real blockers while recovery is unresolved. After completion, offer the ordinary fresh-REQ route only when currently permitted. Preserve current scope, one-open-root, source, Plan, correction-hold, product, year, approval and funding checks. No automatic replacement, reopened old handoff, manual restore/release button or new business approval. Keep technical identifiers out of first-view content and apply existing department/read permissions.
6. **Reconcile existing cancelled records.** First produce a read-only inventory and classify exact lineage, held resources, earlier effects and conflicts. Use a versioned, idempotent reconciliation through the same verified recovery service for eligible records. Do not reset balances, fabricate past cancellation decisions or silently repair ambiguous source mappings. Test the reconciliation twice on representative migrated data before applying it to a target environment under that environment's established change process.
7. **Verify and close.** Run the tests below against the actual owner adapters, apply normal repository checks, and complete the implementation/evidence mapping. Update the repository's current registers, navigation/design references or operational documentation where this approved change actually affects them; preserve unrelated external changes and do not substitute stale copies. Requirements approval does not itself close a follow-up or authorise a production deployment.

## Required evidence

Map `PLN-CR-AC-001`–`012`, `TPR-CR-AC-001`–`012`, `REQ-CR-AC-001`–`012` and `BUD-CR-AC-001`–`012` to meaningful verification. A shared integrated scenario can satisfy corresponding owner criteria; do not duplicate identical tests solely to create 48 test names.

- Run CR-F01 and CR-F02 against real Planning, TPR, REQ and Budget adapters, including two reservations on one Budget Line. Check exact quantities, values, owner effects and fresh identities before/after cancellation, replacement authorisation and replay of the old recovery.
- Exercise failure on either owner leg; crashes before commit and after commit/before acknowledgement; duplicate delivery; changed payload; new-key replay; and two distinct cancelled sequential drawdowns. Show no partial effects or duplicate restoration.
- Test cancellation against concurrent award notification/conversion and new REQ authorisation. Missing, stale, foreign, omitted, converted or already-released source evidence must not pass. Preserve all surviving obligations and existing correction holds.
- Verify closed-year historical treatment, no scope enlargement across APP successors, no automatic replacement and ordinary replacement eligibility. Test unrelated items remain usable.
- Exercise the real user screens for Pending, Completed and Needs attention, including permitted next steps, source amounts, issue links, direct-route/read scope and plain user-facing copy. Use browser evidence for the changed journey, not only API tests.
- Verify existing Bid Opening cancellation handling and cancellation compliance work still operate. Regress pre-consumption REQ revocation, ordinary Budget conversion/release, retained Closed commitments and the approved funding controls that this change must preserve.
- Record reconciliation inventory, results, unresolved legacy cases and a second-run no-duplicate result. State explicitly which environment and adapters were tested; simulated-owner tests alone cannot close integration.

Report the implementation commits/files, requirement-to-evidence mapping, actual test commands and results, migration/reconciliation outcome, and any remaining blocker with its exact failed closure condition. Keep uncertain items open and distinguish requirements approval, code completion, deployed migrations, integration evidence and production release.
