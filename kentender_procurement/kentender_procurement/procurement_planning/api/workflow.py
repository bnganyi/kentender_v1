# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B3/B4 / PP2 — Whitelisted Procurement Planning workflow actions.

Deprecated aliases (delegate to PP2): ``complete_package``, ``mark_ready_for_tender``, ``reject_package``.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.utils.data import parse_json

from kentender_procurement.procurement_planning.permissions import pp_policy, pp_scope
from kentender_procurement.procurement_planning.services.planning_audit_constants import (
	PACKAGE_CANCELLED as AUDIT_PACKAGE_CANCELLED,
	PLAN_ACTIVATED,
	PLAN_CANCELLED as AUDIT_PLAN_CANCELLED,
	PLAN_CLOSED as AUDIT_PLAN_CLOSED,
	PLAN_SUPERSEDED as AUDIT_PLAN_SUPERSEDED,
)
from kentender_procurement.procurement_planning.services.planning_audit_service import (
	record_planning_audit_event,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_CANCELLED,
	PKG_CONSUMED,
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PKG_READY_FOR_RELEASE,
	PKG_RELEASED,
	PKG_RETURNED,
	PLAN_ACTIVE,
	PLAN_CANCELLED,
	PLAN_CLOSED,
	PLAN_DRAFT,
	PLAN_SUPERSEDED,
)

_AUDIT_REASON_MAX = 800


def _require_id(value: str | None, label: str) -> str:
	name = (value or "").strip()
	if not name:
		frappe.throw(_("{0} is required.").format(label), title=_("Missing parameter"))
	return name


def _require_reason(reason: str | None, label: str) -> str:
	text = (reason or "").strip()
	if not text:
		frappe.throw(_("{0} is required.").format(label), title=_("Missing reason"))
	return text


def _truncate_audit(text: str) -> str:
	if len(text) <= _AUDIT_REASON_MAX:
		return text
	return text[:_AUDIT_REASON_MAX] + "…"


def _assert_status(doc, expected: str, doctype_label: str) -> None:
	if doc.status != expected:
		frappe.throw(
			_('{0} must be in status "{1}" for this action (current: {2}).').format(
				doctype_label, expected, doc.status or ""
			),
			title=_("Invalid state"),
		)


def _audit(doc, action: str, extra: str | None = None) -> None:
	lines = [f"[Workflow] {action}", f"User: {frappe.session.user}"]
	if extra:
		lines.append(f"Detail: {_truncate_audit(extra)}")
	doc.add_comment("Comment", text="\n".join(lines))


def _record_workflow_audit(
	*,
	event_type: str,
	object_type: str,
	object_code: str,
	from_state: str | None = None,
	to_state: str | None = None,
	reason: str | None = None,
	journey_code: str | None = None,
) -> None:
	record_planning_audit_event(
		event_type=event_type,
		object_type=object_type,
		object_code=object_code,
		from_state=from_state,
		to_state=to_state,
		reason=reason,
		journey_code=journey_code,
		actor=frappe.session.user,
	)


def _load_plan_read(plan_id: str):
	if not frappe.has_permission("Procurement Plan", "read", plan_id):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	doc = frappe.get_doc("Procurement Plan", plan_id)
	doc.check_permission("read")
	return doc


def _load_package_read(package_id: str):
	if not frappe.has_permission("Procurement Package", "read", package_id):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	doc = frappe.get_doc("Procurement Package", package_id)
	doc.check_permission("read")
	return doc


def _load_package_by_release_code(release_code: str):
	rc = _require_id(release_code, _("Planning Release Package"))
	handoff = frappe.db.get_value(
		"Procurement Handoff Card",
		{"handoff_code": rc},
		("source_object_code",),
		as_dict=True,
	)
	if not handoff or not handoff.get("source_object_code"):
		if frappe.db.exists("Procurement Handoff Card", rc):
			handoff = frappe.db.get_value(
				"Procurement Handoff Card",
				rc,
				("source_object_code",),
				as_dict=True,
			)
	if not handoff or not handoff.get("source_object_code"):
		frappe.throw(
			_("Planning release package was not found."),
			title=_("Release not found"),
		)
	return _load_package_read(str(handoff.get("source_object_code")))


def _parse_demand_ids(raw) -> list[str]:
	if raw is None:
		return []
	if isinstance(raw, (list, tuple, set)):
		return [str(x).strip() for x in raw if str(x).strip()]
	text = str(raw).strip()
	if not text:
		return []
	if text.startswith("["):
		parsed = parse_json(text)
		if isinstance(parsed, list):
			return [str(x).strip() for x in parsed if str(x).strip()]
		frappe.throw(_("demand_ids must be a JSON list."), title=_("Invalid parameter"))
	return [p for p in (s.strip() for s in text.split(",")) if p]


def _parse_apply_options(raw) -> dict:
	if raw is None or raw == "":
		return {}
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str):
		parsed = parse_json(raw)
		return parsed if isinstance(parsed, dict) else {}
	return {}


def _block_self_approval_package(doc) -> None:
	roles = set(frappe.get_roles(frappe.session.user))
	if "Administrator" in roles or "System Manager" in roles:
		return
	if (doc.created_by or "") and doc.created_by == frappe.session.user:
		frappe.throw(
			_("You cannot approve a procurement package you created (separation of duties)."),
			title=_("Not permitted"),
		)


@frappe.whitelist()
def activate_plan(plan_id: str | None = None):
	"""Draft → Active."""
	plan_id = _require_id(plan_id, _("Procurement Plan"))
	pp_scope.assert_may_act_on_procurement_plan(plan_id)
	doc = _load_plan_read(plan_id)
	_assert_status(doc, PLAN_DRAFT, _("Procurement Plan"))
	pp_policy.assert_may_run_plan_workflow("activate_plan", doc)
	doc.status = PLAN_ACTIVE
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)
	_audit(doc, "activate_plan")
	_record_workflow_audit(
		event_type=PLAN_ACTIVATED,
		object_type="Procurement Plan",
		object_code=doc.name,
		from_state=PLAN_DRAFT,
		to_state=PLAN_ACTIVE,
	)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def close_plan(plan_id: str | None = None):
	"""Active → Closed."""
	plan_id = _require_id(plan_id, _("Procurement Plan"))
	pp_scope.assert_may_act_on_procurement_plan(plan_id)
	doc = _load_plan_read(plan_id)
	_assert_status(doc, PLAN_ACTIVE, _("Procurement Plan"))
	pp_policy.assert_may_run_plan_workflow("close_plan", doc)
	doc.status = PLAN_CLOSED
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)
	_audit(doc, "close_plan")
	_record_workflow_audit(
		event_type=AUDIT_PLAN_CLOSED,
		object_type="Procurement Plan",
		object_code=doc.name,
		from_state=PLAN_ACTIVE,
		to_state=PLAN_CLOSED,
	)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def cancel_plan(plan_id: str | None = None, reason: str | None = None):
	"""Draft / Active → Cancelled."""
	plan_id = _require_id(plan_id, _("Procurement Plan"))
	reason = _require_reason(reason, _("Cancel reason"))
	pp_scope.assert_may_act_on_procurement_plan(plan_id)
	doc = _load_plan_read(plan_id)
	st = doc.status or ""
	if st not in (PLAN_DRAFT, PLAN_ACTIVE):
		frappe.throw(
			_('Procurement Plan must be Draft or Active for this action (current: {0}).').format(st),
			title=_("Invalid state"),
		)
	pp_policy.assert_may_run_plan_workflow("cancel_plan", doc)
	from_state = st
	doc.workflow_reason = reason
	doc.status = PLAN_CANCELLED
	doc.save(ignore_permissions=True)
	_audit(doc, "cancel_plan", reason)
	_record_workflow_audit(
		event_type=AUDIT_PLAN_CANCELLED,
		object_type="Procurement Plan",
		object_code=doc.name,
		from_state=from_state,
		to_state=PLAN_CANCELLED,
		reason=reason,
	)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def supersede_plan(plan_id: str | None = None):
	"""Active → Superseded."""
	plan_id = _require_id(plan_id, _("Procurement Plan"))
	pp_scope.assert_may_act_on_procurement_plan(plan_id)
	doc = _load_plan_read(plan_id)
	_assert_status(doc, PLAN_ACTIVE, _("Procurement Plan"))
	pp_policy.assert_may_run_plan_workflow("supersede_plan", doc)
	doc.status = PLAN_SUPERSEDED
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)
	_audit(doc, "supersede_plan")
	_record_workflow_audit(
		event_type=AUDIT_PLAN_SUPERSEDED,
		object_type="Procurement Plan",
		object_code=doc.name,
		from_state=PLAN_ACTIVE,
		to_state=PLAN_SUPERSEDED,
	)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def submit_package(package_id: str | None = None):
	"""Draft / Returned for Correction → In Review."""
	from kentender_procurement.procurement_planning.services.package_review_service import (
		submit_package_for_review,
	)

	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	pp_policy.assert_may_run_package_workflow("submit_package", doc)
	out = submit_package_for_review(package_id, frappe.session.user)
	return {"name": out.get("package_code") or package_id, "status": out.get("status")}


@frappe.whitelist()
def approve_package(package_id: str | None = None):
	"""In Review → Approved."""
	from kentender_procurement.procurement_planning.services.package_review_service import (
		record_package_review_decision,
	)

	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	pp_policy.assert_may_run_package_workflow("approve_package", doc)
	out = record_package_review_decision(
		package_id, {"decision": "Approved"}, frappe.session.user
	)
	return {"name": out.get("package_code") or package_id, "status": out.get("status")}


@frappe.whitelist()
def return_package(
	package_id: str | None = None,
	reason: str | None = None,
	required_correction: str | None = None,
):
	"""In Review → Returned for Correction."""
	from kentender_procurement.procurement_planning.services.package_review_service import (
		record_package_review_decision,
	)

	package_id = _require_id(package_id, _("Procurement Package"))
	reason = _require_reason(reason, _("Return reason"))
	doc = _load_package_read(package_id)
	pp_policy.assert_may_run_package_workflow("return_package", doc)
	out = record_package_review_decision(
		package_id,
		{
			"decision": "Returned for Correction",
			"reason": reason,
			"required_correction": required_correction,
		},
		frappe.session.user,
	)
	return {"name": out.get("package_code") or package_id, "status": out.get("status")}


@frappe.whitelist()
def request_clarification(package_id: str | None = None, message: str | None = None):
	"""In Review — record clarification request without changing package status."""
	from kentender_procurement.procurement_planning.services.package_review_service import (
		request_clarification_on_package,
	)

	package_id = _require_id(package_id, _("Procurement Package"))
	message = _require_reason(message, _("Clarification message"))
	doc = _load_package_read(package_id)
	pp_policy.assert_may_run_package_workflow("return_package", doc)
	out = request_clarification_on_package(package_id, message, frappe.session.user)
	return {"name": out.get("package_code") or package_id, "status": out.get("status")}


@frappe.whitelist()
def cancel_package(package_id: str | None = None, reason: str | None = None):
	"""In Review → Cancelled."""
	package_id = _require_id(package_id, _("Procurement Package"))
	reason = _require_reason(reason, _("Cancel reason"))
	pp_scope.assert_may_act_on_procurement_package(package_id)
	doc = _load_package_read(package_id)
	_assert_status(doc, PKG_IN_REVIEW, _("Procurement Package"))
	pp_policy.assert_may_run_package_workflow("cancel_package", doc)
	doc.workflow_reason = reason
	doc.status = PKG_CANCELLED
	doc.save(ignore_permissions=True)
	_audit(doc, "cancel_package", reason)
	_record_workflow_audit(
		event_type=AUDIT_PACKAGE_CANCELLED,
		object_type="Procurement Package",
		object_code=doc.name,
		from_state=PKG_IN_REVIEW,
		to_state=PKG_CANCELLED,
		reason=reason,
		journey_code=(doc.journey_code or None),
	)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def apply_template_to_demands(
	plan_id: str | None = None,
	template_id: str | None = None,
	demand_ids=None,
	actor: str | None = None,
	options=None,
):
	"""C2 — Create package(s) and lines from demands using a template (Draft/Active plan)."""
	from kentender_procurement.procurement_planning.services.planning_references import (
		resolve_demand_name,
		resolve_procurement_plan_name,
		resolve_procurement_template_name,
	)
	from kentender_procurement.procurement_planning.services.template_application import (
		apply_template_to_demands as _apply,
	)

	pp_policy.assert_may_apply_template_to_demands()

	plan_ref = _require_id(plan_id, _("Procurement Plan"))
	template_ref = _require_id(template_id, _("Procurement Template"))
	plan_resolved = resolve_procurement_plan_name(plan_ref)
	template_resolved = resolve_procurement_template_name(template_ref)
	plan_doc = _load_plan_read(plan_resolved)
	pp_scope.assert_may_act_on_procurement_plan(plan_doc)
	if not frappe.has_permission("Procurement Template", "read", template_resolved):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	dids = _parse_demand_ids(demand_ids)
	if not dids:
		frappe.throw(_("At least one demand is required."), title=_("Missing demands"))
	resolved_demands = [resolve_demand_name(d) for d in dids]
	for demand_name in resolved_demands:
		pp_scope.assert_may_act_on_demand(demand_name)
	opts = _parse_apply_options(options)
	if not opts and frappe.form_dict:
		opts = _parse_apply_options(frappe.form_dict.get("options"))
	return _apply(plan_resolved, template_resolved, resolved_demands, actor=actor, options=opts or None)


@frappe.whitelist()
def mark_ready_for_release(package_id: str | None = None):
	"""Approved → Ready for Release."""
	from kentender_procurement.procurement_planning.services.package_release_service import (
		mark_package_ready_for_release,
	)

	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	pp_policy.assert_may_run_package_workflow("mark_ready_for_release", doc)
	out = mark_package_ready_for_release(package_id, frappe.session.user)
	return {"name": out.get("package_code") or package_id, "status": out.get("status")}


@frappe.whitelist()
def release_package_to_tender(package_id: str | None = None):
	"""Ready for Release → Released to Tender (handoff + idempotent)."""
	from kentender_procurement.procurement_planning.services.package_release_service import (
		release_package_to_tender_management,
	)

	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	pp_policy.assert_may_run_package_workflow("release_package_to_tender", doc)
	out = release_package_to_tender_management(package_id, frappe.session.user)
	return {
		"name": out.get("package_code") or package_id,
		"status": out.get("status"),
		"release_code": out.get("release_code"),
		"handoff": out.get("handoff"),
		"already_released": out.get("action") == "recalled",
	}


@frappe.whitelist()
def mark_planning_release_consumed(
	release_code: str | None = None, tender_code: str | None = None
):
	"""Released to Tender → Consumed by Tender Management."""
	from kentender_procurement.procurement_planning.services.planning_release_consumption_service import (
		mark_planning_release_consumed as consume_release,
	)

	release_code = _require_id(release_code, _("Planning Release Package"))
	tender_code = _require_id(tender_code, _("TM2 Tender"))
	doc = _load_package_by_release_code(release_code)
	pp_policy.assert_may_mark_planning_release_consumed(doc)
	out = consume_release(release_code, tender_code, frappe.session.user)
	return {
		"release_code": out.get("release_code") or release_code,
		"tender_code": out.get("tender_code") or tender_code,
		"package_code": out.get("package_code"),
		"consumption_code": out.get("consumption_code"),
		"status": out.get("status"),
		"already_consumed": out.get("action") == "recalled",
	}


@frappe.whitelist()
def create_planning_correction_or_supersession(
	package_id: str | None = None, payload=None
):
	"""Apply governed post-release correction or supersession (P2-013)."""
	from kentender_procurement.procurement_planning.services.planning_correction_service import (
		create_planning_correction_or_supersession as _create,
	)

	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	pp_policy.assert_may_create_planning_correction(doc)
	raw = payload
	if isinstance(raw, str) and raw.strip():
		raw = parse_json(raw)
	if not isinstance(raw, dict):
		raw = {}
	out = _create(package_id, raw, frappe.session.user)
	return {
		"correction_code": out.get("correction_code"),
		"package_code": out.get("package_code"),
		"correction_type": out.get("correction_type"),
		"status": out.get("status"),
		"from_state": out.get("from_state"),
		"to_state": out.get("to_state"),
		"action": out.get("action"),
	}


# Back-compat aliases for callers not yet migrated (PP2 renames).
@frappe.whitelist()
def mark_ready_for_tender(package_id: str | None = None):
	return mark_ready_for_release(package_id)


@frappe.whitelist()
def complete_package(package_id: str | None = None):
	return submit_package(package_id)


@frappe.whitelist()
def reject_package(package_id: str | None = None, reason: str | None = None):
	return cancel_package(package_id, reason=reason)
