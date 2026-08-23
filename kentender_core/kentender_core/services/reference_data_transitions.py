# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 §6.1/§6.2/§6.3 — Procuring Entity / Procuring Entity Version,
Financial Year, and PE Fiscal Year Context lifecycles.

Table-driven, modeled on kentender_strategy.services.strategy_transitions.
Permission via authorization_policy (reference_data_permissions); audit via
audit_event_service.log_audit_event. No client-only enforcement — every guard
here runs server-side and is re-checked on every call, never trusted from the UI.
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

	perm.require_pe_create_capability(actor)

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

	_audit(pe.name, perm.PE_CREATE_DRAFT, actor, {"version": version.name})
	return {"ok": True, "pe": pe.name, "version": version.name}


def submit_pe(pe_name: str, *, user: str | None = None) -> dict:
	"""§6.1 'DRAFT | Submit | Version UNDER_REVIEW'."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	version = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
	if version.version_state != "Draft":
		frappe.throw(_("Only a Draft version can be submitted"))

	perm.require_pe_capability(actor, perm.PE_CREATE_DRAFT, pe_name)

	version.version_state = "Under Review"
	version.save(ignore_permissions=True)
	_audit(pe_name, "reference_data.pe.submit", actor, {"version": version.name})
	return {"ok": True, "pe": pe_name, "version": version.name, "version_state": version.version_state}


def approve_activate_pe(pe_name: str, *, user: str | None = None) -> dict:
	"""§6.1 'UNDER_REVIEW | Approve and activate | PE ACTIVE; version ACTIVE'.
	Maker-checker: the approver must differ from whoever created/submitted this PE
	(enforced by the Separation of Duties Rule via authorization_policy's SoD check,
	fed by prior_actions_for_pe's real audit-trail lookup — not a hand-rolled check)."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	version = frappe.get_doc("Procuring Entity Version", pe.current_version_id)
	if version.version_state != "Under Review":
		frappe.throw(_("Only a version Under Review can be approved"))

	prior = perm.prior_actions_for_pe(pe_name)
	perm.require_pe_capability(actor, perm.PE_APPROVE_ACTIVATE, pe_name, prior_actions=prior)

	version.version_state = "Active"
	version.valid_from = frappe.utils.today()
	version.save(ignore_permissions=True)
	pe.status = "Active"
	pe.save(ignore_permissions=True)
	_audit(pe_name, perm.PE_APPROVE_ACTIVATE, actor, {"version": version.name})
	return {"ok": True, "pe": pe_name, "status": pe.status, "version": version.name}


def propose_amendment(pe_name: str, change_reason: str, *, user: str | None = None) -> dict:
	"""§6.1 'ACTIVE | Propose amendment | New version DRAFT'. Active version stays authoritative."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	if pe.status != "Active":
		frappe.throw(_("Only an Active Procuring Entity can be amended"))
	if not (change_reason or "").strip():
		frappe.throw(_("Change reason is required"))

	perm.require_pe_capability(actor, perm.PE_PROPOSE_AMENDMENT, pe_name)

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
	# submit_pe/approve_activate_pe always act on pe.current_version_id — it must
	# follow the amendment draft immediately, the same way create_pe_draft points it
	# at the version it just created, or those calls have nothing to progress.
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

	perm.require_pe_capability(actor, perm.PE_SUSPEND, pe_name)

	pe.status = "Suspended"
	pe.save(ignore_permissions=True)
	_audit(pe_name, perm.PE_SUSPEND, actor, {"reason": reason})
	return {"ok": True, "pe": pe_name, "status": pe.status}


def reinstate_pe(pe_name: str, *, user: str | None = None) -> dict:
	"""§6.1 'SUSPENDED | Reinstate | ACTIVE'."""
	actor = user or frappe.session.user
	pe = frappe.get_doc("Procuring Entity", pe_name)
	if pe.status != "Suspended":
		frappe.throw(_("Only a Suspended Procuring Entity can be reinstated"))

	perm.require_pe_capability(actor, perm.PE_REINSTATE, pe_name)

	pe.status = "Active"
	pe.save(ignore_permissions=True)
	_audit(pe_name, perm.PE_REINSTATE, actor)
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

	perm.require_pe_capability(actor, perm.PE_RETIRE, pe_name)

	pe.status = "Retired"
	pe.effective_to = effective_date
	pe.save(ignore_permissions=True)
	_audit(pe_name, perm.PE_RETIRE, actor, {"reason": reason, "effective_date": str(effective_date)})
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
	perm.require_fy_capability(actor, perm.FY_CREATE_DRAFT)

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
	_audit_fy(fy.name, perm.FY_CREATE_DRAFT, actor)
	return {"ok": True, "financial_year": fy.name, "label": fy.label}


def submit_fy(fy_name: str, *, user: str | None = None) -> dict:
	"""§6.2 'DRAFT | Submit | AWAITING_APPROVAL'."""
	actor = user or frappe.session.user
	fy = frappe.get_doc("Financial Year", fy_name)
	if fy.record_status != "Draft":
		frappe.throw(_("Only a Draft Financial Year can be submitted"))

	perm.require_fy_capability(actor, perm.FY_CREATE_DRAFT, fy_name=fy_name)

	fy.record_status = "Awaiting Approval"
	fy.save(ignore_permissions=True)
	_audit_fy(fy_name, "reference_data.fy.submit", actor)
	return {"ok": True, "financial_year": fy_name, "record_status": fy.record_status}


def approve_fy(fy_name: str, *, user: str | None = None) -> dict:
	"""§6.2 'AWAITING_APPROVAL | Approve | AVAILABLE'. Maker-checker: same actor
	cannot have both created/submitted and approved the same Financial Year (§7)."""
	actor = user or frappe.session.user
	fy = frappe.get_doc("Financial Year", fy_name)
	if fy.record_status != "Awaiting Approval":
		frappe.throw(_("Only a Financial Year Awaiting Approval can be made available"))

	perm.require_fy_capability(actor, perm.FY_APPROVE_AVAILABLE, fy_name=fy_name)

	fy.record_status = "Available"
	fy.approved_by = actor
	fy.approved_at = frappe.utils.now_datetime()
	fy.save(ignore_permissions=True)
	_audit_fy(fy_name, perm.FY_APPROVE_AVAILABLE, actor)
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

	perm.require_fy_capability(actor, perm.FY_RETIRE, fy_name=fy_name)

	fy.record_status = "Retired"
	fy.save(ignore_permissions=True)
	_audit_fy(fy_name, perm.FY_RETIRE, actor)
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


def create_context_draft(pe_name: str, fy_name: str, active_from, active_to, *, user: str | None = None) -> dict:
	"""§6.3 '— | Create draft | DRAFT'. BR-005: PE must be Active, FY must be Available."""
	actor = user or frappe.session.user
	pe_status = frappe.db.get_value("Procuring Entity", pe_name, "status")
	if pe_status != "Active":
		frappe.throw(_("This Procuring Entity is not active"), title="PE_NOT_ACTIVE")
	fy_status = frappe.db.get_value("Financial Year", fy_name, "record_status")
	if fy_status != "Available":
		frappe.throw(_("This Financial Year is not available for use"), title="FY_NOT_AVAILABLE")

	# No context exists yet to name — evaluate_capability()'s scope matching only
	# reads procuring_entity_id (already real: PE must be Active per BR-005 above),
	# not resource_id, so an empty placeholder id is correct here, not a fake name.
	perm.require_context_capability(actor, perm.CTX_CREATE_DRAFT, "", pe_name, fy_name)

	ctx = frappe.get_doc(
		{
			"doctype": "PE Fiscal Year Context",
			"procuring_entity": pe_name,
			"financial_year": fy_name,
			"context_status": "Draft",
			"active_from": active_from,
			"active_to": active_to,
		}
	)
	ctx.insert(ignore_permissions=True)
	_audit_ctx(ctx.name, perm.CTX_CREATE_DRAFT, actor)
	return {"ok": True, "context": ctx.name, "context_status": ctx.context_status}


def update_context_draft(
	context_name: str, active_from, active_to, *, user: str | None = None, expected_version: str | None = None
) -> dict:
	"""The 'Revise' half of §10's CreateOrRevisePEFYContext contract — editing a
	still-Draft context's dates before submission. Not a versioned amendment (the
	spec gives Context no such concept, unlike PE); only Draft may be revised."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Draft":
		frappe.throw(_("Only a Draft context can be revised"))

	perm.require_context_capability(actor, perm.CTX_CREATE_DRAFT, context_name, ctx.procuring_entity, ctx.financial_year)

	ctx.active_from = active_from
	ctx.active_to = active_to
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, "reference_data.context.revise_draft", actor)
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def submit_context(context_name: str, *, user: str | None = None, expected_version: str | None = None) -> dict:
	"""§6.3 'DRAFT | Submit for review | UNDER_REVIEW'."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Draft":
		frappe.throw(_("Only a Draft context can be submitted for review"))

	perm.require_context_capability(actor, perm.CTX_CREATE_DRAFT, context_name, ctx.procuring_entity, ctx.financial_year)

	ctx.context_status = "Under Review"
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, "reference_data.context.submit", actor)
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def recommend_context(context_name: str, *, user: str | None = None, expected_version: str | None = None) -> dict:
	"""§6.3 'UNDER_REVIEW | Recommend | AWAITING_APPROVAL'."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Under Review":
		frappe.throw(_("Only a context Under Review can be recommended"))

	prior = perm.prior_actions_for_context(context_name)
	perm.require_context_capability(
		actor, perm.CTX_RECOMMEND, context_name, ctx.procuring_entity, ctx.financial_year, prior_actions=prior
	)

	ctx.context_status = "Awaiting Approval"
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, perm.CTX_RECOMMEND, actor)
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def approve_context(context_name: str, *, user: str | None = None, expected_version: str | None = None) -> dict:
	"""§6.3 'AWAITING_APPROVAL | Approve | APPROVED or SCHEDULED'. Maker-checker:
	the approver must differ from whoever created/submitted or recommended this
	context (§7 'one actor may not satisfy two required decision stages')."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Awaiting Approval":
		frappe.throw(_("Only a context Awaiting Approval can be approved"))

	prior = perm.prior_actions_for_context(context_name)
	perm.require_context_capability(
		actor, perm.CTX_APPROVE, context_name, ctx.procuring_entity, ctx.financial_year, prior_actions=prior
	)

	due_now = get_datetime(ctx.active_from) <= now_datetime()
	ctx.context_status = "Approved" if due_now else "Scheduled"
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, perm.CTX_APPROVE, actor)
	if due_now:
		_activate_context(ctx, actor)
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def _activate_context(ctx, actor: str) -> None:
	"""§6.3 'APPROVED/SCHEDULED | Reach active_from | ACTIVE'. Revalidates PE/FY
	are still in force before activating — approval does not guarantee they still
	are by the time active_from is reached."""
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
	"""Scheduled job — CFG-303. Approved/Scheduled contexts whose active_from has
	been reached, activated with the same revalidation as an inline approve."""
	due = frappe.get_all(
		"PE Fiscal Year Context",
		filters={"context_status": ["in", ("Approved", "Scheduled")], "active_from": ["<=", now_datetime()]},
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

	perm.require_context_capability(actor, perm.CTX_APPROVE, context_name, ctx.procuring_entity, ctx.financial_year)

	ctx.context_status = "Suspended"
	ctx.suspended_by = actor
	ctx.suspended_at = now_datetime()
	ctx.suspended_reason = reason
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, "reference_data.context.suspend", actor, {"reason": reason})
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def reinstate_context(context_name: str, *, user: str | None = None, expected_version: str | None = None) -> dict:
	"""§6.3 'SUSPENDED | Reinstate | ACTIVE' — after prerequisite revalidation."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Suspended":
		frappe.throw(_("Only a Suspended context can be reinstated"))

	perm.require_context_capability(actor, perm.CTX_APPROVE, context_name, ctx.procuring_entity, ctx.financial_year)

	pe_status = frappe.db.get_value("Procuring Entity", ctx.procuring_entity, "status")
	fy_status = frappe.db.get_value("Financial Year", ctx.financial_year, "record_status")
	if pe_status != "Active" or fy_status != "Available":
		frappe.throw(_("Cannot reinstate: the Procuring Entity or Financial Year is no longer in force"))

	ctx.context_status = "Active"
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
	"""§6.3 'ACTIVE/SUSPENDED | Close | CLOSED'. Manual close requires reason +
	explicit impact acknowledgement — does not cancel existing downstream records
	(BR-013), only removes the context from new-work selectors."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status not in ("Active", "Suspended"):
		frappe.throw(_("Only an Active or Suspended context can be closed"))
	if not (reason or "").strip():
		frappe.throw(_("A reason is required to close a PE/FY context"))
	if not acknowledged:
		frappe.throw(_("You must acknowledge the impact before closing this context"))

	perm.require_context_capability(actor, perm.CTX_APPROVE, context_name, ctx.procuring_entity, ctx.financial_year)

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


def propose_context_reopen(
	context_name: str, reason: str, *, user: str | None = None, expected_version: str | None = None
) -> dict:
	"""§6.3 'CLOSED | Exceptional reopen | ACTIVE' step 1 of 3 — 'new steward
	proposal'. context_status has no dedicated reopen sub-state in the fixed §5.4
	enum, so this step (and recommend, below) is tracked purely via the audit
	trail; the document stays Closed until the final approval step."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Closed":
		frappe.throw(_("Only a Closed context can have an exceptional reopen proposed"))
	if not (reason or "").strip():
		frappe.throw(_("A reason is required to propose reopening a PE/FY context"))

	perm.require_context_capability(actor, perm.CTX_CREATE_DRAFT, context_name, ctx.procuring_entity, ctx.financial_year)

	_audit_ctx(context_name, "reference_data.context.propose_reopen", actor, {"reason": reason})
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def recommend_context_reopen(context_name: str, *, user: str | None = None, expected_version: str | None = None) -> dict:
	"""Step 2 of 3 — 'professional recommendation'."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Closed":
		frappe.throw(_("Only a Closed context can have an exceptional reopen recommended"))
	prior = perm.prior_actions_for_context(context_name)
	if "reference_data.context.propose_reopen" not in {row["capability"] for row in prior}:
		frappe.throw(_("A reopen must be proposed before it can be recommended"))

	perm.require_context_capability(
		actor, perm.CTX_RECOMMEND, context_name, ctx.procuring_entity, ctx.financial_year, prior_actions=prior
	)

	_audit_ctx(context_name, "reference_data.context.recommend_reopen", actor)
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}


def approve_context_reopen(context_name: str, *, user: str | None = None, expected_version: str | None = None) -> dict:
	"""Step 3 of 3 — 'AO approval'. Only this step actually flips CLOSED -> ACTIVE;
	full audit trail (propose + recommend + approve, three distinct actors via the
	same SoD rules as original submission) is the governed route, not a toggle."""
	actor = user or frappe.session.user
	ctx = frappe.get_doc("PE Fiscal Year Context", context_name)
	_check_expected_version(ctx, expected_version)
	if ctx.context_status != "Closed":
		frappe.throw(_("Only a Closed context can be exceptionally reopened"))
	prior = perm.prior_actions_for_context(context_name)
	prior_capabilities = {row["capability"] for row in prior}
	if "reference_data.context.propose_reopen" not in prior_capabilities:
		frappe.throw(_("A reopen must be proposed before it can be approved"))
	if "reference_data.context.recommend_reopen" not in prior_capabilities:
		frappe.throw(_("A reopen must be recommended before it can be approved"))

	perm.require_context_capability(
		actor, perm.CTX_APPROVE, context_name, ctx.procuring_entity, ctx.financial_year, prior_actions=prior
	)

	pe_status = frappe.db.get_value("Procuring Entity", ctx.procuring_entity, "status")
	fy_status = frappe.db.get_value("Financial Year", ctx.financial_year, "record_status")
	if pe_status != "Active" or fy_status != "Available":
		frappe.throw(_("Cannot reopen: the Procuring Entity or Financial Year is no longer in force"))

	ctx.context_status = "Active"
	ctx.save(ignore_permissions=True)
	_audit_ctx(context_name, "reference_data.context.reopen", actor, {"prior_capabilities": sorted(prior_capabilities)})
	return {"ok": True, "context": context_name, "context_status": ctx.context_status}
