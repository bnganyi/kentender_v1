# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""
Per-step and overall configuration progress (UI-01).

Each CFG step contributes 0–100% from its exit-condition checklist (same gates that
unlock Continue / Complete). Steps without a field-level checker yet use a single
status-derived condition so overall % stays honest for all nine steps.

Overall = round(average of the nine step percents).
"""

from __future__ import annotations

from typing import Any, Callable

from frappe.utils import cstr

from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_COMPLETE,
	STEP_IN_PROGRESS,
	STEP_NEEDS_ATTENTION,
	STEP_NOT_AVAILABLE,
	STEP_NOT_STARTED,
)

ConditionBuilder = Callable[[Any, dict[str, Any]], list[dict[str, Any]]]


def _condition(key: str, label: str, met: bool) -> dict[str, Any]:
	return {"key": key, "label": label, "met": bool(met)}


def evaluate_conditions(conditions: list[dict[str, Any]]) -> dict[str, Any]:
	"""Return met/required counts and progress_pct (0–100)."""
	total = len(conditions)
	met = sum(1 for c in conditions if c.get("met"))
	pct = int(round((100.0 * met / total))) if total else 0
	pct = max(0, min(100, pct))
	return {
		"required_count": total,
		"met_count": met,
		"progress_pct": pct,
		"conditions": conditions,
	}


def _status_fallback_conditions(status_label: str) -> list[dict[str, Any]]:
	"""
	Until a step registers a field checklist: one condition —
	required local setup complete (met only when status is Complete).
	"""
	return [
		_condition(
			"step_complete",
			"Required local setup complete",
			status_label == STEP_COMPLETE,
		)
	]


def _cfg01_conditions(doc: Any, _step_state: dict[str, Any]) -> list[dict[str, Any]]:
	"""CFG-01 Tender Profile exit conditions (C2-CFG1 §7 / §10)."""
	from kentender_procurement.tender_configurations.services.profile import (
		ALLOWED_LOT_STRUCTURES,
		LOT_MULTIPLE,
		_parse_lots,
	)

	title = cstr(getattr(doc, "tender_title", None) or "").strip()
	scope = cstr(getattr(doc, "short_scope_summary", None) or "").strip()
	lot_structure = cstr(getattr(doc, "lot_structure", None) or "").strip()
	lots = _parse_lots(getattr(doc, "lots", None))
	family = cstr(getattr(doc, "std_family_label", None) or "").strip()
	std_doc = cstr(getattr(doc, "std_document_label", None) or "").strip()

	conditions = [
		_condition("title", "Tender title", bool(title)),
		_condition("scope", "Short scope summary", bool(scope)),
		_condition(
			"lot_structure",
			"Lot structure confirmed",
			bool(lot_structure) and lot_structure in ALLOWED_LOT_STRUCTURES,
		),
	]
	if lot_structure == LOT_MULTIPLE:
		usable = [r for r in lots if r.get("lot_title")]
		conditions.append(_condition("lots", "Lot summary rows", bool(usable)))
	conditions.append(_condition("std_family", "STD family", bool(family)))
	conditions.append(_condition("std_document", "Standard tender document", bool(std_doc)))
	return conditions


def _cfg02_conditions(doc: Any, _step_state: dict[str, Any]) -> list[dict[str, Any]]:
	"""CFG-02 Tender Data Sheet exit conditions (C2-CFG2 §8 / §15)."""
	from kentender_procurement.tender_configurations.services.tds import (
		tds_exit_conditions_for_doc,
	)

	return tds_exit_conditions_for_doc(doc)


def _cfg03_conditions(doc: Any, _step_state: dict[str, Any]) -> list[dict[str, Any]]:
	"""CFG-03 IT Requirements exit conditions (C2-CFG3 §16 / §22)."""
	from kentender_procurement.tender_configurations.services.it_requirements import (
		requirements_exit_conditions_for_doc,
	)

	return requirements_exit_conditions_for_doc(doc)


def _cfg04_conditions(doc: Any, _step_state: dict[str, Any]) -> list[dict[str, Any]]:
	"""CFG-04 Implementation Schedule exit conditions (C2-CFG4)."""
	from kentender_procurement.tender_configurations.services.implementation_schedule import (
		schedule_exit_conditions_for_doc,
	)

	return schedule_exit_conditions_for_doc(doc)


def _cfg05_conditions(doc: Any, _step_state: dict[str, Any]) -> list[dict[str, Any]]:
	"""CFG-05 System Inventory & Bidder Background exit conditions (C2-CFG5)."""
	from kentender_procurement.tender_configurations.services.system_inventory import (
		inventory_exit_conditions_for_doc,
	)

	return inventory_exit_conditions_for_doc(doc)


def _cfg06_conditions(doc: Any, _step_state: dict[str, Any]) -> list[dict[str, Any]]:
	"""CFG-06 Price Schedule exit conditions (C2-CFG6)."""
	from kentender_procurement.tender_configurations.services.price_schedule import (
		price_schedule_exit_conditions_for_doc,
	)

	return price_schedule_exit_conditions_for_doc(doc)


def _cfg07_conditions(doc: Any, _step_state: dict[str, Any]) -> list[dict[str, Any]]:
	"""CFG-07 Evaluation Setup exit conditions (C2-CFG7)."""
	from kentender_procurement.tender_configurations.services.evaluation_setup import (
		evaluation_setup_exit_conditions_for_doc,
	)

	return evaluation_setup_exit_conditions_for_doc(doc)


def _cfg08_conditions(doc: Any, _step_state: dict[str, Any]) -> list[dict[str, Any]]:
	"""CFG-08 Forms & Evidence exit conditions (C2-CFG8)."""
	from kentender_procurement.tender_configurations.services.forms_and_evidence import (
		forms_and_evidence_exit_conditions_for_doc,
	)

	return forms_and_evidence_exit_conditions_for_doc(doc)


def _cfg09_conditions(doc: Any, _step_state: dict[str, Any]) -> list[dict[str, Any]]:
	"""CFG-09 Contract Values exit conditions (C2-CFG9)."""
	from kentender_procurement.tender_configurations.services.contract_values import (
		contract_values_exit_conditions_for_doc,
	)

	return contract_values_exit_conditions_for_doc(doc)


# Register field-level checkers as each CFG screen ships. Unregistered → status fallback.
STEP_CONDITION_BUILDERS: dict[str, ConditionBuilder] = {
	"CFG-01": _cfg01_conditions,
	"CFG-02": _cfg02_conditions,
	"CFG-03": _cfg03_conditions,
	"CFG-04": _cfg04_conditions,
	"CFG-05": _cfg05_conditions,
	"CFG-06": _cfg06_conditions,
	"CFG-07": _cfg07_conditions,
	"CFG-08": _cfg08_conditions,
	"CFG-09": _cfg09_conditions,
}


def register_step_condition_builder(step_id: str, builder: ConditionBuilder) -> None:
	"""Allow CFG modules to register exit-condition builders (tests / future screens)."""
	STEP_CONDITION_BUILDERS[step_id] = builder


def compute_step_progress(
	step_id: str,
	*,
	status_label: str,
	doc: Any | None = None,
	step_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""
	Compute progress for one step.

	- Not available yet → 0%
	- Complete → 100% (authoritative status)
	- Else → met/required from checklist (CFG checker or status fallback)
	"""
	status = status_label or STEP_NOT_STARTED
	step_state = step_state or {}

	if status == STEP_NOT_AVAILABLE:
		return {
			"required_count": 0,
			"met_count": 0,
			"progress_pct": 0,
			"conditions": [],
			"show_progress_bar": False,
		}

	if status == STEP_COMPLETE:
		builder = STEP_CONDITION_BUILDERS.get(step_id)
		if builder and doc is not None:
			out = evaluate_conditions(builder(doc, step_state))
		else:
			out = evaluate_conditions(_status_fallback_conditions(STEP_COMPLETE))
		out["progress_pct"] = 100
		out["show_progress_bar"] = False
		return out

	builder = STEP_CONDITION_BUILDERS.get(step_id)
	if builder and doc is not None:
		out = evaluate_conditions(builder(doc, step_state))
	else:
		out = evaluate_conditions(_status_fallback_conditions(status))

	out["show_progress_bar"] = status in (STEP_IN_PROGRESS, STEP_NEEDS_ATTENTION)
	return out


def overall_progress_pct(step_rows: list[dict[str, Any]]) -> int:
	"""Average of per-step progress_pct values (equal weight per CFG step)."""
	if not step_rows:
		return 0
	total = 0
	for row in step_rows:
		try:
			total += int(row.get("progress_pct") or 0)
		except (TypeError, ValueError):
			pass
	return int(round(total / len(step_rows)))


def complete_step_count(step_rows: list[dict[str, Any]]) -> int:
	return sum(1 for row in step_rows if row.get("status_label") == STEP_COMPLETE)
