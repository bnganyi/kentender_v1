# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0900 — append-only Works completion audit façade.

Emits parallel ``WORKS_*`` ``Audit Event`` rows (STDINST-1100 STD events remain).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import frappe
from frappe.utils import now_datetime

from kentender_core.services.audit_event_service import log_audit_event
from kentender_procurement.tender_management.std_instance.parameter import parse_outputs_stale_flags
from kentender_procurement.tender_management.works_completion.services.output_staleness import (
	WorksOutputStalenessService,
)

WORKS_ENTITY = "WORKS_COMPLETION"
WORKS_DOCUMENT_TYPE = "Tender STD Instance"

WORKS_TDS_VALUES_CHANGED = "WORKS_TDS_VALUES_CHANGED"
WORKS_EVALUATION_OPTIONS_CHANGED = "WORKS_EVALUATION_OPTIONS_CHANGED"
WORKS_REQUIREMENTS_CHANGED = "WORKS_REQUIREMENTS_CHANGED"
WORKS_ATTACHMENT_ADDED = "WORKS_ATTACHMENT_ADDED"
WORKS_DRAWING_REGISTER_CHANGED = "WORKS_DRAWING_REGISTER_CHANGED"
WORKS_BOQ_CHANGED = "WORKS_BOQ_CHANGED"
WORKS_SCC_VALUES_CHANGED = "WORKS_SCC_VALUES_CHANGED"
WORKS_OUTPUTS_GENERATED = "WORKS_OUTPUTS_GENERATED"
WORKS_OUTPUT_MARKED_STALE = "WORKS_OUTPUT_MARKED_STALE"
WORKS_READINESS_RUN = "WORKS_READINESS_RUN"
WORKS_READINESS_BLOCKED = "WORKS_READINESS_BLOCKED"
WORKS_CONFIGURATION_SNAPSHOT_CREATED = "WORKS_CONFIGURATION_SNAPSHOT_CREATED"
WORKS_LOCKED_FOR_APPROVAL = "WORKS_LOCKED_FOR_APPROVAL"
WORKS_MANUAL_CRITERIA_DENIED = "WORKS_MANUAL_CRITERIA_DENIED"
WORKS_EDIT_DENIED_LOCKED = "WORKS_EDIT_DENIED_LOCKED"
WORKS_RETURNED_TO_PREPARATION = "WORKS_RETURNED_TO_PREPARATION"

WORKS_EVENT_ACTIONS: dict[str, str] = {
	WORKS_TDS_VALUES_CHANGED: "works_tds_values_changed",
	WORKS_EVALUATION_OPTIONS_CHANGED: "works_evaluation_options_changed",
	WORKS_REQUIREMENTS_CHANGED: "works_requirements_changed",
	WORKS_ATTACHMENT_ADDED: "works_attachment_added",
	WORKS_DRAWING_REGISTER_CHANGED: "works_drawing_register_changed",
	WORKS_BOQ_CHANGED: "works_boq_changed",
	WORKS_SCC_VALUES_CHANGED: "works_scc_values_changed",
	WORKS_OUTPUTS_GENERATED: "works_outputs_generated",
	WORKS_OUTPUT_MARKED_STALE: "works_output_marked_stale",
	WORKS_READINESS_RUN: "works_readiness_run",
	WORKS_READINESS_BLOCKED: "works_readiness_blocked",
	WORKS_CONFIGURATION_SNAPSHOT_CREATED: "works_configuration_snapshot_created",
	WORKS_LOCKED_FOR_APPROVAL: "works_locked_for_approval",
	WORKS_MANUAL_CRITERIA_DENIED: "works_manual_criteria_denied",
	WORKS_EDIT_DENIED_LOCKED: "works_edit_denied_locked",
	WORKS_RETURNED_TO_PREPARATION: "works_returned_to_preparation",
}


def _safe_details(details: dict[str, Any] | None) -> dict[str, Any]:
	payload = dict(details or {})
	try:
		json.dumps(payload, sort_keys=True, separators=(",", ":"))
		return payload
	except Exception:
		return {"raw": frappe.as_json(payload)}


def resolve_tender_code_for_instance(instance_code: str) -> str:
	"""``tender_reference`` when set, else tender name, else procurement tender id."""
	code = (instance_code or "").strip()
	if not code:
		return ""
	pt = frappe.db.get_value("Tender STD Instance", code, "procurement_tender")
	if not pt:
		return ""
	ref = frappe.db.get_value("Procurement Tender", pt, "tender_reference")
	if (ref or "").strip():
		return str(ref).strip()
	name = frappe.db.get_value("Procurement Tender", pt, "name")
	return (name or pt or "").strip()


def union_stale_outputs_for_parameter_codes(parameter_codes: Iterable[str]) -> list[str]:
	"""Union of pack logical outputs that become stale when given parameter codes change."""
	out: set[str] = set()
	for raw in parameter_codes:
		pc = (raw or "").strip()
		if not pc:
			continue
		got = WorksOutputStalenessService.get_stale_outputs_for_parameter_code(pc)
		if got:
			out |= set(got)
	return sorted(out)


def stale_logical_outputs_snapshot(instance_code: str) -> frozenset[str]:
	"""Current ``outputs_stale_flags`` logical keys on the instance."""
	code = (instance_code or "").strip()
	if not code or not frappe.db.exists("Tender STD Instance", code):
		return frozenset()
	doc = frappe.get_doc("Tender STD Instance", code)
	return frozenset(parse_outputs_stale_flags(doc))


def new_stale_outputs_since(before: frozenset[str], instance_code: str) -> list[str]:
	"""Logical outputs newly present in ``outputs_stale_flags`` since ``before``."""
	after = stale_logical_outputs_snapshot(instance_code)
	return sorted(set(after) - set(before))


def emit_works_completion_audit(
	event_code: str,
	instance_code: str,
	*,
	tender_code: str | None = None,
	affected_outputs: list[str] | None = None,
	details: dict[str, Any] | None = None,
	performed_by: str | None = None,
) -> str | None:
	"""Best-effort ``Audit Event`` insert for Works completion (never raises to callers)."""
	try:
		inst = (instance_code or "").strip()
		actor = performed_by or getattr(frappe.session, "user", None) or "Administrator"
		ts = now_datetime()
		tc = (tender_code or "").strip() or (resolve_tender_code_for_instance(inst) if inst else "")
		outs = list(affected_outputs) if affected_outputs is not None else []
		meta: dict[str, Any] = {
			"event_code": event_code,
			"instance_code": inst,
			"tender_code": tc,
			"actor": actor,
			"timestamp": ts.isoformat(),
			"affected_outputs": outs,
			"details": _safe_details(details),
		}
		doc_name = inst or "UNKNOWN"
		return log_audit_event(
			event_type=event_code,
			entity=WORKS_ENTITY,
			document_type=WORKS_DOCUMENT_TYPE,
			document_name=doc_name,
			action=WORKS_EVENT_ACTIONS.get(event_code, "works_completion_event"),
			performed_by=actor,
			timestamp=ts,
			metadata=meta,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "WORKS-COMP-0900 audit emit failed")
		return None


def emit_works_output_stale_if_new(
	instance_code: str,
	stale_before: frozenset[str],
	*,
	source: str,
	performed_by: str | None = None,
	extra_details: dict[str, Any] | None = None,
) -> None:
	"""Emit ``WORKS_OUTPUT_MARKED_STALE`` when ``outputs_stale_flags`` gained logical outputs."""
	new_keys = new_stale_outputs_since(stale_before, instance_code)
	if not new_keys:
		return
	details: dict[str, Any] = {"source": source}
	if extra_details:
		details.update(extra_details)
	emit_works_completion_audit(
		WORKS_OUTPUT_MARKED_STALE,
		instance_code,
		affected_outputs=new_keys,
		details=details,
		performed_by=performed_by,
	)
