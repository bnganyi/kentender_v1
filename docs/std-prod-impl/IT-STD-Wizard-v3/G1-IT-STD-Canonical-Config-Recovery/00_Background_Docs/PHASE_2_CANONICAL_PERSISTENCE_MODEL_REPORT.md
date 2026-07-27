# G1 Phase 2 — Canonical Persistence Model Report

| Field | Value |
|---|---|
| Status | **Complete — Phase 2 lifecycle alignment** (not Phase 3) |
| Scope | Canonical BWMF persistence only |
| Site | `kentender.midas.com` |
| Date | 2026-07-24 |

## Goal

Finish Phase 2 persistence with canonical workspace statuses (no `Open`), derived preparatory readiness, controlled transactional transitions, complete manifest lifecycle including `Cancelled`, and single-owner submission totals — without compiler, UI, publication UX, checklist cutover, or legacy migration.

---

## What you will see / What changed

### What changed

Final lifecycle alignment: workspace `status` uses canonical values; preparatory statuses are derived; only `ready_to_submit→submitted`, policy-gated withdrawal, and close transitions are transactional; manifest adds `Cancelled`; snapshot `totals` owns money with `total_amount` as enforced projection.

### What you will see

- Workspace created as `not_started` (never `Open`)
- Optional `operational_state` (does not replace `status`)
- Manifest: `Draft → Published → Superseded|Cancelled`
- Sealed submission rejects `total_amount` ≠ snapshot `totals.grand_total`

### What should NOT change

- No C01–C22, Desk UI, checklist cutover, or legacy migration

### How to verify

```bash
make -C apps/kentender_v1 bw-manifest-phase1-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-manifest-phase2-gate SITE=kentender.midas.com
make -C apps/kentender_v1 bw-a2-domain-gate SITE=kentender.midas.com
make -C apps/kentender_v1 nssf-calibration-gate SITE=kentender.midas.com
```

### Cross-check

| Claim | Evidence |
|---|---|
| `Open` rejected | `test_open_status_rejected` |
| Preparatory not directly settable | `test_direct_preparatory_status_mutation_rejected` |
| Derived readiness boundary | `test_derived_readiness_state_calculation_boundary` |
| Policy withdrawal | `test_policy_controlled_withdrawal` |
| Manifest cancel | `test_manifest_cancellation_without_payload_mutation` |
| Totals mismatch | `test_total_mismatch_rejected` |
| No Phase 3/UI | Change list below |

---

## Corrected lifecycle tables

### BWMF Workspace (`status`)

Canonical values (no `Open`):

`not_started` · `draft` · `in_progress` · `needs_attention` · `ready_to_submit` · `submitted` · `withdrawn` · `closed`

| Class | Values | How set |
|---|---|---|
| Preparatory | `not_started`…`ready_to_submit` | **Derived only** via `refresh_derived_workspace_status` / `derive_workspace_status` from responses, blockers, confirmations, dependencies, readiness |
| Transactional | `submitted`, `withdrawn`, `closed` | Controlled services only |

| Transition | Service | Notes |
|---|---|---|
| `ready_to_submit` → `submitted` | `submit_workspace` | Sets `active_submission` (server-controlled) |
| `submitted` → `withdrawn` | `withdraw_workspace` | Only if `payload.submission_policy.withdrawal_mode` is `permitted_before_deadline` or `governed_special` (Phase 3 corrected; was briefly `control.allow_withdrawal`) |
| `submitted` → `closed` | `close_workspace` | |
| `withdrawn` → `closed` | `close_workspace` | |
| `closed` | — | Terminal |

`operational_state` is optional coarse internal marker; **never** substitutes for canonical `status`.

Bidder/client direct mutation of preparatory or transactional `status` is rejected (`BWMF_WORKSPACE_SERVICE_ONLY` / forbidden status).

### BWMF Manifest Version

| Transition | Terminal? | Content |
|---|---|---|
| `Draft` → `Published` | | payload/bindings/resources/digest immutable throughout |
| `Published` → `Superseded` | Yes | Audit `manifest.superseded` |
| `Published` → `Cancelled` | Yes | Audit `manifest.cancelled` |

### BWMF Compile Run (unchanged from 2B)

`Queued → Running → Succeeded|Failed|Cancelled`; stage traces append-only; terminals immutable.

### Submission totals (single owner)

| Field | Role |
|---|---|
| Snapshot `totals` | **Authoritative** |
| Top-level `total_amount` | Server-derived immutable projection; must equal `totals.grand_total` or reject (`BWMF_TOTAL_MISMATCH`) |

---

## Constraints / indexes (revised notes)

Unchanged from 2B except:

- Workspace field `state` removed; canonical field is `status`
- Legacy `Open` / `Submitted` / `Closed` workspace labels forbidden
- Manifest lifecycle options include `Cancelled`
- Evidence `content_digest` remains non-unique (lookup index only)

---

## Named new lifecycle-alignment tests (Phase 2C)

| Test | Covers |
|---|---|
| `test_open_status_rejected` | No `Open` |
| `test_direct_preparatory_status_mutation_rejected` | Preparatory not client-settable |
| `test_derived_readiness_state_calculation_boundary` | Pure + persisted derive boundary |
| `test_policy_controlled_withdrawal` | Deny without policy; allow with `allow_withdrawal` |
| `test_manifest_cancellation_without_payload_mutation` | Cancel + audit + immutable payload |
| `test_total_mismatch_rejected` | Snapshot totals vs `total_amount` |

Module: `test_bwmf_persistence_phase2c.py` (included in `bw-manifest-phase2-gate`).

---

## Files changed (this alignment)

| Path |
|---|
| `…/persistence/workspace_lifecycle.py` **(new)** |
| `…/persistence/guards.py` |
| `…/persistence/services.py` |
| `…/doctype/bwmf_workspace/bwmf_workspace.json` |
| `…/doctype/bwmf_manifest_version/bwmf_manifest_version.json` |
| `…/patches/ensure_bwmf_persistence_indexes.py` |
| `…/tests/test_bwmf_persistence_phase2b.py` |
| `…/tests/test_bwmf_persistence_phase2c.py` **(new)** |
| `apps/kentender_v1/Makefile` |
| This report |

---

## Test commands and non-zero counts

| Gate | Result | Counts |
|---|---|---|
| `make bw-manifest-phase1-gate` | **OK** | **12** + **7** |
| `make bw-manifest-phase2-gate` | **OK** | **7** + **19** + **15** + **6** |
| `make bw-a2-domain-gate` | **OK** | **10** + **2** |
| `make nssf-calibration-gate` | **OK** | **1** × 5 |

---

## Confirmation: no Phase 3 or UI code

**Confirmed.** This alignment did not implement compiler C01–C22, publication workflow UI, runtime checklist cutover, Desk/portal screens, or legacy migration DocTypes.
