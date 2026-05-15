# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0300 — ``ApprovalReviewPackageService`` (read-only approver package).

Cursor pack §8 / std engine §8: ``getApprovalReviewPackage`` must bind to the **current Final
Configuration snapshot** (not live mutable draft). Structured sections 1–14; no mutation API.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.attachment import section_attachments_snapshot
from kentender_procurement.tender_management.std_instance.parameter import parameter_values_snapshot
from kentender_procurement.tender_management.std_instance.snapshot import _compute_boq_hash, _sha256_json
from kentender_procurement.tender_management.std_instance.works_requirement import works_requirements_snapshot
from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_TENDER_PUBLICATION_APPROVAL_REVIEW_OPENED,
)
from kentender_procurement.tender_management.tender_publication.audit.publication_audit import (
	emit_publication_audit_event,
)
from kentender_procurement.tender_management.tender_publication.readiness.schema import (
	is_critical_code,
	is_warning_code,
)
from kentender_procurement.tender_management.services.tm2_tender_resolve import (
	canonical_tm2_tender_code,
	resolve_tm2_tender_document,
)
from kentender_procurement.tender_management.tender_publication.snapshot.configuration_snapshot import (
	ConfigurationSnapshotService,
)

# Stable denial when no Final Configuration snapshot exists for the tender.
APPROVAL_REVIEW_CONFIGURATION_SNAPSHOT_REQUIRED = "APPROVAL_REVIEW_CONFIGURATION_SNAPSHOT_REQUIRED"


def _strip(value: str | None) -> str:
	return (value or "").strip()


def _peek_content_headline(content_json: Any) -> str:
	if isinstance(content_json, str):
		content_json = frappe.parse_json(content_json) if content_json.strip() else {}
	if not isinstance(content_json, dict):
		return ""
	for k in ("title", "bundle_title", "heading", "name", "document_title"):
		v = content_json.get(k)
		if isinstance(v, str) and v.strip():
			return v.strip()[:240]
	return ""


def _output_summary_for_snapshot(
	snap: Document,
	output_code: str | None,
	output_label: str,
) -> dict[str, Any]:
	code = _strip(output_code)
	if not code:
		return {
			"output_label": output_label,
			"available": False,
			"message": _("No output reference on configuration snapshot."),
		}
	if not frappe.db.exists("Tender STD Generated Output", code):
		return {
			"output_label": output_label,
			"reference": code,
			"available": False,
			"message": _("Referenced output document is missing."),
		}
	row = frappe.get_doc("Tender STD Generated Output", code)
	if _strip(row.tender_std_instance) != _strip(snap.tender_std_instance):
		return {
			"output_label": output_label,
			"reference": code,
			"available": False,
			"message": _("Referenced output does not belong to the snapshot STD instance."),
		}
	cj: Any = row.content_json
	return {
		"output_label": output_label,
		"available": True,
		"reference": code,
		"output_type": _strip(row.output_type),
		"output_status": _strip(row.output_status),
		"version_number": int(row.version_number or 0),
		"headline": _peek_content_headline(cj),
		"rendered_file_reference": _strip(row.rendered_file_reference),
		"published_at": str(row.published_at) if row.published_at else None,
	}


def _parse_readiness_summary(raw: str | None) -> dict[str, Any] | None:
	s = _strip(raw)
	if not s:
		return None
	try:
		obj = json.loads(s)
	except Exception:
		return None
	return obj if isinstance(obj, dict) else None


def _integrity_vs_instance(instance_name: str, snap: Document) -> dict[str, Any]:
	inst = frappe.get_doc("Tender STD Instance", instance_name)
	ph = _sha256_json(parameter_values_snapshot(inst))
	wh = _sha256_json(works_requirements_snapshot(inst))
	ah = _sha256_json(section_attachments_snapshot(inst))
	bh = _compute_boq_hash(instance_name)
	return {
		"parameter_values_match_snapshot": ph == _strip(snap.parameter_values_hash),
		"works_requirements_match_snapshot": wh == _strip(snap.works_requirements_hash),
		"attachments_match_snapshot": ah == _strip(snap.attachments_hash),
		"boq_match_snapshot": bh == _strip(snap.boq_hash),
	}


def _section_14_approval_actions(tender_key: str) -> dict[str, Any]:
	tk = _strip(tender_key)
	tm2 = resolve_tm2_tender_document(tk)
	if not tm2:
		return {
			"actions": [
				{
					"code": "APPROVE_FOR_PUBLICATION",
					"label": _("Approve for Publication"),
					"available": False,
				},
			]
		}
	filters: dict[str, str] = {"tm2_tender": tm2.name}
	latest_rows = frappe.get_all(
		"Tender Publication Approval Decision",
		filters=filters,
		pluck="decision",
		order_by="decided_at desc",
		limit=1,
	)
	approved = bool(latest_rows and (latest_rows[0] or "").strip() == "Approved for Publication")
	return {
		"actions": [
			{
				"code": "APPROVE_FOR_PUBLICATION",
				"label": _("Approve for Publication"),
				"available": not approved,
			},
			{
				"code": "RETURN_FOR_CORRECTION",
				"label": _("Return for Correction"),
				"available": not approved,
			},
			{
				"code": "REJECT_PUBLICATION",
				"label": _("Reject Publication"),
				"available": not approved,
			},
			{
				"code": "REQUEST_CLARIFICATION",
				"label": _("Request Clarification"),
				"available": not approved,
			},
		],
		"latest_decision": (latest_rows[0] if latest_rows else None),
		"note": _(
			"When the latest decision is Approved for Publication, further desk actions are disabled until a new approval cycle."
		),
	}


def _recent_std_audit_rows(instance_name: str, *, limit: int = 25) -> list[dict[str, Any]]:
	try:
		rows = frappe.db.sql(
			"""
			select event_type, action, performed_by, timestamp
			from `tabAudit Event`
			where document_type = 'Tender STD Instance'
				and document_name = %s
			order by timestamp desc
			limit %s
			""",
			(instance_name, int(limit)),
			as_dict=True,
		)
	except Exception:
		return []
	out: list[dict[str, Any]] = []
	for r in rows or []:
		out.append(
			{
				"event_type": (r.get("event_type") or "").strip(),
				"action": (r.get("action") or "").strip(),
				"performed_by": (r.get("performed_by") or "").strip(),
				"timestamp": str(r.get("timestamp") or ""),
			}
		)
	return out


class ApprovalReviewPackageService:
	"""Read-only approval review payload (PUB-0300)."""

	@staticmethod
	def getApprovalReviewPackage(tender_code: str, actor: str | None = None) -> dict[str, Any]:
		"""Build sections 1–14 from the current **Final** Configuration snapshot for ``tender_code``."""
		tc = _strip(tender_code)
		if not tc:
			frappe.throw(_("Tender code is required."), exc=frappe.ValidationError)
		tm2 = resolve_tm2_tender_document(tc)
		if not tm2:
			frappe.throw(
				_("TM2 Tender {0} does not exist.").format(tc),
				frappe.DoesNotExistError,
			)
		canon = canonical_tm2_tender_code(tm2)

		cur = ConfigurationSnapshotService.getCurrentConfigurationSnapshot(tc)
		if not cur:
			frappe.throw(
				_("A Final configuration snapshot is required before opening the approval review package."),
				title=APPROVAL_REVIEW_CONFIGURATION_SNAPSHOT_REQUIRED,
				exc=frappe.ValidationError,
			)

		snap = frappe.get_doc("Tender STD Instance Snapshot", cur["snapshot_code"])
		if (snap.snapshot_type or "").strip() != "Configuration" or (snap.snapshot_status or "").strip() != "Final":
			frappe.throw(
				_("Current configuration snapshot is not in a reviewable state."),
				title=APPROVAL_REVIEW_CONFIGURATION_SNAPSHOT_REQUIRED,
				exc=frappe.ValidationError,
			)

		tender = tm2
		inst = frappe.get_doc("Tender STD Instance", snap.tender_std_instance)
		integrity = _integrity_vs_instance(inst.name, snap)

		readiness_at_snapshot = _parse_readiness_summary(getattr(snap, "readiness_summary_json", None))
		findings = list((readiness_at_snapshot or {}).get("findings") or [])
		critical_codes = [str((f.get("code") or "").strip()) for f in findings if is_critical_code((f.get("code") or "").strip())]
		warning_codes = [str((f.get("code") or "").strip()) for f in findings if is_warning_code((f.get("code") or "").strip())]

		pkg_ref = _strip(tender.get("procurement_package"))
		pkg_row: dict[str, Any] = {}
		if pkg_ref and frappe.db.exists("Procurement Package", pkg_ref):
			pkg_row = frappe.db.get_value(
				"Procurement Package",
				pkg_ref,
				("name", "package_name", "status"),
				as_dict=True,
			) or {}

		sections: dict[str, Any] = {
			"1_tender_summary": {
				"tender_title": _strip(tender.get("tender_title")),
				"tender_reference": _strip(tender.get("tender_reference")),
				"tender_status": _strip(tender.get("status")),
				"source_package_code": _strip(tender.get("source_package_code")),
			},
			"2_procurement_package": {
				"package_code": pkg_ref,
				"package_name": _strip((pkg_row or {}).get("package_name")),
				"package_status": _strip((pkg_row or {}).get("status")),
			},
			"3_std_template_profile": {
				"snapshot_template_version_code": _strip(snap.source_template_version_code),
				"instance_template_version_code": _strip(inst.template_version_code),
				"applicability_profile_code": _strip(inst.applicability_profile_code),
				"procurement_category": _strip(inst.procurement_category),
				"instance_status": _strip(inst.instance_status),
			},
			"4_readiness_result": readiness_at_snapshot
			or {
				"note": _("Readiness summary was not stored on this configuration snapshot row."),
				"snapshot_code": snap.name,
			},
			"5_bundle": _output_summary_for_snapshot(snap, snap.ref_bundle_output, "Bundle"),
			"6_dsm": _output_summary_for_snapshot(snap, snap.ref_dsm_output, "DSM"),
			"7_dom": _output_summary_for_snapshot(snap, snap.ref_dom_output, "DOM"),
			"8_dem": _output_summary_for_snapshot(snap, snap.ref_dem_output, "DEM"),
			"9_dcm": _output_summary_for_snapshot(snap, snap.ref_dcm_output, "DCM"),
			"10_boq": {
				"snapshot_boq_hash": _strip(snap.boq_hash),
				"boq_matches_snapshot": integrity.get("boq_match_snapshot"),
			},
			"11_works_spec_drawings": {
				"snapshot_works_requirements_hash": _strip(snap.works_requirements_hash),
				"snapshot_attachments_hash": _strip(snap.attachments_hash),
				"works_requirements_match_snapshot": integrity.get("works_requirements_match_snapshot"),
				"attachments_match_snapshot": integrity.get("attachments_match_snapshot"),
				"parameter_values_match_snapshot": integrity.get("parameter_values_match_snapshot"),
			},
			"12_blockers_and_warnings": {
				"critical_finding_codes": critical_codes,
				"warning_finding_codes": warning_codes,
				"readiness_status_at_snapshot": (readiness_at_snapshot or {}).get("status"),
			},
			"13_audit_evidence_summary": {
				"recent_std_instance_events": _recent_std_audit_rows(inst.name),
			},
			"14_available_approval_actions": _section_14_approval_actions(tc),
		}

		act_log = _strip(actor) or frappe.session.user
		emit_publication_audit_event(
			event_type=AUDIT_TENDER_PUBLICATION_APPROVAL_REVIEW_OPENED,
			tender_code=canon,
			action="approval_review_package_opened",
			performed_by=act_log,
			instance_code=inst.name,
			configuration_snapshot_code=snap.name,
			details={"read_only": True},
		)

		return {
			"tender_code": canon,
			"actor": _strip(actor),
			"read_only": True,
			"configuration_snapshot_code": snap.name,
			"configuration_snapshot_status": _strip(snap.snapshot_status),
			"snapshot_created_at": str(snap.created_at) if snap.created_at else None,
			"sections": sections,
		}
