# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §5.4 — the review result (plan D17): a deterministic
projection, not a workflow state. A Draft may be incomplete; submission,
approval and publication authorisation may not. Findings are **Must fix**
(prevents the decision and links to the exact task/field/owner route) or
**Review note** (visible through every later decision, never dismissed).
The result verifies the source handoff, template release, the nine
compatibility checks, officer fields, dates, inherited completeness,
grouping lineage, schedules, response schema, evaluation/contract
mappings, file treatments, security/contract values, both renders and the
package digest (TPR08-AC-026..028)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate

from kentender_procurement.tenders.services import clock, compatibility, configuration_gateway, controls, digest, evidence, handoff_gateway, render_service, serializer, template_binding
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services.errors import TendersError

MUST_FIX = "Must fix"
REVIEW_NOTE = "Review note"
READY = "Ready to submit"
NEEDS_ATTENTION = "Needs attention"

FINDING_CODES: frozenset[str] = frozenset(
	{
		"HANDOFF_INVALID", "HANDOFF_CONSUMED_ELSEWHERE", "HANDOFF_DIGEST_CHANGED", "TEMPLATE_UNAVAILABLE", "COMPATIBILITY_FAILED",
		"CONTROL_MISSING", "DATE_ORDER", "PUBLICATION_PERIOD", "PERIOD_REASON", "SNAPSHOT_CHANGED", "SCHEDULE_MISMATCH", "MAPPING_INCOMPLETE", "EVIDENCE_UNLINKED",
		"FILE_INVALID", "VALUES_INCONSISTENT", "RENDER_FAILED", "RENDER_PROBLEM", "PACKAGE_DIGEST_FAILED",
		"NOTE_MANUFACTURER_AUTHORISATION", "NOTE_SHORT_PERIOD",
	}
)
MANUFACTURER_NOTE = "Confirm that manufacturer authorisation is proportionate for this purchase."
MAPPING_MESSAGE = "A published requirement is not fully connected to its supplier response and downstream treatment."
TASK_ROUTE_LABELS = {controls.TASK_DETAILS: "Review Tender details", controls.TASK_REQUIREMENTS: "Review supplier requirements", "contract": "Review contract terms", controls.TASK_REVIEW: "Review and generated documents"}


def goods_schedule_reconciles(snapshot: dict[str, Any], lines: list[dict[str, Any]]) -> bool:
	"""RG-24 — the goods schedule carries every inherited item once, exactly: the quantities of the schedule's
	source items add up, in exact decimal arithmetic, to the quantities of the inherited items. (The rendered
	line quantity is a formatted, rounded text, so the lineage rows are what is compared.)"""
	if not lines:
		return False
	scheduled = sum((Decimal(cstr(src.get("quantity") or 0)) for line in lines for src in line.get("source_items") or []), Decimal(0))
	return scheduled == snap.total_quantity_exact(snapshot)


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


def _mappings(tender, version) -> dict[str, set[str]]:
	"""§5.8(6) from the compiled Published Bid Definition (plan D25). A compile
	failure is itself the finding (raised as a TendersError)."""
	from kentender_procurement.tenders.services import bid_definition

	projection = bid_definition.technical_mapping_sets(bid_definition.compile_version(tender, version))
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

	# 2. the bound release may still be used and its digests match
	# (TPR-CHG-001 v0.11 §5.3; never rebinds)
	problems = template_binding.verify(version)
	for problem in problems:
		findings.append(_finding("TEMPLATE_UNAVAILABLE", problem, task=controls.TASK_DETAILS))
	bound_support = template_binding.bound_support(version) if not problems else ()

	# 3. the nine compatibility checks (TPR-CHG-001 v0.12 §5.3)
	for check in compatibility.evaluate(snapshot, bound_support):
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
	# §5.2 / §5.5.6 (v0.16): two different numbers. Below the verified legal minimum is a Must fix, so it cannot reach the Accounting
	# Officer; below the usual period is allowed but needs a stated reason, which then stays visible to the approvers as a Review note.
	# Authorisation rechecks the legal minimum on the day of the decision.
	if issue and sub:
		period = configuration_gateway.preparation_period(issue, cstr(snapshot.get("procurement_category")) or "Goods")
		if period:
			minimum, usual = period["minimum_days"], period["default_days"]
			floor = configuration_gateway.period_shortfall(issue_date=issue, submission_deadline=sub, today=clock.today(), minimum_days=minimum) if minimum else None
			if floor:
				findings.append(_finding(
					"PUBLICATION_PERIOD",
					f"The submission deadline must be at least {floor['minimum_days']} days after publication (the legal minimum). Published from {serializer.fmt_date_short(floor['earliest_publication'])}, the earliest allowed deadline is {serializer.fmt_date_short(floor['earliest_deadline'])}.",
					task=controls.TASK_DETAILS, field="submission_deadline",
				))
			shorter = configuration_gateway.period_shortfall(issue_date=issue, submission_deadline=sub, today=clock.today(), minimum_days=usual) if usual else None
			if shorter:
				reason = cstr(state.get("shortened_period_reason")).strip()
				if not reason:
					findings.append(_finding(
						"PERIOD_REASON", f"State why the tendering period is {shorter['days_allowed']} days, shorter than the usual {usual}.",
						task=controls.TASK_DETAILS, field="shortened_period_reason",
					))
				else:
					findings.append(_finding(
						"NOTE_SHORT_PERIOD", f"The tendering period is {shorter['days_allowed']} days, shorter than the usual {usual}. Reason given: {reason}",
						severity=REVIEW_NOTE, task=controls.TASK_DETAILS, field="shortened_period_reason", link_label="Review Tender details",
					))
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
	if not goods_schedule_reconciles(snapshot, lines):
		findings.append(_finding("SCHEDULE_MISMATCH", "The goods schedule does not reconcile to the inherited items.", task=controls.TASK_REVIEW))
	if len(serializer.price_schedule(snapshot)["rows"]) != len(lines) + len(snapshot.get("related_services") or []):
		findings.append(_finding("SCHEDULE_MISMATCH", "The price schedule does not reconcile to the goods and services schedules.", task=controls.TASK_REVIEW))

	# 8. every published technical requirement has one response, evaluation and
	# contract mapping in the compiled definition (only once the Version is
	# complete enough to compile; the missing values are findings already)
	published = {r.get("technical_requirement_id") for r in snapshot.get("technical_requirements") or []}
	if not [f for f in findings if f["finding_code"] in ("CONTROL_MISSING", "HANDOFF_INVALID", "TEMPLATE_UNAVAILABLE", "COMPATIBILITY_FAILED", "DATE_ORDER", "PUBLICATION_PERIOD", "PERIOD_REASON")]:
		try:
			mapped = _mappings(tender, version)
		except TendersError as exc:
			findings.append(_finding("MAPPING_INCOMPLETE", f"{MAPPING_MESSAGE} {(exc.detail or {}).get('reason') or ''}".strip(), task=controls.TASK_REVIEW))
		else:
			for kind, ids in mapped.items():
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
	tender = frappe.get_doc("Tender", version.tender)
	components = {"response_schema_digest": "", "evaluation_contract_digest": "", "contract_projection_digest": ""}
	if not result["must_fix_count"]:
		from kentender_procurement.tenders.services import bid_definition

		try:
			components = bid_definition.component_digests(tender, version)
		except TendersError:
			pass
	version.response_schema_digest = components["response_schema_digest"]
	version.evaluation_contract_digest = components["evaluation_contract_digest"]
	version.contract_projection_digest = components["contract_projection_digest"]
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
