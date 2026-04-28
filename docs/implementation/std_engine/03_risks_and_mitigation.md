# STD Engine Works v2 - Risks and Mitigation (Phase 0)

Date: 2026-04-28  
Status: Planning baseline.

## Risk register

| ID | Risk | Severity | Mitigation (planning) | Residual risk |
|---|---|---|---|---|
| R-001 | Reintroduction of file-upload-as-source behavior | Critical | Keep anti-pattern lockout explicit in tracker and phase acceptance criteria | Medium until Phase 9 lockouts implemented |
| R-002 | Downstream modules continue manual rule ownership | Critical | Enforce roadmap dependencies: Phase 9+ cannot be skipped | Medium |
| R-003 | Missing legal source trace for seeded text | Critical | Require source page/hash metadata and QA fields in seed plan | Medium |
| R-004 | Governance implemented late causing unsafe mutations | High | Keep Phase 3 as prerequisite before broader integration | Low/Medium |
| R-005 | Feature-flag ambiguity during transition | High | Define explicit on/off behavior in decision log and tracker | Medium |
| R-006 | UI validation claimed without runtime evidence | High | Require Playwright evidence in tracker DoD definitions | Medium |
| R-007 | Addendum impact rules inconsistently applied | Critical | Keep smoke contract invariants visible in tracker phase map | Medium |
| R-008 | Incomplete evidence/audit lineage at release | High | Reserve Phase 13 evidence export checks and retain as mandatory gate | Medium |

## Top planning controls

1. Keep phase map and ticket IDs immutable in tracker.
2. Do not mark execution-phase tickets as Done from planning-only activity.
3. Treat smoke contract as non-negotiable acceptance baseline for future execution.
4. Keep explicit stop condition: no Phase 1+ runtime work without approval.

## Escalation triggers (for future execution)

- Any attempt to bypass `ITT/GCC` lock rules.
- Any manual downstream criteria or checklist definition outside generated models.
- Any overwrite of published output instead of supersession.
- Any readiness pass without generated model references.

## Phase 0 closeout record template

| Field | Value |
|---|---|
| Date | |
| Completed | |
| Not completed | |
| Assumptions | |
| Files changed | |
| Evidence | |
| Residual risks | |

