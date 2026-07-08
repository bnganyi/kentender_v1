# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Downstream consumption contracts — resolve current Bundle / DSM / DOM / DEM / DCM; deny manual rules.

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


def try_resolve_current_output(instance_name: str, output_type: str) -> dict[str, Any]:
	"""Resolve current generated output for ``instance_name`` / ``output_type`` without throwing.

	Returns a dict with ``ok`` plus ``missing`` / ``stale_or_invalid`` booleans (doc 9 §8.2 / P3-04).
	``reason`` is a stable machine token; ``message`` is human-readable English.
	"""
	ot = (output_type or "").strip()
	inm = (instance_name or "").strip()
	base: dict[str, Any] = {"output_type": ot, "missing": False, "stale_or_invalid": False}
	if not inm:
		return {
			"ok": False,
			"reason": "INSTANCE_CODE_REQUIRED",
			"message": _("Tender STD instance code is required."),
			**base,
			"missing": True,
		}
	if ot not in OUTPUT_KEY_TO_PARENT_FIELD:
		return {
			"ok": False,
			"reason": "UNSUPPORTED_OUTPUT_TYPE",
			"message": _("Unsupported downstream output type {0}.").format(ot),
			**base,
			"stale_or_invalid": True,
		}
	if not frappe.db.exists("Tender STD Instance", inm):
		return {
			"ok": False,
			"reason": "INSTANCE_NOT_FOUND",
			"message": _("Tender STD Instance {0} not found.").format(inm),
			**base,
			"missing": True,
		}

	instance_field = OUTPUT_KEY_TO_PARENT_FIELD[ot]
	output_name = (frappe.db.get_value("Tender STD Instance", inm, instance_field) or "").strip()
	if not output_name:
		return {
			"ok": False,
			"reason": "OUTPUT_NOT_LINKED",
			"message": _("Current {0} output is not set on STD Instance {1}.").format(ot, inm),
			**base,
			"missing": True,
		}

	if not frappe.db.exists("Tender STD Generated Output", output_name):
		return {
			"ok": False,
			"reason": "OUTPUT_DOC_MISSING",
			"message": _("Current {0} output {1} does not exist.").format(ot, output_name),
			**base,
			"missing": True,
		}

	doc = frappe.get_doc("Tender STD Generated Output", output_name)
	doc_type = (doc.output_type or "").strip()
	if doc_type != ot:
		return {
			"ok": False,
			"reason": "WRONG_OUTPUT_TYPE",
			"message": _("Current field for {0} points to output type {1} ({2}).").format(ot, doc_type or "Unknown", output_name),
			**base,
			"stale_or_invalid": True,
		}

	status = (doc.output_status or "").strip()
	if status not in CONSUMER_OUTPUT_STATUS_ALLOWED:
		return {
			"ok": False,
			"reason": "OUTPUT_NOT_CONSUMABLE",
			"message": _("{0} output {1} has non-consumable status {2}.").format(ot, output_name, status or "Unknown"),
			**base,
			"stale_or_invalid": True,
		}

	return {
		"ok": True,
		**base,
		"instance": inm,
		"output_code": doc.name,
		"output_type": doc_type,
		"output_status": status,
		"input_hash": doc.input_hash,
		"output_hash": doc.output_hash,
		"published_at": doc.published_at,
	}


def _resolve_current_output(instance_name: str, output_type: str) -> dict[str, Any]:
	out = try_resolve_current_output(instance_name, output_type)
	if out.get("ok"):
		return {
			"instance": out["instance"],
			"output_code": out["output_code"],
			"output_type": out["output_type"],
			"output_status": out["output_status"],
			"input_hash": out.get("input_hash"),
			"output_hash": out.get("output_hash"),
			"published_at": out.get("published_at"),
		}
	frappe.throw(_(out.get("message") or out.get("reason") or _("STD downstream contract violation.")), title=_("STD Downstream Contract"))


class StdDownstreamConsumptionService:
	"""Resolve current downstream outputs and deny manual rule injection."""

	@staticmethod
	def get_current_bundle(instance_name: str) -> dict[str, Any]:
		return _resolve_current_output(instance_name, "Bundle")

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
			"Bundle": StdDownstreamConsumptionService.get_current_bundle(instance_name),
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
