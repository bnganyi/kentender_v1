# Procurement Officer Tender Configuration POC — issues, decisions, blockers

**Governance:** Follow the **Rules of engagement** in [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md): scope doc 1 for boundaries, specs 2–7 for UX/field contracts, doc 8 for implementation sequence and `OFFICER-IMPL-AC-*`, doc 9 for smoke (`OFF-ST-*`), TDD + Playwright for Desk-visible flows, and **exit conditions** before marking a tracker row **Done**. Log **deviations** here before shipping partial compliance.

**Cross-posting:** For programme-wide visibility, you may **also** append a one-line pointer row to the shared [`../ISSUES_LOG.md`](../ISSUES_LOG.md) when an officer decision affects STD-WORKS-POC or Admin Console contracts — keep detailed narrative here.

Append new entries at the bottom. Reference **Tracker step** as `Officer 1` … `Officer 9` or `Impl seq N` (implementation sequence row from the officer tracker).

**Id prefix:** **`STD-OFFICER-NNN`** (this workstream only).

| Id | Date | Tracker step | Type | Summary | Resolution / link |
|----|------|--------------|------|---------|-------------------|
| STD-OFFICER-001 | 2026-05-01 | — | meta | Officer POC folder trackers and issues log created (`IMPLEMENTATION_TRACKER.md`, `ISSUES_LOG.md`, `README.md`). | This file + [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) |
| STD-OFFICER-002 | 2026-05-01 | Officer 1 / Impl seq 1 | decision | Officer POC code lives at `kentender_procurement/.../tender_management/services/officer_tender_config.py` (not `{app}/procurement/officer_tender_config.py`). Prevents path drift vs doc 8 literal. | [`officer_tender_config.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/officer_tender_config.py); Officer step **1** tracker row. |
| STD-OFFICER-003 | 2026-05-01 | Officer 9 | decision | Frappe Desk routes tender forms as `/desk/procurement-tender/{name}` (not `/app/procurement-tender/...`). Playwright assertions must allow `/desk/` prefix. | [`officer-tender-poc-mvp.spec.ts`](../../../../tests/ui/smoke/procurement/officer-tender-poc-mvp.spec.ts) |
| STD-OFFICER-004 | 2026-05-01 | Officer 3 / 8 / Impl seq 3–5 | debt → resolved | Prior officer POC shipped validation/output without full guided DocType surface and subset-only sync (independent audit). **Remediation:** `officer_guided_field_registry` (`og_*` columns, Frappe ≤64 chars), full `merge_officer_overlay_into_configuration`, `apply_config_to_tender_doc` hydration, doc **8** §11-ish `field_order`, `get_officer_conditional_state_for_tender` merged overlay + `hidden_fieldnames` for Desk, validation row enrichment, tests `test_officer_guided_field_registry`, Playwright OFF-ST-003 labels. Cursor rule: [`.cursor/rules/kentender-officer-guided-surface-gate.mdc`](../../../../.cursor/rules/kentender-officer-guided-surface-gate.mdc) (in `kentender_v1`). | [`officer_guided_field_registry.py`](../../../../kentender_procurement/kentender_procurement/tender_management/services/officer_guided_field_registry.py) · [`IMPLEMENTATION_TRACKER.md`](IMPLEMENTATION_TRACKER.md) Officer steps **3**, **8**, **9** |

**Types:** `blocker` | `question` | `decision` | `debt` | `deviation` | `meta`

- **`deviation`:** intentional departure from a spec (e.g. doc 8 §6 path `{app}/procurement/...` vs `tender_management/services/` slice); record approval context and tracker step.

### Entry template (copy row)

```markdown
| STD-OFFICER-00N | YYYY-MM-DD | Officer 8 | deviation | Short title | See resolution |
```
