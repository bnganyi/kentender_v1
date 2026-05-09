# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Downstream consumption contracts — resolve current DSM/DOM/DEM/DCM by reference; deny manual rules.

STDINST-0900.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import (
	EVT_STDINST_DENIED_DOWNSTREAM_RULE_INJECTION,
)
from kentender_procurement.tender_management.std_instance.parameter import OUTPUT_KEY_TO_PARENT_FIELD

CONSUMER_OUTPUT_STATUS_ALLOWED: frozenset[str] = frozenset({"Published", "Current"})

MANUAL_RULE_INJECTION_CODE = "MANUAL_RULE_INJECTION_DENIED"
MANUAL_RULE_INJECTION_MESSAGE = (
	"Submission, opening, evaluation, and contract rules must originate from STD outputs."
)

OUTPUT_TYPE_TO_INSTANCE_FIELD: dict[str, str] = {
	"DSM": OUTPUT_KEY_TO_PARENT_FIELD["DSM"],
	"DOM": OUTPUT_KEY_TO_PARENT_FIELD["DOM"],
	"DEM": OUTPUT_KEY_TO_PARENT_FIELD["DEM"],
	"DCM": OUTPUT_KEY_TO_PARENT_FIELD["DCM"],
}


def _resolve_current_output(instance_name: str, output_type: str) -> dict[str, Any]:
	if output_type not in OUTPUT_TYPE_TO_INSTANCE_FIELD:
		frappe.throw(_("Unsupported downstream output type {0}.").format(output_type), title=_("STD Downstream Contract"))

	if not frappe.db.exists("Tender STD Instance", instance_name):
		frappe.throw(_("Tender STD Instance {0} not found.").format(instance_name), frappe.DoesNotExistError)

	instance_field = OUTPUT_TYPE_TO_INSTANCE_FIELD[output_type]
	output_name = (frappe.db.get_value("Tender STD Instance", instance_name, instance_field) or "").strip()
	if not output_name:
		frappe.throw(
			_("Current {0} output is not set on STD Instance {1}.").format(output_type, instance_name),
			title=_("STD Downstream Contract"),
		)

	if not frappe.db.exists("Tender STD Generated Output", output_name):
		frappe.throw(
			_("Current {0} output {1} does not exist.").format(output_type, output_name),
			title=_("STD Downstream Contract"),
		)

	doc = frappe.get_doc("Tender STD Generated Output", output_name)
	doc_type = (doc.output_type or "").strip()
	if doc_type != output_type:
		frappe.throw(
			_("Current field for {0} points to output type {1} ({2}).").format(output_type, doc_type or "Unknown", output_name),
			title=_("STD Downstream Contract"),
		)

	status = (doc.output_status or "").strip()
	if status not in CONSUMER_OUTPUT_STATUS_ALLOWED:
		frappe.throw(
			_("{0} output {1} has non-consumable status {2}.").format(output_type, output_name, status or "Unknown"),
			title=_("STD Downstream Contract"),
		)

	return {
		"instance": instance_name,
		"output_code": doc.name,
		"output_type": doc_type,
		"output_status": status,
		"input_hash": doc.input_hash,
		"output_hash": doc.output_hash,
		"published_at": doc.published_at,
	}


class StdDownstreamConsumptionService:
	"""Resolve current downstream outputs and deny manual rule injection."""

	@staticmethod
	def get_current_dsm(instance_name: str) -> dict[str, Any]:
		return _resolve_current_output(instance_name, "DSM")

	@staticmethod
	def get_current_dom(instance_name: str) -> dict[str, Any]:
		return _resolve_current_output(instance_name, "DOM")

	@staticmethod
	def get_current_dem(instance_name: str) -> dict[str, Any]:
		return _resolve_current_output(instance_name, "DEM")

	@staticmethod
	def get_current_dcm(instance_name: str) -> dict[str, Any]:
		return _resolve_current_output(instance_name, "DCM")

	@staticmethod
	def get_current_outputs(instance_name: str) -> dict[str, dict[str, Any]]:
		return {
			"DSM": StdDownstreamConsumptionService.get_current_dsm(instance_name),
			"DOM": StdDownstreamConsumptionService.get_current_dom(instance_name),
			"DEM": StdDownstreamConsumptionService.get_current_dem(instance_name),
			"DCM": StdDownstreamConsumptionService.get_current_dcm(instance_name),
		}

	@staticmethod
	def deny_manual_rule_injection(*, context: str | None = None) -> None:
		emit_std_instance_event(
			EVT_STDINST_DENIED_DOWNSTREAM_RULE_INJECTION,
			details={"context": context},
			document_type="STD Downstream Contract",
			document_name=context or "default",
			entity="STD_DOWNSTREAM",
		)
		if context:
			frappe.throw(
				_("{0} Context: {1}").format(MANUAL_RULE_INJECTION_MESSAGE, context),
				title=_(MANUAL_RULE_INJECTION_CODE),
			)
		frappe.throw(
			_(MANUAL_RULE_INJECTION_MESSAGE),
			title=_(MANUAL_RULE_INJECTION_CODE),
		)
