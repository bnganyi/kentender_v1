# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Addendum impact analysis and controlled regeneration — ``StdAddendumImpactService``.

STDINST-0800.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.derived_models.events.audit import emit_derived_model_audit
from kentender_procurement.tender_management.derived_models.events.codes import (
	ADDENDUM_DERIVED_MODELS_REGENERATED,
)
from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_ADDENDUM_IMPACT_ANALYSED,
)
from kentender_procurement.tender_management.std_instance.generated_output import (
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.std_instance.snapshot import (
	StdInstanceSnapshotService,
)

CHANGE_TYPE_TO_OUTPUTS: dict[str, tuple[str, ...]] = {
	"submission_deadline": ("Bundle", "DSM", "DOM"),
	"evaluation_criteria": ("Bundle", "DEM"),
	"contract_condition": ("Bundle", "DCM"),
	"boq_quantity": ("Bundle", "DSM", "DEM", "DCM"),
	"specification_attachment": ("Bundle", "DSM", "DEM"),
}

CANONICAL_OUTPUT_ORDER: tuple[str, ...] = ("Bundle", "DSM", "DOM", "DEM", "DCM")

OUTPUT_TYPE_TO_GENERATE_METHOD: dict[str, str] = {
	"Bundle": "generate_bundle",
	"DSM": "generate_dsm",
	"DOM": "generate_dom",
	"DEM": "generate_dem",
	"DCM": "generate_dcm",
}


def _normalize_change_type(value: str | None) -> str:
	return (value or "").strip().lower()


def _validate_instance_exists(instance_name: str) -> None:
	if not frappe.db.exists("Tender STD Instance", instance_name):
		frappe.throw(_("Tender STD Instance {0} not found.").format(instance_name), frappe.DoesNotExistError)


class StdAddendumImpactService:
	"""Deterministic addendum impact mapping and regeneration planning."""

	@staticmethod
	def identify_affected_outputs(change_types: list[str]) -> list[str]:
		normalized = [_normalize_change_type(v) for v in (change_types or []) if _normalize_change_type(v)]
		if not normalized:
			return []

		unknown = sorted({ct for ct in normalized if ct not in CHANGE_TYPE_TO_OUTPUTS})
		if unknown:
			frappe.throw(
				_("Unknown addendum change types: {0}").format(", ".join(unknown)),
				title=_("STD Addendum Impact"),
			)

		affected: set[str] = set()
		for ct in normalized:
			affected.update(CHANGE_TYPE_TO_OUTPUTS[ct])

		return [k for k in CANONICAL_OUTPUT_ORDER if k in affected]

	@staticmethod
	def analyse_impact(
		instance_name: str,
		change_types: list[str],
		*,
		source_addendum_code: str | None = None,
		requires_supplier_notification_override: bool | None = None,
	) -> dict[str, Any]:
		_validate_instance_exists(instance_name)
		affected_outputs = StdAddendumImpactService.identify_affected_outputs(change_types)
		reasons = {_normalize_change_type(ct): list(CHANGE_TYPE_TO_OUTPUTS[_normalize_change_type(ct)]) for ct in change_types if _normalize_change_type(ct) in CHANGE_TYPE_TO_OUTPUTS}

		requires_supplier_notification = (
			("DSM" in affected_outputs or "DOM" in affected_outputs)
			if requires_supplier_notification_override is None
			else bool(requires_supplier_notification_override)
		)

		result = {
			"instance": instance_name,
			"source_addendum_code": (source_addendum_code or "").strip() or None,
			"affected_outputs": affected_outputs,
			"requires_supplier_notification": requires_supplier_notification,
			"requires_addendum_snapshot": True,
			"reasons": reasons,
		}
		emit_std_instance_event(
			EVT_STDINST_ADDENDUM_IMPACT_ANALYSED,
			instance_code=instance_name,
			details={
				"change_types": change_types,
				"affected_outputs": affected_outputs,
				"requires_supplier_notification": requires_supplier_notification,
			},
		)
		return result

	@staticmethod
	def create_regeneration_plan(
		instance_name: str,
		change_types: list[str],
		*,
		source_addendum_code: str | None = None,
		execute: bool = False,
		publish_outputs: bool = True,
	) -> dict[str, Any]:
		_validate_instance_exists(instance_name)
		impact = StdAddendumImpactService.analyse_impact(
			instance_name,
			change_types,
			source_addendum_code=source_addendum_code,
		)
		affected = impact["affected_outputs"]
		ad_code = (source_addendum_code or "").strip() or None

		steps: list[dict[str, Any]] = []
		for output_type in affected:
			steps.append(
				{
					"output_type": output_type,
					"actions": [
						{"name": "mark_output_stale"},
						{"name": OUTPUT_TYPE_TO_GENERATE_METHOD[output_type]},
						{"name": "publish_output" if publish_outputs else "leave_draft"},
					],
				}
			)

		plan: dict[str, Any] = {
			"instance": instance_name,
			"source_addendum_code": ad_code,
			"affected_outputs": affected,
			"requires_supplier_notification": impact["requires_supplier_notification"],
			"requires_addendum_snapshot": True,
			"snapshot_type": "Addendum",
			"publish_outputs": bool(publish_outputs),
			"steps": steps,
		}

		if not execute:
			return plan

		inst = frappe.get_doc("Tender STD Instance", instance_name)
		tm2_only_no_pt = bool((inst.tm2_tender or "").strip())

		executed_outputs: list[dict[str, Any]] = []
		_allow = bool((ad_code or "").strip())
		for output_type in affected:
			StdInstanceGeneratedOutputService.mark_output_stale(
				instance_name,
				output_type=output_type,
				ignore_generated_output_immutability=_allow,
			)
			gen_method = getattr(StdInstanceGeneratedOutputService, OUTPUT_TYPE_TO_GENERATE_METHOD[output_type])
			new_doc = gen_method(
				instance_name,
				source_addendum_code=ad_code,
				ignore_generated_output_lock=_allow,
			)
			if publish_outputs:
				new_doc = StdInstanceGeneratedOutputService.publish_output(
					new_doc.name,
					ignore_generated_output_immutability=_allow,
				)
			executed_outputs.append(
				{
					"output_type": output_type,
					"output_code": new_doc.name,
					"status": new_doc.output_status,
				}
			)

		snap_code: str | None = None
		if not tm2_only_no_pt:
			snapshot = StdInstanceSnapshotService.create_addendum_snapshot(
				instance_name,
				snapshot_reason=_("Addendum regeneration for {0}").format(ad_code or "N/A"),
				source_addendum_code=ad_code,
			)
			snap_code = snapshot.name
		else:
			# TM2-only instances (doc 9 §9.2) have no ``procurement_tender``; snapshot rows still require it.
			plan["addendum_snapshot_skipped_reason"] = "tm2_only_no_procurement_tender"

		plan["executed"] = True
		plan["executed_outputs"] = executed_outputs
		plan["addendum_snapshot_code"] = snap_code
		emit_derived_model_audit(
			ADDENDUM_DERIVED_MODELS_REGENERATED,
			instance_code=instance_name,
			extra={
				"source_addendum_code": ad_code,
				"executed_outputs": executed_outputs,
				"addendum_snapshot_code": snap_code or "",
				"publish_outputs": bool(publish_outputs),
			},
		)
		return plan
