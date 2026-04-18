**📘 KenTender — Wave 0 Prompt Pack (Architecture Foundation v2)**

This pack is used to build:

The platform skeleton BEFORE any business module (Strategy, Budget, etc.)

**🔒 GLOBAL INSTRUCTION (PREFIX EVERY PHASE)**

You are implementing the KenTender base architecture.

Rules:

1\. Do not implement business modules (Strategy, Budget, Procurement).

2\. Only implement shared architecture and platform foundations.

3\. Follow strict app boundaries and dependency rules.

4\. Do not introduce extra apps or abstractions.

5\. Keep implementation minimal and explicit.

6\. No UI-heavy work except minimal scaffolding.

You MUST follow these rules:

kentender_architecture_rules.md

If any rule is violated, the implementation is incorrect.

**🧩 PHASE A — App Skeleton Creation**

Implement Wave 0 Phase A: App Skeleton.

Goal:

Create all KenTender apps with clean structure only.

Apps to create:

\- kentender_core

\- kentender_strategy

\- kentender_budget

\- kentender_procurement

\- kentender_governance

\- kentender_compliance

\- kentender_stores

\- kentender_assets

\- kentender_integrations

For EACH app:

\- create standard structure:

doctype/

services/

api/

tests/

utils/

Do:

\- initialize apps

\- ensure apps load without errors

\- ensure apps can be installed on site

Do NOT:

\- create business DocTypes (except core basics later)

\- implement workflows

\- implement APIs beyond placeholders

\- add cross-app dependencies

Deliverable:

All apps exist and load cleanly with consistent structure.

**🧩 PHASE B — Core Foundational DocTypes**

Implement Wave 0 Phase B: Core Foundational DocTypes in kentender_core.

Goal:

Create minimal shared master data.

Create DocTypes:

1\. Procuring Entity

\- name

\- entity_code

\- entity_name

2\. Department

\- name

\- department_name

\- procuring_entity

3\. Business Unit (optional lightweight)

\- name

\- unit_name

\- department

Do:

\- basic CRUD

\- link relationships

Do NOT:

\- implement complex permissions yet

\- implement workflows

\- create extra fields

Deliverable:

Core master data entities exist and can be created/linked.

**🧩 PHASE C — Numbering Service**

Implement Wave 0 Phase C: Numbering / Business ID Service.

Goal:

Centralize document numbering.

Create service in kentender_core/services:

Function:

generate_business_id(prefix, entity, year)

Behavior:

\- returns structured ID like:

PREFIX-ENTITY-YEAR-XXXX

Do:

\- simple counter-based logic

\- store counters per prefix/entity/year

Do NOT:

\- overengineer formatting

\- build UI for this

\- duplicate logic in other apps

Deliverable:

Reusable numbering service callable from other modules.

**🧩 PHASE D — Audit Event Framework**

Implement Wave 0 Phase D: Audit Event Framework.

Goal:

Capture structured audit events.

Create DocType:

Audit Event

Fields:

\- event_type

\- entity

\- document_type

\- document_name

\- action

\- performed_by

\- timestamp

\- metadata (JSON)

Create service:

log_audit_event(...)

Do:

\- ensure service can be called anywhere

\- minimal implementation

Do NOT:

\- create dashboards

\- overcomplicate schema

Deliverable:

Audit events can be recorded via service.

**🧩 PHASE E — Exception Record Framework**

Implement Wave 0 Phase E: Exception Record.

Goal:

Formalize policy bypass / override tracking.

Create DocType:

Exception Record

Fields:

\- reference_doctype

\- reference_name

\- reason

\- approved_by

\- status

\- created_by

Do:

\- basic create/save

\- link to any document

Do NOT:

\- implement approval workflows yet

\- add heavy logic

Deliverable:

Exception records can be created and linked.

**🧩 PHASE F — Typed Attachment Model**

Implement Wave 0 Phase F: Typed Attachments.

Goal:

Standardize document attachments.

Create DocType:

Typed Attachment

Fields:

\- file

\- attachment_type

\- linked_doctype

\- linked_name

\- sensitivity_level

Do:

\- basic upload/linking

\- allow association with any record

Do NOT:

\- build access control logic yet

\- build file viewers

Deliverable:

Structured attachment system exists.

**🧩 PHASE G — Entity Scope & Permission Helpers**

Implement Wave 0 Phase G: Entity Scope Helpers.

Goal:

Prepare for scoped access control.

Create utilities in kentender_core/utils:

Functions:

\- get_user_entity(user)

\- get_user_departments(user)

Create placeholder permission helper:

\- filter_by_entity(query, entity)

Do:

\- minimal logic or stubbed logic

Do NOT:

\- implement full permission system yet

\- enforce in all queries yet

Deliverable:

Basic entity-aware helpers exist.

**🧩 PHASE H — Workflow Guard Framework**

Implement Wave 0 Phase H: Workflow Guard Framework.

Goal:

Standardize validation before critical actions.

Create service:

run_workflow_guard(action, document)

Behavior:

\- placeholder checks

\- return pass/fail with message

Do:

\- simple structure

\- callable from future modules

Do NOT:

\- implement full rules engine

\- hardcode business rules

Deliverable:

Workflow guard hook exists for future use.

**🧩 PHASE I — Controlled Business Action Pattern**

Implement Wave 0 Phase I: Controlled Business Actions.

Goal:

Standardize how critical actions are executed.

Pattern:

\- UI calls API

\- API calls service

\- service performs action + audit + guard

Create example service:

execute_business_action(action, doc)

Do:

\- enforce pattern structure

\- integrate audit + guard calls

Do NOT:

\- build complex action registry

\- overgeneralize

Deliverable:

Reusable pattern for all future modules.

Note:

\- Backend validation lives in `test_business_action.py`. Browser-level Desk/workspace checks are **PHASE La** (Playwright), not Phase L.

**🧩 PHASE La — UI Smoke (Playwright / npm)**

Implement Wave 0 Phase La: optional UI smoke on top of Phase I (pattern) and Phase K (workspaces).

Goal:

Repeatable **UI smoke**: logged-in Desk, KenTender workspaces reachable, stable shell (aligned with existing specs under `apps/kentender_v1/tests/ui/smoke/`).

Prereqs:

\- Frappe site reachable at `UI_BASE_URL` (see `playwright.config.ts`; default `http://127.0.0.1:8000`)

\- Copy/configure `.env.ui` from `.env.ui.example`; users/passwords must match `tests/ui/helpers/auth.ts`

Verify:

\- From `apps/kentender_v1`: `npm run test:ui:smoke` (full UI suite: `npm run test:ui`)

Do:

\- keep smoke fast and deterministic

\- reuse helpers under `tests/ui/helpers/`

Do NOT:

\- replace backend tests

\- duplicate Phase L coverage in the UI layer

\- grow into a full E2E suite in Wave 0

Depends on:

\- **PHASE I** (controlled action pattern exists)

\- **PHASE K** (workspaces to navigate)

\- **PHASE L** (backend smoke green)

Deliverable:

`npm run test:ui:smoke` passes when the site and credentials are configured.

**🧩 PHASE J — Notification Framework (Lightweight)**

Implement Wave 0 Phase J: Notification Framework.

Goal:

Centralize notifications.

Create service:

send_notification(user, message)

Do:

\- minimal implementation

\- placeholder or log-based

Do NOT:

\- build full messaging system

\- integrate external services

Deliverable:

Basic notification service exists.

**🧩 PHASE K — Base Workspace Scaffolding**

Implement Wave 0 Phase K: Workspace Scaffolding.

Goal:

Prepare module entry points.

Create basic workspaces:

\- Strategy Management (empty)

\- Budget Management (empty)

\- Procurement (empty)

Do:

\- make workspaces accessible from menu

\- minimal placeholder content

Do NOT:

\- implement full UI

\- create module logic

Deliverable:

Navigation structure exists for modules.

**🧩 PHASE L — Smoke Test Foundation**

Implement Wave 0 Phase L: Smoke Test Foundation.

Goal:

Ensure architecture is stable.

Tests:

\- apps load without errors

\- core DocTypes can be created

\- services callable:

\- numbering

\- audit

\- exception

\- workflow guard

Do:

\- minimal deterministic tests

Do NOT:

\- write full module tests

\- add UI tests

Deliverable:

Wave 0 smoke tests pass consistently.

**🚨 Hard Stop Rule**

Do NOT proceed to Strategy module until:

\- all apps load cleanly

\- core services work

\- no cross-app violations exist

\- smoke tests pass (Phase L — backend; excludes UI tests by design)

For **full-stack** confidence when a browser and test users are available, also run **Phase La** (`npm run test:ui:smoke`). Phase L remains the non-UI quality gate.

**💥 Why this version is different (and better)**

Compared to your original Wave 0 :

**Before**

- conceptual
- broad
- not enforceable by AI

**Now**

- phase-driven
- prompt-ready
- architecture-enforced
- minimal + controlled

**🚀 What you do next**

Start exactly like this:

Phase A → Phase B → Phase C

Then STOP and verify.

If you want, next I can:

👉 walk you through **Phase A execution in Windsurf (what it will get wrong + how to fix it immediately)**