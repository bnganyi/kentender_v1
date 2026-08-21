# Strategy Alignment — Disposition Matrix

**Document ID:** KENTENDER-ROIDA-02-1.0  
**Date:** 11 August 2026  
**Mode:** Read-only  
**App:** `kentender_strategy` → `apps/kentender_v1/kentender_strategy`  
**Controls:** CMOM §6.1, §9; SWA §7.1–7.4, §8.1

Matrix columns per audit prompt §8.3.

| Artifact | Exact location | Current purpose/effect | Evidence | Disposition | Required correction | Dependencies | Migration/seed impact | Tests affected |
|---|---|---|---|---|---|---|---|---|
| Strategic Plan DocType | `kentender_strategy/.../doctype/strategic_plan/` | Versioned plan; PE ownership; status Draft→Active | JSON + `transition_plan` | **Keep** | — | PVC, hierarchy | Seeds plant `MOH-SP-2026-2030` | `test_strategy_mvp1_domain`, activation concurrency |
| Hierarchy DocTypes (Programme…Target) | `doctype/strategy_*`, `strategic_outcome`, `performance_*` | Structure under plan version | JSON + structure APIs | **Keep** | Ensure codes not user-typed in UI | Plan | Seed hierarchy | structure / create-plan tests |
| Plan Value Commitment DocType | `doctype/plan_value_commitment/` | Strategy→procurement linkage | Name + `list_plan_value_commitments` | **Correct** | Rename/label **Strategy Value Commitment** consistently | Budget treatments, Demand refs | Rename migration / dual-read | `test_strategy_plan_value_commitments`, DEM-INT-008 |
| PVC Link child | `doctype/plan_value_commitment_link/` | Links outcomes/targets | JSON | **Keep** (with rename) | Follow PVC rename | PVC | Cascade rename | PVC tests |
| Public Value Objective + applicability triggers | `doctype/public_value_objective/`, `objective_applicability_trigger/` | Rules-engine catalogue | Pages `strategy-pvo-*` | **Defer** | Reassess admission before MVP1 | — | Leave data; stop new UI | PVO transition tests → quarantine if deferred |
| Strategy Corrective Action | `doctype/strategy_corrective_action/` | Advanced CA workflow | Transitions in `strategy_transitions.py` | **Defer** (advanced) | Keep minimal or gate | Measurements | Seed optional | CA tests |
| Strategy Audit Event | `doctype/strategy_audit_event/` | Append-only audit | JSON | **Keep** | — | Transitions | — | audit consumers |
| Reference allocator | `services/strategy_reference.py` | `{PE}-{TYPE}-####` | Create ignores client code | **Keep** | Hide codes in create UX | All strategy docs | — | `test_strategy_reference` |
| `strategy_api` transitions | `api/strategy_api.py`, `strategy_transitions.py` | Submit/Return/Approve/Activate | Role: Planning Authority approve | **Keep** | — | Permissions | — | AC matrix / readiness |
| Active-plan supersede | activation path + guards | Supersede peers by plan_code+PE | `validate_plan_activation` | **Correct** | Overlap by type/scope/period (SWA §7.2) | Plan status | Business rule change | activation concurrency |
| Portfolio / plan pages | `page/strategy_*`, hooks `page_js` | Desk surfaces | `hooks.py` | **Keep** core; **Defer** performance dashboard if no consumer | Drop or gate `strategy-performance` if deferred | Chrome registry | — | nav / layout guard |
| `entity_for_user` / Admin inflation | `services/strategy_permissions.py` | Admin gets all roles; list PE soft | Code | **Correct** | Align Admin with USA; never invent PE | Shared scope | Seed Admin USA if needed | role matrix |
| Fixture plan hardcode | `public/js/strategy_alignment_shell.js` `FIXTURE_PLAN` | Demo chrome may pin MOH plan | JS | **Investigate** | Ensure live bind does not mask empty scope | UI | — | Playwright nav |
| Seed upsert | `seeds/kentender_mvp_v1_strategy.py` | Canonical Strategy story | Orchestrator | **Keep** arithmetic; **Correct** Admin-as-verifier | Use role users | Budget/Demand | Seed rebuild | validate.py Strategy checks |
| Works-master hierarchy seed | `seeds/works_master_strategy_hierarchy.py` | Parallel hierarchy | Still active | **Investigate** | Avoid dual stories | Planning works | Clear policy | works tests |

### Strategy summary

Preserve versioned plans, targets, measurements and commitment linkage. Highest Correct items: **PVC naming**, **Active-plan overlap rule**, **Admin/scope**. Defer PVO engine and advanced performance/CA unless concept gate passes.
