# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WG-02 Review & Approval Workspace (D1-WG2)."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_configurations.constants import (
	STATUS_APPROVED_FOR_PREVIEW,
	STATUS_READY_FOR_REVIEW,
	STATUS_RETURNED_FOR_CORRECTION,
	STATUS_UNDER_REVIEW,
)
from kentender_procurement.tender_configurations.services.configuration_home import (
	_STATUS_LABELS,
	build_configuration_context,
)
from kentender_procurement.tender_configurations.services.configuration_steps import (
	STEP_COMPLETE,
	STEP_ROUTES,
	get_steps_for_family,
	merge_step_rows,
)
from kentender_procurement.tender_configurations.services.readiness import get_readiness_report

REVIEWER_CHECKLIST = (
	"I have reviewed the tender identity, procurement method, and procuring entity context.",
	"I have reviewed the TDS values that control bidder instructions and submission rules.",
	"I have reviewed the IT requirements for clarity, completeness, and bidder neutrality.",
	"I have reviewed the implementation schedule and acceptance expectations.",
	"I have reviewed bidder background and inventory disclosures for usefulness and sensitivity.",
	"I have reviewed the price schedule structure for completeness and comparability.",
	"I have reviewed the evaluation setup for clarity and consistency with the tender requirements.",
	"I have reviewed the forms and evidence requirements for bidder submission completeness.",
	"I have reviewed the contract values and carry-forward obligations.",
	"I understand that approval here does not publish the tender.",
)

SECTION_PURPOSE = {
	"CFG-01": "Confirm tender identity and procurement context.",
	"CFG-02": "Confirm tender-specific instructions and parameters.",
	"CFG-03": "Confirm bidder-facing requirements are clear and complete.",
	"CFG-04": "Confirm delivery approach, milestones, and acceptance expectations.",
	"CFG-05": "Confirm disclosed environment/context is useful and safe.",
	"CFG-06": "Confirm bidder pricing structure is complete.",
	"CFG-07": "Confirm evaluation method, criteria, and weights are clear.",
	"CFG-08": "Confirm bidder submission requirements are complete.",
	"CFG-09": "Confirm tender-specific contract values are complete.",
}

SEV_CORRECTION = "Correction Required"
SEV_CLARIFICATION = "Clarification"
SEV_NOTE = "Note"


def _parse_blob(raw: Any) -> dict[str, Any]:
	if not raw:
		return {}
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str):
		try:
			parsed = json.loads(raw)
			return parsed if isinstance(parsed, dict) else {}
		except (TypeError, ValueError):
			return {}
	return {}


def _default_checklist() -> list[dict[str, Any]]:
	return [{"id": f"CHK-{i+1:02d}", "label": label, "checked": 0} for i, label in enumerate(REVIEWER_CHECKLIST)]


def _ensure_blob(raw: Any) -> dict[str, Any]:
	blob = _parse_blob(raw)
	if not blob.get("checklist"):
		blob["checklist"] = _default_checklist()
	else:
		# Reconcile labels if count mismatches
		existing = {cstr(c.get("id")): c for c in blob["checklist"] if isinstance(c, dict)}
		merged = []
		for i, label in enumerate(REVIEWER_CHECKLIST):
			cid = f"CHK-{i+1:02d}"
			prev = existing.get(cid) or {}
			merged.append(
				{
					"id": cid,
					"label": label,
					"checked": 1 if prev.get("checked") in (1, True, "1", "true") else 0,
				}
			)
		blob["checklist"] = merged
	if not isinstance(blob.get("findings"), list):
		blob["findings"] = []
	if not isinstance(blob.get("decisions"), list):
		blob["decisions"] = []
	_ensure_finding_ids(blob)
	return blob


def _next_finding_id(blob: dict[str, Any]) -> str:
	max_n = 0
	for f in blob.get("findings") or []:
		if not isinstance(f, dict):
			continue
		fid = cstr(f.get("id") or "")
		if fid.startswith("FIN-"):
			try:
				max_n = max(max_n, int(fid.split("-", 1)[1]))
			except (TypeError, ValueError):
				pass
	return f"FIN-{max_n + 1:03d}"


def _ensure_finding_ids(blob: dict[str, Any]) -> None:
	"""Assign stable FIN-NNN ids to findings that lack them (in place)."""
	for f in blob.get("findings") or []:
		if not isinstance(f, dict):
			continue
		if not cstr(f.get("id") or "").strip():
			f["id"] = _next_finding_id(blob)


def _section_owner_route(section: str) -> str:
	text = cstr(section or "")
	if not text:
		return ""
	upper = text.upper()
	for sid, route in STEP_ROUTES.items():
		if upper.startswith(sid) or f"{sid}:" in upper or f"{sid} " in upper:
			return route
	# Title-only match (e.g. "IT Requirements")
	for sid, purpose_title in (
		("CFG-01", "Tender Profile"),
		("CFG-02", "Tender Data Sheet"),
		("CFG-03", "IT Requirements"),
		("CFG-04", "Implementation Schedule"),
		("CFG-05", "System Inventory"),
		("CFG-06", "Price Schedule"),
		("CFG-07", "Evaluation Setup"),
		("CFG-08", "Forms & Evidence"),
		("CFG-09", "Contract Values"),
	):
		if purpose_title.lower() in text.lower():
			return STEP_ROUTES.get(sid, "")
	return ""


def _enrich_correction_finding(f: dict[str, Any]) -> dict[str, Any]:
	section = cstr(f.get("section") or "")
	status = cstr(f.get("status") or "Open") or "Open"
	return {
		"id": cstr(f.get("id") or ""),
		"finding": cstr(f.get("finding") or ""),
		"section": section,
		"severity": cstr(f.get("severity") or SEV_CORRECTION),
		"required_action": cstr(f.get("required_action") or f.get("finding") or ""),
		"status": status,
		"owner_route": cstr(f.get("owner_route") or "") or _section_owner_route(section),
		"resolved_at": cstr(f.get("resolved_at") or ""),
		"resolved_by": cstr(f.get("resolved_by") or ""),
	}


def _checklist_complete(blob: dict[str, Any]) -> bool:
	items = blob.get("checklist") or []
	return bool(items) and all(int(c.get("checked") or 0) for c in items)


def _open_corrections(blob: dict[str, Any]) -> list[dict[str, Any]]:
	out = []
	for f in blob.get("findings") or []:
		if not isinstance(f, dict):
			continue
		if cstr(f.get("severity")) == SEV_CORRECTION and cstr(f.get("status")) in ("", "Open"):
			out.append(f)
	return out


def open_correction_findings(blob: dict[str, Any]) -> list[dict[str, Any]]:
	"""Public helper: open Correction Required findings from a review_workspace blob."""
	return _open_corrections(blob)


def count_open_corrections_for_doc(doc) -> int:
	blob = _ensure_blob(getattr(doc, "review_workspace", None))
	return len(_open_corrections(blob))


def get_review_corrections_for_readiness(doc) -> dict[str, Any]:
	"""Correction-severity findings for WG-01 (does not call readiness — avoids cycles)."""
	blob = _ensure_blob(getattr(doc, "review_workspace", None))
	corrections = [
		_enrich_correction_finding(f)
		for f in (blob.get("findings") or [])
		if isinstance(f, dict) and cstr(f.get("severity")) == SEV_CORRECTION
	]
	open_n = sum(1 for c in corrections if cstr(c.get("status")) in ("", "Open"))
	return {
		"review_corrections": corrections,
		"open_correction_count": open_n,
	}


def resolve_review_finding(configuration_id: str, finding_id: str) -> dict[str, Any]:
	"""Preparer marks one Open Correction Required finding as Resolved."""
	configuration_id = cstr(configuration_id or "").strip()
	finding_id = cstr(finding_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	if not finding_id:
		frappe.throw(frappe._("Finding id is required."), title="FINDING_REQUIRED")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)

	blob = _ensure_blob(getattr(doc, "review_workspace", None))
	matched = None
	for f in blob.get("findings") or []:
		if not isinstance(f, dict):
			continue
		if cstr(f.get("id")) != finding_id:
			continue
		matched = f
		break
	if not matched:
		frappe.throw(frappe._("Finding not found."), title="FINDING_NOT_FOUND")
	if cstr(matched.get("severity")) != SEV_CORRECTION:
		frappe.throw(
			frappe._("Only Correction Required findings can be marked as fixed."),
			title="FINDING_NOT_CORRECTION",
		)
	if cstr(matched.get("status") or "Open") not in ("", "Open"):
		frappe.throw(frappe._("This finding is already resolved."), title="FINDING_ALREADY_RESOLVED")

	matched["status"] = "Resolved"
	matched["resolved_at"] = str(now_datetime())
	matched["resolved_by"] = frappe.session.user
	doc.review_workspace = json.dumps(blob)
	# When all corrections are fixed and readiness blockers are clear, allow Ready for Review.
	from kentender_procurement.tender_configurations.constants import STATUS_READY_FOR_REVIEW

	if (
		cstr(doc.status) == STATUS_RETURNED_FOR_CORRECTION
		and not _open_corrections(blob)
		and int(doc.blocker_count or 0) == 0
	):
		doc.status = STATUS_READY_FOR_REVIEW
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()

	from kentender_procurement.tender_configurations.services.readiness import get_readiness_report

	out = get_readiness_report(configuration_id)
	out["resolved"] = True
	out["resolved_finding_id"] = finding_id
	return out


def _sections(doc) -> list[dict[str, Any]]:
	from kentender_procurement.tender_configurations.services.configuration_home import (
		_parse_steps_state,
	)

	family = cstr(doc.std_family_key or "IT")
	catalog = get_steps_for_family(family)
	state = _parse_steps_state(getattr(doc, "steps_state", None))
	rows = merge_step_rows(catalog, state, doc=doc)
	out = []
	for row in rows:
		sid = row["id"]
		out.append(
			{
				"step_id": sid,
				"section": row["title"],
				"review_purpose": SECTION_PURPOSE.get(sid, ""),
				"status": row.get("status_label") or STEP_COMPLETE,
				"action_label": "View",
				"owner_route": STEP_ROUTES.get(sid, row.get("route") or ""),
			}
		)
	return out


def _dto(doc, blob: dict[str, Any]) -> dict[str, Any]:
	context = build_configuration_context(doc)
	status = cstr(doc.status or "")
	readiness = get_readiness_report(doc.name)
	checklist_ok = _checklist_complete(blob)
	open_corr = _open_corrections(blob)
	can_approve = (
		status == STATUS_UNDER_REVIEW and checklist_ok and not open_corr and int(readiness.get("blocker_count") or 0) == 0
	)
	steps = _sections(doc)
	complete_n = sum(1 for s in steps if s.get("status") == STEP_COMPLETE)

	return {
		"configuration_id": doc.name,
		"configuration_ref": cstr(doc.configuration_ref or doc.name),
		"procurement_package_ref": context["procurement_package_ref"],
		"tender_title": cstr(doc.tender_title or ""),
		"std_family_label": context["std_family_label"],
		"procuring_entity_name": context["procuring_entity_name"],
		"procurement_method_label": context.get("procurement_method_label") or "",
		"review_status_label": _STATUS_LABELS.get(status, status),
		"readiness_result": readiness.get("overall_result") or "",
		"readiness_blocker_count": readiness.get("blocker_count") or 0,
		"configuration_status_label": _STATUS_LABELS.get(status, status),
		"summary": {
			"configuration_steps": f"{complete_n} of {len(steps)} complete",
			"readiness_check": "Passed" if int(readiness.get("blocker_count") or 0) == 0 and readiness.get("has_run") else "Not ready",
			"warnings": f"{int(readiness.get('warning_count') or 0)} accepted warnings",
			"submitted_on": (_parse_blob(getattr(doc, "readiness_report", None)).get("submitted_at") or ""),
			"submitted_by": (_parse_blob(getattr(doc, "readiness_report", None)).get("submitted_by") or ""),
			"assigned_reviewer": blob.get("assigned_reviewer") or frappe.session.user,
		},
		"sections": steps,
		"checklist": blob.get("checklist") or [],
		"findings": blob.get("findings") or [],
		"decisions": blob.get("decisions") or [],
		"can_approve": can_approve,
		"approve_enabled": can_approve,
		# Return only when open Correction Required findings already exist (Add Finding first).
		"return_enabled": status == STATUS_UNDER_REVIEW and bool(open_corr),
		"clarify_enabled": status == STATUS_UNDER_REVIEW,
		"open_correction_count": len(open_corr),
		"preview_route": "it-tender-configuration-render-preview",
		"readiness_route": "it-tender-configuration-validation-report",
		"home_route": "it-tender-configuration-overview",
		"context": context,
		"entry_allowed": status
		in (
			STATUS_READY_FOR_REVIEW,
			STATUS_UNDER_REVIEW,
			STATUS_APPROVED_FOR_PREVIEW,
			STATUS_RETURNED_FOR_CORRECTION,
		),
	}


def _ensure_review_started(doc) -> bool:
	"""Promote Ready for Review → Under Review when a reviewer opens or acts on WG-02.

	Configs often land on Review & Approval after readiness without a separate
	submit click (same Admin acting as preparer+reviewer). Return/Approve stay
	disabled until status is Under Review — start review on first workspace access.
	"""
	if cstr(doc.status) != STATUS_READY_FOR_REVIEW:
		return False
	if not frappe.has_permission(doc=doc, ptype="write"):
		return False
	doc.status = STATUS_UNDER_REVIEW
	# Stamp submit metadata on the readiness blob when missing (summary fields).
	try:
		blob = json.loads(doc.readiness_report or "{}")
		if not isinstance(blob, dict):
			blob = {}
	except (TypeError, ValueError):
		blob = {}
	if not blob.get("submitted_at"):
		blob["submitted_at"] = str(now_datetime())
		blob["submitted_by"] = frappe.session.user
		doc.readiness_report = json.dumps(blob)
	return True


def get_review_workspace(configuration_id: str) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="read"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	blob = _ensure_blob(getattr(doc, "review_workspace", None))
	updates: dict[str, Any] = {}
	# Persist defaults once without full doc.save (avoids race on double page mount).
	if not getattr(doc, "review_workspace", None):
		updates["review_workspace"] = json.dumps(blob)
		doc.review_workspace = updates["review_workspace"]
	if _ensure_review_started(doc):
		updates["status"] = STATUS_UNDER_REVIEW
		if getattr(doc, "readiness_report", None):
			updates["readiness_report"] = doc.readiness_report
	if updates:
		frappe.db.set_value(
			"Tender Configuration",
			configuration_id,
			updates,
			update_modified=False,
		)
		frappe.db.commit()
	return _dto(doc, blob)


def save_review_workspace(
	configuration_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	if not configuration_id or not frappe.db.exists("Tender Configuration", configuration_id):
		frappe.throw(frappe._("Tender configuration not found."), title="TCFG_NOT_FOUND")
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}
	_ensure_review_started(doc)
	blob = _ensure_blob(getattr(doc, "review_workspace", None))
	if isinstance(payload.get("checklist"), list):
		checked_map = {
			cstr(c.get("id")): 1 if c.get("checked") in (1, True, "1", "true") else 0
			for c in payload["checklist"]
			if isinstance(c, dict)
		}
		for item in blob["checklist"]:
			if item["id"] in checked_map:
				item["checked"] = checked_map[item["id"]]
	if isinstance(payload.get("findings"), list):
		blob["findings"] = [f for f in payload["findings"] if isinstance(f, dict)]
		_ensure_finding_ids(blob)
	doc.review_workspace = json.dumps(blob)
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	return _dto(doc, blob)


def approve_for_preview(
	configuration_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	if cstr(doc.status) != STATUS_UNDER_REVIEW:
		frappe.throw(frappe._("Configuration is not under review."), title="REVIEW_STATE")
	blob = _ensure_blob(getattr(doc, "review_workspace", None))
	if not _checklist_complete(blob):
		frappe.throw(frappe._("Complete the reviewer checklist before approving."), title="REVIEW_CHECKLIST")
	if _open_corrections(blob):
		frappe.throw(
			frappe._("Resolve correction-required findings before approving."),
			title="REVIEW_FINDINGS",
		)
	readiness = get_readiness_report(configuration_id)
	if int(readiness.get("blocker_count") or 0) > 0:
		frappe.throw(frappe._("Readiness blockers remain."), title="READINESS_BLOCKERS")

	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}
	if not payload.get("confirm_preview_only"):
		frappe.throw(
			frappe._("Confirm that approval only allows document preview."),
			title="REVIEW_CONFIRM",
		)

	blob["decisions"].append(
		{
			"decision": "approve_for_preview",
			"at": str(now_datetime()),
			"by": frappe.session.user,
		}
	)
	blob["approved_at"] = str(now_datetime())
	blob["approved_by"] = frappe.session.user
	doc.review_workspace = json.dumps(blob)
	doc.status = STATUS_APPROVED_FOR_PREVIEW
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	out = _dto(doc, blob)
	out["approved"] = True
	return out


def return_for_correction(
	configuration_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	"""Return config using existing open Correction Required findings (confirm-only).

	Findings are captured via Add Finding. Optional affected_section / correction_required
	in payload remain as a seed/compat path when no open corrections exist yet.
	"""
	configuration_id = cstr(configuration_id or "").strip()
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	_ensure_review_started(doc)
	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}
	section = cstr(payload.get("affected_section") or "").strip()
	reason = cstr(payload.get("correction_required") or payload.get("reason") or "").strip()
	blob = _ensure_blob(getattr(doc, "review_workspace", None))
	open_corr = _open_corrections(blob)
	if not open_corr:
		# Compat/seed: allow one-shot return that creates the finding from payload.
		if not section or not reason:
			frappe.throw(
				frappe._(
					"Add at least one Correction Required finding before returning for correction."
				),
				title="RETURN_FINDINGS_REQUIRED",
			)
		blob["findings"].append(
			{
				"id": _next_finding_id(blob),
				"finding": reason[:120],
				"section": section,
				"severity": SEV_CORRECTION,
				"required_action": reason,
				"status": "Open",
				"owner_route": _section_owner_route(section),
			}
		)
		open_corr = _open_corrections(blob)

	first = open_corr[0]
	section = section or cstr(first.get("section") or "")
	reason = reason or cstr(first.get("required_action") or first.get("finding") or "")
	blob["decisions"].append(
		{
			"decision": "return_for_correction",
			"affected_section": section,
			"reason": reason,
			"open_correction_count": len(open_corr),
			"finding_ids": [cstr(f.get("id") or "") for f in open_corr],
			"note": cstr(payload.get("reviewer_note") or ""),
			"at": str(now_datetime()),
			"by": frappe.session.user,
		}
	)
	doc.review_workspace = json.dumps(blob)
	doc.status = STATUS_RETURNED_FOR_CORRECTION
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	out = _dto(doc, blob)
	out["returned"] = True
	return out


def request_clarification(
	configuration_id: str, payload: dict[str, Any] | str | None = None
) -> dict[str, Any]:
	configuration_id = cstr(configuration_id or "").strip()
	doc = frappe.get_doc("Tender Configuration", configuration_id)
	if not frappe.has_permission(doc=doc, ptype="write"):
		frappe.throw(frappe._("Not permitted"), frappe.PermissionError)
	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	payload = payload or {}
	question = cstr(payload.get("question") or payload.get("clarification") or "").strip()
	if not question:
		frappe.throw(frappe._("Clarification question is required."), title="CLARIFY_REQUIRED")
	blob = _ensure_blob(getattr(doc, "review_workspace", None))
	blob["decisions"].append(
		{
			"decision": "request_clarification",
			"question": question,
			"section": cstr(payload.get("affected_section") or ""),
			"at": str(now_datetime()),
			"by": frappe.session.user,
		}
	)
	section = cstr(payload.get("affected_section") or "")
	blob["findings"].append(
		{
			"id": _next_finding_id(blob),
			"finding": question[:120],
			"section": section,
			"severity": SEV_CLARIFICATION,
			"required_action": question,
			"status": "Open",
			"owner_route": _section_owner_route(section),
		}
	)
	doc.review_workspace = json.dumps(blob)
	# Remains Under Review
	if cstr(doc.status) != STATUS_UNDER_REVIEW:
		doc.status = STATUS_UNDER_REVIEW
	doc.flags.ignore_mandatory = True
	doc.save(ignore_permissions=False)
	frappe.db.commit()
	out = _dto(doc, blob)
	out["clarification_requested"] = True
	return out
