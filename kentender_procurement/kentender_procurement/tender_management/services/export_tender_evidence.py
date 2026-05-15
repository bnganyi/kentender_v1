# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Doc 9 §13.3 — ``export_tender_evidence`` / ``exportTenderEvidence``.

Assembles a **read-only** evidence dict for audit reconstruction (doc 8 §19 TM2-SMOKE-AUD-001–004):

package lineage, tender + timeline, STD bindings, readiness + publication rows, snapshot/output refs,
clarifications/addenda, supplier participation, bid metadata/receipts/components (redacted before lawful
post-opening unless ``include_confidential`` is true), closing/opening/evaluation/contract handoff
references, full audit trail, and extracted sensitive denial events.

**Before lawful opening** (tender status not in the post-opening corridor aligned with §11.7), sealed
bid–bearing fields (bid submission components, draft ``validation_summary``, late-attempt payload
metadata) are **never** included even when ``include_confidential`` is true.

Authorization: ``AUD2_EXPORT_EVIDENCE`` on ``object_type`` **TM2 Tender**, ``object_code`` = business
``tender_code`` (see :func:`~kentender_procurement.tender_management.security.action_availability.service.get_action_availability`).

Tests: ``tender_management.tests.test_p8_02_export_tender_evidence`` (includes doc 9 §25 **EX-19** ``test_EX_19_*`` — reconstruction surface / TM2-SMOKE-AUD-002);
``tender_management.tests.test_p9_21a_evidence_export_denied_actions`` (``tender_status_in_post_opening_evidence_corridor``).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_management.security.action_availability.service import (
	get_action_availability,
)
from kentender_procurement.tender_management.security.authorization.denial_codes import DenialCode
from kentender_procurement.tender_management.services.tm2_sensitive_denial_events import (
	extract_sensitive_denial_events_from_audit_rows,
)

_ACTION = "AUD2_EXPORT_EVIDENCE"
_OBJECT_TYPE = "TM2 Tender"

# Align with ``get_bid_content._POST_OPENING_TM2_STATUSES`` — post-opening corridor for §13.3 / §11.7.
_POST_OPENING_STATUSES: frozenset[str] = frozenset(
	{
		"Opening Completed",
		"Evaluation Ready",
		"Evaluation In Progress",
		"Awarded",
		"Contract Handoff Completed",
	}
)


def tender_status_in_post_opening_evidence_corridor(tender_status: str) -> bool:
	"""True when §13.3 may honor ``include_confidential`` for sealed bid bodies (same set as ``export_tender_evidence``)."""
	return cstr(tender_status or "").strip() in _POST_OPENING_STATUSES

# Doc 9 §13.3 — stable top-level keys for API/tests (subset of full export).
EVIDENCE_EXPORT_SECTION_KEYS: tuple[str, ...] = (
	"package_lineage",
	"tender_lifecycle",
	"std_binding",
	"readiness_records",
	"publication_records",
	"publication_snapshots",
	"std_output_refs",
	"clarification_history",
	"addendum_history",
	"supplier_participation",
	"bid_submissions",
	"bid_receipts",
	"bid_submission_components",
	"bid_draft_metadata",
	"late_submission_attempts",
	"tender_access_rules",
	"tender_closing_record",
	"opening_readiness_record",
	"evaluation_handoff_record",
	"contract_handoff_reference",
	"audit_trail",
	"sensitive_denial_events",
)


def _resolve_tm2_name(tender_code: str) -> str | None:
	tc = cstr(tender_code).strip()
	if not tc:
		return None
	name = frappe.db.get_value("TM2 Tender", {"tender_code": tc}, "name")
	if name and frappe.db.exists("TM2 Tender", name):
		return str(name)
	if frappe.db.exists("TM2 Tender", tc):
		return str(tc)
	return None


def _deny(denial_code: str, message: str) -> dict[str, Any]:
	return {"ok": False, "denial_code": cstr(denial_code).strip(), "message": _(message)}


def _row_as_dict(doctype: str, name: str) -> dict[str, Any]:
	if not name or not frappe.db.exists(doctype, name):
		return {}
	doc = frappe.get_doc(doctype, name)
	return doc.as_dict(no_nulls=True)


def _get_all_dicts(doctype: str, filters: dict[str, Any], *, order_by: str = "modified asc") -> list[dict[str, Any]]:
	rows = frappe.get_all(doctype, filters=filters, fields=["name"], order_by=order_by, pluck="name")
	out: list[dict[str, Any]] = []
	for n in rows:
		d = _row_as_dict(doctype, str(n))
		if d:
			out.append(d)
	return out


def _active_binding(tm2_name: str) -> dict[str, Any] | None:
	row = frappe.db.get_value(
		"TM2 Tender STD Binding",
		{"tm2_tender": tm2_name, "is_active": 1},
		"name",
	)
	if not row:
		return None
	return _row_as_dict("TM2 Tender STD Binding", str(row))


def _collect_publication_snapshot_summaries(
	tm2_name: str, bindings: list[dict[str, Any]], pub_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
	seen: set[str] = set()
	out: list[dict[str, Any]] = []

	def _add(src: str, snap: str | None, extras: dict[str, Any] | None = None) -> None:
		code = cstr(snap or "").strip()
		if not code or code in seen:
			return
		seen.add(code)
		item: dict[str, Any] = {"publication_snapshot_code": code, "source": src}
		if extras:
			item.update(extras)
		out.append(item)

	for b in bindings:
		_add(
			"std_binding",
			str(b.get("publication_snapshot_code") or ""),
			{
				"binding_code": b.get("binding_code"),
				"bundle_output_code": b.get("bundle_output_code"),
				"dsm_output_code": b.get("dsm_output_code"),
				"dom_output_code": b.get("dom_output_code"),
				"dem_output_code": b.get("dem_output_code"),
				"dcm_output_code": b.get("dcm_output_code"),
			},
		)
	for p in pub_records:
		_add(
			"publication_record",
			str(p.get("publication_snapshot_code") or ""),
			{
				"publication_code": p.get("publication_code"),
				"bundle_output_code": p.get("bundle_output_code"),
				"dsm_output_code": p.get("dsm_output_code"),
				"dom_output_code": p.get("dom_output_code"),
				"dem_output_code": p.get("dem_output_code"),
				"dcm_output_code": p.get("dcm_output_code"),
			},
		)
	for ev in frappe.get_all(
		"TM2 Tender Audit Event",
		filters={"tm2_tender": tm2_name},
		fields=["name", "event_payload", "publication_snapshot_code"],
	):
		pl = ev.get("event_payload")
		if isinstance(pl, dict):
			_add("audit_payload", cstr(pl.get("publication_snapshot_code") or "").strip() or None)
		_add("audit_row", cstr(ev.get("publication_snapshot_code") or "").strip() or None)

	return out


def _redact_bid_component_row(row: dict[str, Any]) -> dict[str, Any]:
	return {
		"name": row.get("name"),
		"bsc_code": row.get("bsc_code"),
		"bid_code": row.get("bid_code"),
		"tm2_bid_submission": row.get("tm2_bid_submission"),
		"component_type": row.get("component_type"),
		"component_label": row.get("component_label"),
		"std_submission_requirement_code": row.get("std_submission_requirement_code"),
		"required": row.get("required"),
		"submitted": row.get("submitted"),
		"validation_status": row.get("validation_status"),
		"sealed_bid_fields_redacted": True,
	}


def _redact_draft_row(row: dict[str, Any]) -> dict[str, Any]:
	d = dict(row)
	d.pop("validation_summary", None)
	d["sealed_bid_fields_redacted"] = True
	return d


def _redact_late_attempt_row(row: dict[str, Any]) -> dict[str, Any]:
	d = dict(row)
	d.pop("attempted_payload_metadata", None)
	d["sealed_bid_fields_redacted"] = True
	return d


def export_tender_evidence(
	actor: str,
	tender_code: str,
	include_confidential: bool = False,
	*,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""Build the §13.3 evidence export dict for ``tender_code`` (TM2 business code)."""
	ctx = dict(context or {})
	tc = cstr(tender_code).strip()
	if not tc:
		return _deny(DenialCode.STD_AUTH_PERMISSION_DENIED.value, _("Tender code is required."))

	tm2_name = _resolve_tm2_name(tc)
	if not tm2_name:
		return _deny(
			DenialCode.STD_AUTH_OBJECT_SCOPE_DENIED.value,
			_("TM2 Tender {0} was not found.").format(tc),
		)

	avail = get_action_availability(_ACTION, _OBJECT_TYPE, tc, actor, context=ctx)
	if not avail.get("allowed"):
		return {
			"ok": False,
			"denial_code": cstr(avail.get("denial_code") or DenialCode.STD_AUTH_PERMISSION_DENIED.value).strip(),
			"message": cstr(avail.get("user_message") or avail.get("message") or _("Export not allowed.")).strip(),
			"action_availability": avail,
		}

	tm2 = frappe.get_doc("TM2 Tender", tm2_name)
	status = cstr(tm2.status).strip()
	post_opening = status in _POST_OPENING_STATUSES
	allow_sealed_bodies = post_opening and bool(include_confidential)

	pkg_lineage: dict[str, Any] = {}
	pkg_name = cstr(tm2.get("procurement_package") or "").strip()
	if pkg_name and frappe.db.exists("Procurement Package", pkg_name):
		pkg = _row_as_dict("Procurement Package", pkg_name)
		pkg_lineage["procurement_package"] = {
			"name": pkg.get("name"),
			"package_code": pkg.get("package_code"),
			"package_name": pkg.get("package_name"),
			"status": pkg.get("status"),
			"procurement_plan": pkg.get("plan_id") or pkg.get("procurement_plan"),
		}
	plan_name = cstr(tm2.get("procurement_plan") or "").strip()
	if plan_name and frappe.db.exists("Procurement Plan", plan_name):
		pl = _row_as_dict("Procurement Plan", plan_name)
		pkg_lineage["procurement_plan"] = {
			"name": pl.get("name"),
			"plan_code": pl.get("plan_code") or pl.get("name"),
			"status": pl.get("status"),
		}
	pkg_lineage["tm2_lineage_fields"] = {
		"retender_of_tender_code": tm2.get("retender_of_tender_code"),
		"supersedes_tender_code": tm2.get("supersedes_tender_code"),
		"procurement_package_code": tm2.get("procurement_package_code"),
		"procurement_plan_code": tm2.get("procurement_plan_code"),
	}

	timeline_name = frappe.db.get_value("TM2 Tender Timeline", {"tm2_tender": tm2_name}, "name")
	timeline = _row_as_dict("TM2 Tender Timeline", str(timeline_name)) if timeline_name else {}

	tm2_lifecycle = tm2.as_dict(no_nulls=True)

	bindings = _get_all_dicts("TM2 Tender STD Binding", {"tm2_tender": tm2_name}, order_by="creation asc")
	active = _active_binding(tm2_name)

	readiness = _get_all_dicts("TM2 Publication Readiness", {"tm2_tender": tm2_name}, order_by="creation asc")
	pub_records = _get_all_dicts("TM2 Publication Record", {"tm2_tender": tm2_name}, order_by="creation asc")
	snapshots = _collect_publication_snapshot_summaries(tm2_name, bindings, pub_records)

	std_output_refs: dict[str, Any] = {}
	if active:
		std_output_refs = {
			"binding_code": active.get("binding_code"),
			"std_template_code": active.get("std_template_code"),
			"std_template_version_code": active.get("std_template_version_code"),
			"std_applicability_profile_code": active.get("std_applicability_profile_code"),
			"tender_std_instance_code": active.get("tender_std_instance_code"),
			"bundle_output_code": active.get("bundle_output_code"),
			"dsm_output_code": active.get("dsm_output_code"),
			"dom_output_code": active.get("dom_output_code"),
			"dem_output_code": active.get("dem_output_code"),
			"dcm_output_code": active.get("dcm_output_code"),
			"publication_snapshot_code": active.get("publication_snapshot_code"),
			"published_snapshot_hash": active.get("published_snapshot_hash"),
		}

	cl_req = _get_all_dicts("TM2 Clarification Request", {"tm2_tender": tm2_name}, order_by="creation asc")
	cl_resp = _get_all_dicts("TM2 Clarification Response", {"tm2_tender": tm2_name}, order_by="creation asc")
	addenda = _get_all_dicts("TM2 Addendum", {"tm2_tender": tm2_name}, order_by="creation asc")

	participation = _get_all_dicts("TM2 Supplier Participation", {"tm2_tender": tm2_name}, order_by="creation asc")
	access_rules = _get_all_dicts("TM2 Tender Access Rule", {"tm2_tender": tm2_name}, order_by="creation asc")

	bids = _get_all_dicts("TM2 Bid Submission", {"tm2_tender": tm2_name}, order_by="creation asc")
	receipts = _get_all_dicts("TM2 Bid Receipt", {"tm2_tender": tm2_name}, order_by="creation asc")

	components_raw: list[dict[str, Any]] = []
	for b in bids:
		bn = cstr(b.get("name") or "").strip()
		if not bn:
			continue
		components_raw.extend(
			_get_all_dicts("TM2 Bid Submission Component", {"tm2_bid_submission": bn}, order_by="creation asc")
		)

	if allow_sealed_bodies:
		components_out = components_raw
	else:
		components_out = [_redact_bid_component_row(r) for r in components_raw]

	drafts_raw = _get_all_dicts("TM2 Bid Draft Metadata", {"tm2_tender": tm2_name}, order_by="creation asc")
	if allow_sealed_bodies:
		drafts_out = drafts_raw
	else:
		drafts_out = [_redact_draft_row(r) for r in drafts_raw]

	late_raw = _get_all_dicts("TM2 Late Submission Attempt", {"tm2_tender": tm2_name}, order_by="creation asc")
	if allow_sealed_bodies:
		late_out = late_raw
	else:
		late_out = [_redact_late_attempt_row(r) for r in late_raw]

	def _single_optional(doctype: str, filters: dict[str, Any]) -> dict[str, Any] | None:
		name = frappe.db.get_value(doctype, filters, "name")
		if not name:
			return None
		return _row_as_dict(doctype, str(name))

	closing = _single_optional("TM2 Tender Closing Record", {"tm2_tender": tm2_name})
	orr = _single_optional("TM2 Opening Readiness Record", {"tm2_tender": tm2_name})
	ehr = _single_optional("TM2 Evaluation Handoff Record", {"tm2_tender": tm2_name})
	chr_ = _single_optional("TM2 Contract Handoff Reference", {"tm2_tender": tm2_name})

	audit_rows = frappe.get_all(
		"TM2 Tender Audit Event",
		filters={"tm2_tender": tm2_name},
		fields=["name"],
		order_by="occurred_at asc, creation asc",
		pluck="name",
	)
	audit_trail = [_row_as_dict("TM2 Tender Audit Event", str(n)) for n in audit_rows]

	sensitive = extract_sensitive_denial_events_from_audit_rows(audit_trail)

	return {
		"ok": True,
		"actor": cstr(actor).strip(),
		"tender_code": tc,
		"tm2_tender": tm2_name,
		"export_generated_at": now_datetime(),
		"package_lineage": pkg_lineage,
		"tender_lifecycle": {"tm2_tender": tm2_lifecycle, "tm2_tender_timeline": timeline},
		"std_binding": {"active": active, "all_bindings": bindings},
		"readiness_records": readiness,
		"publication_records": pub_records,
		"publication_snapshots": snapshots,
		"std_output_refs": std_output_refs,
		"clarification_history": {"requests": cl_req, "responses": cl_resp},
		"addendum_history": addenda,
		"supplier_participation": participation,
		"tender_access_rules": access_rules,
		"bid_submissions": bids,
		"bid_receipts": receipts,
		"bid_submission_components": components_out,
		"bid_draft_metadata": drafts_out,
		"late_submission_attempts": late_out,
		"tender_closing_record": closing,
		"opening_readiness_record": orr,
		"evaluation_handoff_record": ehr,
		"contract_handoff_reference": chr_,
		"audit_trail": audit_trail,
		"sensitive_denial_events": sensitive,
		"export_flags": {
			"tender_status": status,
			"post_opening_corridor": post_opening,
			"include_confidential_requested": bool(include_confidential),
			"sealed_bid_content_included": allow_sealed_bodies,
		},
	}


def exportTenderEvidence(
	actor: str,
	tender_code: str,
	include_confidential: bool = False,
	*,
	context: dict[str, Any] | None = None,
) -> dict[str, Any]:
	"""CamelCase alias for :func:`export_tender_evidence`."""
	return export_tender_evidence(actor, tender_code, include_confidential, context=context)
