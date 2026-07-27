# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Immutability and lifecycle guards for BWMF DocTypes (Phase 2B)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.registry_doctypes import (
	DT_ADDENDUM_IMPACT_PLAN,
	DT_AUDIT_EVENT,
	DT_ARTIFACT_RESOURCE_BINDING,
	DT_COMPILE_ARTIFACT,
	DT_COMPILE_REQUEST,
	DT_COMPILE_RUN,
	DT_CONTENT_OBJECT,
	DT_MATERIALIZATION_REPORT,
	DT_CONFIRMATION,
	DT_DEPENDENCY_SNAPSHOT,
	DT_EVIDENCE_LINK,
	DT_EVIDENCE_VERSION,
	DT_IDEMPOTENCY_RECORD,
	DT_INVALIDATION_EVENT,
	DT_APPROVAL_DECISION,
	DT_LIFECYCLE_EVENT,
	DT_MANIFEST_APPROVAL,
	DT_MANIFEST_PUBLICATION,
	DT_MANIFEST_RESOURCE,
	DT_MANIFEST_RESOURCE_BINDING,
	DT_MANIFEST_VERSION,
	DT_PUBLICATION_REQUEST,
	DT_REVIEW_PACKAGE,
	DT_RESPONSE_VERSION,
	DT_SUBMISSION,
	DT_SUBMISSION_RECEIPT,
	DT_VALIDATION_FINDING,
	DT_VALIDATION_REPORT,
	DT_VALIDATION_SNAPSHOT,
	DT_WORKSPACE,
)
from kentender_procurement.tender_configurations.bidder_workspace_manifest.persistence.workspace_lifecycle import (
	FORBIDDEN_WORKSPACE_STATUSES,
	PREPARATORY_WORKSPACE_STATUSES,
	TRANSACTIONAL_WORKSPACE_STATUSES,
	WORKSPACE_TRANSACTION_TRANSITIONS,
	WS_CLOSED,
	assert_canonical_workspace_status,
)

# Records that must never change after insert (replacement = new row / event).
IMMUTABLE_FROM_CREATE: frozenset[str] = frozenset(
	{
		DT_RESPONSE_VERSION,
		DT_EVIDENCE_VERSION,
		DT_EVIDENCE_LINK,
		DT_CONFIRMATION,
		DT_DEPENDENCY_SNAPSHOT,
		DT_VALIDATION_SNAPSHOT,
		DT_VALIDATION_FINDING,
		DT_VALIDATION_REPORT,
		DT_MANIFEST_APPROVAL,
		DT_MANIFEST_PUBLICATION,
		DT_APPROVAL_DECISION,
		DT_MANIFEST_RESOURCE_BINDING,
		DT_LIFECYCLE_EVENT,
		DT_SUBMISSION,
		DT_SUBMISSION_RECEIPT,
		DT_AUDIT_EVENT,
		DT_IDEMPOTENCY_RECORD,  # atomic insert-on-completion; keys/fingerprint never updated
		DT_INVALIDATION_EVENT,
		DT_MANIFEST_RESOURCE,
		DT_COMPILE_ARTIFACT,
		DT_CONTENT_OBJECT,
		DT_ARTIFACT_RESOURCE_BINDING,
		DT_MATERIALIZATION_REPORT,
	}
)

# Review package: content immutable after SubmittedForApproval; state transitions allowed.
REVIEW_PACKAGE_CONTENT_FIELDS: frozenset[str] = frozenset(
	{
		"package_id",
		"package_version",
		"review_package_digest",
		"compile_artifact",
		"payload_digest",
		"target_manifest_id",
		"proposed_manifest_version",
		"published_tender_ref",
		"published_tender_version",
		"organization",
		"package_json",
	}
)
REVIEW_PACKAGE_TRANSITIONS: dict[str, frozenset[str]] = {
	"Prepared": frozenset({"SubmittedForApproval"}),
	"SubmittedForApproval": frozenset({"Approved", "Returned"}),
}
PUBLICATION_REQUEST_TRANSITIONS: dict[str, frozenset[str]] = {
	"Requested": frozenset({"Succeeded", "Failed"}),
}
PUBLICATION_REQUEST_IMMUTABLE_FIELDS: frozenset[str] = frozenset(
	{
		"request_id",
		"review_package",
		"approval_decision",
		"organization",
		"requester",
		"idempotency_key",
		"request_fingerprint",
	}
)

COMPILE_RUN_TERMINAL: frozenset[str] = frozenset({"Succeeded", "Failed", "Cancelled"})
COMPILE_RUN_TRANSITIONS: dict[str, frozenset[str]] = {
	"Queued": frozenset({"Running", "Cancelled"}),
	"Running": frozenset({"Succeeded", "Failed", "Cancelled"}),
}

MANIFEST_IMMUTABLE_CONTENT_FIELDS: frozenset[str] = frozenset(
	{
		"manifest_id",
		"manifest_version",
		"manifest_schema_version",
		"payload_digest",
		"envelope_json",
		"payload_json",
		"published_tender_ref",
		"published_tender_version",
		"organization",
	}
)
MANIFEST_LIFECYCLE_TRANSITIONS: dict[str, frozenset[str]] = {
	"Draft": frozenset({"Published"}),
	"Published": frozenset({"Superseded", "Cancelled"}),
}
MANIFEST_TERMINAL: frozenset[str] = frozenset({"Superseded", "Cancelled"})

COMPILE_RUN_IDENTITY_FIELDS: frozenset[str] = frozenset(
	{"run_id", "idempotency_key", "compile_request", "compiler_version"}
)


def _db_value(doctype: str, name: str, field: str) -> Any:
	return frappe.db.get_value(doctype, name, field)


def cstr(value: Any) -> str:
	return "" if value is None else str(value)


def cint(value: Any) -> int:
	try:
		return int(value or 0)
	except (TypeError, ValueError):
		return 0


def _child_rows_fingerprint(rows: list[Any]) -> list[dict[str, Any]]:
	out: list[dict[str, Any]] = []
	for row in rows or []:
		# Avoid row.as_dict(): frappe._dict can shadow it with a None key/value.
		name = row.get("name") if isinstance(row, dict) else getattr(row, "name", None)
		stage = row.get("stage") if isinstance(row, dict) else getattr(row, "stage", None)
		state = row.get("state") if isinstance(row, dict) else getattr(row, "state", None)
		detail = row.get("detail_json") if isinstance(row, dict) else getattr(row, "detail_json", None)
		out.append(
			{
				"name": cstr(name),
				"stage": cstr(stage),
				"state": cstr(state),
				"detail_json": cstr(detail),
			}
		)
	return out


def _enforce_compile_run(doc: Document) -> None:
	prior_state = cstr(_db_value(DT_COMPILE_RUN, doc.name, "state"))
	new_state = cstr(doc.state)

	if prior_state in COMPILE_RUN_TERMINAL:
		frappe.throw(
			_("BWMF Compile Run in terminal state {0} is immutable.").format(prior_state),
			title="BWMF_COMPILE_RUN_TERMINAL",
		)

	for field in COMPILE_RUN_IDENTITY_FIELDS:
		if cstr(getattr(doc, field, None)) != cstr(_db_value(DT_COMPILE_RUN, doc.name, field)):
			frappe.throw(
				_("Compile run identity field {0} is immutable.").format(field),
				title="BWMF_COMPILE_RUN_IDENTITY_IMMUTABLE",
			)

	if new_state != prior_state:
		allowed = COMPILE_RUN_TRANSITIONS.get(prior_state, frozenset())
		if new_state not in allowed:
			frappe.throw(
				_("Illegal compile run transition {0} -> {1}.").format(prior_state, new_state),
				title="BWMF_COMPILE_RUN_ILLEGAL_TRANSITION",
			)

	# Stage traces are append-only: existing rows may not be rewritten or removed.
	prior_rows = frappe.get_all(
		"BWMF Compile Stage Trace",
		filters={"parent": doc.name, "parenttype": DT_COMPILE_RUN},
		fields=["name", "stage", "state", "detail_json", "idx"],
		order_by="idx asc",
	)
	prior_fp = _child_rows_fingerprint(prior_rows)
	new_fp = _child_rows_fingerprint(list(doc.get("stage_trace") or []))
	if len(new_fp) < len(prior_fp):
		frappe.throw(_("Compile stage traces are append-only."), title="BWMF_STAGE_TRACE_APPEND_ONLY")
	for i, prior in enumerate(prior_fp):
		# Match by position for unnamed/new rows; when name present require equality
		cur = new_fp[i]
		if prior["name"] and cur["name"] and prior["name"] != cur["name"]:
			frappe.throw(_("Compile stage traces are append-only."), title="BWMF_STAGE_TRACE_APPEND_ONLY")
		compare_keys = ("stage", "state", "detail_json")
		if any(prior[k] != cur[k] for k in compare_keys):
			frappe.throw(
				_("Existing compile stage trace rows are immutable."),
				title="BWMF_STAGE_TRACE_APPEND_ONLY",
			)


def _enforce_manifest_version(doc: Document) -> None:
	prior_state = cstr(_db_value(DT_MANIFEST_VERSION, doc.name, "lifecycle_state"))
	new_state = cstr(doc.lifecycle_state)

	if prior_state in MANIFEST_TERMINAL:
		frappe.throw(
			_("BWMF Manifest Version in terminal state {0} is fully immutable.").format(prior_state),
			title="BWMF_MANIFEST_TERMINAL_IMMUTABLE",
		)

	for field in MANIFEST_IMMUTABLE_CONTENT_FIELDS:
		if cstr(getattr(doc, field, None)) != cstr(_db_value(DT_MANIFEST_VERSION, doc.name, field)):
			frappe.throw(
				_("Manifest content field {0} is immutable after creation.").format(field),
				title="BWMF_MANIFEST_CONTENT_IMMUTABLE",
			)

	if new_state != prior_state:
		allowed = MANIFEST_LIFECYCLE_TRANSITIONS.get(prior_state, frozenset())
		if new_state not in allowed:
			frappe.throw(
				_("Illegal manifest lifecycle transition {0} -> {1}.").format(prior_state, new_state),
				title="BWMF_MANIFEST_ILLEGAL_TRANSITION",
			)


def _enforce_workspace(doc: Document) -> None:
	# Identity fields always immutable
	for field in ("workspace_id", "organization", "bidder_party", "published_tender_ref"):
		if cstr(getattr(doc, field, None)) != cstr(_db_value(DT_WORKSPACE, doc.name, field)):
			frappe.throw(
				_("Workspace identity field {0} is immutable.").format(field),
				title="BWMF_WORKSPACE_IDENTITY_IMMUTABLE",
			)

	# Prefer canonical `status`; reject legacy `state` / Open if present on stale docs.
	prior_status = cstr(_db_value(DT_WORKSPACE, doc.name, "status") or _db_value(DT_WORKSPACE, doc.name, "state"))
	new_status = cstr(getattr(doc, "status", None) or getattr(doc, "state", None))
	prior_sub = cstr(_db_value(DT_WORKSPACE, doc.name, "active_submission"))
	new_sub = cstr(doc.active_submission)
	prior_ops = cstr(_db_value(DT_WORKSPACE, doc.name, "operational_state"))
	new_ops = cstr(getattr(doc, "operational_state", None))

	if new_status in FORBIDDEN_WORKSPACE_STATUSES or new_status == "Open":
		frappe.throw(
			_("Workspace status Open (and legacy Submitted/Closed labels) are forbidden."),
			title="BWMF_WORKSPACE_FORBIDDEN_STATUS",
		)
	assert_canonical_workspace_status(new_status)

	mode = getattr(frappe.flags, "bwmf_workspace_lifecycle_mode", None)
	service_ok = mode in {"derive", "transaction"}

	if (new_status != prior_status or new_sub != prior_sub) and not service_ok:
		frappe.throw(
			_("Workspace status/active_submission may only change via designated BWMF services."),
			title="BWMF_WORKSPACE_SERVICE_ONLY",
		)

	# operational_state may be updated only with service flag (never substitutes for status)
	if new_ops != prior_ops and not service_ok:
		frappe.throw(
			_("Workspace operational_state may only change via designated BWMF services."),
			title="BWMF_WORKSPACE_SERVICE_ONLY",
		)

	if new_status == prior_status:
		return

	if prior_status == WS_CLOSED:
		frappe.throw(_("closed workspace status is terminal."), title="BWMF_WORKSPACE_TERMINAL")

	if mode == "derive":
		if prior_status in TRANSACTIONAL_WORKSPACE_STATUSES:
			frappe.throw(
				_("Cannot refresh derived status after a transactional workspace status."),
				title="BWMF_WORKSPACE_DERIVE_FORBIDDEN",
			)
		if new_status not in PREPARATORY_WORKSPACE_STATUSES:
			frappe.throw(
				_("Derived refresh may only set preparatory workspace statuses."),
				title="BWMF_WORKSPACE_DERIVE_FORBIDDEN",
			)
		return

	if mode == "transaction":
		allowed = WORKSPACE_TRANSACTION_TRANSITIONS.get(prior_status, frozenset())
		if new_status not in allowed:
			frappe.throw(
				_("Illegal workspace transaction {0} -> {1}.").format(prior_status, new_status),
				title="BWMF_WORKSPACE_ILLEGAL_TRANSITION",
			)
		return

	frappe.throw(
		_("Illegal workspace status mutation."),
		title="BWMF_WORKSPACE_ILLEGAL_TRANSITION",
	)


def _enforce_compile_request(doc: Document) -> None:
	prior = cstr(_db_value(DT_COMPILE_REQUEST, doc.name, "status"))
	if prior in {"Accepted", "Immutable"}:
		# Identity + bindings immutable after acceptance
		for field in (
			"compile_request_id",
			"idempotency_key",
			"compile_mode",
			"target_manifest_id",
			"target_manifest_version",
			"published_tender_ref",
			"published_tender_version",
			"organization",
			"operation",
			"request_fingerprint",
			"expected_input_digests_json",
		):
			if cstr(getattr(doc, field, None)) != cstr(_db_value(DT_COMPILE_REQUEST, doc.name, field)):
				frappe.throw(
					_("Compile request is immutable after acceptance."),
					title="BWMF_COMPILE_REQUEST_IMMUTABLE",
				)
		# Child bindings: reject any mutation by comparing JSON snapshots
		prior_bindings = frappe.get_all(
			"BWMF Compile Input Binding",
			filters={"parent": doc.name},
			fields=["binding_id", "binding_type", "object_ref", "object_version", "document_content_digest"],
			order_by="idx asc",
		)
		new_bindings = [
			{
				"binding_id": cstr(r.binding_id),
				"binding_type": cstr(r.binding_type),
				"object_ref": cstr(r.object_ref),
				"object_version": cstr(r.object_version),
				"document_content_digest": cstr(r.document_content_digest),
			}
			for r in (doc.get("input_bindings") or [])
		]
		prior_norm = [
			{
				"binding_id": cstr(r.binding_id),
				"binding_type": cstr(r.binding_type),
				"object_ref": cstr(r.object_ref),
				"object_version": cstr(r.object_version),
				"document_content_digest": cstr(r.document_content_digest),
			}
			for r in prior_bindings
		]
		if json.dumps(prior_norm, sort_keys=True) != json.dumps(new_bindings, sort_keys=True):
			frappe.throw(
				_("Compile request input bindings are immutable after acceptance."),
				title="BWMF_COMPILE_REQUEST_IMMUTABLE",
			)
		if cstr(doc.status) != prior:
			frappe.throw(
				_("Accepted compile request status is terminal."),
				title="BWMF_COMPILE_REQUEST_IMMUTABLE",
			)


def _enforce_review_package(doc: Document) -> None:
	prior_state = cstr(_db_value(DT_REVIEW_PACKAGE, doc.name, "state"))
	new_state = cstr(doc.state)
	frozen = prior_state != "Prepared" or cint(_db_value(DT_REVIEW_PACKAGE, doc.name, "immutable"))
	if frozen:
		for field in REVIEW_PACKAGE_CONTENT_FIELDS:
			if cstr(getattr(doc, field, None)) != cstr(_db_value(DT_REVIEW_PACKAGE, doc.name, field)):
				frappe.throw(
					_("Review package content field {0} is immutable.").format(field),
					title="BWMF_REVIEW_IMMUTABLE",
				)
	if new_state != prior_state:
		allowed = REVIEW_PACKAGE_TRANSITIONS.get(prior_state, frozenset())
		if new_state not in allowed:
			frappe.throw(
				_("Illegal review package transition {0} -> {1}.").format(prior_state, new_state),
				title="BWMF_REVIEW_ILLEGAL_TRANSITION",
			)


def _enforce_publication_request(doc: Document) -> None:
	prior_state = cstr(_db_value(DT_PUBLICATION_REQUEST, doc.name, "state"))
	new_state = cstr(doc.state)
	for field in PUBLICATION_REQUEST_IMMUTABLE_FIELDS:
		if cstr(getattr(doc, field, None)) != cstr(_db_value(DT_PUBLICATION_REQUEST, doc.name, field)):
			frappe.throw(
				_("Publication request field {0} is immutable.").format(field),
				title="BWMF_PUBLICATION_REQUEST_IMMUTABLE",
			)
	if new_state != prior_state:
		allowed = PUBLICATION_REQUEST_TRANSITIONS.get(prior_state, frozenset())
		if new_state not in allowed:
			frappe.throw(
				_("Illegal publication request transition {0} -> {1}.").format(prior_state, new_state),
				title="BWMF_PUBLICATION_REQUEST_ILLEGAL_TRANSITION",
			)


def enforce_doctype_immutability(doc: Document) -> None:
	if doc.is_new():
		return
	doctype = doc.doctype

	if doctype == DT_COMPILE_RUN:
		_enforce_compile_run(doc)
		return

	if doctype == DT_MANIFEST_VERSION:
		_enforce_manifest_version(doc)
		return

	if doctype == DT_WORKSPACE:
		_enforce_workspace(doc)
		return

	if doctype == DT_COMPILE_REQUEST:
		_enforce_compile_request(doc)
		return

	if doctype == DT_REVIEW_PACKAGE:
		_enforce_review_package(doc)
		return

	if doctype == DT_PUBLICATION_REQUEST:
		_enforce_publication_request(doc)
		return

	if doctype in IMMUTABLE_FROM_CREATE:
		frappe.throw(
			_("{0} records are immutable after creation; create a new version or event.").format(doctype),
			title="BWMF_IMMUTABLE_FROM_CREATE",
		)

	if doctype == DT_ADDENDUM_IMPACT_PLAN:
		prior = cstr(_db_value(doctype, doc.name, "status"))
		if prior in {"Approved", "Immutable"}:
			frappe.throw(
				_("{0} in state {1} is immutable.").format(doctype, prior),
				title="BWMF_LIFECYCLE_IMMUTABLE",
			)

	# Workspace bindings: historical rows (inactive) are immutable; active may only deactivate.
	if doctype == "BWMF Workspace Manifest Binding":
		prior_active = cint(_db_value(doctype, doc.name, "is_active"))
		if not prior_active:
			frappe.throw(
				_("Historical BWMF workspace bindings are immutable."),
				title="BWMF_BINDING_IMMUTABLE",
			)
		if cstr(doc.manifest_doc) != cstr(_db_value(doctype, doc.name, "manifest_doc")):
			frappe.throw(_("Cannot rewrite workspace binding target."), title="BWMF_BINDING_IMMUTABLE")
		if not cint(doc.is_active):
			doc.active_binding_key = None
