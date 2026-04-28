# STD Engine Works v2 - Phase Completion Checklists (Planning Template)

Date: 2026-04-28  
Status: Planning template for future execution phases.

## Global checklist (applies to every phase)

- [ ] Scope boundary respected.
- [ ] Tracker updated with ticket-level status.
- [ ] Tests executed and evidence captured.
- [ ] Negative/permission path covered.
- [ ] UI evidence captured (if UI touched).
- [ ] Remaining risks documented.

## Phase 0 checklist (planning/background only)

- [ ] Tracker file created and aligned with Cursor ticket IDs.
- [ ] Existing-state inventory produced.
- [ ] Decision log produced.
- [ ] Environment and test matrix produced.
- [ ] Risk register produced.
- [ ] Feature-flag transition strategy defined at planning level.

## Phase 1-13 checklist stubs (reference only)

These are placeholders for future execution. Do not use them to mark implementation done during Phase 0.

### Phase 1 - Core model/migrations
- [ ] Domain objects and constraints implemented
- [ ] Migration safety validated
- [ ] Test evidence logged

### Phase 2 - Seed package/loader
- [ ] Modular seed package implemented
- [ ] Seed validation and traceability checks pass
- [ ] Test evidence logged

### Phase 3 - Governance/auth/audit
- [ ] State transitions enforced server-side
- [ ] Authorization and SOD enforced
- [ ] Audit events validated

### Phase 4-8 - Core runtime services
- [ ] Instance/configuration services validated
- [ ] Generation/readiness/addendum contracts validated

### Phase 9-11 - Cross-module and UI integration
- [ ] TM/downstream ownership rules enforced
- [ ] Workbench/instance UI validated with Playwright

### Phase 12 - Smoke contract
- [ ] Full smoke suite passing with zero critical failures

### Phase 13 - Hardening
- [ ] Evidence export and production safety checks validated

## Standard closeout entry (required for every ticket/phase)

| Field | Value |
|---|---|
| Completed | |
| Not completed | |
| Assumptions | |
| Files changed | |
| Evidence | |
| Residual risks | |

