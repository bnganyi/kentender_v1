# KenTender CTX-CHG-001 — Working Context, v1.0

Status: **Implemented** (2026-08-30). Cross-cutting; future module change
documents reference this specification instead of restating context rules.

## 1. The durable rule

> Permissions determine what the user may access. Context only filters what
> the user is currently working on. It is visible, reversible,
> module-appropriate and never authoritative.

## 2. The six rules

1. **Access scope.** Server-side Frappe Roles and User Permissions (with
   User Scope Assignment where present) determine which Procuring Entities
   and departments a user may access. Browser storage grants no authority —
   and is not used even as a cache.
2. **Procuring Entity.** The selected PE is one GLOBAL working preference per
   user: always visible, always changeable, validated by the server on every
   request, and never able to prevent an authorised direct record link from
   opening. Administrators may select any Active PE; ordinary users only
   their permitted ones. The UI surface is the shared Industry PageRail
   switcher, rendered only when the user can genuinely switch (`can_switch`:
   more than one permitted PE, or unrestricted); single-PE users see a plain
   chip.
3. **Financial Year.** FY is selected within each module, never platform-wide:
   Budget may work the current FY while Needs collects the next, Planning
   prepares a future one and Audit inspects a past one. Each workspace has
   its own FY selector and remembers only that module's last FY.
4. **Departmental Needs behaviour.** The Needs workspace always shows the
   selected PE, the selected department (with an always-available *Change
   context*), a changeable Financial Year, the intake-window state and its
   exact opening and closing instants.

   | Window state | Permitted behaviour |
   |---|---|
   | Open | Create and initially submit Needs |
   | Scheduled | View existing records; creation disabled; offer *Change financial year* |
   | Closed | View records and permitted corrections; no new Need or initial submission |

   Selecting a future FY before its window opens never traps the user: it
   disables *Create need* for that year behind an inline notice while another
   FY stays one click away.
5. **Context persistence.** The last-used selection is a server-side user
   preference (`frappe.defaults`). Selection rules: a single eligible option
   auto-selects; several use the user's last valid module selection; a saved
   selection that is no longer valid prompts again (never an error, never
   access); *Change context* is always provided.
6. **Existing records.** Every record stores its PE, department and FY
   permanently. Opening a record uses that record's own context after
   permission validation — never the working preference.

## 3. Service contract (kentender_core)

`kentender_core/kentender_core/services/working_context.py` owns persistence
and resolution; **modules own eligibility** and may narrow the offer, never
widen it.

Keys (all `frappe.defaults`, all MANDATORY snake_case — `key ==
frappe.scrub(key)`; a Title-Case key silently fails to round-trip through
`get_user_default` via `is_a_user_permission_key`, which is exactly how
Planning's old keys never restored):

| Key | Scope | Value |
|---|---|---|
| `kt_working_procuring_entity` | global per user | Procuring Entity docname |
| `kt_{module}_financial_year` | per module | the module's offered FY id (opaque to core) |
| `kt_{module}_org_unit` | per module | Organisation Unit docname |

Service surface: `pe_options`, `get_working_pe(requested=)` /
`select_working_pe`, `default_fy_options(pe)` (PE Fiscal Year Context rows,
non-Suspended), `get_module_fy(module, requested=, offered=)` /
`select_module_fy`, `get_module_ou` / `select_module_ou`, `pe_label` (the one
canonical PE display rule: legal_name → entity_name → id).

Resolution order, identical for every dimension and never authoritative:
explicit request (validated against the offer, then persisted — a deep link
is a deliberate choice) → saved preference if still offered → auto-select a
single option → `None` with `selection_required`.

Whitelisted endpoints (`api/working_context_api.py`): `get_working_context
(module=None, requested_pe=None)`, `select_working_pe(pe_id)`,
`select_module_financial_year(module, financial_year)`.

UI propagation: `mountPageRail(el, {showPeSwitcher, onPeChange})` (per-app
`usePageRail(elRef, trailRef, opts)` copies forward it); a switch invokes the
host's `onPeChange(selected)` and dispatches the
`kt:working-pe-changed` DOM CustomEvent for non-Vue pages. The switcher is
dormant unless the page opts in.

## 4. Eligibility model

- **PE**: one canonical rule —
  `org_scope_access.permitted_procuring_entities(user)` (`None` =
  unrestricted; falls back to ALL of the user's `Procuring Entity` User
  Permission rows) intersected with Active entities.
- **FY**: module-owned, passed as `offered=`. Needs filters Available,
  unexpired years by the caller's Financial Year User Permissions; Budget
  and the registry default use `PE Fiscal Year Context` rows; Planning
  speaks ERPNext Fiscal Year labels; Home speaks int start years. Governed
  `Financial Year` docnames are the TARGET vocabulary (CTX-FU-02).
- `PE Fiscal Year Context` (Scheduled/Active/Suspended/Closed) remains the
  registry of valid (PE, FY) pairs; `validate_context_for_command` remains
  the write-time registry-state gate. Business commands keep their own
  Role/scope/state checks — a working context grants nothing.

## 5. Per-module adoption

| Module | PE source | FY | OU | UI |
|---|---|---|---|---|
| Departmental Needs | global pref via rail | `kt_needs_financial_year`, module offer | `kt_needs_org_unit` | rail switcher + band FY select + cross-PE picker |
| Budget & Funding | global pref via rail | `kt_budget_financial_year` (registry offer) | — | rail switcher + context picker (compat shim keeps its contract) |
| Planning workspace | global pref (narrowed by Planning scope) | `kt_planning_financial_year` (label vocabulary) | — | own header selects + `kt:working-pe-changed` |
| Procurement Home | global pref | `kt_home_financial_year` (int-year vocabulary) | — | own header selects + `kt:working-pe-changed` |
| Strategy | global pref via rail | n/a | — | rail switcher |

Retired: Needs' `kt-nds-context` localStorage; Budget's
`kt_budget_working_context` context-id default (migrated);
Planning's Title-Case defaults (deleted — they never worked);
`User.kt_procuring_entity` custom field (migrated).

## 6. Follow-ups

- **CTX-FU-01** — `User Scope Assignment.effective_from/to` is selected but
  never enforced in `org_scope_access.user_scope_rows`. Deliberately out of
  scope here: enforcing dates changes real access outcomes mid-redesign.
  All PE eligibility now routes through `permitted_procuring_entities`, so
  the eventual date filter is a one-line change in exactly one place, with
  its own test pass.
- **CTX-FU-02** — FY vocabulary unification onto governed `Financial Year`
  docnames (Planning's labels, Home's int years). Supersedes the Needs
  FU-07 entry.
- **CTX-FU-03** — Planning's Demand-era remnants: `test_planning_context_chg016.py`
  and the Playwright planning suite import/seed retired Demand services
  (dead since the NDS greenfield rebuild). Their recovery is the "Planning
  sources accepted Needs" integration, not a context concern. The module
  API itself was restored to importability by this change
  (PLN_DEMANDS_RETIRED governs the two retired formation endpoints).
