# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-1000 — Whitelisted STD Engine generated-output API (pack §17).

Maps REST-style resources to ``frappe.call`` targets::

	POST .../outputs/generate-all  → ``std_engine_generate_all_outputs``
	POST .../outputs/{type}/generate → ``std_engine_generate_output``
	GET  .../outputs/{type}/current → ``std_engine_get_current_output``
	GET  .../outputs/{output_code} → ``std_engine_get_output``
	POST .../validate-consumption → ``std_engine_validate_output_consumption``
	POST .../record-consumption → ``std_engine_record_output_consumption``

**Error envelope** (pack §17)::

	{"success": false, "error_code": "...", "message": "...", "details": {}}

**Consumption validate** returns pack §14 fields at the top level with ``success: true``
(``allowed`` may be ``false`` with ``blockers`` — business rule denial, not transport error).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.derived_models.consumption.output_consumption import (
	OutputConsumptionService,
)
from kentender_procurement.tender_management.derived_models.events.audit import emit_derived_model_audit
from kentender_procurement.tender_management.derived_models.events.codes import DERIVED_MODEL_CONSUMPTION_DENIED
from kentender_procurement.tender_management.derived_models.orchestration import (
	DerivedModelGenerationService,
)
from kentender_procurement.tender_management.std_instance.generated_output import OUTPUT_TYPES
from kentender_procurement.tender_management.std_instance.parameter import OUTPUT_KEY_TO_PARENT_FIELD

DERIVED_API_INTERNAL = "DERIVED_API_INTERNAL_ERROR"
DERIVED_API_NOT_FOUND = "DERIVED_API_NOT_FOUND"
DERIVED_API_PERMISSION = "DERIVED_API_PERMISSION_DENIED"
DERIVED_API_INVALID_OUTPUT_TYPE = "DERIVED_API_INVALID_OUTPUT_TYPE"
DERIVED_API_OUTPUT_NOT_SET = "DERIVED_API_OUTPUT_NOT_SET"
DERIVED_API_VALIDATION_FAILED = "DERIVED_API_VALIDATION_FAILED"

_SLUG_TO_LABEL: dict[str, str] = {
	"bundle": "Bundle",
	"dsm": "DSM",
	"dom": "DOM",
	"dem": "DEM",
	"dcm": "DCM",
}


def _as_bool(value: Any, *, default: bool = False) -> bool:
	if value is None:
		return default
	if isinstance(value, bool):
		return value
	if isinstance(value, (int, float)):
		return bool(value)
	return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _api_fail(error_code: str, message: str, *, details: dict[str, Any] | None = None) -> dict[str, Any]:
	return {
		"success": False,
		"error_code": error_code,
		"message": str(message),
		"details": dict(details or {}),
	}


def _api_ok(**payload: Any) -> dict[str, Any]:
	out: dict[str, Any] = {"success": True}
	out.update(payload)
	return out


def _normalize_output_type_slug(raw: str | None) -> str | None:
	key = (raw or "").strip().lower().replace(" ", "").replace("_", "")
	return _SLUG_TO_LABEL.get(key)


def _serialize_output_doc(doc: Document) -> dict[str, Any]:
	meta: dict[str, Any] = {
		"output_code": doc.name,
		"output_type": (doc.output_type or "").strip(),
		"output_status": (doc.output_status or "").strip(),
		"version_number": int(doc.version_number or 0),
		"instance_code": (doc.tender_std_instance or "").strip(),
		"tender_code": (doc.tender_code or "").strip() or None,
		"source_instance_snapshot_code": (doc.source_instance_snapshot_code or "").strip() or None,
		"source_addendum_code": (doc.source_addendum_code or "").strip() or None,
		"input_hash": (doc.input_hash or "").strip() or None,
		"output_hash": (doc.output_hash or "").strip() or None,
		"published_at": doc.published_at,
		"generated_by_job_code": (doc.generated_by_job_code or "").strip() or None,
	}
	content: Any = None
	try:
		raw = doc.get("content_json")
		if isinstance(raw, dict):
			content = raw
		elif isinstance(raw, str) and raw.strip():
			content = json.loads(raw)
	except Exception:
		content = None
	meta["content_json"] = content
	return meta


def _map_exception(exc: BaseException) -> tuple[str, str]:
	if isinstance(exc, frappe.PermissionError):
		return DERIVED_API_PERMISSION, _("Permission denied.")
	if isinstance(exc, frappe.DoesNotExistError):
		return DERIVED_API_NOT_FOUND, str(exc)
	if isinstance(exc, frappe.ValidationError):
		return DERIVED_API_VALIDATION_FAILED, str(exc)
	return DERIVED_API_INTERNAL, _("Unexpected server error.")


@frappe.whitelist()
def std_engine_generate_all_outputs(
	instance_code: str,
	publish: int | bool | None = None,
	rollback_on_failure: int | bool | None = None,
	run_works_prechecks: int | bool | None = None,
	actor_or_job: str | None = None,
	generated_by_job_code: str | None = None,
) -> dict[str, Any]:
	"""Generate Bundle → DSM → DOM → DEM → DCM for ``instance_code`` (pack §17)."""
	try:
		result = DerivedModelGenerationService.generate_all(
			instance_code,
			actor_or_job,
			publish=_as_bool(publish),
			rollback_on_failure=_as_bool(rollback_on_failure),
			run_works_prechecks=_as_bool(run_works_prechecks),
			generated_by_job_code=(generated_by_job_code or "").strip() or None,
		)
		return _api_ok(**result)
	except Exception as exc:
		code, msg = _map_exception(exc)
		if code == DERIVED_API_INTERNAL:
			frappe.log_error(frappe.get_traceback(), "DERIVED-1000 generate_all_outputs")
		return _api_fail(code, msg, details={"instance_code": instance_code})


@frappe.whitelist()
def std_engine_generate_output(
	instance_code: str,
	output_type: str,
	publish: int | bool | None = None,
	rollback_on_failure: int | bool | None = None,
	run_works_prechecks: int | bool | None = None,
	actor_or_job: str | None = None,
	generated_by_job_code: str | None = None,
) -> dict[str, Any]:
	"""Generate a single output. ``output_type`` is ``bundle|dsm|dom|dem|dcm`` (case-insensitive)."""
	label = _normalize_output_type_slug(output_type)
	if not label or label not in OUTPUT_TYPES:
		return _api_fail(
			DERIVED_API_INVALID_OUTPUT_TYPE,
			_("output_type must be one of: bundle, dsm, dom, dem, dcm."),
			details={"output_type": output_type},
		)
	try:
		result = DerivedModelGenerationService.generate_output(
			instance_code,
			label,
			actor_or_job,
			publish=_as_bool(publish),
			rollback_on_failure=_as_bool(rollback_on_failure),
			run_works_prechecks=_as_bool(run_works_prechecks),
			generated_by_job_code=(generated_by_job_code or "").strip() or None,
		)
		return _api_ok(**result)
	except Exception as exc:
		code, msg = _map_exception(exc)
		if code == DERIVED_API_INTERNAL:
			frappe.log_error(frappe.get_traceback(), "DERIVED-1000 generate_output")
		return _api_fail(
			code,
			msg,
			details={"instance_code": instance_code, "output_type": label},
		)


@frappe.whitelist()
def std_engine_get_current_output(instance_code: str, output_type: str) -> dict[str, Any]:
	"""Return metadata + ``content_json`` for the logical current row (pack §17).

	Uses the instance ``current_*_output_code`` pointer when it references a
	Current/Published row (set on publish); otherwise resolves the latest
	Current/Published version for that type (covers Draft→Current before publish).
	"""
	ic = (instance_code or "").strip()
	label = _normalize_output_type_slug(output_type)
	if not label or label not in OUTPUT_TYPES:
		return _api_fail(
			DERIVED_API_INVALID_OUTPUT_TYPE,
			_("output_type must be one of: bundle, dsm, dom, dem, dcm."),
			details={"output_type": output_type},
		)
	if not ic or not frappe.db.exists("Tender STD Instance", ic):
		return _api_fail(DERIVED_API_NOT_FOUND, _("Tender STD Instance not found."), details={"instance_code": ic})

	field = OUTPUT_KEY_TO_PARENT_FIELD.get(label)
	if not field:
		return _api_fail(DERIVED_API_INVALID_OUTPUT_TYPE, _("Unknown output field."), details={"output_type": label})

	def _resolve_row_name() -> str | None:
		"""Prefer instance pointer when it references a Current/Published row; else latest Current/Published version."""
		ptr = (frappe.db.get_value("Tender STD Instance", ic, field) or "").strip()
		if ptr and frappe.db.exists("Tender STD Generated Output", ptr):
			st = (frappe.db.get_value("Tender STD Generated Output", ptr, "output_status") or "").strip()
			if st in ("Current", "Published"):
				return ptr
		rows = frappe.get_all(
			"Tender STD Generated Output",
			filters={
				"tender_std_instance": ic,
				"output_type": label,
				"output_status": ["in", ["Current", "Published"]],
			},
			pluck="name",
			order_by="version_number desc",
			limit=1,
		)
		return rows[0] if rows else None

	out_name = _resolve_row_name()
	if not out_name:
		return _api_fail(
			DERIVED_API_OUTPUT_NOT_SET,
			_("No current output is set for this type on the instance."),
			details={"instance_code": ic, "output_type": label},
		)

	doc = frappe.get_doc("Tender STD Generated Output", out_name)
	return _api_ok(output=_serialize_output_doc(doc))


@frappe.whitelist()
def std_engine_get_output(output_code: str) -> dict[str, Any]:
	"""Fetch a generated output by document name / pack ``output_code``."""
	name = (output_code or "").strip()
	if not name or not frappe.db.exists("Tender STD Generated Output", name):
		return _api_fail(
			DERIVED_API_NOT_FOUND,
			_("Generated output not found."),
			details={"output_code": name},
		)
	doc = frappe.get_doc("Tender STD Generated Output", name)
	return _api_ok(output=_serialize_output_doc(doc))


@frappe.whitelist()
def std_engine_validate_output_consumption(
	output_code: str,
	consumer_module: str,
	consumer_context_code: str | None = None,
) -> dict[str, Any]:
	"""Pack §14 envelope (``allowed``, ``output_status``, ``snapshot_code``, ``blockers``) + ``success: true``."""
	env = OutputConsumptionService.validate_consumption(output_code, consumer_module, consumer_context_code)
	return _api_ok(
		allowed=env.get("allowed"),
		output_status=env.get("output_status"),
		snapshot_code=env.get("snapshot_code"),
		blockers=env.get("blockers") or [],
	)


@frappe.whitelist()
def std_engine_record_output_consumption(
	output_code: str,
	consumer_module: str,
	consumer_context_code: str | None = None,
	actor_or_system: str | None = None,
) -> dict[str, Any]:
	"""Record consumption when allowed; otherwise pack §17 error envelope (no throw)."""
	env = OutputConsumptionService.validate_consumption(output_code, consumer_module, consumer_context_code)
	if not env.get("allowed"):
		blockers = list(env.get("blockers") or [])
		b0 = blockers[0] if blockers else {"code": "OUTPUT_NOT_FOUND", "message": "Generated output was not found."}
		denial = str(b0.get("code") or "OUTPUT_NOT_FOUND")
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
			actor_or_job=(actor_or_system or "").strip() or None,
			extra={
				"consumer_context_code": (consumer_context_code or "").strip() or None,
				"message": str(b0.get("message") or ""),
				"blockers": blockers,
				"source": "std_engine_record_output_consumption",
			},
		)
		return _api_fail(
			denial,
			str(b0.get("message") or ""),
			details={"blockers": blockers},
		)
	payload = OutputConsumptionService.build_consumption_success_payload(
			output_code,
			consumer_module,
			consumer_context_code,
			actor_or_system,
		)
	return _api_ok(recorded=True, **{k: v for k, v in payload.items() if k != "ok"})
