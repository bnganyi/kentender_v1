# Copyright (c) 2026, KenTender and contributors
"""Idempotent MOH-SP-2026-2030 Strategy seed (STRATEGY-MVP1-REQ-1.0 §19).

Also keeps legacy constant aliases for works-master / stable-platform importers.
"""

from __future__ import annotations

from typing import Any, Final

import frappe

from kentender_strategy.services.strategy_permissions import ensure_strategy_roles

# --- Canonical MVP-1 codes (KENTENDER_MVP_V1 contract) ---
STRATEGY_PLAN_CODE: Final[str] = "MOH-SP-2026-2030"
PLAN_TITLE: Final[str] = "Ministry of Health Strategic Plan 2026–2030"
START_YEAR: Final[int] = 2026
END_YEAR: Final[int] = 2030
PROGRAM_CODE: Final[str] = "MOH-PROG-DH"
PROGRAM_TITLE: Final[str] = "Digital Health Services"
PROGRAM_DESCRIPTION: Final[str] = (
	"Digital clinical services and health information systems that improve access and continuity of care."
)
SUB_PROGRAM_CODE: Final[str] = "MOH-SUB-HIS"
SUB_PROGRAM_TITLE: Final[str] = "Health Information Systems"
OBJECTIVE_CODE: Final[str] = "MOH-OUT-RELIABILITY"
OBJECTIVE_TITLE: Final[str] = "Reliable and accessible digital clinical services"
OBJECTIVE_DESCRIPTION: Final[str] = OBJECTIVE_TITLE
INDICATOR_CODE: Final[str] = "MOH-IND-AVAIL-01"
INDICATOR_TITLE: Final[str] = "Availability of core clinical information systems"
TARGET_CODE: Final[str] = "MOH-TGT-AVAIL-2028"
TARGET_TITLE: Final[str] = "At least 99.9% annual availability by 30 June 2028"
TARGET_METRIC_TEXT: Final[str] = "Percent availability"

# Legacy import aliases (pre-teardown codes) — map to MVP-1 where possible
LEGACY_STRATEGY_PLAN_CODE: Final[str] = "STRAT-MOH-2026"

# Dev/fixture Programme Strategy that may coexist with the Active ESP (STR-FR-005).
HR_PROGRAMME_PLAN_CODE: Final[str] = "MOH-SP-0002"
HR_PROGRAMME_SCOPE_ID: Final[str] = "MOH-PROG-HR"

# Remap retired 000x codes → contract identities (KENTENDER_MVP_V1).
_LEGACY_PERIOD_CODE_REMAP: Final[tuple[tuple[str, str, str, str], ...]] = (
	("Strategic Plan", "plan_code", "MOH-SP-0001", STRATEGY_PLAN_CODE),
	("Strategic Plan", "plan_code", "MOH-HR-2026-2030", HR_PROGRAMME_PLAN_CODE),
	("Strategic Plan", "plan_code", "MOH-SP-HR-2026", HR_PROGRAMME_PLAN_CODE),
	("Strategic Plan", "plan_code", "MOH-SP-REVIEW-BLOCK", "MOH-SP-9001"),
	("Strategic Plan", "plan_code", "MOH-SP-REVIEW-TX", "MOH-SP-9002"),
	("Strategy Programme", "programme_code", "MOH-PROG-0001", PROGRAM_CODE),
	("Strategy Sub Programme", "sub_programme_code", "MOH-SUB-0001", SUB_PROGRAM_CODE),
	("Strategic Outcome", "outcome_code", "MOH-OUT-0001", OBJECTIVE_CODE),
	("Performance Indicator", "indicator_code", "MOH-IND-0001", INDICATOR_CODE),
	("Performance Target", "target_code", "MOH-TGT-0001", TARGET_CODE),
)


def _remap_legacy_period_codes() -> None:
	"""Rewrite retired 000x business codes to KENTENDER_MVP_V1 contract references."""
	for doctype, field, old_code, new_code in _LEGACY_PERIOD_CODE_REMAP:
		if old_code == new_code:
			continue
		names = frappe.get_all(doctype, filters={field: old_code}, pluck="name")
		for name in names:
			frappe.db.set_value(doctype, name, field, new_code, update_modified=False)


def _backfill_active_subordinate_parents(pe: str, esp_plan: str) -> None:
	"""Ensure Active non-ESP plans for the entity have parent_plan + distinct scope."""
	rows = frappe.get_all(
		"Strategic Plan",
		filters={
			"procuring_entity": pe,
			"status": "Active",
			"plan_type": ["!=", "Entity Strategic Plan"],
		},
		fields=["name", "plan_code", "parent_plan", "scope_type", "scope_id"],
	)
	for row in rows:
		scope_id = row.scope_id
		if not scope_id:
			if row.plan_code == HR_PROGRAMME_PLAN_CODE:
				scope_id = HR_PROGRAMME_SCOPE_ID
			else:
				scope_id = f"SCOPE-{row.plan_code}"
		frappe.db.set_value(
			"Strategic Plan",
			row.name,
			{
				"parent_plan": esp_plan,
				"scope_type": row.scope_type or "Programme",
				"scope_id": scope_id,
			},
			update_modified=False,
		)


def desk_visibility(procuring_entity_name: str) -> dict[str, str]:
	return {
		"procuring_entity": procuring_entity_name,
		"scope_rule": "Entity-scoped Strategy Alignment (MVP-1).",
		"optional_seed_flag": "MOH-SP-2026-2030",
	}


def resolve_procuring_entity_moh() -> str | None:
	for code in ("PE-MOH", "MOH"):
		name = frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name")
		if name:
			return name
	# Fallback: any PE containing Health
	name = frappe.db.get_value("Procuring Entity", {"entity_name": ["like", "%Health%"]}, "name")
	if name:
		return name
	rows = frappe.get_all("Procuring Entity", pluck="name", limit=1)
	return rows[0] if rows else None


def _upsert_by_code(doctype: str, code_field: str, code: str, values: dict) -> str:
	existing = frappe.db.get_value(doctype, {code_field: code}, "name")
	if existing:
		doc = frappe.get_doc(doctype, existing)
		# Only update while Draft/Returned for plan-bound docs
		plan = values.get("plan_version") or doc.get("plan_version")
		if plan:
			status = frappe.db.get_value("Strategic Plan", plan, "status")
			if status not in ("Draft", "Returned", None):
				return existing
		doc.update(values)
		doc.save(ignore_permissions=True)
		return doc.name
	doc = frappe.get_doc({"doctype": doctype, code_field: code, **values})
	doc.insert(ignore_permissions=True)
	return doc.name


def upsert_works_master_strategy_hierarchy(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	"""Idempotent loader — delegates to KENTENDER_MVP_V1 contract Strategy seed."""
	ensure_strategy_roles()
	_remap_legacy_period_codes()
	from kentender_strategy.seeds.moh_mvp_v1_strategy import upsert_moh_mvp_v1_strategy

	result = upsert_moh_mvp_v1_strategy(reset=bool(_kwargs.get("reset")))
	# Preserve legacy response keys used by stable-platform / tests.
	if result.get("ok"):
		result.setdefault("plan_code", STRATEGY_PLAN_CODE)
		result.setdefault("program", frappe.db.get_value("Strategy Programme", {"programme_code": PROGRAM_CODE}, "name"))
		result.setdefault(
			"sub_program",
			frappe.db.get_value("Strategy Sub Programme", {"sub_programme_code": SUB_PROGRAM_CODE}, "name"),
		)
		result.setdefault(
			"objective",
			frappe.db.get_value("Strategic Outcome", {"outcome_code": OBJECTIVE_CODE}, "name"),
		)
		result.setdefault("target", result.get("target_avail"))
		result.setdefault("skipped", False)
	return result


