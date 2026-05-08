# Doc 8 smoke — environment and results (§C gate)

**Specification:** [`8. std_template_governance_lifecycle_smoke_test_specification.md`](8.%20std_template_governance_lifecycle_smoke_test_specification.md)  
**Tracker:** [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) §C  
**Deviations / logs:** [`ISSUES_LOG.md`](ISSUES_LOG.md) **STD-GOV-103** (doc 8 §32 evidence pack), **STD-GOV-104** (doc 8 §33 nil issues)

## 1. Environment (doc 8 §7)

| Field | Value to record | Captured value |
|-------|-----------------|----------------|
| Test date |  | 2026-05-03 |
| Tester |  | Automated (bench + Playwright) |
| Frappe site |  | `kentender.midas.com` (site name for `bench` / local `default_site`) |
| Custom app name |  | `kentender_procurement` |
| Git branch |  | Not captured |
| Git commit |  | Not captured |
| Frappe version |  | Not captured |
| ERPNext version, if installed |  | Not captured |
| Browser |  | Chromium (Playwright) |
| Database |  | Not captured |
| Seed command used |  | `after_migrate` + STD-GOV-012 seed (WORKS POC); doc 8 users from smoke test module |
| Test package used |  | `KE-PPRA-WORKS-BLDG-2022-04-POC` (WORKS POC) |

| Item | Value |
|------|--------|
| Bench root | `frappe-bench` |
| Automated API/lifecycle module | `kentender_procurement.tender_management.tests.test_std_template_governance_smoke_doc8` |
| Desk UI (ST-018 / ST-019) | `apps/kentender_v1/tests/ui/smoke/procurement/std-template-governance-smoke-doc8.spec.ts` |
| Regression (supersede + usage JSON payload) | `…test_std_template_governance_lifecycle_gov007` — `test_std_gov_007_supersede_with_usage_serializes_impact_payload` |

## 2. Doc 8 §8 user mapping (API vs Desk)

| Doc 8 §8 user | Used in | Notes |
|-----------------|---------|--------|
| `proc.officer@test.local` | `test_std_template_governance_smoke_doc8.py` | Created in smoke ST-001/ST-016; `has_permission` read **false** on `STD Template`. |
| `UI_PROCUREMENT_OFFICER_USER` (default `procurement.officer@moh.test`) | Playwright | Seeded site user; Desk may show **Not found** for `/app/std-template/...` (no route/workspace) in addition to DocPerm checks. |
| All other `std.*@test.local` / `system.manager@test.local` | Bench smoke only | Not used in Playwright (ST-018 is **Administrator** slice). |

## 3. Result matrix (doc 8 §31)

| Test ID | Expected (summary) | Automated evidence | Pass |
|---------|-------------------|-------------------|:----:|
| ST-001 | Roles, doc 8 users, PO boundary | `TestStdTemplateGovernanceSmokeDoc8ST001` | Yes |
| ST-002 | POC import | `TestStdTemplateGovernanceSmokeDoc8PocST002ST003` | Yes |
| ST-003 | POC validate | `TestStdTemplateGovernanceSmokeDoc8PocST002ST003` | Yes |
| ST-004 | Invalid package blocks submit | `TestStdTemplateGovernanceSmokeDoc8ST004` | Yes |
| ST-005 … ST-015 | Lifecycle chain through archive | `TestStdTemplateGovernanceSmokeDoc8FullChain` | Yes |
| ST-016 | Permission negatives | `TestStdTemplateGovernanceSmokeDoc8ST016` | Yes |
| ST-017 | Replace / staleness | `TestStdTemplateGovernanceSmokeDoc8ST017` | Yes |
| ST-018 | UI — state/role-aware (doc 5) | Playwright: **Administrator** only — governance group, summary dialog, optional Suspend reason dialog; **not** approver/activator/auditor multi-role | Partial |
| ST-019 | Officer boundary | Bench: `proc.officer@test.local` read denied (`smoke_doc8`). Playwright: **`procurement.officer@moh.test`** — `/app/std-template/…` blocked. Tender **`std_template`** reference (no governance desk): run OFF-ST-002 in [`officer-tender-poc-off-st-desk.spec.ts`](../../../../tests/ui/smoke/procurement/officer-tender-poc-off-st-desk.spec.ts) (serial). | Yes* |
| ST-020 | WORKS POC seed governed | `TestStdTemplateGovernanceSmokeDoc8ST020` | Yes |

\*Doc 8 desk gate: `npx playwright test tests/ui/smoke/procurement/std-template-governance-smoke-doc8.spec.ts` (**2** tests; `UI_BASE_URL` / `.env.ui`). For ST-019 tender **`std_template`** visibility, also run OFF-ST-002 in [`officer-tender-poc-off-st-desk.spec.ts`](../../../../tests/ui/smoke/procurement/officer-tender-poc-off-st-desk.spec.ts) (serial bundle).

## 4. C3 — server-side enforcement (principle)

| Check | Evidence |
|-------|----------|
| Submitted template blocks package edit | `TestStdTemplateGovernanceSmokeDoc8C3Principle.test_std_gov_c3_submitted_blocks_package_edit` |
| `allowed_for_tender_creation` clamp when not Active | `TestStdTemplateGovernanceSmokeDoc8C3Principle.test_std_gov_c3_clamped_allowed_for_tender_creation_when_not_active` |
| Supersede/retire with usage: lifecycle payload JSON-safe | `test_std_gov_007_supersede_with_usage_serializes_impact_payload` + `std_template_governance_lifecycle.py` (`_json_safe_usage_impact`) |

## 5. Commands (copy-paste)

```bash
bench --site kentender.midas.com run-tests --app kentender_procurement \
  --module kentender_procurement.tender_management.tests.test_std_template_governance_smoke_doc8
```

```bash
cd apps/kentender_v1
npx playwright install chromium   # once per agent machine if needed
npx playwright test tests/ui/smoke/procurement/std-template-governance-smoke-doc8.spec.ts
```

---

**Desk navigation (add-on):** [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) **§E** — `test_std_governance_workspace_nav` + `std-governance-workspace-nav.spec.ts` (STD-GOV-NAV-AC-001…008).

---

**Last update:** 2026-05-03 — §C gate; doc 8 §32/§33 logged in [`ISSUES_LOG.md`](ISSUES_LOG.md); §E navigation.
