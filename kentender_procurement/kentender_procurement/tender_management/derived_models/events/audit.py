# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-1100 — Append-only ``Audit Event`` rows with pack §18 metadata shape."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from kentender_core.services.audit_event_service import log_audit_event

from kentender_procurement.tender_management.derived_models.events.codes import (
	ADDENDUM_DERIVED_MODELS_REGENERATED,
	CONTRACT_BINDING_VIOLATION_DENIED,
	DERIVED_MODEL_CONSUMED,
	DERIVED_MODEL_CONSUMPTION_DENIED,
	DERIVED_MODEL_GENERATED,
	DERIVED_MODEL_GENERATION_FAILED,
	DERIVED_MODEL_GENERATION_REQUESTED,
	DERIVED_MODEL_MARKED_STALE,
	DERIVED_MODEL_SUPERSEDED,
	MANUAL_EVALUATION_CRITERIA_DENIED,
	MANUAL_OPENING_EVALUATION_FIELD_DENIED,
	MANUAL_SUBMISSION_REQUIREMENT_DENIED,
)

DERIVED_MODEL_ENTITY = "DERIVED_MODEL"

DERIVED_MODEL_EVENT_ACTIONS: dict[str, str] = {
	DERIVED_MODEL_GENERATION_REQUESTED: "derived_model_generation_requested",
	DERIVED_MODEL_GENERATED: "derived_model_generated",
	DERIVED_MODEL_GENERATION_FAILED: "derived_model_generation_failed",
	DERIVED_MODEL_MARKED_STALE: "derived_model_marked_stale",
	DERIVED_MODEL_SUPERSEDED: "derived_model_superseded",
	DERIVED_MODEL_CONSUMED: "derived_model_consumed",
	DERIVED_MODEL_CONSUMPTION_DENIED: "derived_model_consumption_denied",
	MANUAL_SUBMISSION_REQUIREMENT_DENIED: "manual_submission_requirement_denied",
	MANUAL_OPENING_EVALUATION_FIELD_DENIED: "manual_opening_evaluation_field_denied",
	MANUAL_EVALUATION_CRITERIA_DENIED: "manual_evaluation_criteria_denied",
	CONTRACT_BINDING_VIOLATION_DENIED: "contract_binding_violation_denied",
	ADDENDUM_DERIVED_MODELS_REGENERATED: "addendum_derived_models_regenerated",
}


def _safe_metadata(meta: dict[str, Any]) -> dict[str, Any]:
	try:
		json.dumps(meta, sort_keys=True, separators=(",", ":"))
		return meta
	except Exception:
		return {"raw": frappe.as_json(meta)}


def emit_derived_model_audit(
	event_code: str,
	*,
	instance_code: str | None = None,
	output_code: str | None = None,
	output_type: str | None = None,
	version_number: int | None = None,
	tender_code: str | None = None,
	actor_or_job: str | None = None,
	snapshot_code: str | None = None,
	consumer_module: str | None = None,
	denial_code: str | None = None,
	extra: dict[str, Any] | None = None,
) -> str | None:
	"""Insert an ``Audit Event`` with pack §17/§18 style ``metadata`` (best-effort)."""
	try:
		# ``performed_by`` on ``Audit Event`` is a Link to ``User``; job codes live in metadata only.
		performed_by_user = (frappe.session.user if frappe.session else None) or "Administrator"
		job_or_actor = (actor_or_job or "").strip() or performed_by_user
		ts = now_datetime()
		meta: dict[str, Any] = {
			"event_code": event_code,
			"output_code": output_code,
			"output_type": output_type,
			"version_number": version_number,
			"instance_code": (instance_code or "").strip() or None,
			"tender_code": tender_code,
			"actor_or_job": job_or_actor,
			"timestamp": ts.isoformat(),
			"snapshot_code": snapshot_code,
			"consumer_module": consumer_module,
			"denial_code": denial_code,
		}
		if extra:
			meta.update(extra)
		doc_name = (output_code or instance_code or "UNKNOWN").strip() or "UNKNOWN"
		return log_audit_event(
			event_type=event_code,
			entity=DERIVED_MODEL_ENTITY,
			document_type="Tender STD Generated Output" if output_code else "Tender STD Instance",
			document_name=doc_name,
			action=DERIVED_MODEL_EVENT_ACTIONS.get(event_code, "derived_model_event"),
			performed_by=performed_by_user,
			timestamp=ts,
			metadata=_safe_metadata(meta),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "DERIVED-1100 derived audit emit failed")
		return None


def emit_derived_model_audit_for_output(
	event_code: str,
	doc: Document,
	*,
	actor_or_job: str | None = None,
	extra: dict[str, Any] | None = None,
) -> str | None:
	"""Build §18 fields from a ``Tender STD Generated Output`` row."""
	job = (actor_or_job or "").strip() or (doc.get("generated_by_job_code") or "").strip() or None
	return emit_derived_model_audit(
		event_code,
		instance_code=(doc.tender_std_instance or "").strip() or None,
		output_code=doc.name,
		output_type=(doc.output_type or "").strip() or None,
		version_number=int(doc.version_number or 0),
		tender_code=(doc.tender_code or "").strip() or None,
		actor_or_job=job,
		snapshot_code=(doc.source_instance_snapshot_code or "").strip() or None,
		extra=extra,
	)


def emit_derived_model_generation_failed(
	instance_name: str,
	output_type: str,
	error: str,
	*,
	source: str,
	output_code: str | None = None,
	version_number: int | None = None,
) -> None:
	emit_derived_model_audit(
		DERIVED_MODEL_GENERATION_FAILED,
		instance_code=instance_name,
		output_type=(output_type or "").strip() or None,
		output_code=output_code,
		version_number=version_number,
		extra={"error": (error or "").strip(), "source": source},
	)


def pack_manual_denial_event_code(denial_code: str) -> str | None:
	"""Map internal denial codes to pack §18 ``event_type`` strings."""
	dc = (denial_code or "").strip()
	if dc == "CONTRACT_BINDING_VIOLATION":
		return CONTRACT_BINDING_VIOLATION_DENIED
	if dc in (
		MANUAL_SUBMISSION_REQUIREMENT_DENIED,
		MANUAL_OPENING_EVALUATION_FIELD_DENIED,
		MANUAL_EVALUATION_CRITERIA_DENIED,
		CONTRACT_BINDING_VIOLATION_DENIED,
	):
		return dc
	return None
