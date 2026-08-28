# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.4 §6.1/§6.2/§6.3 — Procuring Entity / Procuring Entity Version,
Financial Year, and PE Fiscal Year Context lifecycles.

Every lifecycle action requires only the Reference Data Manager Frappe Role
(reference_data_permissions.require_reference_data_manager) — no maker-checker,
no separate review/recommend/approve stage, no reference_data.* capability
string. Audit via audit_event_service.log_audit_event. No client-only
enforcement — every guard here runs server-side and is re-checked on every
call, never trusted from the UI.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from kentender_core.services import reference_data_permissions as perm
from kentender_core.services.audit_event_service import log_audit_event


def _audit(pe_name: str, action: str, actor: str, metadata: dict | None = None) -> None:
	log_audit_event(
		event_type="reference_data.pe",
		entity=pe_name,
		document_type="Procuring Entity",
		document_name=pe_name,
		action=action,
		performed_by=actor,
		metadata=metadata or {},
	)


def create_pe_draft(payload: dict, *, user: str | None = None) -> dict:
	"""§6.1 '— | Create draft | DRAFT'. payload: entity_code, legal_name, display_name,
	pe_type_code, timezone (optional, defaults Africa/Nairobi), effective_from (optional)."""
	actor = user or frappe.session.user
	entity_code = (payload.get("entity_code") or "").strip()
	if not entity_code:
		frappe.throw(_("Entity code is required"))
	if frappe.db.exists("Procuring Entity", entity_code):
		frappe.throw(_("A Procuring Entity with this code already exists"), title="PE_CODE_DUPLICATE")

	perm.require_reference_data_manager(actor)

	pe = frappe.get_doc(
		{
			"doctype": "Procuring Entity",
			"entity_code": entity_code,
			"legal_name": payload.get("legal_name") or payload.get("display_name"),
			"entity_name": payload.get("display_name") or payload.get("legal_name"),
			"entity_type": None,
			"reporting_currency": payload.get("reporting_currency") or "KES",
			"status": "Draft",
			"effective_from": payload.get("effective_from"),
		}
	)
	pe.insert(ignore_permissions=True)

	version = frappe.get_doc(
		{
			"doctype": "Procuring Entity Version",
			"procuring_entity": pe.name,
			"version_no": 1,
			"legal_name": payload.get("legal_name") or payload.get("display_name"),
			"display_name": payload.get("display_name") or payload.get("legal_name"),
			"pe_type_code": payload["pe_type_code"],
			"timezone": payload.get("timezone") or "Africa/Nairobi",
			"version_state": "Draft",
		}
	)
	version.insert(ignore_permissions=True)
	pe.db_set("current_version_id", version.name, update_modified=False)

	_audit(pe.name, "reference_data.pe.create_draft", actor, {"version": version.name})
	return {"ok": True, "pe": pe.name, "version": version.name}


def update_pe_draft(pe_name: str, payload: dict, *, user: str | None = None) -> dict:
	"""§6.1 'DRAFT | Edit draft | DRAFT' — a Draft PE's Version fields are still
	editable up to Activate; entity_code is immutable once created (it's the PE's
	own name)."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	version = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
	if version.version_state != "Draft":
		frappe.throw(_("Only a Draft version can be edited"))

	perm.require_reference_data_manager(actor)

	legal_name = payload.get("legal_name") or payload.get("display_name")
	display_name = payload.get("display_name") or payload.get("legal_name")

	version.legal_name = legal_name
	version.display_name = display_name
	version.pe_type_code = payload.get("pe_type_code")
	version.timezone = payload.get("timezone") or version.timezone or "Africa/Nairobi"
	version.save(ignore_permissions=True)

	pe.legal_name = legal_name
	pe.entity_name = display_name
	pe.effective_from = payload.get("effective_from") or pe.effective_from
	pe.save(ignore_permissions=True)

	_audit(pe.name, "reference_data.pe.update_draft", actor, {"version": version.name})
	return {"ok": True, "pe": pe.name, "version": version.name}


def activate_pe(pe_name: str, *, user: str | None = None) -> dict:
	"""§6.1 'DRAFT | Activate | PE ACTIVE; version ACTIVE' and 'Amendment DRAFT |
	Apply amendment | Successor version ACTIVE; prior version SUPERSEDED'. One
	action covers both cases: an already-Active PE just supersedes its prior
	version; a still-Draft PE also flips to Active for the first time."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	version = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
	if version.version_state != "Draft":
		frappe.throw(_("Only a Draft version can be activated"))

	perm.require_reference_data_manager(actor)

	is_amendment = pe.status == "Active"
	if is_amendment:
		for prior_name in frappe.get_all(
			"Procuring Entity Version",
			filters={"procuring_entity": pe_name, "version_state": "Active"},
			pluck="name",
		):
			prior = frappe.get_doc("Procuring Entity Version", prior_name)
			prior.version_state = "Superseded"
			prior.save(ignore_permissions=True)

	version.version_state = "Active"
	version.valid_from = frappe.utils.today()
	version.save(ignore_permissions=True)
	if not is_amendment:
		pe.status = "Active"
		pe.save(ignore_permissions=True)

	action = "reference_data.pe.apply_amendment" if is_amendment else "reference_data.pe.activate"
	_audit(pe_name, action, actor, {"version": version.name})
	return {"ok": True, "pe": pe_name, "status": pe.status, "version": version.name}


def propose_amendment(pe_name: str, change_reason: str, *, user: str | None = None) -> dict:
	"""§6.1 'ACTIVE | Propose amendment | New version DRAFT'. Active version stays authoritative."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	if pe.status != "Active":
		frappe.throw(_("Only an Active Procuring Entity can be amended"))
	if not (change_reason or "").strip():
		frappe.throw(_("Change reason is required"))

	perm.require_reference_data_manager(actor)

	current = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
	draft = frappe.get_doc(
		{
			"doctype": "Procuring Entity Version",
			"procuring_entity": pe.name,
			"version_no": (current.version_no or 1) + 1,
			"legal_name": current.legal_name,
			"display_name": current.display_name,
			"pe_type_code": current.pe_type_code,
			"timezone": current.timezone,
			"change_reason": change_reason,
			"version_state": "Draft",
		}
	)
	draft.insert(ignore_permissions=True)
	# activate_pe always acts on pe.current_version_id — it must follow the
	# amendment draft immediately, the same way create_pe_draft points it at
	# the version it just created, or activate_pe has nothing to progress.
	pe.db_set("current_version_id", draft.name, update_modified=False)
	_audit(pe_name, "reference_data.pe.propose_amendment", actor, {"version": draft.name})
	return {"ok": True, "pe": pe_name, "version": draft.name}


def suspend_pe(pe_name: str, reason: str, *, user: str | None = None) -> dict:
	"""§6.1 'ACTIVE | Suspend | SUSPENDED'."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	if pe.status != "Active":
		frappe.throw(_("Only an Active Procuring Entity can be suspended"))
	if not (reason or "").strip():
		frappe.throw(_("A reason is required to suspend a Procuring Entity"))

	perm.require_reference_data_manager(actor)

	pe.status = "Suspended"
	pe.save(ignore_permissions=True)
	_audit(pe_name, "reference_data.pe.suspend", actor, {"reason": reason})
	return {"ok": True, "pe": pe_name, "status": pe.status}


def reinstate_pe(pe_name: str, *, user: str | None = None) -> dict:
	"""§6.1 'SUSPENDED | Reinstate | ACTIVE'."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	if pe.status != "Suspended":
		frappe.throw(_("Only a Suspended Procuring Entity can be reinstated"))

	perm.require_reference_data_manager(actor)

	pe.status = "Active"
	pe.save(ignore_permissions=True)
	_audit(pe_name, "reference_data.pe.reinstate", actor)
	return {"ok": True, "pe": pe_name, "status": pe.status}


_BLOCKING_CONTEXT_STATUSES = ("Active", "Scheduled")


def _blocking_context_count(*, procuring_entity: str | None = None, financial_year: str | None = None) -> int:
	filters: dict = {"context_status": ["in", _BLOCKING_CONTEXT_STATUSES]}
	if procuring_entity:
		filters["procuring_entity"] = procuring_entity
	if financial_year:
		filters["financial_year"] = financial_year
	return frappe.db.count("PE Fiscal Year Context", filters)


def retire_pe(pe_name: str, reason: str, effective_date, *, user: str | None = None) -> dict:
	"""§6.1 'ACTIVE or SUSPENDED | Retire | RETIRED'."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	if pe.status not in ("Active", "Suspended"):
		frappe.throw(_("Only an Active or Suspended Procuring Entity can be retired"))
	if not (reason or "").strip():
		frappe.throw(_("A reason is required to retire a Procuring Entity"))
	blocking = _blocking_context_count(procuring_entity=pe_name)
	if blocking:
		frappe.throw(
			_("Cannot retire: {0} active/scheduled PE/FY context(s) still reference this Procuring Entity").format(
				blocking
			),
			title="REFERENCE_IN_USE",
		)

	perm.require_reference_data_manager(actor)

	pe.status = "Retired"
	pe.effective_to = effective_date
	pe.save(ignore_permissions=True)
	_audit(pe_name, "reference_data.pe.retire", actor, {"reason": reason, "effective_date": str(effective_date)})
	return {"ok": True, "pe": pe_name, "status": pe.status}


# --- Financial Year lifecycle (§6.2) --------------------------------------------


def _audit_fy(fy_name: str, action: str, actor: str, metadata: dict | None = None) -> None:
	log_audit_event(
		event_type="reference_data.fy",
		entity=fy_name,
		document_type="Financial Year",
		document_name=fy_name,
		action=action,
		performed_by=actor,
		metadata=metadata or {},
	)


def create_fy_draft(start_year: int, *, user: str | None = None) -> dict:
	"""§6.2 '— | Create from start year | DRAFT'."""
	actor = user or frappe.session.user
	perm.require_reference_data_manager(actor)

	fy = frappe.get_doc(
		{
			"doctype": "Financial Year",
			"start_year": start_year,
			"record_status": "Draft",
			"created_by_actor": actor,
			"created_at": frappe.utils.now_datetime(),
		}
	)
	fy.insert(ignore_permissions=True)
	_audit_fy(fy.name, "reference_data.fy.create_draft", actor)
	return {"ok": True, "financial_year": fy.name, "label": fy.label}


def make_fy_available(fy_name: str, *, user: str | None = None) -> dict:
	"""§6.2 'DRAFT | Make available | AVAILABLE'."""
	actor = user or frappe.session.user
	fy = frappe.get_doc("Financial Year", fy_name)
	if fy.record_status != "Draft":
		frappe.throw(_("Only a Draft Financial Year can be made available"))

	perm.require_reference_data_manager(actor)

	fy.record_status = "Available"
	fy.approved_by = actor
	fy.approved_at = frappe.utils.now_datetime()
	fy.save(ignore_permissions=True)
	_audit_fy(fy_name, "reference_data.fy.make_available", actor)
	return {"ok": True, "financial_year": fy_name, "record_status": fy.record_status}


def retire_fy(fy_name: str, *, user: str | None = None) -> dict:
	"""§6.2 'AVAILABLE | Retire | RETIRED'. Blocked while referenced by an
	active/scheduled PE/FY Context."""
	actor = user or frappe.session.user
	fy = frappe.get_doc("Financial Year", fy_name)
	if fy.record_status != "Available":
		frappe.throw(_("Only an Available Financial Year can be retired"))
	blocking = _blocking_context_count(financial_year=fy_name)
	if blocking:
		frappe.throw(
			_("Cannot retire: {0} active/scheduled PE/FY context(s) still reference this Financial Year").format(
				blocking
			),
			title="REFERENCE_IN_USE",
		)

	perm.require_reference_data_manager(actor)

	fy.record_status = "Retired"
	fy.save(ignore_permissions=True)
	_audit_fy(fy_name, "reference_data.fy.retire", actor)
	return {"ok": True, "financial_year": fy_name, "record_status": fy.record_status}


# --- PE Fiscal Year Context lifecycle (§6.3) ------------------------------------

_SYSTEM_ACTOR = "Administrator"  # scheduler-driven transitions (BR §6.3 "Automated ...")


def _check_expected_version(ctx, expected_version: str | None) -> None:
	"""BR-016/AC-017 — a command carrying a stale expected_version has no partial
	effect. Uses the document's own `modified` timestamp as the version token (no
	separate counter needed); the caller echoes back whatever `get_pe_fy_context`
	returned at read time. Omitted expected_version is not checked — only real UI
	round-trips are enforced, never a blanket requirement on every call site."""
	if expected_version is None:
		return
	if str(ctx.modified) != str(expected_version):
		frappe.throw(
			_("This record changed after you opened it. Refresh and review the latest version."),
			frappe.ValidationError,
			title="VERSION_CONFLICT",
		)


def _audit_ctx(context_name: str, action: str, actor: str, metadata: dict | None = None) -> None:
	log_audit_event(
		event_type="reference_data.context",
		entity=context_name,
		document_type="PE Fiscal Year Context",
		document_name=context_name,
		action=action,
		performed_by=actor,
		metadata=metadata or {},
	)


def enable_context(pe_name: str, fy_name: str, active_from, active_to, *, user: str | None = None) -> dict:
	"""§6.3 '— | Enable PE for Financial Year | ACTIVE or SCHEDULED'. One
	governed action: no Draft/Submitted/Recommended/Approved sub-states.
	BR-005: PE must be Active, FY must be Available. BR-006: active_to later
	than active_from. Uniqueness on (pe, fy) is a database constraint."""
	actor = user or frappe.session.user
	pe_status = frappe.db.get_value("Procuring Entity", pe_name, "status")
	if pe_status != "Active":
		frappe.throw(_("This Procuring Entity is not active"), title="PE_NOT_ACTIVE")
	fy_status = frappe.db.get_value("Financial Year", fy_name, "record_status")
	if fy_status != "Available":
		frappe.throw(_("This Financial Year is not available for use"), title="FY_NOT_AVAILABLE")
	if frappe.db.exists("PE Fiscal Year Context", {"procuring_entity": pe_name, "financial_year": fy_name}):
		frappe.throw(_("This PE/FY context already exists"), title="PEFY_CONTEXT_DUPLICATE")
	if get_datetime(active_to) <= get_datetime(active_from):
		frappe.throw(_("The context availability end must be later than its start"), title="PEFY_DATES_INVALID")

	perm.require_reference_data_manager(actor)

	due_now = get_datetime(active_from) <= now_datetime()
	ctx = frappe.get_doc(
		{
			"doctype": "PE Fiscal Year Context",
			"procuring_entity": pe_name,
			"financial_year": fy_name,
			"context_status": "Active" if due_now else "Scheduled",
			"active_from": active_from,
			"active_to": active_to,
		}
	)
	ctx.insert(ignore_permissions=True)
	_audit_ctx(ctx.name, "reference_data.context.enable", actor)
	if due_now:
		_audit_ctx(ctx.name, "reference_data.context.activate", actor, {"automated": False})
	return {"ok": True, "context": ctx.name, "context_status": ctx.context_status}


def _activate_context(ctx, actor: str) -> None:
	"""§6.3 'SCHEDULED | Reach active_from | ACTIVE'. Revalidates PE/FY are
	still in force before activating — enablement does not guarantee they
	still are by the time active_from is reached."""
	pe_status = frappe.db.get_value("Procuring Entity", ctx.procuring_entity, "status")
	fy_status = frappe.db.get_value("Financial Year", ctx.financial_year, "record_status")
	if pe_status != "Active" or fy_status != "Available":
		# Revalidation failed — leave in place for governed correction, not a silent
		# skip: BR-009 requires this to be re-evaluated on every read/command too.
		return
	ctx.context_status = "Active"
	ctx.save(ignore_permissions=True)
	_audit_ctx(ctx.name, "reference_data.context.activate", actor, {"automated": actor == _SYSTEM_ACTOR})


def activate_due_contexts() -> dict:
	"""Scheduled job — CFG-303. Scheduled contexts whose active_from has been
	reached, activated with the same revalidation as an inline enable."""
	due = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"context_status": "Scheduled", "active_from": ["<=", now_datetime()]},
		pluck="name",
	)
	for name in due:
		_activate_context(frappe.get_doc("PE Fiscal Year Context", name), _SYSTEM_ACTOR)
	return {"activated": due}


def suspend_context(
	context_name: str, reason: str, *, user: str | None = None, expected_version: str | None = None
) -> dict:
	"""§6.3 'ACTIVE | Suspend | SUSPENDED'."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Active":
		frappe.throw(_("Only an Active context can be suspended"))
	if not (reason or "").strip():
		frappe.throw(_("A reason is required to suspend a PE/FY context"))

	perm.require_reference_data_manager(actor)

	ctx.context_status = "Suspended"
	ctx.suspended_by = actor
	ctx.suspended_at = now_datetime()
	ctx.suspended_reason = reason
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, "reference_data.context.suspend", actor, {"reason": reason})
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def reinstate_context(context_name: str, *, user: str | None = None, expected_version: str | None = None) -> dict:
	"""§6.3 'SUSPENDED | Reinstate | ACTIVE or SCHEDULED' — after prerequisite revalidation."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Suspended":
		frappe.throw(_("Only a Suspended context can be reinstated"))

	perm.require_reference_data_manager(actor)

	pe_status = frappe.db.get_value("Procuring Entity", ctx.procuring_entity, "status")
	fy_status = frappe.db.get_value("Financial Year", ctx.financial_year, "record_status")
	if pe_status != "Active" or fy_status != "Available":
		frappe.throw(_("Cannot reinstate: the Procuring Entity or Financial Year is no longer in force"))

	due_now = get_datetime(ctx.active_from) <= now_datetime()
	ctx.context_status = "Active" if due_now else "Scheduled"
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, "reference_data.context.reinstate", actor)
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def close_context(
	context_name: str,
	reason: str,
	*,
	acknowledged: bool = False,
	user: str | None = None,
	expected_version: str | None = None,
) -> dict:
	"""§6.3 'ACTIVE/SUSPENDED/SCHEDULED | Close | CLOSED'. Manual close requires
	reason + explicit impact acknowledgement — does not cancel existing
	downstream records (BR-013), only removes the context from new-work
	selectors."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status not in ("Active", "Suspended", "Scheduled"):
		frappe.throw(_("Only an Active, Suspended or Scheduled context can be closed"))
	if not (reason or "").strip():
		frappe.throw(_("A reason is required to close a PE/FY context"))
	if not acknowledged:
		frappe.throw(_("You must acknowledge the impact before closing this context"))

	perm.require_reference_data_manager(actor)

	ctx.context_status = "Closed"
	ctx.closed_by = actor
	ctx.closed_at = now_datetime()
	ctx.closed_reason = reason
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, "reference_data.context.close", actor, {"reason": reason})
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def close_due_contexts() -> dict:
	"""Scheduled job — CFG-303. Active contexts whose active_to has passed are
	closed automatically, with scheduler audit (§6.3 'ACTIVE | Reach active_to |
	CLOSED')."""
	due = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"context_status": "Active", "active_to": ["<=", now_datetime()]},
		pluck="name",
	)
	for name in due:
		ctx = frappe.get_doc("PE Fiscal Year Context", name)
		ctx.context_status = "Closed"
		ctx.closed_by = _SYSTEM_ACTOR
		ctx.closed_at = now_datetime()
		ctx.closed_reason = "Automated closure: active_to reached"
		ctx.save(ignore_permissions=True)
		_audit_ctx(name, "reference_data.context.auto_close", _SYSTEM_ACTOR, {"automated": True})
	return {"closed": due}


def run_scheduled_context_transitions() -> dict:
	"""Single scheduler entry point (kentender_core hooks.py `scheduler_events`)."""
	return {"activated": activate_due_contexts()["activated"], "closed": close_due_contexts()["closed"]}


def reopen_context(
	context_name: str, reason: str, active_from, active_to, *, user: str | None = None, expected_version: str | None = None
) -> dict:
	"""§6.3 'CLOSED | Reopen | ACTIVE or SCHEDULED'. One governed action with a
	reason and new availability dates — no separate propose/recommend/approve
	stages."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Closed":
		frappe.throw(_("Only a Closed context can be reopened"))
	if not (reason or "").strip():
		frappe.throw(_("A reason is required to reopen a PE/FY context"))
	if get_datetime(active_to) <= get_datetime(active_from):
		frappe.throw(_("The context availability end must be later than its start"), title="PEFY_DATES_INVALID")

	perm.require_reference_data_manager(actor)

	pe_status = frappe.db.get_value("Procuring Entity", ctx.procuring_entity, "status")
	fy_status = frappe.db.get_value("Financial Year", ctx.financial_year, "record_status")
	if pe_status != "Active" or fy_status != "Available":
		frappe.throw(_("Cannot reopen: the Procuring Entity or Financial Year is no longer in force"))

	due_now = get_datetime(active_from) <= now_datetime()
	ctx.context_status = "Active" if due_now else "Scheduled"
	ctx.active_from = active_from
	ctx.active_to = active_to
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, "reference_data.context.reopen", actor, {"reason": reason})
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}
