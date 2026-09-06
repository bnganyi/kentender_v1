# KT-STD-001 — Document, Design and Verification Standards

| Control | Value |
|---|---|
| Document ID | KT-STD-001 |
| Version | 1.3 |
| Status | Proposed for approval |
| Date | 4 September 2026 |
| Supersedes | v1.2, approved 3 September 2026 |
| Applies to | Every KenTender change unit, architecture decision record and module requirements document |
| Change type | Adds Brian Wafula (Procurement Officer, Tender Preparation) to §8.3, needed because SEED-001 had incorrectly given Charles Mutiso both the preparer and approver role for the same Tender Version — a direct violation of TPR-CHG-001's own segregation rule. Corrects "Head of Procurement" to "Head of Procurement Function" per the statutory term. Earlier: extracted rules previously duplicated across AUTH-ADR-001, CFG-CHG-002 and NDS-CHG-001. |

**Controlling decision:** Rules that apply to every KenTender document are written once here. A change unit states its domain and cites this standard. Where a change unit repeats a rule from this standard verbatim, this standard prevails and the repetition is deleted at the next revision.

---

## 1. Purpose and precedence

Before this standard existed, the same closed-input rules, page shell, verification protocol, release evidence and fixture actors appeared in three documents. They would have drifted: the first change to artboard width or test cadence would have been applied to two of three and the divergence would not have been noticed until a design comparison failed.

Precedence:

1. A module document's **domain** rules always prevail for that module.
2. This standard prevails for design-input mechanics, verification protocol, release evidence, page behaviour and shared fixtures.
3. A change unit may **add** a rule in these areas. It may not silently contradict one. A deliberate departure is stated as an exception naming this document.

---

## 2. Static design contract standard

### 2.1 Prompt assembly

A Claude Design prompt consists of **section 2 of this standard plus the single design section of one change unit**. Nothing else is supplied. No requirements, service contract, business rule, acceptance criterion or functional interaction section is ever pasted into a design prompt.

Each change unit's design section states only what is specific to it: its artboards, its fixture data, and its own list of elements that must not appear.

### 2.2 Closed-input rules

- Produce desktop artboards at **1440 × 1024 px**. Dialogs are **520 px** wide over a dimmed parent artboard.
- Reuse the approved KenTender visual system, spacing, type scale, tokens, cards, badges, tables, fields, buttons, tabs, empty states and dialogs.
- The artboard starts below the Frappe Desk header. Do not draw Frappe navigation, the Desk header, breadcrumb, user menu, notifications, Help or global search.
- Fixture context — actor, identifier, timestamp and breadcrumb — is data outside the artboard, supplied to confirm location only. It is not rendered.
- Use only the visible labels, values, badges, controls, sections and states stated for that artboard.
- Do not invent data. If a value or state is not stated, omit it. Do not substitute a placeholder, generated name, lorem ipsum or inferred content for a stated value.
- Do not encode behaviour, validation, permissions, APIs, routing, transitions, concurrency or implementation instructions in the visual output.
- Do not add summary cards, count cards, charts, percentages, trend arrows, illustrations, side panels, steppers, timelines, helper panels, action menus, metadata or table columns unless explicitly stated.
- Do not render requirement identifiers, fixture notes or implementation guidance in the artboard.
- Generated identifiers may be displayed on saved records but never as editable fields.
- Never represent a failure, a forbidden result or a missing configuration as an empty successful table or register.

### 2.3 Product-wide prohibitions

These apply to every artboard in every document, because the underlying concept was removed from the product:

- No Procuring Entity selector, switcher, column or context record.
- No PE/FY context record or readiness matrix.
- No Financial Year, module, capability, User Permission or arbitrary-scope control on a permission or assignment surface.
- No `lft`, `rgt`, `old_parent`, raw parent identifier or nested-set repair control.
- No submission, approval, review or draft control on a configuration or setup surface.

### 2.4 Approved desktop shell

Inside every full-page artboard:

- full-width warm-white page background;
- a 1200 px maximum-width content column centred in the available page area;
- 32 px top and bottom page padding;
- page header followed by 24 px vertical spacing;
- where a tab row is present, the tab row followed by 24 px vertical spacing;
- 16 px gaps between cards or table sections; and
- no custom sidebar.

### 2.5 Division of supply

Frappe supplies the Desk header, breadcrumb, session controls, route lifecycle, dialogs, toasts, the tree control and accessibility primitives. KenTender supplies the established `--kt-*` tokens and shared Vue components. Claude Design supplies only the page content defined in the change unit's design section.

Design export runtime files are design evidence under `docs/`. They are never imported into production.

---

## 3. Common page behaviour and accessibility

Applies to every KenTender page unless a change unit states an exception.

- Use semantic headings, labels, tables, status text and keyboard-operable controls. Colour is never the only carrier of state.
- Dialog focus is trapped and restored. Validation focus moves to the first invalid control or the error summary.
- Loading, empty, forbidden and error states are visibly distinct and use the exact copy in the owning change unit's state variant table.
- Field errors bind to their exact controls. A business-rule error appears in the approved error summary and moves focus there.
- The UI disables an initiating button while its command is pending and reuses one idempotency key for retries.
- All dates display in the site timezone. Service and audit instants remain UTC.
- Route changes unmount the Vue app and cancel stale requests. Returning to a cached Desk page re-resolves context and authorisation.
- Do not wait for `networkidle` on a Frappe Desk page. Tests wait for DOM content plus the exact page-ready selector.

---

## 3A. Authorisation and page states

### 3A.1 Resolve the verdict before rendering

A page's first server call returns the authorisation verdict **together with** its data, and the page renders exactly one state:

```
mount -> one resolve call
      -> permitted        -> content
      -> denied           -> inline Forbidden panel
      -> not configured   -> inline Not-configured panel
      -> error            -> inline Error panel with Try again
```

Nothing paints until the verdict arrives; the Loading state covers the wait. A page shall never render its header, filters, content or empty state and **then** discover the actor is not permitted. Showing a working screen and a refusal at the same time is a defect, not a race condition.

### 3A.2 A page-load denial is never a modal

The user pressed nothing, so there is nothing to dismiss back to. A modal on page load leaves them on a surface they cannot use, and its only affordance closes the explanation.

| Trigger | Treatment |
|---|---|
| Page load or route entry | **Inline page state. Never a modal.** |
| A control the user pressed | Toast, or an inline error bound to that control |
| A destructive or blocked command the user initiated | A dialog is appropriate — the user asked |

Server implementations return a **typed verdict** for page-load authorisation rather than raising, because raising produces the framework's stock permission modal and its stock copy. Raising remains correct for command-level denials.

### 3A.3 Gate navigation, do not hide it

A module the actor cannot enter stays in the navigation. Selecting it pushes that module's own route, highlights that module, and lands on its Forbidden state.

Hiding modules produces "where did it go?" support traffic and makes the product look broken. It also conceals a misconfiguration that the Forbidden panel would have explained.

**Route and view shall never diverge.** A navigation action that swaps the rendered view without pushing its route breaks refresh, breaks the back button, and produces URLs that open something else.

### 3A.4 Forbidden copy

The Forbidden panel names the responsibilities that open the surface and the person who grants them. Which responsibility opens a door is not protected information — the non-disclosure rules govern the existence and contents of records, not the shape of the permission model. A dead end the user cannot act on generates a support ticket; a named responsibility generates a correct request.

The template, with each document supplying its surface name and responsibility list:

> **You do not have access to {surface}**
> This area needs one of these responsibilities: {responsibility list}.
> Ask your KenTender administrator to assign one in System setup.

For a surface reached by technical access rather than a business responsibility, the second line reads: **This area needs Administrator or System Manager access.**

The panel shall not name a line manager, a supervisor or a department head. Responsibilities are granted by an Administrator or System Manager in System setup, and no other route exists.

### 3A.5 Identity chrome

Where a page displays the signed-in user's role, it displays **every** active responsibility with its scope, or none at all. A single role label is wrong for any user holding more than one assignment, which the authorisation model expressly permits.

---

## 4. Frappe and Vue implementation standard

- Implement domain records as explicit Frappe DocTypes with server-side controllers and services. Do not store business state in client-only objects.
- Reuse a native Frappe or ERPNext record, control or hook before creating a KenTender equivalent. Do not fork, override or duplicate an ERPNext DocType.
- Mount Vue 3 pages through the existing `frappe.ui.make_app_page()` → built bundle → `createApp().mount()` pattern.
- Port design markup and tokens into scoped Vue single-file components. Keep component styles scoped beneath one page root. Do not add Tailwind Preflight, a CDN, global element resets or rules that restyle Frappe Desk.
- Use Frappe RPC or resource APIs for authorised services. Do not expose writable DocType endpoints that bypass a governed command.
- Every mutation is authorised, validated and version-checked server-side. Options, summaries, counts and available actions come from the server. Client controls are never authority.
- Every state command carries `expected_version`; a stale command has no partial effect. Every retriable command carries an idempotency key and returns the original committed result on replay.
- Register routes in `cl_surface_registry` and `STITCH_DESK_SURFACES`. Provide `data-testid="back-to-workbench"` and return to the owning workspace rather than raw `/desk`.
- Add stable accessible test selectors to page-ready state, field controls, tables, dialogs and primary commands. Do not select by visual CSS classes.

---

## 5. TDD and efficient verification

For each behaviour change:

1. write or identify the smallest failing test that proves the rule;
2. run that test file or exact test node;
3. implement the minimum coherent fix;
4. rerun the same focused test;
5. run the directly affected domain or component group;
6. run the one relevant browser smoke and screenshot when UI changed; and
7. run the owning module suite once the focused group is green.

Do not rerun the whole repository suite, all browser tests or every screenshot after each small fix. The broader integrated suite runs at the release gate or when a shared contract or component changed.

Where a change unit modifies shared infrastructure — authorisation, configuration, or a component used by more than one module — the release gate additionally requires affected-module tests and cross-app contract tests. A happy-path module test alone is insufficient.

The repository test map documents, for each module: the exact domain test node; the module domain group; the exact Vue component test; the exact Playwright scenario; the module suite; and the integrated release suite.

When a failure occurs, preserve the first useful traceback, server response, browser console error and screenshot. Classify it as product, fixture, selector, environment or unrelated failure before changing code. Do not adjust a product screen to satisfy an ambiguous selector.

---

## 6. Required release evidence

Every change unit's release requires:

- a targeted red-green test record for every acceptance criterion changed during implementation;
- a clean module suite and clean contract tests for every document the change unit cites;
- a successful production-mode asset build;
- a scripted browser smoke with zero page console errors and zero failed own requests;
- visual comparison for all approved artboards at 1440 × 1024; and
- a schema and repository scan proving every removed DocType, field, role, capability string and route named in the change unit's disposition register is absent.

---

## 7. Change unit structure

Every KenTender change unit and architecture decision record uses this skeleton. A section that does not apply is omitted, not filled with prose.

| # | Section | Content |
|---|---|---|
| — | Control table and controlling decision | Identity, version, status, and the decision in one paragraph. |
| 1 | Governing decision and disposition register | What this document decides, and a table of every earlier item with its disposition. |
| 2 | Purpose, outcomes and scope exclusions | What it provides and what it explicitly does not. |
| 3 | Ownership and dependency boundary | Who owns each record or concern, and the permitted dependency paths. |
| 4 | Canonical domain model | Field tables with rules. Server-generated identifiers noted. |
| 5 | Lifecycle and business rules | States, transitions, invariants and their enforcement points. |
| 6 | Roles and permissions | Business responsibilities and their permitted work. Never a permission mechanism. |
| 7 | Service and command contracts | Inputs, outputs and required controls. |
| 8 | Error contract | Code and user-visible message. Messages never name internal tables or algorithms. |
| 9 | UI architecture, menu and routes | Canonical routes and their purpose. |
| 10 | Static design contract | Closed visual input. Cites KT-STD-001 §2 and adds only what is specific. |
| 11 | Functional interaction requirements | Runtime behaviour. Headed **excluded from design prompts**. |
| 12 | Audit and historical integrity | What every material command records and what is immutable. |
| 13 | Seed contract | Deterministic fixtures, citing KT-STD-001 §8 for shared actors. |
| 14 | Acceptance contract | Numbered, testable required results. |
| 15 | Implementation and test constraints | Domain-specific only. Cites KT-STD-001 §4–6. |
| 16 | Prohibited shortcuts | Domain-specific only. Cites KT-STD-001 §2.3 for product-wide prohibitions. |
| 17 | Traceability and precedence | Which document owns what, and which documents need a matching correction. |
| 18 | Approval effect | What approval authorises and what implementers must not retain. |

Two rules govern content everywhere:

**Data-purpose gate.** No stored field is permitted unless a current operational decision or output uses it, the screen, rule or service consuming it is named, and its validation and system effect are defined. "Useful later", "normally captured", "helpful context" and "the design showed it" are not sufficient reasons. An undocumented field is omitted, not added as optional data.

**Default to omit.** If an implementation ambiguity would add a field, action, screen, object or role, the answer is omit it until a current operational purpose, named consumer, validation and effect are approved.

---

## 8. Shared fixture register

These fixtures are canonical across every KenTender document, seed and artboard. A change unit uses them rather than inventing names, and adds an actor only when its scenario genuinely needs one.

### 8.1 Site

| Item | Value |
|---|---|
| Procuring Entity | `PE-MOH` · Ministry of Health · National Government Ministry · `Africa/Nairobi` |
| Root Organisation Unit | Ministry of Health · `PE-MOH` · Active |
| ERPNext Company | Ministry of Health |
| Email domain | `moh.example.test` |

### 8.2 Organisation Units

| Code | Unit | Parent |
|---|---|---|
| `OU-MOH-DHP` | Directorate of Digital Health and Policy | Root |
| `OU-MOH-DHI` | Digital Health | `OU-MOH-DHP` |
| `OU-MOH-HRMD` | Human Resources Management and Development | Root |

### 8.3 Actors

| User | Login | Responsibility | Scope |
|---|---|---|---|
| Grace Wanjiku | `grace.wanjiku@moh.example.test` | Departmental Author | `OU-MOH-DHI` |
| Dr Peter Kimani | `peter.kimani@moh.example.test` | Head of User Department | `OU-MOH-HRMD` |
| Julia Njeri | `julia.njeri@moh.example.test` | Head of User Department, Acting | `OU-MOH-DHI` |
| Mercy Kilonzo | `mercy.kilonzo@moh.example.test` | Procurement Planner | Site-wide |
| Samuel Otieno | `samuel.otieno@moh.example.test` | Head of User Department, expired | `OU-MOH-DHP` |
| Administrator | `administrator@moh.example.test` | Technical only | — |
| Esther Muthoni | `esther.muthoni@moh.example.test` | Strategy Author | Site-wide |
| Dr Alfred Ochieng | `alfred.ochieng@moh.example.test` | Strategy Approver | Site-wide |
| Naomi Chebet | `naomi.chebet@moh.example.test` | Auditor | Site-wide |
| Josphat Mwangi | `josphat.mwangi@moh.example.test` | Budget Officer, and separately Finance Confirmation Officer | Site-wide |
| Beatrice Kamau | `beatrice.kamau@moh.example.test` | Budget Approver | Site-wide |
| Amina Hassan | `amina.hassan@moh.example.test` | Accounting Officer | Site-wide |
| Daniel Rotich | `daniel.rotich@moh.example.test` | Statutory approver, in the entity's configured route | Site-wide |
| Charles Mutiso | `charles.mutiso@moh.example.test` | Head of Procurement Function | Site-wide |
| Brian Wafula | `brian.wafula@moh.example.test` | Procurement Officer, site-wide — Tender Preparation only | Site-wide |

Grace additionally holds Head of User Department in `OU-MOH-HRMD` in the Cartesian-product regression fixture, so the same-user-different-scope test has a concrete subject.

Josphat Mwangi holds two responsibilities deliberately: BUD-CHG-001 distinguishes Budget Officer, who authors budget versions, from Finance Confirmation Officer, who confirms a plan sits within budget. One person holding both exercises the no-self-approval rule.

**Head of Procurement Function is not Procurement Planner.** Mercy Kilonzo owns the annual procurement plan; Charles Mutiso owns the annual asset disposal plan and approves Tenders in Tender Preparation. They are separate registry entries under AUTH-ADR-001 §4.4 and may be held by different people. **Brian Wafula is not Charles Mutiso.** Tender Preparation requires a Procurement Officer to prepare a Tender Version and a separate Head of Procurement Function to approve it — the same person cannot hold both for one Version, per TPR-CHG-001's segregation rule.

### 8.4 Fiscal years

| Year | Period | Needs submission |
|---|---|---|
| FY 2026/27 | 1 Jul 2026 – 30 Jun 2027 | Closed |
| FY 2027/28 | 1 Jul 2027 – 30 Jun 2028 | Open, closing 25 Nov 2026, 23:59 EAT |

### 8.4A Fixture instants

Each module works in a distinct window so the fixtures compose into one coherent year without colliding.

| Purpose | Instants |
|---|---|
| Site configuration history | 29 Jun 2026, 10:10 EAT |
| Responsibility administration | 1 Sep 2026, between 09:00 and 10:30 EAT |
| Strategy journeys | 24–25 Nov 2026, between 11:00 and 17:00 EAT |
| Departmental Needs journeys | 24 Nov 2026, between 09:00 and 15:30 EAT |
| Procurement Planning journeys | 24 Nov 2026 through 20 Dec 2026, EAT |
| Budget journeys | 1 Oct 2026 through 16 Mar 2027, EAT — registration precedes reservation, which precedes revision |
| Asset Disposal journeys | 4 May 2027 through 14 Jan 2028, EAT — the FY 2027/28 disposal plan is prepared before that year begins |

### 8.5 Units of measure

Enabled ERPNext `UOM` records: `Each`, `Programme`, `Set`, `Lot`, `Kilogram`, `Litre`, `Metre`, `Square Metre`, `Cubic Metre`, `Service Month`. All others disabled.

### 8.6 Seed execution rules

- Seeds call the same commands as the UI. They never write a governed DocType directly.
- Seeds create no Frappe User Permission, `User Scope Assignment`, `Capability Profile`, Fiscal Year user grant or `kt_primary_department` value as authority.
- Seeds never grant a business role to Administrator.
- Seeds are deterministic and idempotent. Running them twice creates no duplicate record, version, lifecycle entry or audit entry.
- Seeds fail on conflicting authoritative data and never repair, alias or import legacy records.

### 8.7 Fixture consistency

Every artboard fixture, seed record and test fixture across all documents refers to the same register. Where an artboard needs a state the seed does not contain — a blocked action, a conflict notice, an unsaved draft — the change unit states it as an artboard-only fixture and says so explicitly, so a seed-versus-artboard comparison does not report a false mismatch.

---

## 10. Universal prohibited shortcuts

These apply to every document and every layer, not only to artboards. Section 2.3 covers what may not be *drawn*; this section covers what may not be *built*. A change unit lists only its own domain-specific prohibitions and cites this section for the rest.

- Do not create, model or simulate a second Procuring Entity, including "for reporting".
- Do not add a Procuring Entity field, selector, column or permission anywhere.
- Do not treat a Frappe Role, Frappe User Permission, task, queue, menu, route, UI button or browser context as business authority.
- Do not store authoritative context in local storage, session defaults or a user profile.
- Do not add Fiscal Year to a user grant or an authority record.
- Do not require a pre-entry PE, department or Fiscal Year selection screen, or make a saved filter irreversible.
- Do not use `ignore_permissions=True` in a scoped read path.
- Do not implement client-only permission, lifecycle, uniqueness or duplicate checks.
- Do not add an approval, submission or review stage to a configuration or authorization write.
- Do not create a second Frappe header, breadcrumb, shell or global context selector.
- Do not import Claude Design canvas runtime files into production.
- Do not copy runtime rules into a Claude Design prompt, or infer runtime behaviour from generated markup.
- Do not add compatibility redirects, legacy aliases, migration branches, dual reads or fallback fixtures.
- Do not delete referenced records, or delete legacy records before cutover evidence is complete.
- Do not delete ERPNext or HRMS records during a KenTender cutover.
- Do not run the full repository suite after each small correction.

---

## 11. Error contract conventions

- Codes are uppercase and prefixed by the owning document's abbreviation, for example `AUTH_SCOPE_REQUIRED` or `CFG_FY_IN_USE`.
- Messages are one plain sentence addressed to the user.
- Messages never name internal tables, DocTypes, hooks, permission algorithms or framework mechanisms.
- Where existence itself is protected, a cross-scope read returns Not found rather than a permission error.
- Every state command carries `expected_version`; a stale command has no partial effect. Every retriable command carries an idempotency key and returns the original committed result on replay.

---

## 12. Approval effect

On approval, KT-STD-001 v1.3 becomes the single source for KenTender design-input mechanics, page behaviour, implementation standards, verification protocol, release evidence, document structure, shared fixtures, universal prohibitions and error-contract conventions.

Where a citing document conflicts with this standard, the citing document prevails only where it states the departure explicitly and gives a reason. A silent divergence is a defect, not a decision. This standard governs form and delivery; it never overrides a domain decision in an architecture decision record or a module requirements document.

v1.3 adds Brian Wafula to §8.3 and corrects "Head of Procurement" to "Head of Procurement Function." v1.2 adds section 3A. v1.1 added sections 10 and 11 to v1.0, and completes the shared fixture register in §8.3 and §8.4A with the actors and instants required by STR-CHG-001, BUD-CHG-001, PLN-CHG-001 and DSP-CHG-001. Nothing else changes. Existing citations of KT-STD-001 v1.0 through v1.2 remain valid.
