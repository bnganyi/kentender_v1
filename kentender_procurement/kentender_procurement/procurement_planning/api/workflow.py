# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""B3/B4 — Whitelisted Procurement Planning workflow actions (Cursor Pack B3).

Phase E1: loads use **read** where possible; ``pp_policy`` asserts role + state;
``doc.save(ignore_permissions=True)`` applies transitions when DocPerm write is
intentionally narrow (e.g. Planning Authority on Draft packages).
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
from frappe.utils.data import parse_json

from kentender_procurement.procurement_planning.permissions import pp_policy
from kentender_procurement.tender_management.services.planning_tender_handoff_xmv import (
	format_xmv_critical_message,
	validate_package_for_release_xmv,
)
from kentender_procurement.tender_management.services.release_procurement_package_to_tender import (
	package_has_release_tender,
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


def _assert_plan_submit_state(doc) -> None:
	st = doc.status or ""
	if st not in ("Draft", "Returned"):
		frappe.throw(
			_('Procurement Plan must be Draft or Returned for this action (current: {0}).').format(st),
			title=_("Invalid state"),
		)


def _audit(doc, action: str, extra: str | None = None) -> None:
	lines = [f"[Workflow] {action}", f"User: {frappe.session.user}"]
	if extra:
		lines.append(f"Detail: {_truncate_audit(extra)}")
	doc.add_comment("Comment", text="\n".join(lines))


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


def _block_self_approval_plan(doc) -> None:
	roles = set(frappe.get_roles(frappe.session.user))
	if "Administrator" in roles or "System Manager" in roles:
		return
	if (doc.created_by or "") and doc.created_by == frappe.session.user:
		frappe.throw(
			_("You cannot approve a procurement plan you created (separation of duties)."),
			title=_("Not permitted"),
		)


@frappe.whitelist()
def submit_plan(plan_id: str | None = None):
	"""Draft / Returned → Submitted."""
	plan_id = _require_id(plan_id, _("Procurement Plan"))
	doc = _load_plan_read(plan_id)
	_assert_plan_submit_state(doc)
	pp_policy.assert_may_run_plan_workflow("submit_plan", doc)
	doc.status = "Submitted"
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)
	_audit(doc, "submit_plan")
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def approve_plan(plan_id: str | None = None):
	"""Submitted → Approved."""
	plan_id = _require_id(plan_id, _("Procurement Plan"))
	doc = _load_plan_read(plan_id)
	_assert_status(doc, "Submitted", _("Procurement Plan"))
	pp_policy.assert_may_run_plan_workflow("approve_plan", doc)
	_block_self_approval_plan(doc)
	doc.status = "Approved"
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)
	_audit(doc, "approve_plan")
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def return_plan(plan_id: str | None = None, reason: str | None = None):
	"""Submitted → Returned."""
	plan_id = _require_id(plan_id, _("Procurement Plan"))
	reason = _require_reason(reason, _("Return reason"))
	doc = _load_plan_read(plan_id)
	_assert_status(doc, "Submitted", _("Procurement Plan"))
	pp_policy.assert_may_run_plan_workflow("return_plan", doc)
	doc.workflow_reason = reason
	doc.status = "Returned"
	doc.save(ignore_permissions=True)
	_audit(doc, "return_plan", reason)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def reject_plan(plan_id: str | None = None, reason: str | None = None):
	"""Submitted → Rejected."""
	plan_id = _require_id(plan_id, _("Procurement Plan"))
	reason = _require_reason(reason, _("Reject reason"))
	doc = _load_plan_read(plan_id)
	_assert_status(doc, "Submitted", _("Procurement Plan"))
	pp_policy.assert_may_run_plan_workflow("reject_plan", doc)
	doc.workflow_reason = reason
	doc.status = "Rejected"
	doc.save(ignore_permissions=True)
	_audit(doc, "reject_plan", reason)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def lock_plan(plan_id: str | None = None):
	"""Approved → Locked."""
	plan_id = _require_id(plan_id, _("Procurement Plan"))
	doc = _load_plan_read(plan_id)
	_assert_status(doc, "Approved", _("Procurement Plan"))
	pp_policy.assert_may_run_plan_workflow("lock_plan", doc)
	doc.status = "Locked"
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)
	_audit(doc, "lock_plan")
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def complete_package(package_id: str | None = None):
	"""Draft / Returned → Completed."""
	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	st = doc.status or ""
	if st not in ("Draft", "Returned"):
		frappe.throw(
			_('Procurement Package must be Draft or Returned for this action (current: {0}).').format(st),
			title=_("Invalid state"),
		)
	pp_policy.assert_may_run_package_workflow("complete_package", doc)
	doc.workflow_reason = None
	doc.status = "Completed"
	doc.save(ignore_permissions=True)
	_audit(doc, "complete_package")
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def submit_package(package_id: str | None = None):
	"""Completed → Submitted."""
	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	_assert_status(doc, "Completed", _("Procurement Package"))
	pp_policy.assert_may_run_package_workflow("submit_package", doc)
	doc.status = "Submitted"
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)
	_audit(doc, "submit_package")
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def approve_package(package_id: str | None = None):
	"""Submitted → Approved."""
	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	_assert_status(doc, "Submitted", _("Procurement Package"))
	pp_policy.assert_may_run_package_workflow("approve_package", doc)
	_block_self_approval_package(doc)
	doc.status = "Approved"
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)
	_audit(doc, "approve_package")
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def return_package(package_id: str | None = None, reason: str | None = None):
	"""Submitted → Returned."""
	package_id = _require_id(package_id, _("Procurement Package"))
	reason = _require_reason(reason, _("Return reason"))
	doc = _load_package_read(package_id)
	_assert_status(doc, "Submitted", _("Procurement Package"))
	pp_policy.assert_may_run_package_workflow("return_package", doc)
	doc.workflow_reason = reason
	doc.status = "Returned"
	doc.save(ignore_permissions=True)
	_audit(doc, "return_package", reason)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def reject_package(package_id: str | None = None, reason: str | None = None):
	"""Submitted → Rejected."""
	package_id = _require_id(package_id, _("Procurement Package"))
	reason = _require_reason(reason, _("Reject reason"))
	doc = _load_package_read(package_id)
	_assert_status(doc, "Submitted", _("Procurement Package"))
	pp_policy.assert_may_run_package_workflow("reject_package", doc)
	doc.workflow_reason = reason
	doc.status = "Rejected"
	doc.save(ignore_permissions=True)
	_audit(doc, "reject_package", reason)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def apply_template_to_demands(
	plan_id: str | None = None,
	template_id: str | None = None,
	demand_ids=None,
	actor: str | None = None,
	options=None,
):
	"""C2 — Create package(s) and lines from demands using a template (Draft plan only).

	``plan_id`` / ``template_id`` may be internal ``name`` or business ``plan_code`` / ``template_code``.
	``demand_ids`` entries may be internal Demand ``name`` or business ``demand_id``.
	Optional ``options`` JSON dict (e.g. ``package_code`` / ``package_name`` for deterministic seed).
	"""
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
	_load_plan_read(plan_resolved)
	if not frappe.has_permission("Procurement Template", "read", template_resolved):
		frappe.throw(_("Not permitted."), frappe.PermissionError)
	dids = _parse_demand_ids(demand_ids)
	if not dids:
		frappe.throw(_("At least one demand is required."), title=_("Missing demands"))
	resolved_demands = [resolve_demand_name(d) for d in dids]
	opts = _parse_apply_options(options)
	if not opts and frappe.form_dict:
		opts = _parse_apply_options(frappe.form_dict.get("options"))
	return _apply(plan_resolved, template_resolved, resolved_demands, actor=actor, options=opts or None)


@frappe.whitelist()
def mark_ready_for_tender(package_id: str | None = None):
	"""Approved → Ready for Tender."""
	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	_assert_status(doc, "Approved", _("Procurement Package"))
	pp_policy.assert_may_run_package_workflow("mark_ready_for_tender", doc)
	doc.status = "Ready for Tender"
	doc.workflow_reason = None
	doc.save(ignore_permissions=True)
	_audit(doc, "mark_ready_for_tender")
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def release_package_to_tender(package_id: str | None = None):
	"""Ready for Tender → Released to Tender (handoff + idempotent)."""
	from kentender_procurement.procurement_planning.services.package_completeness import (
		get_package_completeness_blockers,
	)
	from kentender_procurement.procurement_planning.services.tendering_handoff import (
		build_release_payload,
		deliver_procurement_package_release,
	)

	package_id = _require_id(package_id, _("Procurement Package"))
	doc = _load_package_read(package_id)
	if (doc.status or "") == "Released to Tender":
		_audit(doc, "release_package_to_tender", "duplicate call (already released)")
		return {"name": doc.name, "status": doc.status, "already_released": True}
	_assert_status(doc, "Ready for Tender", _("Procurement Package"))
	pp_policy.assert_may_run_package_workflow("release_package_to_tender", doc)
	plan_st = frappe.db.get_value("Procurement Plan", doc.plan_id, "status")
	if plan_st != "Approved":
		frappe.throw(
			_("Procurement Plan must be Approved before release to tender."),
			title=_("Plan not approved"),
		)
	blockers = get_package_completeness_blockers(doc)
	if blockers:
		frappe.throw(
			_("Package is not complete: {0}").format("; ".join(blockers)),
			title=_("Package not complete"),
		)
	xmv = validate_package_for_release_xmv(doc)
	if xmv.has_critical():
		frappe.throw(
			format_xmv_critical_message(xmv),
			title=_("Planning-to-tender validation"),
		)
	payload = build_release_payload(doc)
	deliver_procurement_package_release(payload)
	if not package_has_release_tender(doc.name):
		frappe.throw(
			_(
				"No Procurement Tender was linked to this package after the release handoff. "
				"Check Error Log for release-to-tender hook messages."
			),
			title=_("Handoff incomplete"),
		)
	try:
		frappe.local.pp_allow_package_release_to_tender = True
		doc.status = "Released to Tender"
		doc.released_to_tender_at = now_datetime()
		doc.workflow_reason = None
		doc.save(ignore_permissions=True)
	finally:
		if hasattr(frappe.local, "pp_allow_package_release_to_tender"):
			delattr(frappe.local, "pp_allow_package_release_to_tender")
	_audit(doc, "release_package_to_tender", f"payload_keys={list(payload.keys())}")
	return {"name": doc.name, "status": doc.status, "handoff": payload}
