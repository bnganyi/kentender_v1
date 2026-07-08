# STD-LIB-0700 — Implementation review report (Official STD Library UI)

**Programme:** STD production readiness — admin revamp  
**Tracker:** [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md)  
**Pack:** [`2. cursor_pack_std_engine_official_library_ui.md`](2.%20cursor_pack_std_engine_official_library_ui.md)  
**Product spec:** [`1. std_engine_ui_refactor_official_std_library_model.md`](1.%20std_engine_ui_refactor_official_std_library_model.md)  
**Smoke / regression:** [`STD-LIB-section-C_smoke_environment_and_results.md`](STD-LIB-section-C_smoke_environment_and_results.md)

---

## 1. Executive summary

The **Official STD Library** Desk experience under `kentender_procurement` is implemented per doc **2** (pack): routing, library shell (regions A–F), summary queue, search/filters, template cards, detail tabs (Summary through Audit), six-step import wizard, header actions (Register Source, Validate Library), centralized JS facade, user-facing error/empty states, smoke tests (§26), accessibility basics (§27), and §C/C7 regression hooks. Delivery is **Frappe Desk + `frappe.call` whitelist methods**, not a standalone REST gateway or SPA.

**Definition of Done:** §D rows D1–D15 are evidenced in the tracker. This report records **deviations**, **doc 1 §15 mapping**, primary **artefacts**, and **test commands**.

---

## 2. Doc 1 §15 completion gate — evidence mapping

Doc **1** §732–742 lists pre-pack gate items. Programme **§A** and **§B** satisfy them for this bench; the spec PDF may still show unchecked boxes until stakeholders edit doc 1. Use this table as the authoritative mapping.

| Doc 1 §15 item | Evidence |
|----------------|----------|
| Official STD Library accepted as landing model | §A **A1**; **STD-LIB-0001**, **STD-LIB-0100**; workspace + [`std-governance-workspace-nav.spec.ts`](../../../../tests/ui/smoke/procurement/std-governance-workspace-nav.spec.ts) |
| Import Official STD Package as normal workflow | §A **A2**; **STD-LIB-0200**–**0260**, **STD-LIB-0110** |
| Manual template construction advanced/exceptional only | §A **A4**; **STD-LIB-0340**/**0341** (non-default Advanced; read-only technical surface); no manual constructor as primary path |
| Validation Dashboard accepted | §A **A3**; **STD-LIB-0300**, **STD-LIB-0410** |
| Bundle Preview central | §A **A3**; **STD-LIB-0310**, import **STD-LIB-0250** |
| Advanced Technical View hidden-by-default | §A **A4**; **STD-LIB-0340**/**0341**; §C **C4** |
| STD Instances outside primary administrator workflow | §A **A5**; **STD-LIB-0320**, **STD-LIB-0110**/**0140** |
| Previous STD Administrator UI pack superseded | §A programme + **STD-LIB-0001** routing; doc 1 §14 |

---

## 3. Product stance — doc 1 §10.3 / §568 (raw data and “advanced edit”)

**Spec text:** Raw package data read-only *unless* the template is **draft** and the user **explicitly chooses advanced edit mode**.

**Delivered behaviour:** The **Advanced Technical View** tab is **secondary**, **raw package JSON/XML is collapsed by default**, and the surface is **read-only** in the library UI for the scenarios covered by **STD-LIB-0340**/**0341** (including plain-label source mappings and blocker routing). **In-place editing of structured internals** from this tab is **not** implemented; controlled change paths remain **import wizard**, **governance-backed lifecycle**, and **supersession / create revision** (**STD-LIB-0330**), aligned with the pack’s non-default advanced scope.

**Disposition:** **Accepted for Desk-first MVP** — read-only Advanced + import / supersession / governance paths satisfy the pack; **in-product “advanced edit mode”** (editable structured internals for Imported Draft in the library UI) is **out of scope** for this phase. A follow-on would require product sign-off, [`ISSUES_LOG.md`](ISSUES_LOG.md) **STD-LIBU-***, and §A update if scope changes.

---

## 4. Architectural deviations (intentional)

| Topic | Pack / doc expectation | Delivered | Notes |
|-------|------------------------|-----------|--------|
| HTTP API | Doc 2 lists `/api/std-engine/...` REST shapes | Whitelisted Python methods invoked via `frappe.call` from Desk | See [`STD-LIB-REST-mapping.md`](STD-LIB-REST-mapping.md) |
| SPA / TypeScript client | Pack references `frontend/.../stdLibraryApi.ts` | **N/A** — §A6 Desk-first; [`std_library_api.js`](../../../../kentender_procurement/kentender_procurement/public/js/std_library/std_library_api.js) |
| Permissions | Conceptual `PERM_TEMPLATE_*` | Frappe roles + **STD-LIB-0110** [`std_library_action_availability.py`](../../../../kentender_procurement/kentender_procurement/tender_management/api/std_library_action_availability.py) |

---

## 5. Ticket rollup (§B)

All tickets **STD-LIB-0001** through **STD-LIB-0610** are **Done** with evidence in [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) §B. No blocked rows.

---

## 6. Primary implementation artefacts (by area)

| Area | Location |
|------|----------|
| Page routing / shell mount | [`std_engine_page.js`](../../../../kentender_procurement/kentender_procurement/public/js/std_engine_page.js), [`std_engine.json`](../../../../kentender_procurement/kentender_procurement/kentender_procurement/page/std_engine/std_engine.json) |
| Library orchestration | [`std_library_shell.js`](../../../../kentender_procurement/kentender_procurement/public/js/std_library/std_library_shell.js), [`std_library_shell.css`](../../../../kentender_procurement/kentender_procurement/public/css/std_library_shell.css) |
| Detail tab renderers | [`std_library_shell_detail_renderers.js`](../../../../kentender_procurement/kentender_procurement/public/js/std_library/std_library_shell_detail_renderers.js) |
| Import wizard UI | [`std_library_import_wizard_shell.js`](../../../../kentender_procurement/kentender_procurement/public/js/std_library/std_library_import_wizard_shell.js) |
| API facade (Desk) | [`std_library_api.js`](../../../../kentender_procurement/kentender_procurement/public/js/std_library/std_library_api.js) |
| User messages / empty states | [`std_library_user_messages.js`](../../../../kentender_procurement/kentender_procurement/public/js/std_library/std_library_user_messages.js) |
| Backend: templates / detail | [`std_library_templates.py`](../../../../kentender_procurement/kentender_procurement/tender_management/api/std_library_templates.py) |
| Backend: summary | [`std_library_summary.py`](../../../../kentender_procurement/kentender_procurement/tender_management/api/std_library_summary.py) |
| Backend: action availability | [`std_library_action_availability.py`](../../../../kentender_procurement/kentender_procurement/tender_management/api/std_library_action_availability.py) |
| Backend: import wizard | [`std_library_import_wizard.py`](../../../../kentender_procurement/kentender_procurement/tender_management/api/std_library_import_wizard.py) |
| Hooks / asset order | [`hooks.py`](../../../../kentender_procurement/kentender_procurement/hooks.py) |

---

## 7. Automated tests — commands

**Bench (site `kentender.midas.com`):** see [`STD-LIB-section-C_smoke_environment_and_results.md`](STD-LIB-section-C_smoke_environment_and_results.md) §4. Prefer **sequential** module runs for Works POC / governance smoke (see §9).

**Playwright (`apps/kentender_v1`):**

```bash
npm run test:ui:smoke:std-lib-0600
npm run test:ui:smoke:std-lib-0610
```

Broader desk smoke includes [`std-library-shell.spec.ts`](../../../../tests/ui/smoke/procurement/std-library-shell.spec.ts), [`std-engine-route.spec.ts`](../../../../tests/ui/smoke/procurement/std-engine-route.spec.ts), [`std-governance-workspace-nav.spec.ts`](../../../../tests/ui/smoke/procurement/std-governance-workspace-nav.spec.ts).

---

## 8. Blockers and operational notes

- **None** for documented MVP scope.
- **Bench concurrency:** parallel `run-tests` modules that mutate the same `STD Template` can cause lock wait / `TimestampMismatchError`. Mitigation: [`scripts/run-std-library-regression.sh`](../../../../scripts/run-std-library-regression.sh) (sequential).

---

## 9. Related programme items (cross-workstream)

- **Governance doc 8 smoke (ST-018)** — Desk multi-role governance UI remains **Partial** (Administrator slice) per [`../workstream-1/STD-GOV-doc8_smoke_environment_and_results.md`](../workstream-1/STD-GOV-doc8_smoke_environment_and_results.md); owned by Workstream 1, not the library UI track alone.

---

## 10. Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineering | | | |
| Product / owner | | | |

*(Optional paper trail; tracker evidence stands for automated verification.)*
