# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §10.1 — every read, verdict first (KT-STD-001 §3A).

Reads never create a root, Version, package, row, task, decision, drawdown,
reservation or handoff. Each returns one server projection shaped for its
REQ-DES board; permitted actions are computed from the same gates the
commands use (read/offer parity), never from a second copy of the rule.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import (
	authorise as authorise_service,
	catalogue,
	compatibility,
	correction,
	digest,
	eligibility_gateway,
	envelope,
	funding_gateway,
	goods_template,
	handoff as handoff_service,
	precision,
	presenters as p,
	records,
	validation,
)
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services import scope as req_scope
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError, fail
from kentender_procurement.procurement_requisitions.services.requisition_roles import (
	FORBIDDEN_MESSAGE,
	ROLE_AUDITOR,
	ROLE_DEPARTMENTAL_AUTHOR,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_HEAD_OF_USER_DEPARTMENT,
	ROLE_PROCUREMENT_OFFICER,
	ROLE_PROCUREMENT_PLANNER,
	TENDER_SEAM_READER_ROLES,
)

STATE_BADGES = {
	"Draft": ("Draft", "is-draft"),
	"Awaiting Department Approval": ("Awaiting department approval", "is-attention"),
	"Submitted to Procurement": ("Submitted to Procurement", "is-draft"),
	"Authorised": ("Authorised", "is-live"),
	"Withdrawn": ("Withdrawn", "is-critical"),
	"Revoked": ("Authorisation revoked", "is-critical"),
	"Upstream correction required": ("Planning correction requested", "is-attention"),
}


def _can(fn, *args, **kwargs) -> bool:
	try:
		fn(*args, **kwargs)
		return True
	except (ProcurementRequisitionsError, frappe.DoesNotExistError, frappe.PermissionError):
		return False


def _has(actor: str, role: str, unit: str = "") -> bool:
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	return authorise_record(user=actor, business_role=role, organisation_unit=cstr(unit), purpose=PURPOSE_COMMAND).allowed


def _forbidden() -> dict[str, Any]:
	return {"outcome": "FORBIDDEN", "message": FORBIDDEN_MESSAGE}


def _reader(requisition: str, actor: str):
	root = records.require_root(requisition, lock=False)
	authz.require_requisition_reader(actor, contributing_org_units=records.contributing_units(root), state=root.current_state)
	return root


def _projection(root) -> dict[str, Any]:
	try:
		return eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	except frappe.DoesNotExistError:
		return {"sources": [], "eligible": False}


def list_delivery_locations() -> list[dict[str, str]]:
	return frappe.get_all("Delivery Location", filters={"status": "Active"}, fields=["name", "location_name", "address"], order_by="location_name asc", limit_page_length=0)


def _header(root, version, *, badge: tuple[str, str] | None = None, description: str = "") -> dict[str, Any]:
	label, tone = badge or STATE_BADGES.get(root.current_state, (root.current_state, "is-draft"))
	return {
		"requisition": root.name, "reference": root.requisition_reference, "title": version.requirement_title,
		"state": root.current_state, "badge": {"label": label, "tone": tone}, "description": description,
		"record_version": root.record_version, "version": version.name, "version_number": version.version_number,
		"version_record_version": version.record_version,
	}


def _decision_chain(root, version) -> list[dict[str, Any]]:
	"""The board's read-only Decision chain (owner D2) — recorded decisions
	only, plus the next stages not yet reached."""
	prepared = f"{p.date_label(version.creation)} · {p.user_name(version.prepared_by)} · {records.unit_name(root.lead_org_unit_id)}"
	rows = [{"title": "Draft prepared", "meta": prepared, "tone": "is-live"}]
	submit = records.decision_of(version.name, "Submit to Procurement")
	authorise = records.decision_of(version.name, "Authorise requisition")
	state = root.current_state
	if submit:
		rows.append({"title": "Certified and submitted by the department", "meta": f"{p.eat(submit.decided_at)} · {p.user_name(submit.actor)}", "tone": "is-live"})
	else:
		rows.append({"title": "Head of User Department approval", "meta": "Awaiting your decision" if state == "Awaiting Department Approval" else "Not yet reached", "tone": "is-attention" if state == "Awaiting Department Approval" else "is-pending", "upcoming": state != "Awaiting Department Approval"})
	if authorise:
		rows.append({"title": "Authorised by Procurement", "meta": f"{p.eat(authorise.decided_at)} · {p.user_name(authorise.actor)} · funding reserved", "tone": "is-live"})
	elif submit:
		rows.append({"title": "Procurement authorisation", "meta": "Awaiting your decision" if state == "Submitted to Procurement" else "Not yet reached", "tone": "is-attention", "upcoming": False})
	else:
		rows.append({"title": "Procurement authorisation", "meta": "Not yet reached", "tone": "is-pending", "upcoming": True})
	consumed = bool(root.handoff_consumed_at)
	if authorise:
		rows.append({"title": "Tender Preparation", "meta": "Started" if consumed else "Ready to start · not yet consumed", "tone": "is-live" if consumed else "is-attention", "upcoming": False})
	else:
		rows.append({"title": "Tender Preparation", "meta": "Not started", "tone": "is-pending", "upcoming": True})
	return rows


# --------------------------------------------------------------------------
# REQ-DES-01 — workspace
# --------------------------------------------------------------------------


def _next_task(root) -> tuple[str, str]:
	version = frappe.get_doc("Requisition Version", root.current_version)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)
	report = validation.validate(version=records.version_dict(version), package=records.package_dict(package_version), eligibility=_projection(root), unreviewed_line_ids=goods_template.unreviewed_ids(version))
	pending = next((t for t in report["tasks"] if t["status"] != "Complete"), None)
	returned = bool(version.based_on_version)
	labels = {"request_details": "Complete request details", "requirements": "Complete requirements", "review_submit": "Review and submit"}
	blocker = next((f["message"] for f in report["findings"] if f["severity"] == "Blocking" and (pending is None or f["task"] == pending["key"])), "")
	task_label = labels.get(pending["key"], "Review and submit") if pending else "Review and submit"
	if returned:
		last = records.decision_of(version.based_on_version, "Return for correction") or records.decision_of(version.based_on_version, "Return to department") or records.decision_of(version.based_on_version, "Change submitting department and return")
		if last:
			return "Correct returned requisition", cstr(last.reason)
	return task_label, blocker


def get_requisition_workspace(*, filters: dict[str, Any] | None = None, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if not authz.holds_any_requisition_responsibility(actor):
		return _forbidden()
	filters = filters or {}
	technical = authz.is_technical(actor)
	is_hopf = _has(actor, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
	author_units = set()
	hod_units = set()
	from kentender_core.services.authorization import permitted_ou_scopes

	author_units = set(permitted_ou_scopes(actor, ROLE_DEPARTMENTAL_AUTHOR) or ())
	hod_units = set(permitted_ou_scopes(actor, ROLE_HEAD_OF_USER_DEPARTMENT) or ())
	draft_units = author_units | hod_units

	readable = frappe.get_list(
		"Procurement Requisition", fields=["name", "requisition_reference", "plan_item_id", "current_state", "current_version", "lead_org_unit_id", "modified"],
		order_by="modified desc", limit_page_length=0,
	) if not technical else frappe.get_all(
		"Procurement Requisition", fields=["name", "requisition_reference", "plan_item_id", "current_state", "current_version", "lead_org_unit_id", "modified"],
		order_by="modified desc", limit_page_length=0,
	)
	register = []
	your_work = []
	plan_years: dict[str, str] = {}
	references: dict[str, str] = {}
	counts = {"Drafts": 0, "Returned": 0, "Approvals": 0}
	for row in readable:
		root = frappe.get_doc("Procurement Requisition", row.name)
		version = frappe.get_doc("Requisition Version", root.current_version) if root.current_version else None
		units = sorted(records.contributing_units(root))
		label, tone = STATE_BADGES.get(root.current_state, (root.current_state, "is-draft"))
		if version and root.current_state == "Draft" and version.based_on_version:
			label = "Draft correction"
		if root.plan_id not in plan_years:
			plan_years[root.plan_id] = cstr(frappe.db.get_value("Annual Plan", root.plan_id, "fiscal_year"))
		if root.plan_item_id not in references:
			references[root.plan_item_id] = cstr(frappe.db.get_value("Plan Item", root.plan_item_id, "plan_item_reference"))
		entry = {
			"requisition": root.name, "reference": root.requisition_reference, "title": version.requirement_title if version else "",
			"plan_item_id": root.plan_item_id, "plan_item_reference": references[root.plan_item_id], "fiscal_year": plan_years[root.plan_id],
			"status": label, "tone": tone, "state": root.current_state, "departments": p.departments_label(p.ordered_units(records.child_rows(version, "drawdown_lines") if version else [], root.lead_org_unit_id)),
			"units": units, "updated": p.eat(root.modified), "route": f"/app/procurement-requisitions/{root.name}" + ("/authorised" if root.current_state in ("Authorised", "Revoked") else ""),
		}
		register.append(entry)
		if technical:
			continue
		if root.current_state == "Draft" and set(units) & draft_units:
			task_label, detail = _next_task(root)
			returned = bool(version.based_on_version)
			counts["Returned" if returned else "Drafts"] += 1
			your_work.append({**entry, "task": task_label, "detail": detail, "meta": f"{root.requisition_reference} · Updated {p.eat(root.modified)}", "action": "Continue", "kind": "returned" if returned else "draft"})
	if not technical:
		for task in frappe.get_all("Requisition Task", filters={"status": "Open"}, fields=["name", "requisition", "requisition_version", "business_role", "organisation_unit", "creation"]):
			if task.business_role == ROLE_HEAD_OF_USER_DEPARTMENT and task.organisation_unit in hod_units:
				label, route, detail = "Review departmental requisition", f"/app/procurement-requisitions/department-task/{task.name}", "Certify that it states both departments’ need and minimum requirements, or return it for correction."
			elif task.business_role == ROLE_HEAD_OF_PROCUREMENT_FUNCTION and is_hopf:
				label, route, detail = "Decide whether to authorise", f"/app/procurement-requisitions/procurement-task/{task.name}", "Check current funding and procurement checks, then authorise or return it."
			else:
				continue
			root = frappe.get_doc("Procurement Requisition", task.requisition)
			version = frappe.get_doc("Requisition Version", task.requisition_version)
			counts["Approvals"] += 1
			your_work.append(
				{
					"requisition": root.name, "reference": root.requisition_reference, "title": version.requirement_title, "task": label, "detail": detail,
					"meta": f"{root.requisition_reference} · Submitted for your decision {p.eat(task.creation)}", "action": "Review", "route": route, "kind": "decision", "task_id": task.name,
				}
			)

	ready = []
	if not technical and draft_units:
		for item in eligibility_gateway.list_requisition_eligible_plan_items():
			if not set(item.get("contributing_org_unit_ids") or []) & draft_units:
				continue
			open_root = records.open_root_for(item["plan_item_id"])
			detail = eligibility_gateway.get_requisition_eligible_plan_item(item["plan_item_id"])
			lines = [{"contributing_org_unit": s["organisation_unit"], "requested_value": s["remaining_amount"]} for s in detail.get("sources", [])]
			units = p.ordered_units(lines, records.default_lead(lines))
			existing = None
			if open_root:
				ex = frappe.get_doc("Procurement Requisition", open_root)
				ex_version = frappe.get_doc("Requisition Version", ex.current_version)
				task_label, _ = _next_task(ex) if ex.current_state == "Draft" else (STATE_BADGES.get(ex.current_state, (ex.current_state, ""))[0], "")
				# A Draft says its next task after its state; any other state says itself once.
				state_label = STATE_BADGES.get(ex.current_state, (ex.current_state, ""))[0]
				summary = f"{ex.requisition_reference} · {state_label}" + (f" · {task_label.replace('Complete request details', 'Request details need attention')}" if ex.current_state == "Draft" else "")
				existing = {"requisition": ex.name, "summary": summary, "route": f"/app/procurement-requisitions/{ex.name}"}
				if any(w["requisition"] == ex.name for w in your_work):
					continue
			ready.append(
				{
					"plan_item_id": item["plan_item_id"], "plan_item_reference": item.get("plan_item_reference") or "", "title": item.get("title"), "departments": p.departments_label(units),
					"available_quantity": precision.display_quantity(precision.planning_quantity(item.get("remaining_quantity") or "0")),
					"available_value": precision.display_money(item.get("remaining_value") or "0"),
					"needed_by": p.date_label(detail.get("plan_completion_boundary")), "route": f"/app/procurement-requisitions/new/{item['plan_item_id']}",
					"existing": existing,
				}
			)

	status = cstr(filters.get("status"))
	department = cstr(filters.get("department"))
	search = cstr(filters.get("search")).lower().strip()
	fiscal_year = cstr(filters.get("fiscal_year"))
	shown = [
		r for r in register
		if (not status or r["state"] == status) and (not department or department in r["units"]) and (not fiscal_year or r["fiscal_year"] == fiscal_year)
		and (not search or search in (r["reference"] + " " + r["title"]).lower())
	]
	departments = sorted({u for r in register for u in r["units"]} | (set() if technical else draft_units | hod_units))
	# The table-pagination standard: one page of what matched, and how many matched.
	from kentender_core.services.paging import page_of

	page_rows, paging = page_of(shown, filters.get("page"), filters.get("page_size"))
	return {
		"outcome": "OK", "actor": actor, "mode": "technical" if technical else "business",
		"your_work": [] if technical else your_work, "ready_to_start": ready, "register": page_rows, "paging": paging, "register_total": len(register),
		"counts": {k: v for k, v in counts.items() if (k != "Approvals" or is_hopf or hod_units) and not technical},
		"filters": {
			"statuses": [{"value": s, "label": STATE_BADGES[s][0]} for s in STATE_BADGES],
			"departments": [{"value": u, "label": records.unit_name(u)} for u in departments],
			"fiscal_years": [{"value": fy, "label": p.fiscal_year_label(fy)} for fy in sorted({r["fiscal_year"] for r in register if r["fiscal_year"]}, reverse=True)] if technical else [],
		},
		"department_filter_label": "All departments" if technical else "All my departments",
	}


# --------------------------------------------------------------------------
# REQ-DES-02 — start dialog (and the DES-12 purchase states)
# --------------------------------------------------------------------------


_FAILURE_MESSAGES = {
	"requirement_type": "This approved purchase requires {result}, which this release does not support.",
	"reservation_category": "This reservation treatment is not supported by the installed IT-equipment Tender format.",
	"county_resident_reservation": "This reservation treatment is not supported by the installed IT-equipment Tender format.",
	"plan_horizon": "This release supports purchases completed within one financial year.",
}


def _remaining_original(projection: dict[str, Any]) -> dict[str, Any]:
	"""REQ-DES-12 Remaining original amount — shown only once an earlier
	requisition has used part of the approved purchase."""
	sources = projection.get("sources", [])
	zero_qty = precision.planning_quantity("0")
	qty = sum((precision.planning_quantity(s.get("remaining_quantity") or "0") for s in sources), zero_qty)
	used_qty = sum((precision.planning_quantity(s.get("approved_quantity") or "0") - precision.planning_quantity(s.get("remaining_quantity") or "0") for s in sources), zero_qty)
	approved_value = sum((precision.stored_money(s.get("allocated_amount")) for s in sources), precision.stored_money("0"))
	remaining_value = precision.stored_money(projection.get("remaining_value") or "0")
	return {
		"shown": used_qty > 0,
		"original": {"quantity": precision.display_quantity(used_qty + qty), "value": precision.display_money(approved_value)},
		"used": {"quantity": precision.display_quantity(used_qty), "value": precision.display_money(approved_value - remaining_value)},
		"available": {"quantity": precision.display_quantity(qty), "value": precision.display_money(remaining_value)},
	}


def get_start_preview(*, plan_item_id: str, user: str | None = None) -> dict[str, Any]:
	"""§13.3 — the concise start dialog. Opening it creates nothing."""
	actor = authz.actor(user)
	if not authz.holds_any_requisition_responsibility(actor):
		return _forbidden()
	try:
		projection = eligibility_gateway.get_requisition_eligible_plan_item(plan_item_id)
	except frappe.DoesNotExistError:
		return {"outcome": "NOT_FOUND"}
	units = set(projection.get("contributing_org_unit_ids") or [])
	may_prepare = _can(authz.require_draft_author_for_any, units, actor)
	lines = [{"contributing_org_unit": s["organisation_unit"], "requested_value": s["remaining_amount"]} for s in projection.get("sources", []) if precision.stored_money(s.get("remaining_amount")) > 0]
	lead = records.default_lead(lines)
	checks = compatibility.check(projection)
	failure = next((c for c in checks if not c.ok), None)
	qty = sum((precision.planning_quantity(s.get("remaining_quantity") or "0") for s in projection.get("sources", [])), precision.planning_quantity("0"))
	rule = projection.get("reservation_rule") or {}
	existing = records.open_root_for(projection.get("plan_item_id") or plan_item_id)
	existing_row = None
	_existing_root = frappe.get_doc("Procurement Requisition", existing) if existing else None
	if existing and _can(authz.require_requisition_reader, actor, contributing_org_units=records.contributing_units(_existing_root), state=_existing_root.current_state):
		ex = frappe.get_doc("Procurement Requisition", existing)
		existing_row = {"requisition": ex.name, "reference": ex.requisition_reference, "route": f"/app/procurement-requisitions/{ex.name}", "summary": f"{ex.requisition_reference} · {STATE_BADGES.get(ex.current_state, (ex.current_state,''))[0]}"}
	state = "ready"
	message = ""
	if existing:
		state = "existing_open"
	elif failure:
		state = {"reservation_category": "rule_unavailable" if failure.code == "REQ_RESERVATION_RULE_UNAVAILABLE" else "reservation_unsupported", "county_resident_reservation": "reservation_unsupported" if failure.code != "REQ_RESERVATION_RULE_UNAVAILABLE" else "rule_unavailable", "plan_horizon": "multi_year"}.get(failure.test, "unsupported")
		if failure.code == "REQ_RESERVATION_RULE_UNAVAILABLE":
			message = "The applicable reservation rule is not ready for this purchase. Ask your KenTender administrator to complete the rule in System setup."
		else:
			message = _FAILURE_MESSAGES.get(failure.test, failure.failure).format(result=failure.result.lower())
	elif not projection.get("eligible"):
		state = "scope_locked" if (projection.get("scope") or {}).get("locked") else "ineligible"
		message = "This approved purchase already has an authorised requisition. Additional requirements must use a separate approved purchase." if state == "scope_locked" else "This approved purchase is not currently eligible for a requisition."
	remaining_value = precision.stored_money(projection.get("remaining_value") or "0")
	return {
		"outcome": "OK", "state": state, "message": message, "may_start": state == "ready" and may_prepare,
		"plan_item_id": projection.get("plan_item_id"), "plan_item_reference": projection.get("plan_item_reference") or "", "title": projection.get("title"),
		"departments": p.departments_label(p.ordered_units(lines, lead)),
		"available_quantity": precision.display_quantity(qty), "available_value": precision.display_money(remaining_value),
		"plan_completion_boundary": p.date_label(projection.get("plan_completion_boundary")),
		"requirement_product": "IT Equipment" if projection.get("requirement_type") == "Goods" else cstr(projection.get("requirement_type")),
		"reserved_for": p.reserved_for(projection.get("reservation_category")),
		"county_requirement": "County residents" if projection.get("county_resident_reservation") else "",
		"reservation_rule": {"label": f"Applicable verified {p.reserved_for(projection.get('reservation_category'))} reservation rule · Version {rule.get('version_number')}" if rule.get("available") else "Not ready", "available": bool(rule.get("available")), "snapshot_id": rule.get("snapshot_id")},
		"plan_horizon": projection.get("plan_horizon"), "failed_check": failure.label if failure else "",
		"submitting_department": records.unit_name(lead), "combined": len(units) > 1,
		"existing": existing_row,
		"remaining_original": _remaining_original(projection),
		"is_system_manager": authz.is_technical(actor),
	}


# --------------------------------------------------------------------------
# The record route (§12) — editable or immutable by server state
# --------------------------------------------------------------------------


def get_requisition_record(*, requisition: str, version: str | None = None, user: str | None = None) -> dict[str, Any]:
	"""One route, server-chosen rendering (§14.6): a Draft the actor may edit
	opens the editor; everything else renders read-only in its actual state."""
	actor = authz.actor(user)
	if not authz.holds_any_requisition_responsibility(actor):
		return _forbidden()
	try:
		root = _reader(requisition, actor)
	except frappe.DoesNotExistError:
		return {"outcome": "NOT_FOUND"}
	if version and version != root.current_version:
		return get_version_review(root=root, version_name=version, actor=actor)
	if root.current_state == "Draft":
		return get_requisition_editor(root=root, actor=actor)
	if root.current_state == "Upstream correction required":
		return get_stopped_requisition(root=root, actor=actor)
	if root.current_state in ("Authorised", "Revoked"):
		return get_authorised_requisition(root=root, actor=actor)
	return get_locked_requisition(root=root, actor=actor)


# --------------------------------------------------------------------------
# REQ-DES-03/05/06 — the Draft editor
# --------------------------------------------------------------------------


def _catalogue_meta() -> dict[str, Any]:
	return {
		"categories": list(catalogue.EQUIPMENT_CATEGORIES), "characteristics": [c.as_dict() for c in catalogue.CHARACTERISTICS],
		"groups": [{"group": g, "keys": list(k)} for g, k in catalogue.TECHNICAL_GROUPS],
		"service_types": list(catalogue.SERVICE_TYPES), "check_types": list(catalogue.ACCEPTANCE_CHECK_TYPES),
		"evidence_types": list(catalogue.ACCEPTANCE_EVIDENCE_TYPES), "service_evidence": list(catalogue.SERVICE_ACCEPTANCE_EVIDENCE),
		"material_types": list(catalogue.SUPPORTING_MATERIAL_TYPES), "service_locations": ["None", "Within Kenya", "At delivery location"],
		"affected_sections": ["Request details", "Equipment", "Technical requirements", "Warranty and support", "Services", "Acceptance", "Supporting materials", "Whole requisition"],
	}


def _return_panel(version) -> dict[str, Any] | None:
	if not version.based_on_version:
		return None
	decision = None
	for name in ("Return for correction", "Return to department", "Change submitting department and return"):
		decision = records.decision_of(version.based_on_version, name)
		if decision:
			break
	if not decision:
		return None
	target = {"Request details": ("request_details", "request_information"), "Equipment": ("request_details", "equipment"), "Technical requirements": ("requirements", "technical"), "Warranty and support": ("requirements", "warranty_support"), "Services": ("requirements", "services"), "Acceptance": ("requirements", "acceptance"), "Supporting materials": ("requirements", "supporting_materials")}.get(cstr(decision.affected_section), ("request_details", ""))
	return {
		"reason": decision.reason, "returned_by": p.user_name(decision.actor), "returned_at": p.eat(decision.decided_at),
		"affected_section": decision.affected_section, "task": target[0], "section": target[1], "decision": decision.decision,
		"earlier_lead": records.unit_name(frappe.db.get_value("Requisition Version", version.based_on_version, "certified_lead_org_unit_id")),
		"new_lead": records.unit_name(decision.new_lead_org_unit_id) if decision.new_lead_org_unit_id else "",
		"earlier_version_route": f"/app/procurement-requisitions/{version.requisition}/version/{version.based_on_version}",
	}


def _purchase(root, projection: dict[str, Any], version_dict: dict[str, Any]) -> dict[str, Any]:
	units = p.ordered_units(version_dict.get("drawdown_lines") or [], root.lead_org_unit_id)
	qty = sum((precision.stored_quantity(l.get("remaining_quantity")) for l in version_dict.get("drawdown_lines") or []), precision.stored_quantity("0"))
	value = sum((precision.stored_money(l.get("remaining_value")) for l in version_dict.get("drawdown_lines") or []), precision.stored_money("0"))
	package = frappe.db.get_value("IT Equipment Requirement Package", {"requisition": root.name}, ["reservation_category", "county_resident_reservation", "lotting_indicator", "reservation_rule_snapshot_ids"], as_dict=True) or {}
	rule = projection.get("reservation_rule") or {}
	need = "; ".join(sorted({s.get("description", "") for s in projection.get("sources", []) if s.get("description")}))
	return {
		"title": projection.get("title") or version_dict.get("requirement_title"), "departments": p.departments_label(units),
		"available": f"{precision.display_quantity(qty)} · {precision.display_money(value)} available",
		"method": projection.get("procurement_method"), "reserved_for": p.reserved_for(package.get("reservation_category")),
		"county_requirement": "County residents" if package.get("county_resident_reservation") else "",
		"plan_completion_boundary": p.date_label(projection.get("plan_completion_boundary")), "business_need": need,
		"source_details": [
			{"label": "Plan Item reference", "value": cstr(frappe.db.get_value("Plan Item", root.plan_item_id, "plan_item_reference")) or root.plan_item_id},
			{"label": "Estimated completion", "value": p.date_label(projection.get("estimated_completion_date"))},
			{"label": "Lotting", "value": cstr(package.get("lotting_indicator"))},
			{"label": "Strategic objective", "value": " · ".join(v for v in (p.objective_title(root.strategic_objective_id), p.objective_reference(root.strategic_objective_id)) if v)},
			{"label": "Reserved for", "value": f"{p.reserved_for(package.get('reservation_category'))} · Applicable verified {p.reserved_for(package.get('reservation_category'))} reservation rule · Version {rule.get('version_number')}" if rule.get("snapshot_id") else p.reserved_for(package.get("reservation_category"))},
			{"label": "Approved requirements", "value": "; ".join(l.get("source_line_id") for l in version_dict.get("drawdown_lines") or [])},
		],
	}


def _requirements_view(package_dict: dict[str, Any], package_version, version_dict: dict[str, Any] | None = None) -> dict[str, Any]:
	review_state = package_dict.get("standard_package_review_state") or "Not generated"
	return {
		"review_state": review_state, "profile_key": package_version.standard_profile_key, "profile_version": package_version.standard_profile_version,
		"proposal_digest": package_version.proposal_digest, "is_laptop_profile": package_version.standard_profile_key == catalogue.STANDARD_PROFILE_KEY,
		"technical_groups": p.technical_groups(package_dict), "technical_targets": p.technical_targets(package_dict, version_dict), "acceptance": p.acceptance_rows(package_dict),
		"support": {f: package_dict.get(f) for f in ("minimum_warranty_months", "onsite_support_required", "maximum_support_response_hours", "manufacturer_support_required", "service_location_constraint", "support_description")},
		"services": [{**s, "applies_to": p.row_label(s, package_dict), "applies_to_item_ids": req_scope.item_ids(s, package_dict.get("items") or []), "completion_date_label": p.date_label(s.get("completion_date"))} for s in package_dict.get("related_services") or []],
		"materials": [{**m, "linked": records.json_list(m.get("linked_requirement_ids_json"))} for m in package_dict.get("supporting_materials") or []],
	}


def _request_summary(vdict: dict[str, Any], pdict: dict[str, Any], sources: dict[str, dict[str, Any]], unreviewed: set[str]) -> dict[str, Any]:
	"""v1.15 §13.4 — the read-only Request summary: what is available, what the
	items request, the estimated total cost and what stays available."""
	rows = p.amounts_rows(vdict, sources, package=pdict, unreviewed=unreviewed)
	available_q = sum(int(r["remaining_quantity_value"]) for r in rows)
	available_v = sum((precision.stored_money(r["remaining_value_value"]) for r in rows), precision.stored_money("0"))
	requested_q = sum(int(r["requested_quantity_value"]) for r in rows)
	estimate = sum((precision.stored_money(r["requested_value_value"]) for r in rows), precision.stored_money("0"))
	return {
		"available_quantity": precision.display_quantity(available_q), "available_value": precision.display_money(available_v),
		"requested_quantity": precision.display_quantity(requested_q), "estimated_total": precision.display_money(estimate) if estimate > 0 else "",
		"after_quantity": precision.display_quantity(available_q - requested_q), "after_value": precision.display_money(available_v - estimate),
		"review_required": bool(unreviewed),
	}


def get_requisition_editor(*, root, actor: str) -> dict[str, Any]:
	root, version, package_version = records.load(root.name)
	projection = _projection(root)
	vdict = records.version_dict(version)
	pdict = records.package_dict(package_version)
	report = validation.validate(version=vdict, package=pdict, eligibility=projection, unreviewed_line_ids=goods_template.unreviewed_ids(version))
	scope = records.edit_scope(root, actor)
	technical = authz.is_technical(actor) or not scope["units"]
	contributor = bool(scope["units"]) and not scope["shared"]
	is_lead_hod = _has(actor, ROLE_HEAD_OF_USER_DEPARTMENT, root.lead_org_unit_id)
	is_lead_author = _has(actor, ROLE_DEPARTMENTAL_AUTHOR, root.lead_org_unit_id)
	sources = {s["plan_item_line_id"]: s for s in projection.get("sources", [])}
	returned = _return_panel(version)
	badge = ("Draft correction", "is-draft") if version.based_on_version else ("Draft", "is-draft")
	blocking = [f for f in report["findings"] if f["severity"] == "Blocking"]
	footer_hint = {t["key"]: next((f["message"] for f in blocking if f["task"] == t["key"]), "") for t in report["tasks"]}
	direct_hod = is_lead_hod and records.prepared_directly(version, actor)
	actions = {
		"save": bool(scope["units"]) and not technical, "save_label": "Save my changes" if contributor else "Save draft",
		"edit_shared": scope["shared"] and not technical,
		"send_for_department_approval": scope["shared"] and is_lead_author and not direct_hod and not technical,
		"submit_to_procurement": is_lead_hod and not technical and direct_hod and not records.certifier_conflict(version, actor, direct=True),
		"withdraw": is_lead_hod and not technical,
		"request_planning_correction": (is_lead_hod or _has(actor, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)) and not technical,
		"contributor": contributor,
	}
	review = {
		"result": ("Ready to submit to Procurement" if actions["submit_to_procurement"] else "Ready to send for department approval") if report["ready"] else "",
		"sections": p.review_sections(root=root, version=vdict, package=pdict, projection=projection, findings=report["findings"], lead=root.lead_org_unit_id),
		"warnings": [f for f in report["findings"] if f["severity"] == "Warning"],
		"dates": [
			{"label": "Estimated completion", "value": p.date_label(projection.get("estimated_completion_date"))},
			{"label": "Latest delivery date", "value": p.date_label(version.latest_delivery_date)},
			{"label": "Plan completion boundary", "value": p.date_label(projection.get("plan_completion_boundary"))},
		],
	}
	return {
		"outcome": "OK", "kind": "editor", "mode": "technical" if technical else ("contributor" if contributor else "editor"),
		"header": _header(root, version, badge=badge, description="Complete the request using the approved purchase shown below."),
		"package_record_version": package_version.record_version, "lead_org_unit_id": root.lead_org_unit_id,
		"lead_department": records.unit_name(root.lead_org_unit_id),
		"tasks": report["tasks"], "groups": report["groups"], "findings": report["findings"], "footer_hints": footer_hint,
		"returned": returned, "purchase": _purchase(root, projection, vdict), "remaining_original": _remaining_original(projection),
		"request_information": {
			"requirement_title": version.requirement_title, "delivery_location": version.delivery_location, "delivery_location_label": p.location_label(version.delivery_location),
			"latest_delivery_date": cstr(version.latest_delivery_date or ""), "latest_delivery_date_label": p.date_label(version.latest_delivery_date),
			"related_services_required": bool(version.related_services_required), "locations": list_delivery_locations(),
		},
		"amounts": p.amounts_rows(vdict, sources, editable_units=scope["units"], package=pdict, unreviewed=goods_template.unreviewed_ids(version)),
		"summary": _request_summary(vdict, pdict, sources, goods_template.unreviewed_ids(version)),
		"equipment": {
			"rows": [{**r, "editable": r["contributing_org_unit"] in scope["units"]} for r in p.item_rows(vdict, pdict)], "shared_specification": p.shared_specification(pdict), "groups": p.specification_groups(pdict, vdict),
			# v1.15 §13.5 — one row per source the actor may add items to; `room` is what can still be entered
			# (nothing is prefilled: the requester types each quantity once).
			"add_rows": [
				{
					"drawdown_line_id": l["drawdown_line_id"], "department": records.unit_name(l["contributing_org_unit"]), "source_reference": l["source_line_id"],
					"room": goods_template.room(l, pdict["items"]), "remaining_quantity": int(precision.stored_quantity(l["remaining_quantity"])),
					"unit": "Each", "editable": l["contributing_org_unit"] in scope["units"],
				}
				for l in vdict["drawdown_lines"] if goods_template.room(l, pdict["items"]) > 0
			],
		},
		"requirements": _requirements_view(pdict, package_version, vdict),
		"review": review, "decision_chain": _decision_chain(root, version),
		"record_details": p.record_details(root=root, version={**vdict, "content_digest": version.content_digest}, projection=projection),
		"actions": actions, "catalogue": _catalogue_meta(),
	}


# --------------------------------------------------------------------------
# Locked, task and authorised reads (REQ-DES-07/08/10/12)
# --------------------------------------------------------------------------


def _locked_bundle(root, version_name: str):
	version = frappe.get_doc("Requisition Version", version_name)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)
	projection = _projection(root)
	vdict = records.version_dict(version)
	pdict = records.package_dict(package_version)
	report = validation.validate(version=vdict, package=pdict, eligibility=projection, unreviewed_line_ids=goods_template.unreviewed_ids(version)) if version.version_status in ("Awaiting Department Approval", "Submitted to Procurement") else {"findings": [], "blocking_count": 0}
	# §13.8/13.9 — the submitted Version's own date warning stays part of it.
	findings = [f for f in report["findings"] if f["severity"] == "Warning"] or [
		f for f in validation.validate(version=vdict, package=pdict, eligibility=projection, unreviewed_line_ids=goods_template.unreviewed_ids(version))["findings"] if f["code"] == "DATE_AFTER_ESTIMATE"
	]
	sections = p.review_sections(root=root, version=vdict, package=pdict, projection=projection, findings=findings, lead=root.lead_org_unit_id)
	return version, package_version, projection, vdict, pdict, report, sections


def _prepared_line(version) -> dict[str, str]:
	return {"prepared_by": p.user_name(version.prepared_by), "capacity": cstr(version.prepared_capacity)}


def get_department_approval_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if not authz.holds_any_requisition_responsibility(actor):
		return _forbidden()
	if not task or not frappe.db.exists("Requisition Task", task):
		return {"outcome": "NOT_FOUND"}
	task_doc = frappe.get_doc("Requisition Task", task)
	root = frappe.get_doc("Procurement Requisition", task_doc.requisition)
	try:
		mode, _assignment, _unit = authz.require_department_task_access(records.contributing_units(root), actor)
	except frappe.DoesNotExistError:
		return {"outcome": "NOT_FOUND"}
	version, package_version, projection, vdict, pdict, report, sections = _locked_bundle(root, task_doc.requisition_version)
	decider = mode == "decider" and _has(actor, ROLE_HEAD_OF_USER_DEPARTMENT, root.lead_org_unit_id) and task_doc.status == "Open"
	lead_hod_pre = (
		not authz.is_technical(actor) and _has(actor, ROLE_HEAD_OF_USER_DEPARTMENT, root.lead_org_unit_id)
		and root.current_state in ("Awaiting Department Approval", "Submitted to Procurement") and root.current_version == task_doc.requisition_version
	)
	units = p.ordered_units(vdict["drawdown_lines"], root.lead_org_unit_id)
	both = "both departments’" if len(units) == 2 else ("the departments’" if len(units) > 2 else "the department’s")
	badge = ("Awaiting your approval", "is-attention") if decider else STATE_BADGES.get(root.current_state, (root.current_state, "is-draft"))
	return {
		"outcome": "OK", "kind": "department_task", "mode": "decider" if decider else "reader",
		"header": {**_header(root, version, badge=badge, description="Confirm that the request accurately states the departments’ need and minimum requirements."), "title": "Review departmental requisition", "requirement_title": version.requirement_title},
		"task": {"task": task_doc.name, "status": task_doc.status, "record_version": task_doc.record_version},
		"result": "Ready for departmental submission" if not report.get("blocking_count") else "This requisition has issues that must be resolved first.",
		"context": [
			{"label": "Result", "value": "Ready for departmental submission" if not report.get("blocking_count") else "Not ready"},
			{"label": "Prepared by", "value": p.user_name(version.prepared_by)},
			{"label": "Contributing departments", "value": p.departments_label(units)},
			{"label": "Submitting department", "value": records.unit_name(root.lead_org_unit_id)},
		],
		"question": f"Does this requisition accurately state {both} need and minimum requirements?",
		"certification": "I confirm that this requisition states the departments’ operational need and minimum requirements and may be submitted to Procurement.",
		"decision_chain": _decision_chain(root, version), "sections": sections, "findings": report["findings"],
		"record_details": p.record_details(root=root, version={**vdict, "content_digest": version.content_digest}, projection=projection),
		"actions": {
			"submit_to_procurement": decider and not report.get("blocking_count"), "return_for_correction": decider,
			# REQ-DES-07-SUBMITTED: before authorisation the lead HoD keeps
			# Withdraw and Request Planning correction on the read-only task.
			"withdraw": decider or lead_hod_pre, "request_planning_correction": decider or lead_hod_pre,
		},
		"catalogue": {"affected_sections": _catalogue_meta()["affected_sections"]},
		"requisition": root.name, "root_record_version": root.record_version,
	}


def _funding(root, version, projection) -> dict[str, Any]:
	"""§13.9 — current funding for the whole submission: rows sharing a Budget
	Line are totalled before comparing with its availability, exactly as
	Budget's complete-array check does. Display only; authorisation rechecks."""
	from decimal import Decimal

	rows = authorise_service.funding_rows(version, projection)
	sources = [{"department": records.unit_name(r["source_organisation_unit"]), "requested_value": precision.display_money(r["amount"])} for r in rows]
	positions = funding_gateway.line_positions([r["budget_line"] for r in rows])
	required: dict[str, Decimal] = {}
	for row in rows:
		required[row["budget_line"]] = required.get(row["budget_line"], Decimal(0)) + precision.stored_money(row["amount"])
	lines = []
	for line, need in sorted(required.items()):
		pos = (positions.get(line) or {}).get("positions") or {}
		approved = precision.parse_money(format(Decimal(repr(float(pos.get("approved") or 0))), ".2f"), allow_zero=True)
		available = precision.parse_money(format(Decimal(repr(float(pos.get("available") or 0))), ".2f"), allow_zero=True)
		sufficient = available >= need
		share = int((need / available * 100).to_integral_value()) if available and sufficient else 100
		lines.append(
			{
				"budget_line": (positions.get(line) or {}).get("code") or line, "approved": precision.display_money(approved), "available_now": precision.display_money(available),
				"this_requisition": precision.display_money(need), "available_after": precision.display_money(available - need) if sufficient else "",
				"sufficient": sufficient, "shortfall": precision.display_money(max(Decimal(0), need - available)), "reserved_share": share, "free_share": max(0, 100 - share),
			}
		)
	return {"available": bool(positions), "all_sufficient": all(l["sufficient"] for l in lines), "lines": lines, "sources": sources}


def get_procurement_authorisation_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	if not authz.holds_any_requisition_responsibility(actor):
		return _forbidden()
	if not task or not frappe.db.exists("Requisition Task", task):
		return {"outcome": "NOT_FOUND"}
	task_doc = frappe.get_doc("Requisition Task", task)
	root = frappe.get_doc("Procurement Requisition", task_doc.requisition)
	try:
		mode, _assignment = authz.require_procurement_task_access(actor)
	except frappe.DoesNotExistError:
		return {"outcome": "NOT_FOUND"}
	version, package_version, projection, vdict, pdict, report, sections = _locked_bundle(root, task_doc.requisition_version)
	checks = compatibility.check(projection)
	hold = projection.get("hold") or {}
	funding = _funding(root, version, projection) if task_doc.status == "Open" else {"available": False, "sources": []}
	qty, value = p.totals(vdict)
	failing = [c for c in checks if not c.ok]
	baseline_ok = cstr(projection.get("plan_item_version_id")) == cstr(root.plan_item_version_id)
	if hold.get("held"):
		result = {"tone": "is-warning", "title": "Authorisation is on hold while Planning reviews a correction request.", "detail": " · ".join(f"{r['correction_request']} · {r['status']}" for r in hold.get("unresolved_requests") or [])}
	elif funding.get("available") and not funding.get("all_sufficient"):
		result = {"tone": "is-critical", "title": "Cannot authorise — insufficient funding", "detail": ""}
	elif failing or report.get("blocking_count") or not projection.get("eligible") or not baseline_ok:
		result = {"tone": "is-critical", "title": "Cannot authorise — a procurement check failed", "detail": failing[0].failure if failing else ""}
	else:
		result = {"tone": "is-live", "title": "Ready to authorise", "detail": f"Authorising will reserve {precision.display_money(value)} and allow Tender Preparation to begin."}
	decider = mode == "decider" and task_doc.status == "Open"
	can_authorise = decider and result["title"] == "Ready to authorise" and not records.authoriser_conflict(version, actor)
	submit = records.decision_of(version.name, "Submit to Procurement")
	units = sorted(records.contributing_units(root))
	after = funding.get("lines", [{}])[0].get("available_after", "") if funding.get("lines") else ""
	return {
		"outcome": "OK", "kind": "procurement_task", "mode": "decider" if decider else "reader",
		"header": {**_header(root, version, badge=("Submitted to Procurement", "is-draft"), description="Review the request, current funding and procurement checks before authorising it."), "title": "Authorise requisition", "requirement_title": version.requirement_title},
		"task": {"task": task_doc.name, "status": task_doc.status, "record_version": task_doc.record_version},
		"result": result, "question": "Can this complete requisition lawfully use the approved-plan amount and current funding now?",
		"funding": funding,
		"planning": {
			"status": "Eligible" if projection.get("eligible") and baseline_ok else "Not eligible",
			"quantity_available": precision.display_quantity(sum((precision.planning_quantity(s.get("remaining_quantity") or "0") for s in projection.get("sources", [])), precision.planning_quantity("0"))),
			"value_available": precision.display_money(projection.get("remaining_value") or "0"),
			"hold": "None unresolved" if not hold.get("held") else f"{len(hold.get('unresolved_requests') or [])} unresolved",
			"hold_requests": hold.get("unresolved_requests") or [],
			"scope": "Existing procurement scope" if (projection.get("scope") or {}).get("locked") else "No authorised requisition yet",
		},
		"certification": {
			"submitted_by": p.user_name(version.submitted_by), "lead_department": records.unit_name(version.certified_lead_org_unit_id),
			"submitted_at": p.eat(version.submitted_at), "decision": submit.name if submit else "",
		},
		"change_department": {"available": decider and len(units) > 1, "options": [{"value": u, "label": records.unit_name(u)} for u in units], "current": root.lead_org_unit_id},
		"checks": {"summary": f"{sum(1 for c in checks if c.ok)} checks passed" if not failing else f"{len(failing)} check{'s' if len(failing) != 1 else ''} failed", "rows": [c.as_dict() for c in checks], "open": bool(failing)},
		"decision_chain": _decision_chain(root, version), "sections": sections,
		"statement": "I authorise this requisition. The approved-plan amounts will be used, funding will be reserved and Tender Preparation may begin.",
		"confirmation": {
			"quantity": precision.display_quantity(qty), "value": precision.display_money(value),
			"budget_line": ", ".join(l["budget_line"] for l in funding.get("lines", [])), "available_after": after,
			"text": f"The approved-plan amounts will be used, {'two' if len(vdict['drawdown_lines']) == 2 else len(vdict['drawdown_lines'])} funding reservation{'s' if len(vdict['drawdown_lines']) != 1 else ''} will be created and Tender Preparation may begin.",
		},
		"record_details": p.record_details(root=root, version={**vdict, "content_digest": version.content_digest}, projection=projection),
		"actions": {
			"authorise": can_authorise, "return_to_department": decider, "request_planning_correction": decider,
			"change_submitting_department": decider and len(units) > 1, "refresh": decider, "view_planning_request": bool(hold.get("held")),
		},
		"catalogue": {"affected_sections": _catalogue_meta()["affected_sections"]},
		"requisition": root.name, "root_record_version": root.record_version,
	}


def get_locked_requisition(*, root, actor: str) -> dict[str, Any]:
	"""A pre-authorisation locked record read outside its task route
	(REQ-DES-07-SUBMITTED, Withdrawn), plus the technical reader."""
	version, package_version, projection, vdict, pdict, report, sections = _locked_bundle(root, root.current_version)
	is_lead_hod = _has(actor, ROLE_HEAD_OF_USER_DEPARTMENT, root.lead_org_unit_id) and not authz.is_technical(actor)
	withdrawn = records.decision_of(version.name, "Withdraw requisition") if root.current_state == "Withdrawn" else None
	pre = root.current_state in ("Awaiting Department Approval", "Submitted to Procurement")
	return {
		"outcome": "OK", "kind": "locked", "mode": "technical" if authz.is_technical(actor) else "reader",
		"header": _header(root, version, description=""), "sections": sections, "decision_chain": _decision_chain(root, version),
		"withdrawn": {"by": p.user_name(withdrawn.actor), "at": p.eat(withdrawn.decided_at), "reason": withdrawn.reason} if withdrawn else None,
		"record_details": p.record_details(root=root, version={**vdict, "content_digest": version.content_digest}, projection=projection),
		"actions": {"withdraw": is_lead_hod and pre, "request_planning_correction": pre and (is_lead_hod or _has(actor, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)), "export": True},
		"requisition": root.name, "root_record_version": root.record_version,
	}


def get_version_review(*, root, version_name: str, actor: str) -> dict[str, Any]:
	"""History: the exact earlier Version as a complete read-only review."""
	if not frappe.db.exists("Requisition Version", {"name": version_name, "requisition": root.name}):
		return {"outcome": "NOT_FOUND"}
	version, package_version, projection, vdict, pdict, report, sections = _locked_bundle(root, version_name)
	decision = None
	for name in ("Return for correction", "Return to department", "Change submitting department and return", "Withdraw requisition", "Revoke authorisation"):
		decision = records.decision_of(version.name, name)
		if decision:
			break
	return {
		"outcome": "OK", "kind": "version", "header": _header(root, version, badge=(version.version_status, "is-critical" if version.version_status == "Returned" else "is-draft")),
		"decision": {"by": p.user_name(decision.actor), "at": p.eat(decision.decided_at), "reason": decision.reason, "affected_section": decision.affected_section, "decision": decision.decision} if decision else None,
		"current_draft_route": f"/app/procurement-requisitions/{root.name}" if root.current_state == "Draft" else "",
		"sections": sections, "record_details": p.record_details(root=root, version={**vdict, "content_digest": version.content_digest}, projection=projection),
		"actions": {"export": True}, "requisition": root.name,
	}


def get_authorised_requisition(*, root, actor: str) -> dict[str, Any]:
	"""§13.11 REQ-DES-10 — the authorised (or revoked) record."""
	version_name = root.authorised_version or root.current_version
	if root.current_state == "Revoked":
		version_name = frappe.db.get_value("Requisition Version", {"requisition": root.name, "version_status": "Revoked"}, "name", order_by="version_number desc") or version_name
	version, package_version, projection, vdict, pdict, report, sections = _locked_bundle(root, version_name)
	handoff = frappe.get_doc("Authorised Requisition Handoff", {"requisition_version": version.name}) if frappe.db.exists("Authorised Requisition Handoff", {"requisition_version": version.name}) else None
	payload = json.loads(handoff.payload_json or "{}") if handoff else {}
	lines = payload.get("drawdown_lines") or []
	authorise = records.decision_of(version.name, "Authorise requisition")
	revoke = records.decision_of(version.name, "Revoke authorisation")
	consumed = bool(handoff and handoff.consumed_at)
	tender = cstr(handoff.tender) if handoff else ""
	tender_ref = cstr(frappe.db.get_value("Tender", tender, "tender_reference") or tender) if tender and frappe.db.exists("DocType", "Tender") and frappe.db.exists("Tender", tender) else tender
	is_hopf = _has(actor, ROLE_HEAD_OF_PROCUREMENT_FUNCTION)
	is_officer = _has(actor, ROLE_PROCUREMENT_OFFICER)
	scope = records.edit_scope(root, actor)
	qty, value = p.totals(vdict)
	reservations = []
	for line in lines:
		code = cstr(frappe.db.get_value("Funding Reservation", line.get("reservation_id"), "generated_reference") or line.get("reservation_reference") or line.get("reservation_id"))
		reservations.append({"reservation": code, "department": records.unit_name(line.get("contributing_org_unit")), "value": precision.display_money(line.get("requested_value") or "0")})
	correction_draft = False
	if root.current_state == "Revoked" and scope["shared"] and not authz.is_technical(actor):
		correction_draft = cstr(projection.get("plan_item_version_id")) == cstr(root.plan_item_version_id) and bool(projection.get("eligible")) and not records.open_root_for(root.plan_item_id)
	vwith = {**vdict, "content_digest": version.content_digest, "drawdown_lines": [{**l, "reservation_code": r["reservation"]} for l, r in zip(vdict["drawdown_lines"], reservations)] if reservations else vdict["drawdown_lines"]}
	revoked = None
	if revoke:
		revoked = {"by": p.user_name(revoke.actor), "at": p.eat(revoke.decided_at), "reason": revoke.reason, "planning_reversal": "; ".join(f"REV-{l.get('planning_drawdown_reference')}" for l in lines if l.get("planning_drawdown_reference")), "funding_releases": "; ".join(r["reservation"] for r in reservations)}
	badge = ("Authorisation revoked", "is-critical") if root.current_state == "Revoked" else ("Authorised", "is-live")
	return {
		"outcome": "OK", "kind": "authorised", "state": root.current_state,
		"mode": "technical" if authz.is_technical(actor) else ("hopf" if is_hopf else ("officer" if is_officer else "reader")),
		"header": {**_header(root, version, badge=badge, description="This requisition is authorised and ready for Tender Preparation." if root.current_state == "Authorised" and not consumed else ""), "tagline": " · ".join(v for v in (projection.get("procurement_method"), f"Reserved for {p.reserved_for(payload.get('reservation_category'))}" if payload else "", payload.get("lotting_indicator")) if v)},
		"facts": [
			{"label": "Authorised by", "value": p.user_name(authorise.actor) if authorise else ""},
			{"label": "Authorised at", "value": p.eat(authorise.decided_at) if authorise else ""},
			{"label": "Requisition value", "value": precision.display_money(value)},
			{"label": "Tender Preparation", "value": "Started" if consumed else "Not started"},
		],
		"consumed": {"tender": tender, "tender_reference": tender_ref, "route": f"/app/tenders/{tender}" if tender else ""} if consumed else None,
		"revoked": revoked, "decision_chain": _decision_chain(root, version), "sections": sections, "reservations": reservations,
		"handoff": {"handoff": handoff.name, "digest": handoff.handoff_digest, "version": handoff.handoff_version} if handoff else None,
		"record_details": p.record_details(root=root, version=vwith, projection=projection, handoff=handoff),
		"actions": {
			"continue_to_tender_preparation": root.current_state == "Authorised" and not consumed and is_officer and not authz.is_technical(actor),
			"open_tender": consumed, "revoke": root.current_state == "Authorised" and not consumed and is_hopf and not authz.is_technical(actor),
			"start_corrected_draft": correction_draft, "export": True,
		},
		"tender_route": f"/app/tenders/new/{handoff.name}" if handoff and not consumed else "",
		"requisition": root.name, "root_record_version": root.record_version,
	}


def export_requisition(*, requisition: str, version: str | None = None, user: str | None = None) -> dict[str, Any]:
	"""§13.13 Export — the authorised read-only export of the exact displayed
	Version: the same read, with the same masking, minus the actor's controls.
	No lifecycle change and no wider access than the read itself."""
	record = get_requisition_record(requisition=requisition, version=version, user=user)
	if record.get("outcome") != "OK":
		return {"outcome": record.get("outcome")}
	document = {k: v for k, v in record.items() if k not in ("actions", "catalogue", "outcome")}
	header = record.get("header") or {}
	filename = f"{header.get('reference') or requisition}-v{header.get('version_number') or ''}.json"
	return {"outcome": "OK", "filename": filename, "content": json.dumps(document, default=str, indent=2, ensure_ascii=False)}


# --------------------------------------------------------------------------
# REQ-DES-11 — stopped work
# --------------------------------------------------------------------------


def get_stopped_requisition(*, root, actor: str) -> dict[str, Any]:
	version, package_version, projection, vdict, pdict, report, sections = _locked_bundle(root, root.current_version)
	try:
		facts = eligibility_gateway.correction_request_facts(requisition_reference=root.requisition_reference)
		unavailable = False
	except Exception:  # noqa: BLE001 — owner read unavailable is shown, never guessed
		facts, unavailable = [], True
	request = next((f for f in facts if f["correction_request"] == root.planning_correction_request_id), None)
	outcome = correction.terminal_outcome(root)
	status = request["status"] if request else "Open"
	started = next((d for d in (request or {}).get("dispositions", []) if d["action"] == "Start"), None)
	if outcome:
		status = outcome.outcome
	labels = {
		"Open": ("Awaiting Planning correction", "is-attention"), "In progress": ("Planning correction in progress", "is-attention"),
		"Resolved": ("Planning correction completed", "is-live"), "Closed without change": ("Planning request closed without change", "is-pending"),
	}
	label, tone = labels.get(status, labels["Open"])
	others = [r for r in (projection.get("hold") or {}).get("unresolved_requests") or [] if r["correction_request"] != root.planning_correction_request_id]
	is_planner = _has(actor, ROLE_PROCUREMENT_PLANNER)
	scope = records.edit_scope(root, actor)
	may_start = False
	fresh = None
	if outcome and scope["units"] and not authz.is_technical(actor):
		fresh_item = json.loads(outcome.replacement_lineage_json or "{}").get("plan_item_id") if outcome.outcome == "Resolved" else root.plan_item_id
		try:
			current = eligibility_gateway.get_requisition_eligible_plan_item(fresh_item or root.plan_item_id)
		except frappe.DoesNotExistError:
			current = {"eligible": False}
		checks_ok = compatibility.first_failure(current) is None if current.get("eligible") else False
		may_start = bool(current.get("eligible")) and checks_ok and not records.open_root_for(fresh_item or root.plan_item_id)
		fresh = {
			"heading": "Start a new requisition?",
			"text": "Use the Active corrected Planning facts shown. Earlier decisions and funding reservations will not be copied." if outcome.outcome == "Resolved" else "Use the unchanged approved Planning facts. Complete departmental submission and Procurement authorisation again.",
			"facts": [
				{"label": "Stopped requisition", "value": root.requisition_reference},
				{"label": "Current Plan", "value": cstr(current.get("plan_reference"))},
				{"label": "Current Plan Version", "value": cstr(current.get("plan_version_id"))},
				{"label": "Current eligibility", "value": "Eligible" if may_start else "Not eligible"},
			],
			"blocked_message": "" if may_start else "A new requisition cannot be prepared: current Plan funding confirmation is required." if current.get("funding_state") not in (None, "Confirmed") else ("" if may_start else "A new requisition cannot be prepared against the current approved purchase."),
		}
	stop = records.decision_of(version.name, "Request Planning correction")
	chain = [
		{"title": "Requisition submitted to Procurement", "meta": f"{p.date_label(version.submitted_at)} · {p.user_name(version.submitted_by)}", "tone": "is-live"} if version.submitted_at else {"title": "Draft prepared", "meta": f"{p.date_label(version.creation)} · {p.user_name(version.prepared_by)}", "tone": "is-live"},
		{"title": "Planning correction requested · work stopped", "meta": f"{p.eat(stop.decided_at) if stop else ''} · {root.planning_correction_request_id}", "tone": "is-critical"},
		{"title": "Planning review", "meta": f"{p.user_name(started['actor'])} began review on {p.eat(started['disposed_at'])}" if started else "Awaiting Procurement Planner", "tone": "is-live" if outcome else "is-attention", "upcoming": False},
		{"title": "Outcome recorded", "meta": status if outcome else "This requisition will not reopen automatically", "tone": "is-live" if outcome else "is-pending", "upcoming": not outcome},
	]
	outcome_text = ""
	if outcome and outcome.outcome == "Resolved":
		lineage = json.loads(outcome.replacement_lineage_json or "{}")
		outcome_text = f"{outcome.correcting_plan_version_id} is Active; replacement {lineage.get('plan_item_id')} item version {lineage.get('plan_item_version_id')} is eligible; resolved by {p.user_name(outcome.decided_by)}."
	elif outcome:
		outcome_text = f"{outcome.reason} Decided by {p.user_name(outcome.decided_by)}."
	return {
		"outcome": "OK", "kind": "stopped", "status": status, "status_label": label, "status_tone": tone,
		"header": {**_header(root, version, badge=(label, tone), description="Planning is reviewing an approved-plan issue. This requisition is preserved and cannot be edited or resumed.")},
		"request": {
			"reference": root.planning_correction_request_id, "status": f"{root.planning_correction_request_id} · {request['status'] if request else 'Open'}",
			"plan_item": root.plan_item_id, "reason": (request or {}).get("reason") or (stop.reason if stop else ""),
			"requested_by": p.user_name((request or {}).get("requested_by") or (stop.actor if stop else "")), "requested_at": p.eat((request or {}).get("requested_at") or (stop.decided_at if stop else "")),
			"started": f"{p.user_name(started['actor'])} began review on {p.eat(started['disposed_at'])}" if started else "",
		},
		"outcome_text": outcome_text, "unchanged_notice": "The approved Planning facts have not changed. This requisition will not restart." if outcome and outcome.outcome == "Closed without change" else "",
		"unavailable": unavailable, "other_unresolved": [{"reference": r["correction_request"], "status": r["status"]} for r in others],
		"hold_notice": f"Authorisation remains on hold: {len(others)} Planning request{' is' if len(others) == 1 else 's are'} still unresolved." if others else "",
		"correction_chain": chain, "sections": sections, "fresh_start": fresh,
		"record_details": p.record_details(root=root, version={**vdict, "content_digest": version.content_digest}, projection=projection),
		"actions": {
			"view_planning_request": not is_planner, "open_planning_task": is_planner, "start_new_requisition": may_start,
			"try_again": unavailable, "export": True,
		},
		"planning_route": f"/app/procurement-planning/correction/{root.planning_correction_request_id}",
		"requisition": root.name, "root_record_version": root.record_version,
	}


# --------------------------------------------------------------------------
# Handoff and history
# --------------------------------------------------------------------------


def get_authorised_requisition_handoff(*, requisition: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	root = _reader(requisition, actor)
	if not root.handoff:
		authz.not_found()
	doc = frappe.get_doc("Authorised Requisition Handoff", root.handoff)
	return {"handoff": doc.name, "handoff_version": doc.handoff_version, "handoff_digest": doc.handoff_digest, "payload": json.loads(doc.payload_json or "{}"), "consumed_at": cstr(doc.consumed_at), "tender": doc.tender}


def list_eligible_handoffs(*, user: str | None = None) -> list[dict[str, Any]]:
	"""Authorised, unconsumed v1.4 handoffs a Tender may start from."""
	principal = cstr(user or frappe.session.user)
	if not principal or principal == "Guest":
		return []
	if not any(authz.can_read_site(role, principal) for role in TENDER_SEAM_READER_ROLES) and not authz.is_technical(principal):
		return []
	out = []
	for row in frappe.get_all("Authorised Requisition Handoff", filters={"consumed_at": ("is", "not set"), "handoff_version": handoff_service.HANDOFF_VERSION}, fields=["name", "requisition", "requisition_version", "handoff_digest", "handoff_version", "generated_at"], order_by="generated_at asc"):
		root = frappe.db.get_value("Procurement Requisition", row.requisition, ["name", "requisition_reference", "plan_item_id", "current_state", "handoff"], as_dict=True)
		if not root or root.current_state != "Authorised" or root.handoff != row.name:
			continue
		payload = json.loads(frappe.db.get_value("Authorised Requisition Handoff", row.name, "payload_json") or "{}")
		out.append(
			{
				"handoff": row.name, "handoff_version": row.handoff_version, "handoff_digest": row.handoff_digest, "authorised_at": p.eat(row.generated_at),
				"requisition": root.name, "requisition_reference": root.requisition_reference, "requisition_version": row.requisition_version,
				"plan_item_id": root.plan_item_id, "requirement_title": payload.get("requirement_title", ""), "planned_method": payload.get("planned_method", ""),
				"reservation_category": payload.get("reservation_category", ""), "lotting_indicator": payload.get("lotting_indicator", ""),
				"latest_delivery_date": payload.get("latest_delivery_date", ""), "latest_delivery_date_label": p.date_label(payload.get("latest_delivery_date")),
			}
		)
	return out


def get_requisition_history(*, requisition: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	root = _reader(requisition, actor)
	versions = frappe.get_all("Requisition Version", filters={"requisition": root.name}, fields=["name", "version_number", "version_status", "based_on_version", "content_digest", "certified_lead_org_unit_id", "submitted_by", "submitted_at"], order_by="version_number asc")
	decisions = frappe.get_all("Requisition Decision", filters={"requisition_version": ("in", [v.name for v in versions] or ("",))}, fields=["name", "requisition_version", "actor", "legal_capacity", "decision", "reason", "affected_section", "new_lead_org_unit_id", "decided_at"], order_by="decided_at asc")
	outcomes = frappe.get_all("Requisition Correction Outcome", filters={"requisition": root.name}, fields=["name", "event_id", "correction_request_id", "outcome", "producer_sequence", "status", "received_at", "quarantine_reason"], order_by="creation asc")
	events_rows = frappe.get_all("Requisition Event", filters={"requisition": root.name}, fields=["event_id", "event_type", "sequence", "occurred_at", "status"], order_by="sequence asc")
	return {
		"requisition": root.name, "reference": root.requisition_reference,
		"versions": [{**v, "submitted_at": p.eat(v.submitted_at), "route": f"/app/procurement-requisitions/{root.name}?version={v.name}"} for v in versions],
		"decisions": [{**d, "actor_name": p.user_name(d.actor), "decided_at": p.eat(d.decided_at)} for d in decisions],
		"outcomes": outcomes, "events": events_rows, "prior_requisition": root.prior_requisition_id,
	}
