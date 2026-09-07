# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 §10.1 — the seven read services. Reads never create a
root, Version, package, row, task, decision, drawdown, reservation or
handoff (§10.1's own closing line); every function here only loads and
projects.

`GetRequisitionWorkspace` is verdict-first per KT-STD-001 §3A: the caller's
page-level verdict (`holds_any_requisition_responsibility`) is resolved
before anything else runs, exactly the way `plan_read.py`'s own workspace
read starts (see AGENTS.md §6.4/§4.3 — never rely on a client check).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, fmt_money, formatdate

from kentender_procurement.procurement_requisitions.services import (
	catalogue,
	compatibility,
	digest,
	eligibility_gateway,
	funding_gateway,
	validation,
)
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.draft_commands import _contributing_units, _load, _package_dict, _version_dict
from kentender_procurement.procurement_requisitions.services.errors import ProcurementRequisitionsError, fail
from kentender_procurement.procurement_requisitions.services.requisition_roles import ROLE_HEAD_OF_PROCUREMENT_FUNCTION


def _money(amount: float) -> str:
	"""§13.2's fixture values are always written to two decimal places
	("KES 50,000,000.00"), never a rounded whole number."""
	return f"KES {fmt_money(flt(amount), precision=2, currency=None).strip()}"


def _date(value) -> str:
	return formatdate(value, "d MMM yyyy") if value else ""


def _eat(value) -> str:
	"""A UTC instant rendered as EAT (mirrors Planning's own `plan_read._eat`,
	§12.13's convention) — found live via REQ-402's own evidence-capture
	screenshot showing the raw stored UTC string instead of the artboard's
	"15 Mar 2027, 10:00 EAT" form."""
	if not value:
		return ""
	from frappe.utils import convert_utc_to_timezone, format_datetime, get_datetime

	local = convert_utc_to_timezone(get_datetime(value), "Africa/Nairobi")
	return f"{format_datetime(local, 'd MMM yyyy, HH:mm')} EAT"


def _ou_label(ou: str) -> str:
	return cstr(frappe.db.get_value("Organisation Unit", ou, "unit_name") or ou) if ou else ""


def _delivery_location_label(location: str) -> str:
	return cstr(frappe.db.get_value("Delivery Location", location, "location_name") or location) if location else ""


def _business_need_and_result(sources: list[dict[str, Any]]) -> tuple[str, str]:
	"""§13.4/§13.5's combined "one line per Plan Item" business need and
	expected operational result — the same rule `handoff.py::build_payload`
	already applies, so every screen and the handoff itself derive these two
	lines from one place, never a second independently-drifting copy."""
	business_need = "; ".join(sorted({s.get("description", "") for s in sources if s.get("description")}))
	expected_result = "; ".join(sorted({s.get("expected_operational_result", "") for s in sources if s.get("expected_operational_result")}))
	return business_need, expected_result


def list_delivery_locations() -> list[dict[str, str]]:
	"""§13.5's "Delivery location" control — a Location Link — needs real
	options, not a single hardcoded fixture value; Active locations only
	(§2 D2: a Retired location is never offered for a new choice)."""
	return frappe.get_all("Delivery Location", filters={"status": "Active"}, fields=["name", "location_name"], order_by="location_name asc", limit_page_length=0)


def _objective_label(strategic_objective: str) -> str:
	"""§13.4's "Strategic Objective" line needs the objective's own title —
	the projection's own `objective_path` is deliberately ancestor-only
	(`strategy_gateway.list_eligible_strategic_objectives`'s own comment:
	"the objective's title is the field above it"), so this is a direct
	Link-target label read, the same pattern `_ou_label` already uses.

	Deliberately returns "" (not the id again) when the node cannot be
	found: a Plan Item's frozen `strategic_objective` snapshot can outlive
	the Strategy Node it once pointed to (a live, pre-existing dangling
	reference was found this way on the real MOH-2027-002 fixture item
	while browser-verifying this screen) — falling back to the id would
	render "rmndhav4vq — rmndhav4vq", which reads as broken rather than as
	the graceful degradation it actually is."""
	if not strategic_objective:
		return ""
	return cstr(frappe.db.get_value("Strategy Node", strategic_objective, "title") or "")


def _can(fn, *args, **kwargs) -> bool:
	"""Read-offer parity: true only if the exact command gate that guards
	the action would let this actor through — never a second, drifting
	copy of the rule."""
	try:
		fn(*args, **kwargs)
		return True
	except (ProcurementRequisitionsError, frappe.DoesNotExistError, frappe.PermissionError):
		return False


def _requisition_summary(root) -> dict[str, Any]:
	return {
		"requisition": root.name,
		"requisition_reference": root.requisition_reference,
		"plan_item_id": root.plan_item_id,
		"title": frappe.db.get_value("Requisition Version", root.current_version, "requirement_title") or "",
		"current_state": root.current_state,
		"lead_org_unit": root.lead_org_unit,
		"lead_org_unit_label": _ou_label(root.lead_org_unit),
		"contributing_org_unit_ids": sorted(_contributing_units(root)),
		"record_version": root.record_version,
	}


def _department_label_list(contributing_units: list[str], values_by_unit: dict[str, float], *, sep: str = ", ") -> str:
	"""§13.2/13.3/13.4 order departments by their own contributed value,
	largest first — the same rule that names the lead department (§5.1) —
	rather than an arbitrary alphabetical or insertion order. Different
	screens join this list with a different separator (the workspace card
	uses ", ", the Start screen's source panel uses " · "), so the caller
	picks it rather than this function guessing which screen is asking."""
	ordered = sorted(contributing_units, key=lambda u: values_by_unit.get(u, 0), reverse=True)
	return sep.join(_ou_label(u) for u in ordered)


def _ready_to_prepare_card(actor: str) -> dict[str, Any] | None:
	"""REQ-DES-01 — one card, present only when at least one Plan Item is
	both eligible and not already the subject of an open Requisition; one
	row per eligible item (never a table), under a single count headline.

	Read-offer parity with `prepare_it_equipment_requisition`'s own gate
	(`require_draft_author_for_any`): only a Departmental Author or Head of
	User Department for one of an item's own contributing units sees a row
	for it. Every other Requisitions-holding role (Head of Procurement
	Function, Procurement Planner, Auditor) legitimately reads the rest of
	the workspace but is never offered an action the command layer would
	itself refuse — confirmed live: Charles Mutiso (Head of Procurement
	Function) clicking "Prepare Requisition" hit a masked `REQ_NOT_FOUND`
	from the command's own gate before this fix."""
	eligible_items = eligibility_gateway.list_requisition_eligible_plan_items()
	open_by_plan_item = set(
		frappe.get_list(
			"Procurement Requisition", filters={"current_state": ("not in", ("Authorised", "Withdrawn", "Revoked"))}, pluck="plan_item_id",
		)
	)
	rows = []
	for item in eligible_items:
		if item["plan_item_id"] in open_by_plan_item:
			continue
		units = item.get("contributing_org_unit_ids") or []
		if not _can(authz.require_draft_author_for_any, set(units), actor, masked=False):
			continue
		# per-unit value is not returned by the listing projection (only the
		# item total); the detail projection's own `sources` carries it, but
		# calling it per row here would be one extra round trip per row —
		# acceptable at workspace scale, and the same cost `get_eligible_plan_item_detail`
		# already pays once a user opens the Start screen for this same item.
		detail = eligibility_gateway.get_requisition_eligible_plan_item(item["plan_item_id"])
		values_by_unit: dict[str, float] = {}
		for source in detail.get("sources", []):
			values_by_unit[source["organisation_unit"]] = values_by_unit.get(source["organisation_unit"], 0) + flt(source.get("remaining_amount"))
		rows.append(
			{
				"plan_item_id": item["plan_item_id"],
				"supporting": f"{item['title']} · {_department_label_list(units, values_by_unit)} · {_money(item['remaining_value'])}",
				"route": ["procurement-requisitions", "new", item["plan_item_id"]],
			}
		)
	if not rows:
		return None
	noun = "Plan Item" if len(rows) == 1 else "Plan Items"
	return {"headline": f"{len(rows)} {noun} ready to prepare", "rows": rows}


_STATE_STATUS: dict[str, tuple[str, str]] = {
	"Draft": ("Draft", "is-draft"),
	"Awaiting Department Approval": ("Awaiting Department Approval", "is-draft"),
	"Submitted to Procurement": ("Submitted to Procurement", "is-draft"),
	"Authorised": ("Authorised", "is-live"),
	"Withdrawn": ("Withdrawn", "is-draft"),
	"Revoked": ("Revoked", "is-draft"),
	"Upstream correction required": ("Upstream correction required", "is-attention"),
}


def _your_requisitions_rows(actor: str) -> list[dict[str, Any]]:
	"""REQ-DES-01 — one connected list: every Requisition this actor has a
	stake in (visible under the same permission scope `permission_query_conditions`
	enforces), whatever its stage. A row awaiting this actor's own open
	decision reads as that decision, not a plain state label (§13.3)."""
	roots = frappe.get_list(
		"Procurement Requisition",
		fields=["name", "requisition_reference", "plan_item_id", "current_version", "current_state", "lead_org_unit"],
		order_by="modified desc", limit_page_length=0,
	)
	if not roots:
		return []
	open_tasks = frappe.get_all(
		"Requisition Task", filters={"requisition": ("in", [r.name for r in roots]), "status": "Open"},
		fields=["name", "requisition", "business_role", "organisation_unit"],
	)
	tasks_by_requisition: dict[str, Any] = {t.requisition: t for t in open_tasks}
	titles = {
		v.name: v.requirement_title
		for v in frappe.get_all("Requisition Version", filters={"name": ("in", [r.current_version for r in roots if r.current_version])}, fields=["name", "requirement_title"])
	}
	rows = []
	for root in roots:
		title = titles.get(root.current_version) or ""
		status, status_kind = _STATE_STATUS.get(root.current_state, (root.current_state, "is-draft"))
		action_label, route = "", []
		task = tasks_by_requisition.get(root.name)
		if task and task.business_role == "Head of User Department" and _can(authz.require_hod_for_any, {task.organisation_unit}, actor, masked=False):
			status, status_kind = "Awaiting your approval", "is-attention"
			action_label, route = "Review", ["procurement-requisitions", "department-task", task.name]
		elif task and task.business_role == ROLE_HEAD_OF_PROCUREMENT_FUNCTION and _can(authz.require_hopf, actor, masked=False):
			status, status_kind = "Awaiting your approval", "is-attention"
			action_label, route = "Review", ["procurement-requisitions", "procurement-task", task.name]
		elif root.current_state == "Draft":
			action_label, route = "Continue", ["procurement-requisitions", root.name]
		elif root.current_state == "Authorised":
			action_label, route = "View", ["procurement-requisitions", root.name, "authorised"]
		rows.append(
			{
				"requisition": root.name, "requisition_reference": root.requisition_reference, "plan_item_title": title,
				"status": status, "status_kind": status_kind, "action_label": action_label, "route": route,
			}
		)
	return rows


def get_requisition_workspace(*, user: str | None = None) -> dict[str, Any]:
	"""§10.1/§13.3/§14.1 — the "Ready to prepare" card and the one connected
	"Your Requisitions" list, verdict-first (KT-STD-001 §3A)."""
	from kentender_procurement.procurement_requisitions.services.requisition_roles import FORBIDDEN_RESPONSIBILITIES

	actor = authz.actor(user)
	if not authz.holds_any_requisition_responsibility(actor):
		return {
			"outcome": "FORBIDDEN",
			"forbidden": {
				"heading": "You do not have access to Procurement Requisitions.",
				"text": f"This area needs one of these responsibilities: {FORBIDDEN_RESPONSIBILITIES}. Ask your KenTender administrator to assign one in System setup.",
			},
		}

	rows = _your_requisitions_rows(actor)
	return {
		"outcome": "OK",
		"ready_to_prepare": _ready_to_prepare_card(actor),
		"requisitions": rows,
		"count_label": f"{len(rows)} Requisition" + ("" if len(rows) == 1 else "s"),
	}


def get_eligible_plan_item_detail(*, plan_item_id: str, user: str | None = None) -> dict[str, Any]:
	"""§10.1/§13.4 `GetEligiblePlanItemDetail` — the complete Planning
	projection, current remaining balances, reservation category and
	lotting indicator. No mutation; Planning's own gate decides visibility.

	`contributing_departments_label` and the combined `business_need`/
	`expected_operational_result` lines are computed here (not left to the
	client) so the Start screen (§13.4) and the eventual handoff payload
	(`handoff.py::build_payload`) derive the same "one line per Plan Item"
	summary from the same rule, never two independently-drifting copies.

	`can_prepare` is read-offer parity with `prepare_it_equipment_requisition`'s
	own gate: a Head of Procurement Function/Planner/Auditor can legitimately
	load this screen (they hold a Requisitions responsibility, so the
	workspace's own row can still route them here) but is never offered the
	one action the command layer would itself refuse."""
	actor = authz.actor(user)
	projection = eligibility_gateway.get_requisition_eligible_plan_item(plan_item_id)
	compat = compatibility.check(projection)
	sources = projection.get("sources", [])
	units = projection.get("contributing_org_unit_ids") or []
	values_by_unit: dict[str, float] = {}
	for source in sources:
		values_by_unit[source["organisation_unit"]] = values_by_unit.get(source["organisation_unit"], 0) + flt(source.get("remaining_amount"))
	business_need, expected_result = _business_need_and_result(sources)
	return {
		"outcome": "OK", "projection": projection,
		"contributing_departments_label": _department_label_list(units, values_by_unit, sep=" · "),
		# Planning's own `sources[].organisation_unit` is a bare id — the
		# published `get_requisition_eligible_plan_item` contract has its
		# own field-completeness test this module must never grow beyond
		# by mutating that dict, so the display label is a companion map
		# alongside it instead.
		"organisation_unit_labels": {u: _ou_label(u) for u in units},
		"strategic_objective_title": _objective_label(projection.get("strategic_objective")),
		"business_need": business_need,
		"expected_operational_result": expected_result,
		"compatibility": [{"test": r.test, "required": r.required, "actual": r.actual, "ok": r.ok} for r in compat],
		"is_compatible": all(r.ok for r in compat),
		"open_requisition": frappe.db.get_value("Procurement Requisition", {"plan_item_id": plan_item_id, "current_state": ("not in", ("Authorised", "Withdrawn", "Revoked"))}, "name") or "",
		"can_prepare": _can(authz.require_draft_author_for_any, set(units), actor, masked=False),
	}


def _drawdown_context(version_dict: dict[str, Any], projection: dict[str, Any]) -> list[dict[str, Any]]:
	"""§13.5/13.10's drawdown table: each Draft (or locked) drawdown line
	paired with its own live Planning source (department label, current
	remaining balance) — the same shape `authorise.py` itself reads at
	submission time, so every screen that shows this table shows the exact
	numbers a submit/authorise would recheck."""
	sources_by_line = {s["plan_item_line_id"]: s for s in projection.get("sources", [])}
	return [
		{
			"drawdown_line_id": line["drawdown_line_id"],
			"organisation_unit": line["contributing_org_unit"],
			"organisation_unit_label": _ou_label(line["contributing_org_unit"]),
			"source_title": (sources_by_line.get(line["plan_item_line_id"]) or {}).get("title", ""),
			"remaining_quantity": line.get("remaining_quantity"),
			"remaining_value": line.get("remaining_value"),
			"unit": line.get("unit"),
		}
		for line in version_dict.get("drawdown_lines", [])
	]


# §13.11's compatibility table renders friendlier prose for a passing row
# than `compatibility.py`'s own internal test/actual identifiers carry —
# that module's own docstring is explicit these are validation identifiers,
# not display copy, so the translation lives here, at the read boundary,
# never inside the shared validation service. A failing row always shows
# its own real `actual` value instead — the friendly gloss only describes
# the confirmed-good state, never something to hide a real mismatch behind.
_COMPATIBILITY_TEST_LABELS: dict[str, str] = {
	"procurement_category": "procurement_category", "requirement_type": "Requirement type",
	"reservation_category": "Reservation category", "lotting_indicator": "Lotting indicator",
	"currency": "Currency", "award_packages": "Award package",
}
_COMPATIBILITY_OK_GLOSS: dict[str, str] = {"requirement_type": "Straightforward IT equipment", "award_packages": "One"}


def _compatibility_rows(compat: list) -> list[dict[str, Any]]:
	return [
		{
			"test": _COMPATIBILITY_TEST_LABELS.get(r.test, r.test),
			"actual": _COMPATIBILITY_OK_GLOSS.get(r.test, r.actual) if r.ok else r.actual,
			"ok": r.ok,
		}
		for r in compat
	]


def _prepared_by(root) -> dict[str, str]:
	"""§13.10's "Prepared by <name>, <role>" line: the actual preparer is
	whoever created the root (`prepare_it_equipment_requisition`'s own
	actor) — resolved to their real held responsibility for the lead
	department rather than assumed, since a Head of User Department may
	also prepare directly (REQ-AC-021)."""
	full_name = cstr(frappe.db.get_value("User", root.owner, "full_name") or root.owner)
	role = "Head of User Department" if _can(authz.require_hod_for_any, {root.lead_org_unit}, root.owner) else "Departmental Author"
	return {"name": full_name, "role": role}


def _deciding_hod_label(actor: str, org_unit: str) -> dict[str, str]:
	"""§13.10's "Decision by <name>, Head of User Department for
	<department>" line — named for whichever contributing department the
	deciding actor's own Head of User Department assignment actually
	matched (`require_hod_for_any`'s own resolved unit — not assumed to be
	the lead department, since §9.1A's command gate accepts any
	contributing department's HoD, not the lead one exclusively)."""
	full_name = cstr(frappe.db.get_value("User", actor, "full_name") or actor)
	return {"name": full_name, "role": f"Head of User Department for {_ou_label(org_unit)}"}


def get_requisition_editor(*, requisition: str, user: str | None = None) -> dict[str, Any]:
	"""§10.1 `GetRequisitionEditor` — one server projection: Planning
	context, Draft values, package rows, validation, step status and
	permitted actions, all derived from the exact objects the command
	layer would load and gate (§14.2 — no separate client-side model)."""
	actor = authz.actor(user)
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = frappe.get_doc("Procurement Requisition", requisition)
	contributing_units = _contributing_units(root)
	authz.require_requisition_reader(actor, contributing_org_units=contributing_units)
	_root, version, package_version = _load(requisition)
	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	version_dict = _version_dict(version)
	package_dict = _package_dict(package_version)
	report = validation.validate(version=version_dict, package=package_dict, eligibility=projection)

	is_draft = version.version_status == "Draft"
	sources = projection.get("sources", [])
	business_need, expected_result = _business_need_and_result(sources)
	organisation_unit_labels = {u: _ou_label(u) for u in (projection.get("contributing_org_unit_ids") or [])}
	drawdown_context = _drawdown_context(version_dict, projection)

	return {
		"outcome": "OK",
		"requisition": _requisition_summary(root),
		"version": {**version_dict, "requisition_version": version.name, "version_status": version.version_status, "version_number": version.version_number, "content_digest": version.content_digest, "record_version": version.record_version},
		"package": {**package_dict, "package_version": package_version.name, "version_status": package_version.version_status, "catalogue_version": package_version.catalogue_version, "record_version": package_version.record_version},
		"planning_projection": projection,
		"business_need": business_need,
		"expected_operational_result": expected_result,
		"organisation_unit_labels": organisation_unit_labels,
		"drawdown_context": drawdown_context,
		"delivery_location_label": _delivery_location_label(version.delivery_location),
		"delivery_locations": list_delivery_locations(),
		"validation": report,
		"catalogue": {
			"version": catalogue.CATALOGUE_VERSION,
			"characteristics": [c.as_dict() for c in catalogue.CHARACTERISTICS],
			"equipment_categories": list(catalogue.EQUIPMENT_CATEGORIES),
			"service_types": list(catalogue.SERVICE_TYPES),
			"service_acceptance_evidence": list(catalogue.SERVICE_ACCEPTANCE_EVIDENCE),
			"acceptance_check_types": list(catalogue.ACCEPTANCE_CHECK_TYPES),
			"acceptance_evidence_types": list(catalogue.ACCEPTANCE_EVIDENCE_TYPES),
			"supporting_material_types": list(catalogue.SUPPORTING_MATERIAL_TYPES),
		},
		"permitted_actions": {
			"can_edit": is_draft and _can(authz.require_draft_author_for_any, contributing_units, actor),
			"can_send_for_department_approval": is_draft and _can(authz.require_draft_author_for_any, contributing_units, actor),
			"can_submit_directly": is_draft and _can(authz.require_hod_for_any, contributing_units, actor),
			"can_withdraw": root.current_state in ("Awaiting Department Approval", "Submitted to Procurement") and _can(authz.require_hod_for_any, contributing_units, actor),
			# Read-offer-parity with lifecycle.py's `_require_hod_or_hopf` gate
			# (§7.4A step 1): Head of User Department or Head of Procurement
			# Function only — never offered to a plain Departmental Author.
			"can_request_upstream_correction": root.current_state in ("Draft", "Returned", "Awaiting Department Approval", "Submitted to Procurement")
			and (_can(authz.require_hopf, actor) or _can(authz.require_hod_for_any, contributing_units, actor)),
		},
	}


def get_department_approval_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	"""§10.1 `GetDepartmentApprovalTask` — the complete immutable Version
	and package for the exact HoD task (§13.10: drawdown, items, technical
	rows, digest, and who prepared it)."""
	actor = authz.actor(user)
	if not task or not frappe.db.exists("Requisition Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Requisition Task", task)
	root = frappe.get_doc("Procurement Requisition", task_doc.requisition)
	contributing_units = _contributing_units(root)
	_assignment, matched_unit = authz.require_hod_for_any(contributing_units, actor, masked=True)
	version = frappe.get_doc("Requisition Version", task_doc.requisition_version)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)
	version_dict = _version_dict(version)
	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	report = validation.validate(version=version_dict, package=_package_dict(package_version), eligibility=projection)
	return {
		"outcome": "OK", "task": {"task": task_doc.name, "status": task_doc.status, "record_version": task_doc.record_version, "task_token": task_doc.task_token},
		"requisition": _requisition_summary(root),
		"version": {**version_dict, "requisition_version": version.name, "version_number": version.version_number, "content_digest": version.content_digest},
		"package": {**_package_dict(package_version), "package_version": package_version.name, "content_digest": package_version.content_digest},
		"drawdown_context": _drawdown_context(version_dict, projection),
		"prepared_by": _prepared_by(root),
		"deciding_actor": _deciding_hod_label(actor, matched_unit),
		"catalogue": {"characteristics": [{"key": c.key, "label": c.label} for c in catalogue.CHARACTERISTICS]},
		"validation": report,
		"can_act": task_doc.status == "Open" and root.current_state == "Awaiting Department Approval",
	}


def get_procurement_authorisation_task(*, task: str, user: str | None = None) -> dict[str, Any]:
	"""§10.1 `GetProcurementAuthorisationTask` — the complete submitted
	Version, package, files, validation snapshot, fresh Planning
	availability and fresh Budget affordability (a preview only: this
	function never calls `reserve_funding`, so it creates nothing)."""
	actor = authz.actor(user)
	if not task or not frappe.db.exists("Requisition Task", task):
		authz.not_found()
	task_doc = frappe.get_doc("Requisition Task", task)
	root = frappe.get_doc("Procurement Requisition", task_doc.requisition)
	authz.require_hopf(actor, masked=True)
	version = frappe.get_doc("Requisition Version", task_doc.requisition_version)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)
	projection = eligibility_gateway.get_requisition_eligible_plan_item(root.plan_item_id)
	report = validation.validate(version=_version_dict(version), package=_package_dict(package_version), eligibility=projection)
	compat = compatibility.check(projection)

	sources_by_line = {s["plan_item_line_id"]: s for s in projection.get("sources", [])}
	affordability = []
	if not report["blocking_count"] and all(r.ok for r in compat) and projection.get("eligible"):
		try:
			allocations = [
				{"budget_line": sources_by_line[line.plan_item_line_id]["budget_line"], "plan_source_allocation": line.plan_item_line_id, "amount": line.requested_value}
				for line in version.drawdown_lines if line.plan_item_line_id in sources_by_line
			]
			if allocations:
				checked = funding_gateway.check_funding(
					plan_item=root.plan_item_id, plan_version=root.plan_version_id,
					source_set_hash=digest.sha256_hex({"lines": sorted(a["plan_source_allocation"] for a in allocations)}),
					allocations=allocations, correlation_id=f"{root.name}:preview:{frappe.generate_hash(length=8)}",
					caller_reference=root.requisition_reference,
				)
				affordability = checked.get("allocations", [])
				# §13.11's card names the Budget Line by its own reference
				# ("MOH-BL-HWD-2027"), never the internal docname
				# `check_funding` itself returns — found live: the card
				# title rendered a raw hash-like docname instead.
				for row in affordability:
					row["budget_line_label"] = cstr(frappe.db.get_value("Procurement Budget Line", row["budget_line"], "generated_reference") or row["budget_line"])
		except frappe.ValidationError:
			affordability = []

	remaining_quantity = sum(flt(s.get("remaining_quantity")) for s in projection.get("sources", []))
	remaining_amount = sum(flt(s.get("remaining_amount")) for s in projection.get("sources", []))

	# §13.11's "Submitted by <name> · <date>" line: the decision recorded
	# when a HoD submitted from the Department task — direct-from-Draft
	# submission (REQ-AC-021) records no such decision, so this degrades to
	# empty rather than a guessed actor.
	submitted = frappe.get_all(
		"Requisition Decision", filters={"requisition_version": version.name, "decision": "Submit to Procurement"},
		fields=["actor", "decided_at"], order_by="decided_at desc", limit_page_length=1,
	)
	submitted_by = {}
	if submitted:
		submitted_by = {"name": cstr(frappe.db.get_value("User", submitted[0].actor, "full_name") or submitted[0].actor), "decided_at": _eat(submitted[0].decided_at)}

	return {
		"outcome": "OK", "task": {"task": task_doc.name, "status": task_doc.status, "record_version": task_doc.record_version, "task_token": task_doc.task_token},
		"requisition": _requisition_summary(root),
		"version": {**_version_dict(version), "requisition_version": version.name, "version_number": version.version_number},
		"package": {**_package_dict(package_version), "package_version": package_version.name},
		"planning_projection": projection,
		"planning_availability": {"eligible": bool(projection.get("eligible")), "remaining_quantity": remaining_quantity, "remaining_amount": remaining_amount, "unit": (projection.get("sources") or [{}])[0].get("unit", "")},
		"compatibility": _compatibility_rows(compat),
		"validation": report,
		"budget_affordability": affordability,
		"objective_label": _objective_label(root.strategic_objective),
		"submitted_by": submitted_by,
		"contributing_org_unit_labels": {u: _ou_label(u) for u in _contributing_units(root)},
		"can_act": task_doc.status == "Open" and root.current_state == "Submitted to Procurement",
		"can_change_lead_unit": len(_contributing_units(root)) > 1,
	}


def get_authorised_requisition_handoff(*, requisition: str, user: str | None = None) -> dict[str, Any]:
	"""§10.1/§13.12 `GetAuthorisedRequisitionHandoff` — the exact immutable
	v1.3 handoff for an authorised consumer, plus the display-ready extras
	REQ-DES-10 itself needs (reservation/budget-line labels, package row
	counts, who authorised it and when, Tender-consumption status)."""
	actor = authz.actor(user)
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = frappe.get_doc("Procurement Requisition", requisition)
	authz.require_requisition_reader(actor, contributing_org_units=_contributing_units(root))
	if not root.handoff:
		fail("REQ_STALE_VERSION", "This Requisition has no authorised handoff.")
	handoff = frappe.get_doc("Authorised Requisition Handoff", root.handoff)
	payload = json.loads(handoff.payload_json)

	# §13.12's own reservation table names the Reservation and Budget Line
	# by their real references, not the internal hash-like docnames stored
	# on the drawdown line (the same class of gap found and fixed in
	# REQ-307's own Budget-affordability card).
	drawdown_display = []
	for line in payload.get("drawdown_lines", []):
		reservation_id = line.get("reservation_id") or ""
		reservation_label = cstr(frappe.db.get_value("Funding Reservation", reservation_id, "generated_reference") or reservation_id) if reservation_id else ""
		budget_line = cstr(frappe.db.get_value("Funding Reservation", reservation_id, "budget_line") or "") if reservation_id else ""
		budget_line_label = cstr(frappe.db.get_value("Procurement Budget Line", budget_line, "generated_reference") or budget_line) if budget_line else ""
		drawdown_display.append(
			{
				"reservation_label": reservation_label, "organisation_unit_label": _ou_label(line.get("contributing_org_unit")),
				"requested_value": line.get("requested_value"), "budget_line_label": budget_line_label,
			}
		)

	decisions = payload.get("decisions") or []
	authorised_by = {}
	if decisions:
		decision_doc = frappe.db.get_value("Requisition Decision", decisions[0].get("decision"), ["actor", "decided_at"], as_dict=True)
		if decision_doc:
			authorised_by = {
				"name": cstr(frappe.db.get_value("User", decision_doc.actor, "full_name") or decision_doc.actor),
				"role": decisions[0].get("capacity", ""), "decided_at": _eat(decision_doc.decided_at),
			}

	return {
		"outcome": "OK", "requisition": _requisition_summary(root), "handoff": handoff.name, "handoff_version": handoff.handoff_version, "handoff_digest": handoff.handoff_digest,
		"generated_at": cstr(handoff.generated_at), "payload": payload,
		"drawdown_display": drawdown_display,
		"package_summary": {"items": len(payload.get("items", [])), "technical_requirements": len(payload.get("technical_requirements", [])), "acceptance_requirements": len(payload.get("acceptance_requirements", []))},
		"authorised_by": authorised_by,
		"consumption": {
			"tender": handoff.tender, "tender_version": handoff.tender_version, "template_key": handoff.template_key,
			"template_version": handoff.template_version, "consumed_at": cstr(handoff.consumed_at),
		},
		# §9.1A's revoke gate is Head of Procurement Function only — never
		# offered to a plain reader, matching this module's own
		# read-offer-parity discipline.
		"can_revoke": root.current_state == "Authorised" and not root.handoff_consumed_at and _can(authz.require_hopf, actor),
	}


def get_requisition_history(*, requisition: str, user: str | None = None) -> dict[str, Any]:
	"""§10.1/§15 `GetRequisitionHistory` — versions, decisions, drawdown,
	reservation, reversal, upstream-correction and handoff-consumption
	evidence. No mutation."""
	actor = authz.actor(user)
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	root = frappe.get_doc("Procurement Requisition", requisition)
	authz.require_requisition_reader(actor, contributing_org_units=_contributing_units(root))

	versions = frappe.get_all(
		"Requisition Version", filters={"requisition": root.name},
		fields=["name", "version_number", "version_status", "based_on_version", "content_digest"],
		order_by="version_number asc",
	)
	tasks = frappe.get_all("Requisition Task", filters={"requisition": root.name}, fields=["name"], pluck="name")
	decisions = frappe.get_all(
		"Requisition Decision", filters={"task": ("in", tasks or ("",))},
		fields=["name", "task", "requisition_version", "actor", "legal_capacity", "decision", "return_reason", "decided_at"],
		order_by="decided_at asc",
	)
	drawdown_lines = frappe.get_all(
		"Requisition Drawdown Line", filters={"parent": ("in", [v.name for v in versions] or ("",))},
		fields=["parent", "drawdown_line_id", "contributing_org_unit", "requested_quantity", "requested_value", "reservation_id", "planning_drawdown_reference"],
	)
	events = frappe.get_all(
		"Requisition Event", filters={"requisition": root.name},
		fields=["event_id", "event_type", "sequence", "occurred_at", "status"], order_by="sequence asc",
	)
	handoff = None
	if root.handoff:
		h = frappe.get_doc("Authorised Requisition Handoff", root.handoff)
		handoff = {
			"handoff": h.name, "handoff_digest": h.handoff_digest, "generated_at": cstr(h.generated_at),
			"tender": h.tender, "consumed_at": cstr(h.consumed_at),
		}
	return {
		"outcome": "OK", "requisition": _requisition_summary(root),
		"versions": versions, "decisions": decisions, "drawdown_lines": drawdown_lines, "events": events, "handoff": handoff,
	}
