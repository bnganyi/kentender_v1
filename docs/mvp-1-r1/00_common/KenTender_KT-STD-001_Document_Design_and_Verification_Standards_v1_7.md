# KT-STD-001 — Document, Design and Verification Standards

| Control | Value |
|---|---|
| Document ID | KT-STD-001 |
| Version | 1.7 |
| Status | **Approved** |
| Approved on | 21 September 2026 |
| Approval record | Project Owner instruction on 21 September 2026: **Mark as approved, and let's move to Stage 2.** |
| Date | 21 September 2026 |
| Supersedes | v1.6, approved 15 September 2026; retained as historical evidence. |
| Applies to | Every KenTender change unit, architecture decision record and module requirements document |
| Change type | Rewrites the shared design-input standard around task-led hierarchy, page archetypes, structured density, plain-language status and comprehension testing. Corrects rules that encouraged blocky, table-dominant screens. Preserves closed input, no invention, functional separation, technical read and all non-presentation controls. |

**Controlling decision:** KenTender shall make dense public-procurement work understandable without simplifying away required information. Every ordinary screen shall lead with the actor's task, current position and lawful next action; working facts follow; audit, provenance and technical evidence remain available but subordinate. Rules that apply to every KenTender document are written once here. A change unit states its domain and cites this standard. Where a change unit repeats a rule from this standard verbatim, this standard prevails and the repetition is deleted at the next revision.

---

## 1. Purpose and precedence

Before this standard existed, the same closed-input rules, page shell, verification protocol, release evidence and fixture actors appeared in three documents. They would have drifted: the first change to artboard width or test cadence would have been applied to two of three and the divergence would not have been noticed until a design comparison failed.

Precedence:

1. A module document's **domain** rules always prevail for that module.
2. This standard prevails for design-input mechanics, presentation architecture, verification protocol, release evidence, page behaviour and shared fixtures.
3. A change unit may **add** a rule in these areas. It may not silently contradict one. A deliberate departure is stated as an exception naming this document.

---

## 2. Static design and experience contract standard

### 2.1 Design objective and prompt assembly

KenTender's visual objective is **simple, informative and decision-ready**. Simple means that the user does not have to reconstruct the process, interpret internal terminology or search for the next action. It does not mean hiding material evidence, reducing a complete review to a count or removing a lawful decision.

A Claude Design prompt consists of **section 2 of this standard plus the single design section of one change unit**. Nothing else is supplied. No service contract, lifecycle algorithm, permission expression, acceptance criterion or functional interaction section is pasted into a design prompt.

Each change unit's design section states only what is specific to it: the page archetype, actor task, information priority, artboards, visible content, fixture data, action presentation, state variants and its own prohibited elements. The module contract owns **what** must be shown; this standard owns the shared logic for **how it is understood**.

### 2.2 Closed input and content fidelity

- Produce desktop artboards at **1440 × 1024 px**. Dialogs are **520 px** wide over a dimmed parent artboard.
- Reuse the approved KenTender visual system, spacing, type scale, tokens, cards, badges, tables, fields, buttons, tabs, empty states and dialogs.
- The artboard starts below the Frappe Desk header. Do not draw Frappe navigation, the Desk header, breadcrumb, user menu, notifications, Help or global search.
- Fixture context — actor, identifier, timestamp and breadcrumb — is data outside the artboard, supplied to confirm location only. It is not rendered.
- Use only the visible facts, values, actions and states stated for that artboard. Shared structural components explicitly authorised by the chosen archetype in §2.6 may be used to present those facts; they do not authorise new data or actions.
- Do not invent data. If a value or state is not stated, omit it. Do not substitute a placeholder, generated name, lorem ipsum or inferred content for a stated value.
- Do not encode behaviour, validation, permissions, APIs, routing, transitions, concurrency or implementation instructions in the visual output.
- Do not invent dashboard metrics, charts, percentages, trend arrows, illustrations, steppers, timelines, side panels, metadata, actions or table columns. A stated workload count, decision result, issue summary or record summary may use the archetype's standard summary treatment; this is presentation of supplied facts, not permission to invent analytics.
- Do not render requirement identifiers, fixture notes or implementation guidance in the artboard.
- Generated identifiers may be displayed on saved records but never as editable fields.
- Never represent a failure, a forbidden result or a missing configuration as an empty successful table or register.
- **Every material fact must be distinguishable, but it does not require its own box, row or column.** Related facts may be grouped into one readable unit when the relationship is obvious—for example, `250 Each`, a title with its muted reference beneath, or a short sentence naming actor and time. Give a fact its own label when omission of the label could change meaning, when values must be compared, when the fact is editable, or when it affects a decision. Never compress a complete package into a bare count or delimiter-heavy sentence that forces the reader to infer its contents.
- A count or short summary may orient the reader, but it never substitutes for required review content. Complete governed detail remains available in the same page or one clearly named disclosure.
- Do not repeat the same context in a page header, context panel, filter and table unless each occurrence has a distinct task purpose.

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
- 16 px minimum gaps between distinct work regions; and
- no custom sidebar.

The content column is a boundary, not a command to fill the page with bordered rectangles. Whitespace, typography and alignment establish hierarchy before borders or shaded containers.

### 2.5 Division of supply

Frappe supplies the Desk header, breadcrumb, session controls, route lifecycle, dialogs, toasts, the tree control and accessibility primitives. KenTender supplies the established `--kt-*` tokens and shared Vue components. Claude Design supplies only the page content defined in the change unit's design section.

Design export runtime files are design evidence under `docs/`. They are never imported into production.

---

### 2.6 Task-led screen-composition standard

A static design contract must define comprehension, hierarchy and composition—not merely enumerate content or prescribe a succession of tables. Exactness remains mandatory, but exactness is not the same as visual equality.

#### 2.6.1 Four questions every operational screen answers

The first view of an ordinary screen shall make these answers discoverable in this order:

1. **Where am I, and what am I responsible for here?**
2. **What requires attention, or what is the current result?**
3. **What information do I need to understand or complete the work?**
4. **What can I do next, and what will that action mean?**

The first view need not contain every audit fact. It must contain every fact that changes the actor's understanding, decision or permitted next step.

#### 2.6.2 Information priority

Every screen contract assigns visible content to one of three levels:

| Level | Purpose | Normal treatment |
|---|---|---|
| **1 — Attention and action** | Current result, assigned work, material blocker, required decision and primary action | First and visually dominant; never hidden in a disclosure or diluted by register controls |
| **2 — Working or decision information** | Facts the actor edits, compares or must understand to act correctly | Open in the main flow; grouped by the user's task rather than storage model |
| **3 — Supporting evidence** | History, provenance, exact identifiers, calculation detail, audit evidence and technical context | Quieter and normally disclosed after the working content; still complete and accessible |

Critical warnings, proposed-versus-current differences, decision consequences and facts required for lawful review are Level 1 or 2. They never become Level 3 merely because they are technically derived or historically sourced.

One page may contain several sections, but it has one dominant job. A secondary register, history or evidence region must not visually compete with the work that brought the actor to the page.

#### 2.6.3 Page archetypes

Each full-page artboard names one primary archetype. A module may combine a primary archetype with one subordinate region, but it shall not combine two peer primary experiences on the same page.

| Archetype | Dominant user job | Required composition |
|---|---|---|
| **Work workspace** | Find and start the work that needs this actor | Role/scope orientation; dominant actionable work; one obvious action per item; quieter existing/recent records below or through a named view. Omit empty task regions. |
| **Register** | Find, filter and inspect many records | Compact search/filter controls local to the register; comparable rows; result count/paging where needed; no unrelated decision area competing above it. |
| **Form or editor** | Create or correct a record | Plain purpose; logically grouped editable sections; source/read-only context visually distinct; validation beside affected work; persistent but non-obscuring action area. |
| **Review or decision** | Understand one immutable submission and make one governed decision | Result or decision required first; complete material facts and differences; consequence beside the decision; primary and corrective actions clearly differentiated; audit evidence subordinate. |
| **Record detail** | Understand current truth, related process position and history | Current status narrative and key facts first; pending/proposed work explicitly separated from current truth; related process information next; history/provenance last. |
| **Setup** | Maintain controlled configuration | Effective setting and consequence; compact editable group; dependent-use warning where material; audit history subordinate; no business approval styling. |
| **Focused dialog or panel** | Complete one bounded choice or confirmation | Exact object and consequence; minimum fields needed; Cancel and one principal completion action; parent context remains recognisable. |

A workspace is not a register with a heading placed above it. A review page is not a read-only form with buttons appended. A record detail page is not an audit table with the current state mixed into history.

#### 2.6.4 Component selection and structured density

- Use a **table** when users must compare repeated records across common attributes, scan a substantial result set, sort, filter or page. A one- or two-item action queue ordinarily uses compact task rows or another approved action-led treatment, not a full register grid.
- Use a **task row** when one item has one clear next action. Lead with the business name and plain-language work state; keep reference, actor and timestamp subordinate.
- Use a **summary strip or result block** only for supplied facts that orient the current task: workload requiring action, current decision result, material totals or blockers. Equal-sized decorative KPI cards are prohibited.
- Use **labelled fact groups** for a small set of contextual values. Size the group to its content; do not stretch two facts into an empty full-width box.
- Use **disclosures** for Level 3 evidence and long governed text. Use no more than one disclosure depth in ordinary work. A disclosure summary must say what is inside; a bare count is insufficient where the detail matters.
- Use **tabs** only for peer views of the same context. Do not use tabs or steppers to conceal a linear review, divide one decision into artificial stages or make the actor rediscover required facts.
- Put **filters with the records they filter**. Filters for a secondary register do not sit above or visually govern a primary action queue unless the contract explicitly states that they affect both.
- Avoid repeating a field merely to fill a standard component. Omit blank, default, single-value and not-applicable facts unless their absence or value changes interpretation.
- Preserve professional density. Large padding, oversized cards and sparse consumer-dashboard treatments are as defective as cramped grids. The goal is compact, legible grouping with a clear reading order.

#### 2.6.5 Action hierarchy

- One task region has one visually dominant primary action. It shall not be rendered as a weak text link when it is the principal purpose of the screen or row.
- Corrective, destructive and navigational actions remain distinct from the positive primary action. Destructive actions do not borrow the primary colour.
- Put the consequence of a material decision immediately beside or above its action. Do not require a second generic confirmation when the consequence is already clear, except where the owning contract explicitly requires one.
- A disabled action includes the concrete reason and recovery next to it. If no useful recovery exists in that state, omit the action rather than displaying unexplained disabled controls.
- Do not make filters, disclosures, export or history controls visually compete with a current business decision.

#### 2.6.6 Status and process explanation

Formal status remains visible where useful, but ordinary users shall not have to infer its operational meaning. For every material non-terminal state, the screen contract states, using approved facts:

- what has happened;
- who or which responsibility acts next;
- what the current actor can do; and
- any consequence or blocker that changes the next step.

This explanation may be a short status narrative rather than four labelled rows. It must not invent an SLA, priority, assignee or due date.

Current truth, a proposed change, downstream usage and history are visually distinct. A pending update never looks like the accepted record; a downstream planning state never looks like the source record's own approval state.

#### 2.6.7 Visual hierarchy and restraint

- Establish hierarchy in this order: content order, heading scale/weight, whitespace/alignment, restrained surface contrast, then borders.
- Use borders and shaded containers to express a real grouping or state, not around every section. Avoid nested bordered rectangles.
- Reserve the product accent for active navigation, selected controls, key focus and primary actions. Repeated full-width accent rules are not section hierarchy.
- Do not use all-uppercase or letter-spaced headings for ordinary section titles or every table header. Typography must remain readable at dense professional scales.
- Status colour is supplementary. Every state has explicit text and meets contrast requirements.
- A selected, hovered, focused and active row must have distinct meaning. Do not leave a row apparently selected when no selection model or result exists.
- The secondary region of a page is visibly quieter through scale, spacing, surface and action treatment—not merely because it appears lower on the page.

#### 2.6.8 Mandatory module screen-brief format

Every new or revised module design contract uses this structure:

1. **Screen identity, archetype and purpose.** Stable artboard ID, screen name, named archetype and the actor's immediate task in one sentence.
2. **Fixture context — outside the artboard.** Actor, assignment/scope, date/time, exact record/revision and named scenario. Resolve the pictured authority and state; do not ask the designer to calculate them.
3. **Primary question and action.** State what the actor must understand or complete and the one action that should dominate, or explicitly state that the page is read-only.
4. **Information priority.** List Level 1, Level 2 and Level 3 content. Do not leave the designer to decide which facts matter.
5. **Page header and orientation.** Exact title, description, status/reference treatment, visible scope and any header action. Do not duplicate context already clear from the shell or task.
6. **Composition, top to bottom.** Name each region, its job, component type and placement. For a horizontal arrangement, give its left-to-right order. Explain why a table is required where one is used for a small set.
7. **Controls and complete content.** Supply exact labels, values, helper text, field/control types, comparison columns and fixture rows. State how secondary evidence is subordinated. A field inventory alone is insufficient.
8. **Actions and visible state.** For every pictured action, specify label, prominence, location and enabled/disabled/absent treatment. Do not use unresolved phrases such as “when permitted”, “where relevant” or “may appear”.
9. **Supporting detail.** Name each disclosure/secondary section, its initial state and complete supplied content. Critical facts remain outside it.
10. **Separate variants.** Give empty, filtered-empty, closed, error, blocked, pending and alternate-actor compositions stable IDs and definite action sets. A variant may reuse a complete base and state exact changes.
11. **Comprehension acceptance.** State what must be obvious in the first view, what must be findable without leaving the page and what must be visually subordinate.

Use short named subsections, bullets and tables where they genuinely clarify exact fields, rows or comparisons. A table is not a substitute for composition. This format authorises no new business field, metric, role, action or workflow step.

### 2.7 Static specification and functional interaction mapping

The static contract states what the pictured screen contains and how it is arranged. The functional section supplies a matching action map: artboard/action, destination or visible result, applicable existing command/read contract, and outcome/error behavior. These are two coordinated parts of the same module document. Do not put server permissions, API calls, transaction order, concurrency or lifecycle algorithms into the design prompt.

Every visible interactive control must have an unambiguous functional mapping, including navigation, filters, disclosures, retry, Cancel, Save and decisions. The map must distinguish navigation from mutation and identify the exact record/revision being opened. A designer must never invent an action's destination, and an implementer must never infer its behavior from a button's appearance. Existing shared behavior may be cited; domain-specific effects must be explicit.

A closed-input design prompt remains §2 of this standard plus the module's single static design section. Interaction maps, implementation contracts and acceptance tests are excluded from that prompt. A design-only consumer does not need the entire requirements document to find the exact visible content.

### 2.8 Design-contract review gate

Before sending a contract to the design system, confirm:

- Every screen names one primary archetype, one dominant actor task and one primary question or read-only purpose.
- Level 1, Level 2 and Level 3 information are explicit; the first view is not a flat inventory of equally weighted facts.
- Every screen has an explicit top-to-bottom composition and action placement.
- Each named fixture resolves its actor, record/revision and pictured state.
- Every material fact is unambiguous; labels, grouping and narrative follow §2.2 instead of forcing each fact into a separate box.
- Every table has a comparison or register purpose, complete stated columns and rows, and does not serve as the default component for a small action queue.
- Every action has one definite visible treatment in that variant and a functional mapping outside the design input.
- Critical consequences and required review facts are visible without compulsory navigation or disclosures.
- Filters are local to the records they filter and do not visually dominate unrelated work.
- Current truth, proposed work, downstream position and history are distinguishable.
- Alternate states are separate, named variants; no optional-layout decision is delegated to the designer.
- Fixture evidence does not reuse one exact event for conflicting outcomes on the same source revision.
- The contract uses the current approved domain and usability decisions; an older layout example does not restore retired fields, roles or workflows.
- The composition avoids repeated context, unnecessary containers, decorative counts, repeated accent rules and equal visual weight across primary and secondary regions.

Before approval, perform a first-view comprehension check with the rendered artboard. Without reading the specification, a representative actor must be able to identify:

1. the purpose of the screen;
2. the current state or work requiring attention;
3. the primary next action;
4. the information that materially supports that action; and
5. what is current, proposed or historical.

For a decision screen, the actor must also identify what is being decided and the consequence of the positive decision. For a workspace, the actor must distinguish actionable work from the general register. For a form, the actor must see the current section, validation problem and completion action without reconstructing the storage model.

Failure requires correcting the contract before design generation. A complete field inventory, dense requirements table or approved document status is not proof of a usable or sufficiently specified composition. Actual artboard comparison and representative-user validation remain separate evidence.

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
- At narrower supported widths, preserve information meaning rather than merely shrinking the desktop composition. Tables may scroll horizontally or become labelled rows; they never drop a material comparison, result or action. Decision actions remain reachable without covering content.
- Reading order in the DOM follows the visual information priority in §2.6.2. Keyboard and screen-reader users encounter the current result, working information and supporting evidence in the same logical order.

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

For a surface reached by technical access rather than a business responsibility, the second line reads: **This area needs Administrator or System Manager access.** A technical reader (Administrator or System Manager) never sees a Forbidden panel on any KenTender surface; see §3A.6.

The panel shall not name a line manager, a supervisor or a department head. Responsibilities are granted by an Administrator or System Manager in System setup, and no other route exists.

### 3A.5 Identity chrome

Where a page displays the signed-in user's role, it displays **every** active responsibility with its scope, or none at all. A single role label is wrong for any user holding more than one assignment, which the authorisation model expressly permits.

### 3A.6 Technical read

1. Administrator and System Manager are never Forbidden on a KenTender surface and never masked as Not found. The page-state verdict for them is always permitted.
2. Every register shows them every record site-wide, across every Organisation Unit and Fiscal Year, through the module's existing filters. Every detail, task and editor route resolves for them regardless of the record's status, read-only, with every command control absent. Action queues and My Work are empty for them: they read everything and decide nothing.
3. The sitewide **Technical record search** (`/app/technical-search`, owned by kentender_core, specified in AUTH-ADR-001 §8 and AUTH-DES-09) resolves any KenTender reference or title to the record's own route. A module does not build a bespoke filter or search for technical readers.
4. Module documents cite this section and do not restate it. Where a module clause masks, forbids or scopes a technical reader, this section prevails until that document's next version removes the clause.
5. Seeds, fixtures and test profiles never grant Administrator or System Manager a business role.

Every module registers its record types with the Technical record search and its read entry points with the technical-read conformance gate (AUTH-ADR-001 §9); a module that does not register fails release evidence.

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
- visual comparison for all approved artboards at 1440 × 1024 and responsive verification at the module's supported narrow desktop width;
- first-view comprehension evidence for each changed archetype: the representative actor identifies the screen purpose, current work/result, primary action and current/proposed/historical distinction without reading the specification;
- representative-user completion of each materially changed decision or preparation task, including one dense-content and one blocked/error variant; and
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
| 10 | Static design contract | Closed visual input. Cites KT-STD-001 §2; names the archetype, actor task, information priority, exact content/actions and state variants; adds only what is module-specific. |
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
| Dr Peter Kimani | `peter.kimani@moh.example.test` | Head of User Department, succeeding Samuel from 1 Sep 2026 | `OU-MOH-DHP` |
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

Peter succeeds Samuel at the Directorate, open-ended, because Samuel's term is deliberately expired and Julia's acting term at `OU-MOH-DHI` runs only 1 Oct – 30 Nov 2026: without a successor the whole Digital Health branch had no head on any date outside that window, including the date a site is typically reseeded, so its Needs had no reviewer and its departmental plan could not be certified. A grant reaches its unit's descendants, so this one covers `OU-MOH-DHI` as well without adding an earlier `OU-MOH-DHI`-scoped row (SEED-001 records why none was added there). Julia's appointment stays Scheduled and Samuel's Expired, which the AUTH-DES-03 register still requires.

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
| Requisition and Tender Preparation journeys | 1 Mar 2027 through 15 May 2027, EAT — Requisition authorisation (15 Mar 2027) precedes Tender preparation, which precedes the baseline invitation date (SEED-001 §7) |
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

KT-STD-001 v1.7 is approved as the Stage 1 correction to KenTender's presentation architecture. It supersedes v1.6 and authorises Stage 2 rewrites of module static-design sections against §2.6; it does not approve any generated artboard or deployed interface by itself.

Approval makes the following corrections binding:

- simplicity means reduced interpretation effort, not reduced governed information;
- each screen uses a named task-led archetype and explicit information priority;
- related facts may be grouped when meaning remains clear, replacing the v1.6 assumption that each distinct fact needs a separate visual row, field or column;
- tables are used for comparison and registers, not as the default treatment for every queue or summary;
- workspaces, reviews, forms, details and setup surfaces have distinct compositions;
- action hierarchy, plain-language process position and current/proposed/history separation are mandatory; and
- rendered comprehension and representative-user task evidence are required in addition to content-completeness checks.

The complete technical-read requirement in §3A.6, closed-input/no-invention rules, functional separation, page-state behaviour, implementation controls, fixtures, test discipline and domain precedence remain unchanged except where this revision explicitly strengthens presentation or verification.

Stage 2 shall revise the static-design sections of Departmental Needs, Procurement Planning and Procurement Requisitions first. It shall preserve their approved fields, ownership, lifecycle, commands, permissions, integrations, audit and acceptance rules. Existing module artboards and implementations do not become conformant merely because this standard is approved; each owning module requires its own explicit presentation rewrite and verification.

A module's domain decisions remain its own authority. Any deliberate shared-standard departure must be explicitly named with its reason. This approval does not claim that module contracts have already been rewritten, artboards rendered, representative-user validation completed or software deployed.

Version history: v1.6, approved 15 September 2026, added explicit composition, deterministic variants and the design-contract review gate. v1.5, approved 14 September 2026, introduced §3A.6 technical read. v1.4 introduced §2.2's separate-labelled-fact rule; v1.7 corrects its over-literal visual effect while retaining content fidelity. v1.3 added Brian Wafula and corrected Head of Procurement Function. v1.2 introduced §3A. v1.1 added universal prohibitions, error conventions and shared actors/instants. Those provisions are retained.
