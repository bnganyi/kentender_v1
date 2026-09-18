# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §5.4 — the review result (plan D17): a deterministic
projection, not a workflow state. A Draft may be incomplete; submission,
approval and publication authorisation may not. Findings are **Must fix**
(prevents the decision and links to the exact task/field/owner route) or
**Review note** (visible through every later decision, never dismissed).
The result verifies the source handoff, template release, the eight
compatibility checks, officer fields, dates, inherited completeness,
grouping lineage, schedules, response schema, evaluation/contract
mappings, file treatments, security/contract values, both renders and the
package digest (TPR08-AC-026..028)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate

from kentender_procurement.tenders.services import compatibility, controls, digest, evidence, handoff_gateway, render_service, serializer, template_binding
from kentender_procurement.tenders.services import snapshot as snap

MUST_FIX = "Must fix"
REVIEW_NOTE = "Review note"
READY = "Ready to submit"
NEEDS_ATTENTION = "Needs attention"

FINDING_CODES: frozenset[str] = frozenset(
	{
		"HANDOFF_INVALID", "HANDOFF_CONSUMED_ELSEWHERE", "HANDOFF_DIGEST_CHANGED", "TEMPLATE_UNAVAILABLE", "COMPATIBILITY_FAILED",
		"CONTROL_MISSING", "DATE_ORDER", "SNAPSHOT_CHANGED", "SCHEDULE_MISMATCH", "MAPPING_INCOMPLETE", "EVIDENCE_UNLINKED",
		"FILE_INVALID", "VALUES_INCONSISTENT", "RENDER_FAILED", "RENDER_PROBLEM", "PACKAGE_DIGEST_FAILED",
		"NOTE_MANUFACTURER_AUTHORISATION",
	}
)
MANUFACTURER_NOTE = "Confirm that manufacturer authorisation is proportionate for this purchase."
TASK_ROUTE_LABELS = {controls.TASK_DETAILS: "Review Tender details", controls.TASK_REQUIREMENTS: "Review supplier requirements", "contract": "Review contract terms", controls.TASK_REVIEW: "Review and generated documents"}


def _finding(code: str, message: str, *, severity: str = MUST_FIX, task: str = "", field: str = "", link_label: str = "") -> dict[str, Any]:
	if code not in FINDING_CODES:
		raise ValueError(f"{code} is not a review finding code")
	route = f"{task}#{field}" if task and field else (task or "")
	if not link_label:
		group = controls.CATALOGUE.get(field, {}).get("group") if field else ""
		link_label = TASK_ROUTE_LABELS.get("contract" if group == "contract" else task, "") if task else ""
	return {"finding_code": code, "severity": severity, "message": message, "task": task, "field": field, "route": route, "link_label": link_label}


def _missing_message(field: str, label: str) -> str:
	spec = controls.CATALOGUE[field]
	if spec["type"] in (controls.BOOL, controls.SELECT):
		return f"Choose {label[0].lower() + label[1:]}."
	return f"Enter the {label[0].lower() + label[1:]}."


# Test seam: a test may monkeypatch this to drop one mapping and prove the
# review blocks; production never sets it.
_mapping_projection = None


def _mappings(state: dict[str, Any], snapshot: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, set[str]]:
	projection = {
		"supplier response": {r["technical_requirement_id"] for r in serializer.supplier_response_schema(snapshot, evidence_rows)["technical"]},
		"evaluation": {r["technical_requirement_id"] for r in serializer.evaluation_contract(state, snapshot, evidence_rows)["technical_pass_fail"]},
		"contract": {r["technical_requirement_id"] for r in serializer.contract_obligations(state, snapshot)["technical"]},
	}
	if _mapping_projection:
		projection = _mapping_projection(projection)
	return projection


def run(tender, version, *, approval: dict[str, str] | None = None, with_renders: bool = True) -> dict[str, Any]:
	"""Every §5.4 check; returns findings, counts, the renders (when they
	succeeded) and the review-result digest. Stores nothing — the caller does."""
	findings: list[dict[str, Any]] = []
	snapshot = snap.load(version)
	state = serializer.officer_state(version)
	evidence_rows = evidence.rows_as_dicts(version)

	# 1. source handoff valid, Authorised, consumed by this Tender only
	handoff = handoff_gateway.load(version.requisition_handoff)
	if handoff is None:
		findings.append(_finding("HANDOFF_INVALID", "The authorised requisition is no longer available to this Tender.", task=controls.TASK_DETAILS))
	else:
		if handoff_gateway.requisition_state(handoff) != "Authorised":
			findings.append(_finding("HANDOFF_INVALID", "The source Requisition is no longer Authorised.", task=controls.TASK_DETAILS))
		if handoff.consumed_at and cstr(handoff.tender) != cstr(tender.name):
			findings.append(_finding("HANDOFF_CONSUMED_ELSEWHERE", "The authorised requisition is consumed by a different Tender.", task=controls.TASK_DETAILS))
		if not handoff.consumed_at:
			findings.append(_finding("HANDOFF_INVALID", "The authorised requisition is not consumed by this Tender.", task=controls.TASK_DETAILS))
		if cstr(handoff.handoff_digest) != cstr(snapshot.get("handoff_digest")) or cstr(handoff.requisition_version) != cstr(version.requisition_version):
			findings.append(_finding("HANDOFF_DIGEST_CHANGED", "The source Requisition Version or digest changed after this Tender bound it.", task=controls.TASK_DETAILS))

	# 2. template available and digests match
	for problem in template_binding.verify(version):
		findings.append(_finding("TEMPLATE_UNAVAILABLE", problem, task=controls.TASK_DETAILS))

	# 3. the eight compatibility checks
	for check in compatibility.evaluate(snapshot):
		if not check.ok:
			findings.append(_finding("COMPATIBILITY_FAILED", f"{check.check}: required {check.required}; found {check.actual}.", task=controls.TASK_DETAILS))

	# 4. every applicable officer control complete
	for task, field, label in controls.missing(state):
		findings.append(_finding("CONTROL_MISSING", _missing_message(field, label), task=task, field=field))

	# 5. date order (§5.2)
	issue = getdate(state.get("issue_date")) if state.get("issue_date") else None
	clar, sub, meet = state.get("clarification_deadline"), state.get("submission_deadline"), state.get("meeting_datetime")
	if issue and clar and get_datetime(clar).date() <= issue:
		findings.append(_finding("DATE_ORDER", "The clarification deadline must be after the issue date.", task=controls.TASK_DETAILS, field="clarification_deadline"))
	if clar and sub and get_datetime(sub) <= get_datetime(clar):
		findings.append(_finding("DATE_ORDER", "The submission deadline must be after the clarification deadline.", task=controls.TASK_DETAILS, field="submission_deadline"))
	if issue and sub and get_datetime(sub).date() <= issue:
		findings.append(_finding("DATE_ORDER", "The submission deadline must be after the issue date.", task=controls.TASK_DETAILS, field="submission_deadline"))
	if state.get("pre_tender_meeting") and meet and sub and get_datetime(meet) >= get_datetime(sub):
		findings.append(_finding("DATE_ORDER", "The pre-tender meeting must be before the submission deadline.", task=controls.TASK_DETAILS, field="meeting_datetime"))

	# 6. snapshot integrity
	if snap.recompute_digest(snapshot) != version.requisition_snapshot_digest:
		findings.append(_finding("SNAPSHOT_CHANGED", "The inherited snapshot no longer matches its digest.", task=controls.TASK_DETAILS))
	if handoff is not None:
		_live, live_digest = snap.build(handoff)
		if live_digest != version.requisition_snapshot_digest:
			findings.append(_finding("SNAPSHOT_CHANGED", "The inherited snapshot differs from the handoff it was copied from.", task=controls.TASK_DETAILS))

	# 7. schedules reconcile to the inherited rows (grouping lineage)
	lines = serializer.goods_lines(snapshot)
	grouped_total = sum(float(line["quantity"]) for line in lines) if lines else 0.0
	if abs(grouped_total - snap.total_quantity(snapshot)) > 1e-6 or not lines:
		findings.append(_finding("SCHEDULE_MISMATCH", "The goods schedule does not reconcile to the inherited items.", task=controls.TASK_REVIEW))
	if len(serializer.price_schedule(snapshot)["rows"]) != len(lines) + len(snapshot.get("related_services") or []):
		findings.append(_finding("SCHEDULE_MISMATCH", "The price schedule does not reconcile to the goods and services schedules.", task=controls.TASK_REVIEW))

	# 8. every published technical requirement has one response, evaluation and contract mapping
	published = {r.get("technical_requirement_id") for r in snapshot.get("technical_requirements") or []}
	for kind, ids in _mappings(state, snapshot, evidence_rows).items():
		for missing_id in sorted(published - ids):
			findings.append(_finding("MAPPING_INCOMPLETE", f"{missing_id} has no {kind} mapping.", task=controls.TASK_REVIEW, field=missing_id))

	# 9. evidence rows prove a published requirement
	for row_id in evidence.unlinked_rows(evidence_rows, snapshot):
		findings.append(_finding("EVIDENCE_UNLINKED", f"Evidence {row_id} does not prove a published requirement.", task=controls.TASK_REQUIREMENTS, field=row_id))

	# 10. supporting files readable, digest-verified, authorised treatment
	for material in snapshot.get("supporting_materials") or []:
		stored = frappe.db.get_value("Requisition Supporting Material", {"supporting_material_id": material.get("supporting_material_id")}, ["file_digest", "treatment"], as_dict=True)
		if not stored or cstr(stored.file_digest) != cstr(material.get("file_digest")) or cstr(stored.treatment) != cstr(material.get("treatment")):
			findings.append(_finding("FILE_INVALID", f"Supporting material {material.get('supporting_material_id')} failed its digest or treatment check.", task=controls.TASK_DETAILS))

	# 11. security and contract values internally consistent
	if state.get("delay_damages_per_week_percent") is not None and state.get("maximum_delay_damages_percent") is not None and float(state["maximum_delay_damages_percent"]) < float(state["delay_damages_per_week_percent"]):
		findings.append(_finding("VALUES_INCONSISTENT", "Maximum delay damages cannot be less than the weekly rate.", task=controls.TASK_REQUIREMENTS, field="maximum_delay_damages_percent"))
	if state.get("tender_security_amount") is not None and float(state["tender_security_amount"]) <= 0:
		findings.append(_finding("VALUES_INCONSISTENT", "Tender security must be a positive KES amount.", task=controls.TASK_DETAILS, field="tender_security_amount"))

	# 12. both outputs render completely
	renders: dict[str, Any] | None = None
	if with_renders and not [f for f in findings if f["finding_code"] in ("CONTROL_MISSING", "HANDOFF_INVALID", "TEMPLATE_UNAVAILABLE")]:
		try:
			renders = render_service.render(tender, version, snapshot, approval=approval)
		except Exception as exc:  # StrictUndefined or a template fault
			findings.append(_finding("RENDER_FAILED", f"The Invitation or issued Tender could not be rendered: {exc}", task=controls.TASK_REVIEW))
		else:
			for problem in renders["problems"]:
				findings.append(_finding("RENDER_PROBLEM", problem, task=controls.TASK_REVIEW))

	# 13. the canonical package digest can be produced
	try:
		serializer.package_digest(tender, version, snapshot, renders=renders)
	except Exception as exc:
		findings.append(_finding("PACKAGE_DIGEST_FAILED", f"The canonical digest could not be produced: {exc}", task=controls.TASK_REVIEW))

	# Review notes (visible, never dismissable)
	if state.get("manufacturer_authorisation_required"):
		findings.append(_finding("NOTE_MANUFACTURER_AUTHORISATION", MANUFACTURER_NOTE, severity=REVIEW_NOTE, task=controls.TASK_REQUIREMENTS, field="manufacturer_authorisation_required", link_label="Review supplier requirements"))

	must_fix = [f for f in findings if f["severity"] == MUST_FIX]
	notes = [f for f in findings if f["severity"] == REVIEW_NOTE]
	review_result_digest = digest.sha256_hex({"findings": findings, "renders": {"invitation": (renders or {}).get("invitation_digest"), "issued": (renders or {}).get("issued_tender_digest")}})
	return {
		"result": NEEDS_ATTENTION if must_fix else READY,
		"findings": findings,
		"must_fix_count": len(must_fix),
		"review_note_count": len(notes),
		"renders": renders,
		"review_result_digest": review_result_digest,
	}


def store(version, result: dict[str, Any]) -> None:
	"""Write findings and every §4.2 generated digest onto the Version
	(caller bumps/saves under the lifecycle flag)."""
	version.set("review_findings", [])
	for finding in result["findings"]:
		version.append("review_findings", {k: finding[k] for k in ("finding_code", "severity", "message", "task", "field", "route")})
	version.review_result_digest = result["review_result_digest"]
	renders = result.get("renders")
	if renders:
		version.invitation_digest = renders["invitation_digest"]
		version.issued_tender_digest = renders["issued_tender_digest"]
	snapshot = snap.load(version)
	generated = serializer.generated_digests(serializer.officer_state(version), snapshot, evidence.rows_as_dicts(version))
	version.response_schema_digest = generated["response_schema_digest"]
	version.evaluation_contract_digest = generated["evaluation_contract_digest"]
	version.contract_projection_digest = generated["contract_projection_digest"]
	tender = frappe.get_doc("Tender", version.tender)
	version.package_digest = serializer.package_digest(tender, version, snapshot, renders=renders)


def summary(version) -> dict[str, Any]:
	"""The stored result as the screens show it (§10.6): result, counts,
	findings with their links."""
	findings = [
		{"finding_code": r.finding_code, "severity": r.severity, "message": r.message, "task": r.task, "field": r.field, "route": r.route, "link_label": TASK_ROUTE_LABELS.get("contract" if controls.CATALOGUE.get(r.field, {}).get("group") == "contract" else r.task, "")}
		for r in version.get("review_findings") or []
	]
	must_fix = [f for f in findings if f["severity"] == MUST_FIX]
	notes = [f for f in findings if f["severity"] == REVIEW_NOTE]
	return {"result": NEEDS_ATTENTION if must_fix else READY, "findings": findings, "must_fix": must_fix, "review_notes": notes, "must_fix_count": len(must_fix), "review_note_count": len(notes), "review_result_digest": version.review_result_digest}
