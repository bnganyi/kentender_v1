# STD production readiness — programme index

**Purpose:** Coordinate hardening of the STD engine and related surfaces from POC toward production, using scoped workstreams under this folder.

**Programme tracker:** [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) — cross–workstream status, health, and links.

---

## Workstreams

| # | Name | Specs | Tracker | Issues |
|---|------|--------|---------|--------|
| 1 | STD Template Governance and Lifecycle | [`workstream-1/`](workstream-1/) (docs 1–8) | [`workstream-1/IMPLEMENTATION_TRACKER.md`](workstream-1/IMPLEMENTATION_TRACKER.md) | [`workstream-1/ISSUES_LOG.md`](workstream-1/ISSUES_LOG.md) |
| 2 | STD Engine — Official Library UI (admin revamp) | [`admin-revamp/`](admin-revamp/) (spec + Cursor pack) | [`admin-revamp/IMPLEMENTATION_TRACKER.md`](admin-revamp/IMPLEMENTATION_TRACKER.md) | [`admin-revamp/ISSUES_LOG.md`](admin-revamp/ISSUES_LOG.md) |

Additional workstreams get a row here and a sibling folder when authored.

---

## Upstream context (completed or active POC)

| Area | Tracker / notes |
|------|-----------------|
| STD Works POC (package, loader, engine, Desk) | [`../std poc/IMPLEMENTATION_TRACKER.md`](../std%20poc/IMPLEMENTATION_TRACKER.md) |
| STD Admin Console POC | [`../std poc/admin console/IMPLEMENTATION_TRACKER.md`](../std%20poc/admin%20console/IMPLEMENTATION_TRACKER.md) |
| Procurement officer tender configuration POC | [`../std poc/tender configuration/IMPLEMENTATION_TRACKER.md`](../std%20poc/tender%20configuration/IMPLEMENTATION_TRACKER.md) |
| Planning → tender handoff + integrated seed | [`../planning-to-tender-handoff/IMPLEMENTATION_TRACKER.md`](../planning-to-tender-handoff/IMPLEMENTATION_TRACKER.md) |

Workstream 1 **governs** `STD Template` lifecycle; handoff and officer flows must **respect** `lifecycle_status`, `allowed_for_tender_creation`, and hash evidence once implemented (expect coordination issues `STD-GOV-*` and possible cross-posts to `STD-INT-*`).

Workstream 2 (**admin-revamp**) delivers the **Official STD Library** administrator UX; import/activate flows must **integrate with** governance services and server guards (expect coordination `STD-LIBU-*` with `STD-GOV-*` where behaviour overlaps).

---

## Agent rules (bench)

- **TDD; Playwright for Desk** — workspace [`.cursor/rules/kentender-tdd-playwright-quality-gate.mdc`](../../../../../.cursor/rules/kentender-tdd-playwright-quality-gate.mdc); Desk patterns [`.cursor/rules/frappe-desk-playwright-patterns.mdc`](../../../../../.cursor/rules/frappe-desk-playwright-patterns.mdc).
- **`bench build` / app assets** — from bench root use [`./scripts/bench-with-node.sh`](../../../../../scripts/bench-with-node.sh) per [`.cursor/rules/frappe-bench-node.mdc`](../../../../../.cursor/rules/frappe-bench-node.mdc).
