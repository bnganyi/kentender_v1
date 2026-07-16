# IT Tender Wizard — Screen Ownership Correction Plan

**Status:** Active  
**Governing contract:** [`99 IT_Tender_Wizard_Screen_Ownership_Matrix.md`](99%20IT_Tender_Wizard_Screen_Ownership_Matrix.md)  
**Tracker:** [`Screen_Ownership_Implementation_Tracker.md`](Screen_Ownership_Implementation_Tracker.md)  
**UI wiring tracker:** [`UI_IMPLEMENTATION_TRACKER.md`](UI_IMPLEMENTATION_TRACKER.md)

## Goal

Stop ownership sprawl in the IT Tender Configuration Wizard: every visible field has a clear owner, source type, and editability; already-wired screens stop showing magical or cross-owned values; future screens cannot ship without an ownership contract gate.

Done looks like:

- This plan and the ownership tracker under `docs/std-prod-impl/IT-STD-Wizard/`
- Residual ownership defects on ITW-01–07 closed with tests
- Shared ownership contract helpers + `make it-wizard-ownership-gate`
- ITW-08+ wiring blocked until that gate is green and each new screen has an ownership row

## Precedence

**Ownership Matrix (`99`) wins for field ownership / editability / source presentation** over PRD, Domain, API, Governance, Pack, Sprint backlog, and design HTML when they conflict.

Pack docs still define what domain objects must exist; the Matrix decides which screen edits which field.

## Documentation map

| Doc | Role |
|---|---|
| [`99 Ownership Matrix`](99%20IT_Tender_Wizard_Screen_Ownership_Matrix.md) | Correction layer (global rule, field types, immediate fixes) |
| [`01 PRD`](01%20IT_Tender_Configuration_Wizard_PRD.md) | Screen intents; controlled configuration |
| [`02 Domain Model`](02%20IT_Tender_Configuration_Wizard_Domain_Model.md) | Entities (realign scoring + inventory qty conflicts) |
| [`03 Governance`](03%20IT_Tender_Configuration_Wizard_Governance_Roles_Permissions_State_Model.md) | ITREQ / ITINV rules |
| [`05 API UI Service Contract`](05%20IT_Tender_Configuration_Wizard_API_UI_Service_Contract.md) | Per-step API owners |
| [`06 Cursor Implementation Pack`](06%20IT_Tender_Configuration_Wizard_Cursor_Implementation_Pack.md) | §2.1 Master Cursor Instruction |
| [`07 Sprint Backlog`](07%20IT_Tender_Configuration_Wizard_Sprint_Backlog_and_Task_Breakdown.md) | S5 tasks that assumed qty on inventory |
| [`00 Correct Next Sequence`](00%20Correct%20Next%20Sequence%20After%20STD%20Engine.md) | Wizard as configuration bridge |
| [`UI_IMPLEMENTATION_TRACKER.md`](UI_IMPLEMENTATION_TRACKER.md) | ITW-01–15 static/wiring status |

## Field-source contract

Every displayed field must be classifiable as one of:

| Field type | UI behavior |
|---|---|
| User-entered | Editable |
| Template-prefilled | Editable with Reset to template |
| Derived | Read-only with formula/source explanation |
| Owned elsewhere | Read-only with Edit in [owning screen] |
| STD-locked | Read-only with legal/source explanation |
| Not configured | Show “Not configured”, never fake values |

DTO shape (extend existing `field_sources_json` patterns):

```text
{ value, source_type, source_object, owner_screen, editable, readonly_reason }
```

## Phases

### Phase A — Contract freeze and prevention

- ITW-OWN-000 — Adopt Matrix precedence (docs, Pack §2.1, Cursor rule)
- ITW-OWN-GATE-01 — Shared ownership helpers (Python + TS)
- ITW-OWN-GATE-02 — `make it-wizard-ownership-gate`

### Phase B — Correct wired screens

- ITW-OWN-007 — System Inventory magical summaries (blocker)
- ITW-OWN-003 — Profile → TDS-owned references
- ITW-OWN-006 — Schedule turnkey Edit/Reset parity
- ITW-OWN-005 — Requirements `SCORED` surface cleanup
- ITW-OWN-001 / 002 / 004 — Dashboard / Overview / TDS fixture purge

### Phase C — Pack/doc realignment

- ITW-OWN-DOC-01 … DOC-05 — PRD, Domain, API, Governance, Sprint backlog

### Phase D — Future screens (ITW-08+)

Before any Desk wiring for ITW-08+:

1. Ownership tracker row Ready with Owns / Must-not-own / Reference checklist
2. Design audited for magical values and cross-owned editors
3. `make it-wizard-ownership-gate` green
4. Wiring implements field-source metadata; commercial/scoring only on owning screens

## Evidence bar

Done only with automated tests + UX validation for user-visible changes + tracker evidence line. Partial work stays Partial.

## Out of scope

- Full Price Schedule / Evaluation / Forms / SCC / Validation / Review / Preview / Publication wiring beyond ownership preconditions
- STD Engine master package edits
- Publishing tenders from the wizard
