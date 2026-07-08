# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0800 — ``OutputConsumptionService`` (pack §14).

Maps pack method names::

	getCurrentOutputForConsumer → get_current_output_for_consumer
	validateConsumption → validate_consumption
	recordConsumption → record_consumption

Doc 9 §25 **EX-09** (evaluation-side consumption of published DEM, incl. ``boq_arithmetic_correction``):
``tender_management.tests.test_p9_17_evaluation_handoff_tab`` (``test_EX_09_*``);
``tender_management.tests.test_o08_tm2_smoke_eval_005_arithmetic_correction_only_in_evaluation`` (O-08).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.derived_models.events.audit import emit_derived_model_audit
from kentender_procurement.tender_management.derived_models.events.codes import (
	DERIVED_MODEL_CONSUMED,
	DERIVED_MODEL_CONSUMPTION_DENIED,
)
from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_OUTPUT_CONSUMED
from kentender_procurement.tender_management.std_instance.parameter import (
	OUTPUT_KEY_TO_PARENT_FIELD,
	parse_outputs_stale_flags,
)
from kentender_procurement.tender_management.security.authorization.integration import (
	enforce_sec_authorization,
)

OUTPUT_CONSUMPTION_TITLE = "Output Consumption"

# Pack §14 consumer → output type (normalized keys are lowercase, no spaces).
_CONSUMER_MODULE_TO_OUTPUT_TYPE: dict[str, str] = {
	"submission": "DSM",
	"opening": "DOM",
	"evaluation": "DEM",
	"contract": "DCM",
	"publication": "Bundle",
	"supplierportal": "Bundle",
}

# Stable blocker codes (std engine §14.4 / pack §14).
CODE_OUTPUT_NOT_FOUND = "OUTPUT_NOT_FOUND"
CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER = "OUTPUT_TYPE_INVALID_FOR_CONSUMER"
CODE_OUTPUT_STALE = "OUTPUT_STALE"
CODE_OUTPUT_SUPERSEDED = "OUTPUT_SUPERSEDED"
CODE_OUTPUT_NOT_LINKED_TO_SNAPSHOT = "OUTPUT_NOT_LINKED_TO_SNAPSHOT"
CODE_OUTPUT_STATUS_NOT_CONSUMABLE = "OUTPUT_STATUS_NOT_CONSUMABLE"
CODE_PUBLICATION_REQUIRES_PUBLISHED = "PUBLICATION_REQUIRES_PUBLISHED"
CODE_CONSUMER_MODULE_UNKNOWN = "CONSUMER_MODULE_UNKNOWN"

_MSG_STALE = "The requested generated model is stale and must be regenerated before use."
_MSG_SUPERSEDED = "This output was superseded; historical consumption requires explicit context."
_MSG_NOT_FOUND = "Generated output was not found or is not set as current for this instance."
_MSG_WRONG_TYPE = "This consumer module cannot use this output type."
_MSG_SNAPSHOT = "Contract consumption requires a Final STD instance snapshot link on the output."
_MSG_BAD_STATUS = "Output status is not consumable for downstream use."
_MSG_PUBLICATION = "Publication and supplier portal consumption requires a Published bundle output."
_MSG_UNKNOWN_CONSUMER = "Unknown consumer module."
_CONSUME_ACTION_BY_OUTPUT_TYPE: dict[str, str] = {
	"DSM": "CONSUME_DSM",
	"DOM": "CONSUME_DOM",
	"DEM": "CONSUME_DEM",
	"DCM": "CONSUME_DCM",
	"Bundle": "CONSUME_DSM",
}


def _normalize_consumer_module(consumer_module: str | None) -> str:
	return (consumer_module or "").strip().lower().replace(" ", "").replace("_", "")


def _expected_output_type(consumer_module: str | None) -> str | None:
	key = _normalize_consumer_module(consumer_module)
	return _CONSUMER_MODULE_TO_OUTPUT_TYPE.get(key)


def _context_allows_superseded(consumer_context_code: str | None) -> bool:
	raw = (consumer_context_code or "").strip()
	if not raw:
		return False
	u = raw.upper()
	if u in {"HISTORICAL", "ALLOW_SUPERSEDED"}:
		return True
	return u.startswith("HISTORICAL:")


def _envelope(
	allowed: bool,
	*,
	output_status: str | None,
	snapshot_code: str | None,
	blockers: list[dict[str, str]],
) -> dict[str, Any]:
	return {
		"allowed": allowed,
		"output_status": output_status,
		"snapshot_code": snapshot_code,
		"blockers": blockers,
	}


def _instance_has_stale_flag_for_output(instance_name: str, output_type: str) -> bool:
	if not instance_name or not output_type:
		return False
	inst = frappe.get_doc("Tender STD Instance", instance_name)
	return output_type in set(parse_outputs_stale_flags(inst))


def _contract_snapshot_blocker(doc: Document) -> dict[str, str] | None:
	code = (doc.source_instance_snapshot_code or "").strip()
	if not code:
		return {"code": CODE_OUTPUT_NOT_LINKED_TO_SNAPSHOT, "message": _MSG_SNAPSHOT}
	if not frappe.db.exists("Tender STD Instance Snapshot", code):
		return {"code": CODE_OUTPUT_NOT_LINKED_TO_SNAPSHOT, "message": _MSG_SNAPSHOT}
	st = (frappe.db.get_value("Tender STD Instance Snapshot", code, "snapshot_status") or "").strip()
	if st != "Final":
		return {"code": CODE_OUTPUT_NOT_LINKED_TO_SNAPSHOT, "message": _MSG_SNAPSHOT}
	return None


class OutputConsumptionService:
	"""Validate and record downstream consumption of versioned STD outputs (pack §14)."""

	@staticmethod
	def get_current_output_for_consumer(instance_code: str, consumer_module: str) -> dict[str, Any]:
		"""Resolve the instance pointer for the consumer's output type and validate (pack §14)."""
		ic = (instance_code or "").strip()
		if not ic:
			return _envelope(
				False,
				output_status=None,
				snapshot_code=None,
				blockers=[{"code": CODE_OUTPUT_NOT_FOUND, "message": _MSG_NOT_FOUND}],
			)
		if not frappe.db.exists("Tender STD Instance", ic):
			return _envelope(
				False,
				output_status=None,
				snapshot_code=None,
				blockers=[{"code": CODE_OUTPUT_NOT_FOUND, "message": _MSG_NOT_FOUND}],
			)

		expected = _expected_output_type(consumer_module)
		if not expected:
			return _envelope(
				False,
				output_status=None,
				snapshot_code=None,
				blockers=[{"code": CODE_CONSUMER_MODULE_UNKNOWN, "message": _MSG_UNKNOWN_CONSUMER}],
			)

		ot = expected
		field = OUTPUT_KEY_TO_PARENT_FIELD.get(ot)
		if not field:
			return _envelope(
				False,
				output_status=None,
				snapshot_code=None,
				blockers=[{"code": CODE_OUTPUT_NOT_FOUND, "message": _MSG_NOT_FOUND}],
			)

		out_name = (frappe.db.get_value("Tender STD Instance", ic, field) or "").strip()
		if not out_name:
			return _envelope(
				False,
				output_status=None,
				snapshot_code=None,
				blockers=[{"code": CODE_OUTPUT_NOT_FOUND, "message": _MSG_NOT_FOUND}],
			)

		return OutputConsumptionService.validate_consumption(out_name, consumer_module, None)

	@staticmethod
	def validate_consumption(
		output_code: str,
		consumer_module: str,
		consumer_context_code: str | None,
	) -> dict[str, Any]:
		"""Return pack §14 JSON envelope (``allowed``, ``output_status``, ``snapshot_code``, ``blockers``)."""
		expected = _expected_output_type(consumer_module)
		if expected:
			enforce_sec_authorization(
				action_code=_CONSUME_ACTION_BY_OUTPUT_TYPE.get(expected, "CONSUME_DSM"),
				actor=frappe.session.user,
				object_type="Tender STD Generated Output",
				object_code=(output_code or "").strip(),
				context={"object_exists": bool(output_code and frappe.db.exists("Tender STD Generated Output", output_code))},
				fallback_message="Not authorized to consume generated outputs.",
			)
		if not expected:
			return _envelope(
				False,
				output_status=None,
				snapshot_code=None,
				blockers=[{"code": CODE_CONSUMER_MODULE_UNKNOWN, "message": _MSG_UNKNOWN_CONSUMER}],
			)

		name = (output_code or "").strip()
		if not name or not frappe.db.exists("Tender STD Generated Output", name):
			return _envelope(
				False,
				output_status=None,
				snapshot_code=None,
				blockers=[{"code": CODE_OUTPUT_NOT_FOUND, "message": _MSG_NOT_FOUND}],
			)

		doc = frappe.get_doc("Tender STD Generated Output", name)
		st = (doc.output_status or "").strip()
		snap = (doc.source_instance_snapshot_code or "").strip() or None
		blockers: list[dict[str, str]] = []

		doc_type = (doc.output_type or "").strip()
		if doc_type != expected:
			blockers.append({"code": CODE_OUTPUT_TYPE_INVALID_FOR_CONSUMER, "message": _MSG_WRONG_TYPE})
			return _envelope(False, output_status=st or None, snapshot_code=snap, blockers=blockers)

		inst_name = (doc.tender_std_instance or "").strip()
		if st == "Stale" or _instance_has_stale_flag_for_output(inst_name, doc_type):
			blockers.append({"code": CODE_OUTPUT_STALE, "message": _MSG_STALE})
			return _envelope(False, output_status=st or None, snapshot_code=snap, blockers=blockers)

		if st == "Superseded" and not _context_allows_superseded(consumer_context_code):
			blockers.append({"code": CODE_OUTPUT_SUPERSEDED, "message": _MSG_SUPERSEDED})
			return _envelope(False, output_status=st or None, snapshot_code=snap, blockers=blockers)

		norm_mod = _normalize_consumer_module(consumer_module)

		if st == "Superseded" and _context_allows_superseded(consumer_context_code):
			return _envelope(True, output_status=st or None, snapshot_code=snap, blockers=[])

		if norm_mod == "publication" or norm_mod == "supplierportal":
			if st != "Published":
				blockers.append({"code": CODE_PUBLICATION_REQUIRES_PUBLISHED, "message": _MSG_PUBLICATION})
				return _envelope(False, output_status=st or None, snapshot_code=snap, blockers=blockers)
		else:
			if st not in ("Published", "Current"):
				blockers.append({"code": CODE_OUTPUT_STATUS_NOT_CONSUMABLE, "message": _MSG_BAD_STATUS})
				return _envelope(False, output_status=st or None, snapshot_code=snap, blockers=blockers)

		if st in ("Draft", "Failed", "Archived"):
			blockers.append({"code": CODE_OUTPUT_STATUS_NOT_CONSUMABLE, "message": _MSG_BAD_STATUS})
			return _envelope(False, output_status=st or None, snapshot_code=snap, blockers=blockers)

		if norm_mod == "contract":
			snap_block = _contract_snapshot_blocker(doc)
			if snap_block:
				blockers.append(snap_block)
				return _envelope(False, output_status=st or None, snapshot_code=snap, blockers=blockers)

		return _envelope(True, output_status=st or None, snapshot_code=snap, blockers=[])

	@staticmethod
	def build_consumption_success_payload(
		output_code: str,
		consumer_module: str,
		consumer_context_code: str | None,
		actor_or_system: str | None,
	) -> dict[str, Any]:
		"""Emit consumption audit and return payload. Call only after ``validate_consumption`` returned ``allowed``."""
		doc = frappe.get_doc("Tender STD Generated Output", (output_code or "").strip())
		inst = (doc.tender_std_instance or "").strip()
		actor = (actor_or_system or "").strip() or (frappe.session.user if frappe.session else None) or "Administrator"

		emit_std_instance_event(
			EVT_STDINST_OUTPUT_CONSUMED,
			instance_code=inst,
			document_type="Tender STD Generated Output",
			document_name=doc.name,
			details={
				"output_code": doc.name,
				"output_type": doc.output_type,
				"output_status": doc.output_status,
				"consumer_module": consumer_module,
				"consumer_context_code": (consumer_context_code or "").strip() or None,
			},
			performed_by=actor,
		)
		emit_derived_model_audit(
			DERIVED_MODEL_CONSUMED,
			instance_code=inst,
			output_code=doc.name,
			output_type=(doc.output_type or "").strip() or None,
			version_number=int(doc.version_number or 0),
			tender_code=(doc.tender_code or "").strip() or None,
			actor_or_job=actor,
			snapshot_code=(doc.source_instance_snapshot_code or "").strip() or None,
			consumer_module=consumer_module,
			extra={
				"consumer_context_code": (consumer_context_code or "").strip() or None,
				"output_status": (doc.output_status or "").strip() or None,
			},
		)

		payload: dict[str, Any] = {
			"ok": True,
			"output_code": doc.name,
			"output_type": doc.output_type,
			"output_status": doc.output_status,
			"consumer_module": consumer_module,
		}
		try:
			raw = doc.get("content_json")
			if isinstance(raw, dict):
				payload["content_json"] = raw
			elif isinstance(raw, str) and raw.strip():
				payload["content_json"] = json.loads(raw)
		except Exception:
			payload["content_json"] = None

		return payload

	@staticmethod
	def record_consumption(
		output_code: str,
		consumer_module: str,
		consumer_context_code: str | None,
		actor_or_system: str | None,
	) -> dict[str, Any]:
		"""Validate consumption and append an audit row when allowed (pack §14)."""
		res = OutputConsumptionService.validate_consumption(output_code, consumer_module, consumer_context_code)
		if not res.get("allowed"):
			blockers = list(res.get("blockers") or [])
			b0 = blockers[0] if blockers else {"code": CODE_OUTPUT_NOT_FOUND, "message": _MSG_NOT_FOUND}
			denial = str(b0.get("code") or CODE_OUTPUT_NOT_FOUND)
			oc = (output_code or "").strip()
			inst_hint = None
			if oc and frappe.db.exists("Tender STD Generated Output", oc):
				inst_hint = (frappe.db.get_value("Tender STD Generated Output", oc, "tender_std_instance") or "").strip() or None
			emit_derived_model_audit(
				DERIVED_MODEL_CONSUMPTION_DENIED,
				instance_code=inst_hint,
				output_code=oc or None,
				consumer_module=consumer_module,
				denial_code=denial,
				extra={
					"consumer_context_code": (consumer_context_code or "").strip() or None,
					"message": str(b0.get("message") or ""),
					"blockers": blockers,
					"source": "record_consumption",
				},
			)
			frappe.throw(
				_(str(b0.get("message") or _MSG_NOT_FOUND)),
				title=str(b0.get("code") or OUTPUT_CONSUMPTION_TITLE),
				exc=frappe.ValidationError,
			)

		return OutputConsumptionService.build_consumption_success_payload(
			output_code,
			consumer_module,
			consumer_context_code,
			actor_or_system,
		)
