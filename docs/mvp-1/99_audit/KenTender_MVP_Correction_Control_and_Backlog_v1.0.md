# KenTender MVP Correction Control and Backlog

**Document ID:** KENTENDER-MVP-CCB-1.0  
**Version:** 1.0  
**Date:** 11 August 2026  
**Status:** Draft for product-owner validation — no implementation authority until accepted  
**Controlling authority:** KenTender MVP Cross-Module Operating Model v1.0, approved 11 August 2026  
**Evidence:** Cursor Read-Only Implementation Disposition Audit outputs 00–09, dated 11 August 2026

## 1. Decision

The existing platform shall be corrected, not rebuilt.

The audit establishes that the core data and service foundations are substantially sound. The unsafe layer is concentrated in:

- silent or inflated PE/OU authority;
- unauthorised workflow-form exposure;
- generic value/statutory treatment constructs;
- the Planning departmental-contribution workflow;
- inconsistent placement of Finance confirmation;
- provisional documents treated as completed implementation authority; and
- tests and seeds that institutionalise those incorrect semantics.

No new feature work should proceed in Strategy, Budget & Funding, Demands or Procurement Planning until the applicable correction wave has passed its acceptance gate.

## 2. Audit acceptance assessment

The Cursor audit is accepted as a reliable implementation inventory, subject to the product decisions in section 3.

Its evidence is sufficiently specific because it identifies actual DocTypes, services, routes, fixtures, seeds and tests rather than inferring behaviour from documents alone.

The following foundations are retained:

- Procuring Entity, Organisation Unit and User Scope Assignment;
- strict Demand and Planning creation-scope resolution;
- generated references;
- versioned Strategy, Budget, Demand and Plan records;
- Demand and Need Item;
- Budget, Budget Line, Reservation and Commitment foundations;
- Plan, Plan Version, Plan Item, Plan Item Version and Demand Allocation;
- one Demand to one Plan Item by default;
- explicit aggregation only when another source is deliberately combined;
- quietly created/reused Draft successor for an Approved Plan;
- plan validation and professional review/approval foundations;
- canonical seed arithmetic; and
- existing behavioural tests that assert retained business rules.

## 3. Resolution of open decisions

### OD-01 — Operating-model authority

**Decision:** Closed. The Cross-Module Operating Model v1.0 was approved by the product owner on 11 August 2026 and is controlling.

The Semantic and Workflow Assurance Audit v1.1 remains a correction analysis, not an independently approved requirements baseline.

### OD-02 — Finance sign-off location

**Decision:** Finance confirmation occurs after the Procurement Planner has completed the proposed Plan Item and before Head-of-Procurement review/approval.

There shall be one Finance sign-off, not one in Demands plus another in Planning.

Required model:

1. Demand may carry a proposed or inherited funding reference for planning context.
2. HoD approval makes the Demand Planning Ready without completing Finance approval.
3. The planner completes the Plan Item and its source allocations.
4. Finance confirms the Budget Line, amount and availability against the planned requirement.
5. The reservation is created or confirmed atomically with that Finance decision.
6. A material funding change invalidates the Finance decision and requires reconfirmation.
7. Head-of-Procurement review cannot proceed without current Finance confirmation.

Implementation should reuse sound Budget and allocation structures where possible. It must not add a second Budget Officer form while retaining the old one as an approval stage.

The corrected requirements shall decide whether the audit evidence is stored as a Planning `Plan Decision` over the applicable allocation set or by a comparably explicit existing record. Cursor shall not choose the persistence form before requirements are reissued.

### OD-03 — Statutory coverage on PLN-UI-08

**Decision:** Keep only the concrete, read-only **Preference and reservation coverage** projection.

It may show whether applicable named preference/reservation requirements have been assigned across Plan Items. It shall:

- be derived from actual Plan Item decisions;
- have no generic statutory-treatment dropdown;
- have no free-text statutory rationale by default;
- have no planned-treatment value field; and
- be renamed from generic `statutory_coverage` in user-facing copy.

### OD-04 — Unauthorised task routes

**Decision:** A task route is inaccessible to a user who lacks the current task capability. The server must reject the task loader/API call.

An authorised record viewer may use a separate neutral read-only detail route. A restricted approval or review form shall not be reused as that neutral view with disabled controls.

### OD-05 — Reservation-to-commitment conversion

**Decision:** Keep the Commitment schema and lineage contract, but defer the live conversion action until the Tender/Contract lifecycle requires it.

There shall be no manual placeholder conversion UI in the Strategy-to-Planning correction. The gap becomes a mandatory gate before Contract commitment implementation, not a blocker for the present recovery.

### OD-06 — Returned Demand story

**Decision:** The canonical story is:

- original submitted/returned value: KES 95,000,000;
- corrected and resubmitted value: KES 80,000,000; and
- retained audit evidence must make both values and the transition intelligible.

The next seed validator shall test the current KES 80,000,000 value and the historical KES 95,000,000 return evidence. It shall not assert KES 95,000,000 as the current confirmed estimate.

### OD-07 — Annual departmental-plan certification

**Decision:** Deferred. Do not implement it in MVP 1 and do not reuse PLN-UI-07 for it.

It may return only through the concept-admission gate with a precise legal evidence requirement and a single annual batch-certification journey.

### OD-08 — PVO rules engine and advanced Strategy Performance

**Decision:** Deferred from MVP 1.

Existing code and data should not be destructively removed in the first correction pass. Remove the surfaces from ordinary MVP navigation and prevent new dependencies. Later retention or deletion requires a separate disposition after the core Strategy journey is stable.

Strategy Value Commitments remain in scope and are not the same as the deferred generic PVO applicability engine.

### OD-09 — Dual Strategy seeds

**Decision:** `kentender_mvp_v1_strategy` is the authoritative canonical demonstration seed.

The works-master Strategy hierarchy becomes an explicit opt-in regression fixture. It shall not run as part of the canonical demonstration orchestrator and shall not silently modify the canonical story.

### OD-10 — Version-control and rollback baseline

**Decision:** Hard prerequisite. No application correction starts until a recoverable baseline exists.

Because the repository has no commits and a large untracked worktree, Cursor must not run `git add .` blindly. The baseline procedure must:

1. identify the intended repository root and application boundary;
2. review ignore rules and exclude sites, logs, backups, generated assets, caches, virtual environments and secrets;
3. list the exact files proposed for tracking;
4. scan the proposed set for credentials and environment secrets;
5. create a verified database backup and a separate application-file snapshot;
6. create a named baseline branch and initial commit only after the proposed set is reviewed; and
7. record the commit identifier and restore procedure.

The user must approve the proposed tracked-file set before the initial commit.

## 4. Correction sequence

### Wave 0 — Recovery baseline and document control

**Purpose:** Make every later change recoverable and establish document authority.

Tasks:

- complete OD-10 baseline procedure;
- record the approved Operating Model in the repository;
- mark superseded/provisional module documents accurately;
- freeze obsolete Planning contribution and generic-treatment gates as non-authoritative; and
- capture current unit, integration and Playwright results without changing expected outcomes.

**Acceptance gate:** Verified backup, reviewed tracked-file manifest, baseline commit identifier, current-test report and restore instructions.

### Wave 1 — Shared PE/OU scope and task-surface authorisation

**Keep:** PE/OU/USA records, `org_scope_access`, strict Demand and Planning creation-scope logic.

**Correct:**

- Budget `PE-MOH` Administrator fallback;
- Budget sorted-first-PE selection;
- Home preferred-PE fallback;
- Strategy unfiltered listing when no PE is resolved;
- Strategy and Budget Administrator role inflation;
- direct task-route access that renders read-only approval chrome; and
- inconsistent scope use across lists, counts, exports, notifications and APIs.

**Required behaviour:**

- zero scope blocks operational creation/task access;
- one scope is explicit;
- multiple scopes require deliberate selection;
- Administrator receives no operational capability without an explicit assignment;
- neutral record detail is distinct from task forms; and
- the server enforces the same capability used to project the action.

**Acceptance gate:** Role and scope matrix tests across all four modules, including direct URL/API negatives and multi-PE/OU isolation.

### Wave 2 — Strategy correction

**Keep:** Strategic Plan versioning, hierarchy, targets, measurements, audit events and commitment lineage.

**Correct:**

- rename user-facing and domain terminology from Plan Value Commitment to Strategy Value Commitment;
- migrate or compatibly map existing records without losing links;
- hide generated codes from ordinary create/edit UX;
- control Active-plan overlap by plan type, scope and effective period; and
- remove Administrator scope inflation and hard-coded fixture binding from live paths.

**Defer/quarantine:** generic PVO applicability engine, advanced corrective-action workflow and advanced performance dashboard.

**Acceptance gate:** Corrected Strategy requirements approved; migration test preserves commitment links; activation-overlap tests; scoped role tests; canonical Strategy seed only.

### Wave 3 — Budget & Funding correction

**Keep:** Budget registration, Budget Lines, activation, availability arithmetic, reservations, commitments and revisions.

**Remove:** Budget Line Value Treatment questionnaire and related activation/validation dependencies.

**Correct:**

- Strategy links only where supported by the approved budget structure;
- PE resolution and Administrator authority;
- live UI defaults that silently select the MoH budget; and
- Finance service contract so it supports the approved post-Plan-Item confirmation journey.

**Defer:** expenditure operations and live commitment conversion.

**Acceptance gate:** Corrected Budget requirements approved; no generic treatment fields in active UI or required service validation; arithmetic and reservation tests remain green; explicit-scope tests pass.

### Wave 4 — Demands correction

**Keep:** Requester capture, Demand/Need Items, explicit PE/OU ownership, HoD approval, Strategy references and audit decisions.

**Remove:** Demand Value Treatment and Demand-owned package/aggregation decisions.

**Correct:**

- Requester fields to facts the Requester can reasonably know;
- HoD approval as the single normal business approval;
- Demand funding information as proposed context rather than completed Finance approval;
- current Budget Confirmation state/service so it is relocated, not duplicated; and
- Approved Demand detail screens and task-route authority.

**Acceptance gate:** Corrected Demands requirements approved; HoD once in normal path; Demand becomes Planning Ready without a second business approval; no Requester Strategy/Budget/method burden; removed treatment/package controls absent.

### Wave 5 — Procurement Planning correction

**Keep:** Plan/Version/Item model, Demand Allocation, validation, one-Demand default, explicit aggregation, Draft successor, professional review and approval.

**Remove:**

- Departmental Submission DocType and rows;
- `submit_departmental_contribution` and contribution DTO services;
- PLN-UI-07 contribution drawer;
- Planning Contributor capability used for contribution;
- contribution prerequisite in `submit_plan_for_review`;
- contribution seed and test helpers; and
- retired generic statutory/treatment schema after data review.

**Correct:**

- Finance confirmation after Plan Item completion;
- review readiness based on validation plus current Finance confirmation;
- PLN-UI-08 as professional review/approval only;
- concrete Preference and reservation coverage projection;
- targeted HoD reapproval only for materially changed HoD-owned facts;
- seed helpers and test gates; and
- Tender handoff readiness contract without implementing deferred Contract conversion.

PLN-UI-07 shall be retired from the normal journey. Screen numbers may be left unused; do not invent a replacement merely to preserve numbering.

**Acceptance gate:** Corrected Planning requirements and Stitch screens approved; normal and Approved-plan-revision journeys pass without contribution; targeted material-change tests pass; Approved Version remains operational; no default aggregation control.

### Wave 6 — Canonical seed reconciliation

**Keep:** stable identities, amounts, dates, PE/OU isolation and idempotent orchestrator.

**Correct:**

- remove treatment and contribution records;
- apply Strategy Value Commitment terminology;
- represent Finance after Planning;
- validate 95m returned → 80m corrected history;
- keep V1 operational while V2 at KES 535m is Draft; and
- make works-master seeds opt-in.

**Acceptance gate:** Two consecutive clean seed runs produce the same state and arithmetic; MoH and Kisumu remain isolated; no prohibited records are created.

### Wave 7 — Cross-module regression and release gate

Required automated journeys:

1. Requester → HoD → Planner → Finance → Head of Procurement → Tender-ready handoff.
2. Add Approved Demand to Approved Plan through one Draft successor.
3. Explicit multi-Demand aggregation and actual separate-item outcome.
4. Targeted reapproval of a materially changed HoD-owned fact.
5. Neutral record view versus denied unauthorised task form.
6. Zero, one and multiple PE/OU scopes.
7. Reservation continuity and invalidation/reconfirmation after material funding change.
8. Seed repeatability and cross-entity isolation.

**Acceptance gate:** All retained tests and new negative tests pass; tests for removed workflows are deleted or replaced rather than weakened.

## 5. Documentation reissue order

For each module, use this sequence:

1. correction/change matrix based on the Cursor disposition evidence;
2. newly versioned requirements document;
3. product-owner approval;
4. newly versioned Stitch prompts using the screen-contract standard;
5. product-owner review of the generated screens;
6. newly versioned Cursor implementation pack;
7. implementation wave; and
8. acceptance evidence.

The module order is Strategy → Budget & Funding → Demands → Procurement Planning. Shared scope/authorisation corrections are specified first because all modules depend on them.

No older document is silently overwritten. Every replacement names the superseded version.

## 6. Migration policy

Every destructive schema change requires an explicit per-DocType decision:

- **rebuild** when records are disposable MVP fixture data;
- **migrate** when records contain user-entered or approval evidence that must survive; or
- **quarantine** when a deferred feature may be retained temporarily without remaining active.

Before dropping a field or DocType, Cursor must report row counts, non-empty fields, downstream links, exports and audit dependencies. A successful seed rebuild is not evidence that non-seed data is safe to delete.

## 7. Immediate next action

Do not implement Wave 1 yet.

The next action is:

1. product-owner validation of this correction backlog, especially the OD-02 Finance relocation decision;
2. execution of Wave 0 safety baseline; and
3. reissue of the Strategy requirements against the approved Operating Model and accepted backlog.

Cursor shall receive a separate, bounded Wave 0 prompt. It shall not be asked to implement multiple correction waves from this document in one pass.
