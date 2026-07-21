# Tender Publications (electronic-first)

## Goal

KenTender publishes from a **confirmed electronic tender package**. PDF is a generated artifact, not the controlling source of truth. Publications owns dates, notice, visibility, bidder workspace activation, and Publish — never tender content.

## Binding sources

| Artifact | Role |
|---|---|
| [`Tender_Management_Electronic_First_Publication_Workflow_v7.md`](Tender_Management_Electronic_First_Publication_Workflow_v7.md) | Product + workflow contract |
| [`A1-Tender-Package-Review/code.html`](A1-Tender-Package-Review/code.html) | Electronic Tender Package Review |
| [`A2-Publications/code.html`](A2-Publications/code.html) | Publications queue |
| [`A3-Publication-Setup/code.html`](A3-Publication-Setup/code.html) | Publication Setup + Publish |
| [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) | Implementation status |

## Precedence

**v7 + A1–A3 mocks > F1 UX handoff wording > TM2 Works publication services.**

- Confirm Tender Package automatically creates/opens Publication Setup (no separate Send step).
- Civic Ledger Desk chrome: `.cursor/rules/kentender-civic-ledger-queue-lock.mdc`.
- F1 immutability (Confirmed Tender Document Package + hash) is retained.

## Primary workflow

```text
Approved Package → Tender Configuration → Readiness → Review Approval
→ Electronic Tender Package Review → Confirm Tender Package
→ Publication Setup → Publish Tender
```

## Desk routes

| Surface | Route |
|---|---|
| A1 Package Review | `/desk/it-tender-package-review/<configuration_id>` |
| A2 Publications | `/desk/publications` |
| A3 Publication Setup | `/desk/publication-setup/<publication_id>` |

## Gates

```bash
make -C apps/kentender_v1 pub-domain-gate
make -C apps/kentender_v1 ui-publications-gate
make -C apps/kentender_v1 ui-civic-ledger-queue-gate
```
