# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §10.1 — readiness: a deterministic check, not a
workflow state. A Draft may be incomplete; submission may not. Findings are
Blocking or Warning; Warnings stay visible to the approver with no
dismissal control. Every §10.1 bullet is one named check below
(TPR-AC-022, SMOKE-08)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate

from kentender_procurement.tender_preparation.services import compatibility, controls, digest, evidence, handoff_gateway, render_service, serializer
from kentender_procurement.tender_preparation.services import snapshot as snap
from kentender_procurement.tender_templates import registry

BLOCKING = "Blocking"
WARNING = "Warning"

FINDING_CODES: frozenset[str] = frozenset(
	{
		"HANDOFF_INVALID", "HANDOFF_CONSUMED_ELSEWHERE", "HANDOFF_DIGEST_CHANGED", "TEMPLATE_UNAVAILABLE", "COMPATIBILITY_FAILED",
		"CONTROL_MISSING", "DATE_ORDER", "SNAPSHOT_CHANGED", "SCHEDULE_MISMATCH", "MAPPING_INCOMPLETE", "EVIDENCE_UNLINKED",
		"FILE_INVALID", "VALUES_INCONSISTENT", "RENDER_FAILED", "RENDER_PROBLEM", "PACKAGE_DIGEST_FAILED",
		"WARN_MANUFACTURER_AUTHORISATION",
	}
)

MANUFACTURER_WARNING = "Confirm that manufacturer authorisation is proportionate for this item."


def _finding(code: str, message: str, *, severity: str = BLOCKING, task: int | None = None, field: str = "") -> dict[str, Any]:
	if code not in FINDING_CODES:
		raise ValueError(f"{code} is not a readiness finding code")
	return {"finding_code": code, "severity": severity, "task_number": task, "field_reference": field, "message": message}


# Test seam for SMOKE-08: a test may monkeypatch this to drop one mapping and
# prove readiness blocks; production never sets it.
_mapping_projection = None


def _mappings(state: dict[str, Any], snapshot: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
	evidence_ids = {r["linked_requirement_id"] for r in evidence_rows if r["linked_requirement_type"] == "Technical requirement"}
	projection = {
		"responses": {r["technical_requirement_id"] for r in serializer.supplier_response_schema(snapshot, evidence_ids)["technical"]},
		"evaluation": {r["technical_requirement_id"] for r in serializer.evaluation_contract(state, snapshot, evidence_rows)["technical_pass_fail"]},
		"contract": {r["technical_requirement_id"] for r in serializer.contract_obligations(state, snapshot)["technical"]},
	}
	if _mapping_projection:
		projection = _mapping_projection(projection)
	return projection


def run(tender, version, *, approval: dict[str, str] | None = None) -> dict[str, Any]:
	"""Every check; returns findings, counts, the renders (when they
	succeeded) and the readiness digest. Stores nothing — the caller does."""
	findings: list[dict[str, Any]] = []
	snapshot = snap.load(version)
	state = serializer.officer_state(version)
	evidence_rows = evidence.rows_as_dicts(version)

	# 1. source handoff valid, unrevoked, consumed by this Tender only
	handoff = handoff_gateway.load(tender.requisition_handoff)
	if handoff is None:
		findings.append(_finding("HANDOFF_INVALID", "The source Requisition handoff no longer exists.", task=1))
	else:
		if handoff_gateway.requisition_state(handoff) != "Authorised":
			findings.append(_finding("HANDOFF_INVALID", "The source Requisition is no longer Authorised.", task=1))
		if handoff.consumed_at and handoff.tender != tender.name:
			findings.append(_finding("HANDOFF_CONSUMED_ELSEWHERE", "The source handoff is consumed by a different Tender.", task=1))
		if not handoff.consumed_at:
			findings.append(_finding("HANDOFF_INVALID", "The source handoff is not consumed by this Tender.", task=1))
		# 2. stored Requisition Version and digests still match
		if handoff.handoff_digest != tender.handoff_digest or cstr(handoff.requisition_version) != cstr(tender.requisition_version):
			findings.append(_finding("HANDOFF_DIGEST_CHANGED", "The source Requisition Version or digest changed after this Tender bound it.", task=1))

	# 3. template available and digests match
	try:
		resolved = registry.resolve(tender.template_key, tender.template_version)
		if resolved["bundle_digest"] != tender.bundle_digest or resolved["official_source_digest"] != tender.official_source_digest:
			findings.append(_finding("TEMPLATE_UNAVAILABLE", "The installed template release no longer matches the digests this Tender bound.", task=1))
	except Exception as exc:  # TenderPreparationError
		findings.append(_finding("TEMPLATE_UNAVAILABLE", f"Template unavailable: {exc}", task=1))

	# 4. compatibility (incl. reservation category and lotting)
	for row in compatibility.evaluate(snapshot, handoff_version=snapshot.get("handoff_version") or ""):
		if not row.ok:
			findings.append(_finding("COMPATIBILITY_FAILED", f"{row.test}: required {row.required}; found {row.actual}.", task=2))

	# 5. every required officer control complete and valid
	for task, field, label in controls.missing(state):
		findings.append(_finding("CONTROL_MISSING", f"{label} is required.", task=task, field=field))

	# 6. date order
	issue = getdate(state.get("issue_date")) if state.get("issue_date") else None
	clar, sub, meet = state.get("clarification_deadline"), state.get("submission_deadline"), state.get("meeting_datetime")
	if issue and clar and get_datetime(clar).date() <= issue:
		findings.append(_finding("DATE_ORDER", "The clarification deadline must be after the issue date.", task=1, field="clarification_deadline"))
	if clar and sub and get_datetime(sub) <= get_datetime(clar):
		findings.append(_finding("DATE_ORDER", "The submission deadline must be after the clarification deadline.", task=1, field="submission_deadline"))
	if issue and sub and get_datetime(sub).date() <= issue:
		findings.append(_finding("DATE_ORDER", "The submission deadline must be after the issue date.", task=1, field="submission_deadline"))
	if state.get("pre_tender_meeting") and meet and sub and get_datetime(meet) >= get_datetime(sub):
		findings.append(_finding("DATE_ORDER", "The pre-tender meeting must be before the submission deadline.", task=1, field="meeting_datetime"))

	# 7. snapshot integrity against the handoff
	if snap.recompute_digest(snapshot) != version.snapshot_digest:
		findings.append(_finding("SNAPSHOT_CHANGED", "The inherited snapshot no longer matches its digest.", task=2))
	if handoff is not None:
		live_snapshot, live_digest = snap.build(handoff)
		if live_digest != version.snapshot_digest:
			findings.append(_finding("SNAPSHOT_CHANGED", "The inherited snapshot differs from the handoff it was copied from.", task=2))

	# 8. schedules reconcile to the inherited rows
	lines = serializer.goods_lines(snapshot)
	grouped_total = sum(float(line["quantity"]) for line in lines) if lines else 0.0
	if abs(grouped_total - snap.total_quantity(snapshot)) > 1e-6 or not lines:
		findings.append(_finding("SCHEDULE_MISMATCH", "The goods schedule does not reconcile to the inherited items.", task=3))
	price_rows = serializer.price_schedule(snapshot)["rows"]
	if len(price_rows) != len(lines) + len(snapshot.get("related_services") or []):
		findings.append(_finding("SCHEDULE_MISMATCH", "The price schedule does not reconcile to the goods and services schedules.", task=3))

	# 9. every published technical requirement has one response, one evaluation and one contract mapping
	published = {r.get("technical_requirement_id") for r in snapshot.get("technical_requirements") or []}
	mappings = _mappings(state, snapshot, evidence_rows)
	for kind, ids in mappings.items():
		for missing_id in sorted(published - ids):
			findings.append(_finding("MAPPING_INCOMPLETE", f"{missing_id} has no {kind} mapping.", task=4, field=missing_id))

	# 10. evidence rows visible and linked
	for row_id in evidence.unlinked_rows(version, snapshot):
		findings.append(_finding("EVIDENCE_UNLINKED", f"Evidence {row_id} is not linked to a visible inherited requirement.", task=4, field=row_id))

	# 11. supporting files readable, digest-verified, authorised treatment
	for material in snapshot.get("supporting_materials") or []:
		stored = frappe.db.get_value("Requisition Supporting Material", {"supporting_material_id": material.get("supporting_material_id")}, ["file_digest", "treatment"], as_dict=True)
		if not stored or cstr(stored.file_digest) != cstr(material.get("file_digest")) or cstr(stored.treatment) != cstr(material.get("treatment")):
			findings.append(_finding("FILE_INVALID", f"Supporting material {material.get('supporting_material_id')} failed its digest or treatment check.", task=2))

	# 12. security and contract values internally consistent
	if state.get("delay_damages_per_week_percent") is not None and state.get("maximum_delay_damages_percent") is not None and float(state["maximum_delay_damages_percent"]) < float(state["delay_damages_per_week_percent"]):
		findings.append(_finding("VALUES_INCONSISTENT", "Maximum delay damages cannot be less than the weekly rate.", task=5, field="maximum_delay_damages_percent"))
	if state.get("tender_security_amount") is not None and float(state["tender_security_amount"]) <= 0:
		findings.append(_finding("VALUES_INCONSISTENT", "Tender security must be a positive KES amount.", task=1, field="tender_security_amount"))

	# 13. both outputs render completely
	renders: dict[str, Any] | None = None
	if not [f for f in findings if f["finding_code"] in ("CONTROL_MISSING", "HANDOFF_INVALID", "TEMPLATE_UNAVAILABLE")]:
		try:
			renders = render_service.render(tender, version, snapshot, approval=approval)
		except Exception as exc:  # StrictUndefined or a template fault
			findings.append(_finding("RENDER_FAILED", f"The Invitation or issued Tender could not be rendered: {exc}", task=None))
		else:
			for problem in renders["problems"]:
				findings.append(_finding("RENDER_PROBLEM", problem, task=None))

	# 14. the canonical package digest can be produced
	try:
		serializer.content_digest(tender, version, snapshot)
	except Exception as exc:
		findings.append(_finding("PACKAGE_DIGEST_FAILED", f"The canonical digest could not be produced: {exc}"))

	# Warnings (visible, never dismissable)
	if state.get("manufacturer_authorisation_required"):
		findings.append(_finding("WARN_MANUFACTURER_AUTHORISATION", MANUFACTURER_WARNING, severity=WARNING, task=4, field="manufacturer_authorisation_required"))

	for order, finding in enumerate(findings, start=1):
		finding["row_order"] = order
	blocking = sum(1 for f in findings if f["severity"] == BLOCKING)
	warnings = sum(1 for f in findings if f["severity"] == WARNING)
	readiness_digest = digest.sha256_hex({"findings": findings, "content_digest": serializer.content_digest(tender, version, snapshot) if not any(f["finding_code"] == "PACKAGE_DIGEST_FAILED" for f in findings) else ""})
	return {"findings": findings, "blocking_count": blocking, "warning_count": warnings, "renders": renders, "readiness_digest": readiness_digest}


def store(version, result: dict[str, Any]) -> None:
	"""Write findings and digests onto the Version (caller bumps/saves)."""
	from frappe.utils import now_datetime

	version.set("readiness_findings", [])
	for finding in result["findings"]:
		version.append("readiness_findings", finding)
	version.readiness_digest = result["readiness_digest"]
	version.readiness_run_at = now_datetime()
	version.blocking_count = result["blocking_count"]
	version.warning_count = result["warning_count"]
	renders = result.get("renders")
	if renders:
		version.render_context_digest = renders["context_digest"]
		version.invitation_html_digest = renders["invitation_digest"]
		version.issued_tender_html_digest = renders["issued_tender_digest"]
