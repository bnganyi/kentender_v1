# Review — AWD-CHG-001 v0.3 (Award)

Review only. No edit was made to the requirements document.

## 1. Files

- Input: `uploads/KenTender_AWD-CHG-001_Award_v0_3.md` — v0.3, "Proposed requirements — Project Owner review".
- Predecessor: v0.2. Its SHA-256 as held in this project is `da113f25103ac40fba601460b6b3ab10021ddc07982594bfce9b1b9f7851082a`, which matches §18.2.
- Prior reviews: `reviews/AWD-CHG-001_v0_1_review.md` and `reviews/AWD-CHG-001_v0_2_review.md`.

## 2. Read list

- Read in full: §5.8–§5.10, §10.3–§11, §14 (AC-025–031) and §15–§18.2 of v0.3.
- Read in part: the rest of v0.3, located by search against the changes listed in §18.2.
- Not read: the same sibling documents as before. Scripts were not run; checks are manual.

## 3. Disposition of v0.2 findings

| Finding | Status | Evidence |
|---|---|---|
| N1 Record next action outcome | Resolved | §5.10 and §11: the outcome is fixed to **Request decision review**, with evidence attached automatically. The dialog is unchanged. |
| N2 V25 marker | Resolved | The §5.9 correction-cycle row now reads "Current once the exact batch is ready for AO authorisation". V25 shows Notices Current. |
| N3 V25 projected date | Resolved | V25 now says **The waiting period will be calculated after notices are given.** The V23 alternative is aligned. AC-031 covers it. |
| N4 publication obligation | Resolved | §5.8 adds the `AwardDecisionRecorded v1` event and Contracting-owned operations; §4 intro; AWD-IF-05; AC-031. |
| N5 next-step rows | Resolved | §5.9 now has rows for V18, V21, V22, V24 and V25. |
| N6 V17/V19 wording | Resolved | Both read "The reported calculation issue may affect the recommendation." |
| N7 combined label | Resolved | §5.10 maps the combined label to the Record corrected award outcome. |
| N8 tie referral | Resolved | The V18 opinion reason now refers the tie to the AO. |

## 4. Remaining findings

| # | Sev | Where | Finding |
|---|---|---|---|
| P1 | B | §7 vs §5.8 | §5.8: "Committing an initial or corrected Award/No award decision atomically retains an `AwardDecisionRecorded v1` event". The §7 results for `RecordAwardDecision` and `RecordAwardCorrectionDecision` do not mention the event. The term `AwardDecisionRecorded` appears only in §5.8, AC-031 and AWD-IF-05. §4 also does not list the retained event or its outbox, though §4 is described as the complete Award write model. |
| P2 | C | §5.9 row "Revised-notice treatment unresolved" | The holder cell reads "HOP / resolve the rules and notice audience issue with the legal-rule owner". That is a description rather than a named task. Every other row names a task (for example "Resolve notice delivery"). |
| P3 | C | V25 | There is a double full stop: "…calculated after notices are given.**." |

None of these changes an artboard's content or journey markers. P3 is copy punctuation only.

## 5. New content for owner review

`AwardDecisionRecorded v1`; the proposed Contracting operations `ReceiveAwardPublicationEvent` and `RecordContractAwardPublication`; the V25 message "The waiting period will be calculated after notices are given."; and the V18 reason "Refer the unresolved tie to the Accounting Officer for a lawful next step."

## 6. Not verified

- The register entry for v0.3 claimed in §17.2.
- Contracting's acceptance of the proposed operations (AWD-IF-05).
- All sibling documents and amendments after the 2022 Act revision, as before.

## 7. Design readiness

All §10 boards (D01–D07 and V01–V25), including the V23 alternative, are specified well enough to design without inventing facts, actions or roles. P1 and P2 affect implementation and task naming, not the artboards. For V25, drop the second full stop (P3).
