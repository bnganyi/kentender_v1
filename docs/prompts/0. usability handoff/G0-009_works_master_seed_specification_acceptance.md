# G0-009 — WORKS Master Seed Specification: reviewer acceptance

**Parent gate:** [G0-009](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md) (§5).  
**Atomic ticket:** LV-G0-009-01  
**Depends on:** LV-G0-008-01 (**Accepted**) — [G0-008 master codes checklist](./G0-008_works_master_codes_checklist.md) + seed spec **§4**.

---

## 1. Controlling artifact

The [**Procurement Lifecycle WORKS Master Seed Data Specification**](./2.%20procurement_lifecycle_works_master_seed_data_specification.md) (see also tracker front matter in [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md)) is accepted as the **single controlling authority** for:

- deterministic master **seed records** and field values;
- **handoff JSON** and evidence payloads prescribed in that document;
- **checkpoint** semantics and loader/validator contracts (including supported checkpoint names);
- **validation output** shapes and expectations referenced by the spec;
- **negative fixtures** and “do not invent” rules called out there.

Implementation (**R2**, **G9**, etc.) must not silently diverge; changes require an **updated spec** and downstream ticket realignment.

---

## 2. Base checkpoint: `TENDER_PUBLISHED`

- The **base** master seed end state is **Tender Published** with addendum / publication snapshot rules exactly as in seed spec **§3.1** and **§3.2** (Journey View current state for base seed).
- **NG-007A:** The base `TENDER_PUBLISHED` checkpoint **must not** fabricate closing records, opening readiness records, or **CLOSECERT** / **OPENREADY** handoffs unless the spec explicitly allows them for that checkpoint (it does not for base).

---

## 3. Optional checkpoint: `OPENING_READY`

- **SEED-PRIN-005** and seed spec **§3.3** / **§3.4**: optional extended state (tender closed, opening readiness available) is **controlled** and may be loaded only via checkpoint **`OPENING_READY`** when **existing TM2 / fixture data** safely supports it.
- If closing/opening readiness records are **not** available, loaders must **not** invent them (spec **§3.4**); implementation may return **unsupported** until fixtures exist (**R2-001** / **R2-011A** track concrete behaviour).

---

## 4. Master business codes

- Master codes are **frozen** under **G0-008** and seed spec **§4** — see [G0-008_works_master_codes_checklist.md](./G0-008_works_master_codes_checklist.md) (verbatim §4.1–4.3).

---

## 5. Downstream (reference only)

| Area | Tracker examples |
|------|-------------------|
| Loader / validator | **R2-001**, **R2-003**, **R2-011A** |
| Acceptance / smoke | **G9-009**, **G9-002A**, **R8-016** |

---

## 6. Reviewer sign-off

**Accepted:** **G0-009** and **LV-G0-009-01** are **Accepted** on the [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md); G0 exit criterion “WORKS Master Seed Specification accepted as controlling seed authority” is checked.

---

## Acceptance

This note is **primary evidence** for **LV-G0-009-01**. Parent **G0-009** is tracked via [G0-009_works_master_seed_specification_confirmation.md](./G0-009_works_master_seed_specification_confirmation.md). **G0-009**, **LV-G0-009-01**, and the G0 exit item “WORKS Master Seed Specification accepted as controlling seed authority” are **Accepted** on the [implementation tracker](./3.%20procurement_lifecycle_usability_handoff_rectification_implementation_tracker.md).
