"""Departmental Needs read projections (NDS-CHG-001 v1.1 §8.1).

Every read resolves rows through the same native scope predicate used by the
commands (`permissions.can_view`), so counts, rows, detail and exports cannot
diverge (NDS-BR-019, NDS-AC-021).

§1.1 removes the four summary cards, the separate action/waiting sections and
the advanced register filters in favour of one role-appropriate table with
minimal search/status filters; Phase 7 reshapes the screens onto this
projection. The support-lookup surface is removed by §1.1.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, flt, formatdate

from kentender_procurement.departmental_needs.constants import (
	STATE_ACCEPTED,
	STATE_DRAFT,
	STATE_RETURNED,
	STATE_SUBMITTED,
	STATE_WITHDRAWN,
	TASK_OPEN,
	TASK_WITHDRAWAL,
	VERSION_CONTENT_FIELDS,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.context import selectable_financial_years
from kentender_procurement.departmental_needs.services.permissions import (
	actor,
	can_view,
	creation_contexts,
	is_owner,
	require_review_command,
	require_view,
	viewing_contexts,
)
from kentender_procurement.departmental_needs.services.usage import (
	planning_usage,
	planning_usage_detail,
)


def _open_review_task(need: str) -> dict[str, str] | None:
	row = frappe.db.get_value(
		"Departmental Need Review Task",
		{"departmental_need": need, "status": TASK_OPEN},
		["name", "task_type", "decision_token"],
		order_by="opened_at desc",
		as_dict=True,
	)
	if not row:
		return None
	return {"name": row.name, "task_type": row.task_type, "decision_token": row.decision_token}


def _version_facts(version: str) -> dict[str, Any]:
	if not version:
		return {}
	row = frappe.db.get_value(
		"Departmental Need Version",
		version,
		["name", "version_number", "version_status", "content_hash", *VERSION_CONTENT_FIELDS],
		as_dict=True,
	)
	if not row:
		return {}
	facts = dict(row)
	facts["unit_label"] = cstr(
		frappe.db.get_value("Unit Of Measure", facts.get("unit"), "unit_label")
		or facts.get("unit")
		or ""
	)
	return facts


def _quantity_label(version: dict[str, Any]) -> str:
	quantity = flt(version.get("indicative_quantity"))
	if quantity <= 0:
		return ""
	value = int(quantity) if float(quantity).is_integer() else quantity
	label = cstr(
		frappe.db.get_value("Unit Of Measure", version.get("unit"), "unit_label")
		or version.get("unit")
		or ""
	)
	# NDS-DES-01/02 render the unit in lower case beside the quantity.
	return f"{value} {label.lower()}".strip()


def _actions(doc, principal: str, profile: str) -> list[dict[str, str]]:
	"""One row exposes one action; the workspace button wires to actions[0].

	§12.2 — the queue's subject is the **open review task**, not the root state.
	NDS-UI-02 is the reviewer's only route to NDS-UI-05 and NDS-UI-07 (§10 gives
	neither a menu entry), so an action keyed off `current_state == Submitted`
	strands two of the three task types: §5.2 holds the root at `Accepted for
	planning` for the whole successor lifecycle, and a withdrawal request never
	moves the root at all. Both left an Open task the reviewer held and no row
	that offered it.
	"""
	task = _open_review_task(doc.name)
	if task and profile == "department" and not is_owner(doc, principal):
		withdrawal = task["task_type"] == TASK_WITHDRAWAL
		return [
			{
				"code": "withdrawal" if withdrawal else "review",
				"label": "Review withdrawal" if withdrawal else "Review",
				"task": task["name"],
				"decision_token": task["decision_token"],
			}
		]
	if profile == "owner" and doc.current_state in {STATE_DRAFT, STATE_RETURNED}:
		# A Draft or Returned Need is by definition incomplete, so its own author
		# lands straight in the editable form rather than a read-only preview.
		return [{"code": "edit", "label": "Continue"}, {"code": "view", "label": "View"}]
	return [{"code": "view", "label": "View"}] if profile != "none" else []


def _selected_context(principal: str, pe: str, ou: str) -> tuple[dict[str, str] | None, list[dict[str, str]]]:
	# Viewing, not authoring: this resolver also serves NDS-UI-02, whose only
	# audience is the Head of User Department — a role that never authors.
	contexts = viewing_contexts(principal)
	if not contexts:
		return None, contexts
	if pe or ou:
		selected = next(
			(
				row
				for row in contexts
				if row["procuring_entity"] == pe and row["organisation_unit"] == ou
			),
			None,
		)
		if not selected:
			fail(
				"NDS_SCOPE_DENIED",
				"The selected Departmental Needs context is outside your permitted scope.",
			)
		return selected, contexts
	if len(contexts) > 1:
		return None, contexts
	return contexts[0], contexts


def get_workspace(
	*,
	procuring_entity: str = "",
	organisation_unit: str = "",
	financial_year: str = "",
	search: str = "",
	status: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	principal = actor(user)
	selected, contexts = _selected_context(
		principal, cstr(procuring_entity).strip(), cstr(organisation_unit).strip()
	)
	if not selected:
		return {
			"ok": False,
			"outcome": "NO_AUTHORISED_CONTEXT" if not contexts else "CONTEXT_SELECTION_REQUIRED",
			"contexts": contexts,
			"financial_years": selectable_financial_years(),
			"needs": [],
			"actions": [],
		}
	fy = cstr(financial_year).strip()
	_fy_rows = selectable_financial_years()
	filters: dict[str, Any] = {
		"procuring_entity": selected["procuring_entity"],
		"organisation_unit": selected["organisation_unit"],
	}
	if fy:
		filters["financial_year"] = fy
	if cstr(status).strip():
		filters["current_state"] = cstr(status).strip()
	rows = frappe.get_all(
		"Departmental Need",
		filters=filters,
		fields=[
			"name",
			"need_reference",
			"owner",
			"procuring_entity",
			"organisation_unit",
			"financial_year",
			"current_state",
			"current_version",
			"current_accepted_version",
			"record_version",
		],
		order_by="need_reference asc",
		limit_page_length=0,
	)
	term = cstr(search).strip().lower()
	needs = []
	for row in rows:
		doc = frappe._dict(row)
		allowed, profile = can_view(doc, principal)
		if not allowed or doc.current_state == STATE_WITHDRAWN:
			continue
		version = _version_facts(doc.current_version)
		title = cstr(version.get("title"))
		if term and term not in title.lower() and term not in cstr(doc.need_reference).lower():
			continue
		required_by = version.get("required_by_date")
		needs.append(
			{
				"name": doc.name,
				"reference": doc.need_reference,
				"title": title,
				"author_label": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
				"quantity_label": _quantity_label(version),
				"required_by": str(required_by or ""),
				"required_by_label": formatdate(required_by, "d MMM yyyy") if required_by else "",
				"status": doc.current_state,
				"planning_usage": planning_usage(doc.name),
				"record_version": doc.record_version,
				"actions": _actions(doc, principal, profile),
			}
		)
	return {
		"ok": True,
		"outcome": "READY",
		"contexts": contexts,
		"financial_years": selectable_financial_years(),
		"context": {
			**selected,
			"financial_year": fy,
			"financial_year_label": next(
				(row["label"] for row in _fy_rows if row["id"] == fy), fy
			),
		},
		"needs": needs,
		"count_label": f"{len(needs)} need" if len(needs) == 1 else f"{len(needs)} needs",
		# §12.1 / §17 — the server decides the action. A reviewer, Planner or
		# Auditor reaches this contract too (it backs NDS-UI-02 as well), and
		# none of them authors, so Create need is offered only where the user
		# could actually create in this context. The client's separate
		# intake-window check narrows it further; it cannot stand alone,
		# because intake is Open for part of every year.
		"actions": (
			[{"code": "create", "label": "Create need"}]
			if any(
				row["procuring_entity"] == selected["procuring_entity"]
				and row["organisation_unit"] == selected["organisation_unit"]
				for row in creation_contexts(principal)
			)
			else []
		),
	}


def get_review_task(*, task: str, decision_token: str = "", user: str | None = None) -> dict[str, Any]:
	"""§8.1 `get_departmental_review_task` — the exact version under decision.

	Returns the immutable version content, the requester, the scope and the
	permitted decision labels. Labels come from the task type, never from what
	the caller's screen happens to render (§17).
	"""
	principal = actor(user)
	row = frappe.db.get_value(
		"Departmental Need Review Task",
		cstr(task).strip(),
		[
			"name",
			"departmental_need",
			"need_version",
			"withdrawal_request",
			"task_type",
			"status",
			"decision_token",
			"opened_at",
		],
		as_dict=True,
	)
	if not row:
		fail("NDS_SCOPE_DENIED", "Review task not found.")
	doc = frappe.get_doc("Departmental Need", row.departmental_need)
	# §4.4 — the task is available to holders of the HoD role in the exact scope.
	require_review_command(doc, principal)
	if decision_token and cstr(decision_token) != cstr(row.decision_token):
		fail("NDS_STALE_WRITE", "This task was already decided. Reload and try again.")
	version = _version_facts(row.need_version or doc.current_version)
	withdrawal = None
	if row.withdrawal_request:
		withdrawal = frappe.db.get_value(
			"Need Withdrawal Request",
			row.withdrawal_request,
			["name", "reason", "requested_by", "status", "accepted_version"],
			as_dict=True,
		)
		withdrawal = dict(withdrawal) if withdrawal else None
	decisions = (
		["approve", "evaluate", "decline"]
		if row.task_type == TASK_WITHDRAWAL
		else ["return", "accept", "decline"]
	)
	return {
		"ok": True,
		"task": row.name,
		"task_type": row.task_type,
		"status": row.status,
		"decision_token": row.decision_token,
		"opened_at": str(row.opened_at or ""),
		"need": doc.as_dict(no_nulls=True),
		"version": version,
		"withdrawal_request": withdrawal,
		"requester_label": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
		"scope": {
			"procuring_entity": doc.procuring_entity,
			"organisation_unit": doc.organisation_unit,
			"financial_year": doc.financial_year,
		},
		"permitted_decisions": decisions if row.status == TASK_OPEN else [],
		# A maker never decides their own version, so the label set is empty for
		# them even when the task is open (NDS-BR-006).
		"maker_checker_blocked": is_owner(doc, principal),
	}


def get_current_accepted_need(
	*,
	need: str,
	expected_procuring_entity: str = "",
	expected_financial_year: str = "",
	expected_content_hash: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""§8.1 — the typed accepted source contract for Procurement Planning.

	Returns the §7.1 `DepartmentalNeedAccepted.v2` field set, or a typed
	stale/not-accepted error. This is the only supported way for Planning to
	read a Need (firm D1 boundary); the payload deliberately carries no Budget
	Line, amount, funding source, currency, Strategy, requirement type,
	location or attachment (NDS-AC-024).
	"""
	principal = actor(user)
	name = cstr(need).strip()
	if not frappe.db.exists("Departmental Need", name):
		# Try the human reference before disclosing nothing.
		name = cstr(frappe.db.get_value("Departmental Need", {"need_reference": name}, "name") or "")
	if not name:
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	doc = frappe.get_doc("Departmental Need", name)
	require_view(doc, principal)
	if cstr(expected_procuring_entity) and cstr(expected_procuring_entity) != doc.procuring_entity:
		fail("NDS_CONTEXT_REQUIRED", "The Need does not belong to the expected Procuring Entity.")
	if cstr(expected_financial_year) and cstr(expected_financial_year) != doc.financial_year:
		fail("NDS_CONTEXT_REQUIRED", "The Need does not belong to the expected financial year.")
	if doc.current_state != STATE_ACCEPTED or not doc.current_accepted_version:
		fail("NDS_NOT_ACCEPTED", "This Departmental Need has no current accepted version.")
	version = frappe.get_doc("Departmental Need Version", doc.current_accepted_version)
	if cstr(expected_content_hash) and cstr(expected_content_hash) != cstr(version.content_hash):
		fail(
			"NDS_SOURCE_STALE",
			"The requested accepted version is no longer current. Refresh the source.",
		)
	unit_label = cstr(
		frappe.db.get_value("Unit Of Measure", version.unit, "unit_label") or version.unit or ""
	)
	return {
		"ok": True,
		"contract": "DepartmentalNeedAccepted.v2",
		"need": doc.name,
		"need_reference": doc.need_reference,
		"accepted_version": version.name,
		"version_number": version.version_number,
		"content_hash": version.content_hash,
		"procuring_entity": doc.procuring_entity,
		"organisation_unit": doc.organisation_unit,
		"financial_year": doc.financial_year,
		"title": version.title,
		"description": version.description,
		"expected_operational_result": version.expected_operational_result,
		"indicative_quantity": flt(version.indicative_quantity),
		"unit": version.unit,
		"unit_label": unit_label,
		"required_by_date": str(version.required_by_date or ""),
	}


def _scope_labels(doc) -> dict[str, str]:
	"""Display names for the Need's scope; the artboards never show raw IDs."""
	return {
		"procuring_entity": cstr(
			frappe.db.get_value("Procuring Entity", doc.procuring_entity, "legal_name")
			or doc.procuring_entity
		),
		"organisation_unit": cstr(
			frappe.db.get_value("Organisation Unit", doc.organisation_unit, "unit_name")
			or doc.organisation_unit
		),
		"financial_year": cstr(
			frappe.db.get_value("Financial Year", doc.financial_year, "label")
			or doc.financial_year
		),
	}


def get_need(*, need: str, user: str | None = None) -> dict[str, Any]:
	principal = actor(user)
	if not frappe.db.exists("Departmental Need", need):
		# §9 — disclose no protected record data, including its existence.
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	doc = frappe.get_doc("Departmental Need", need)
	profile = require_view(doc, principal)
	latest_return = None
	if doc.current_state == STATE_RETURNED:
		row = frappe.db.get_value(
			"Departmental Need Decision",
			{"departmental_need": doc.name, "action": "Return for correction"},
			["reason", "actor", "occurred_at"],
			order_by="occurred_at desc",
			as_dict=True,
		)
		if row:
			latest_return = {
				"reason": row.reason,
				"actor": row.actor,
				"actor_label": frappe.db.get_value("User", row.actor, "full_name") or row.actor,
				"occurred_at": str(row.occurred_at),
				"occurred_label": formatdate(row.occurred_at, "d MMMM y")
				+ " at "
				+ frappe.utils.format_time(row.occurred_at, "HH:mm"),
			}
	accepted = None
	if doc.current_state == STATE_ACCEPTED:
		row = frappe.db.get_value(
			"Departmental Need Decision",
			{
				"departmental_need": doc.name,
				"action": ("in", ["Accept for planning", "Accept successor"]),
			},
			["actor", "occurred_at"],
			order_by="occurred_at desc",
			as_dict=True,
		)
		if row:
			accepted = {
				"actor": row.actor,
				"actor_label": frappe.db.get_value("User", row.actor, "full_name") or row.actor,
				"occurred_at": str(row.occurred_at),
			}
	return {
		"ok": True,
		"need": doc.as_dict(no_nulls=True),
		"scope_labels": _scope_labels(doc),
		"accepted": accepted,
		"current_version": _version_facts(doc.current_version),
		"accepted_version": _version_facts(doc.current_accepted_version),
		"latest_return": latest_return,
		"author_label": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
		"planning_usage": planning_usage(doc.name),
		"open_task": _open_review_task(doc.name),
		"actions": _actions(doc, principal, profile),
		"access_profile": profile,
	}
